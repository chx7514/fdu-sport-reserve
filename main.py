from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

import cv2
import smtplib

import base64
import re
import uuid
import os
from datetime import datetime, timedelta
import sys

def decode_image(src):
    # 1、信息提取
    result = re.search("data:image/(?P<ext>.*?);base64,(?P<data>.*)", src, re.DOTALL)
    if result:
        ext = result.groupdict().get("ext")
        data = result.groupdict().get("data")

    else:
        raise Exception("Do not parse!")

    # 2、base64解码
    img = base64.urlsafe_b64decode(data)

    # 3、二进制文件保存
    filename = "{}.{}".format(uuid.uuid4(), ext)
    with open(filename, "wb") as f:
        f.write(img)

    return filename


def pass_captcha():
    img_block = browser.find_element(By.ID, "scream")
    url = img_block.get_attribute("src")

    path = decode_image(url)

    image = cv2.imread(path)

    canny = cv2.Canny(image, 300, 300)

    contours, hierarchy = cv2.findContours(canny, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    dx, dy = 0, 0
    min_d = 50
    for _, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        if max(abs(w-36),abs(h-43)) < min_d:
            min_d = max(abs(w-36), abs(h-43))
            dx = x
            dy = y
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    # print(dx, dy)
    
    # plt.imshow(image)
    # plt.show()

    btn = browser.find_element(By.CLASS_NAME, 'slider-btn')
    move = ActionChains(browser)
    move.drag_and_drop_by_offset(btn, (dx-5)/1.75, 0)
    move.perform()
    os.remove(path)


if __name__ == '__main__':

    # 填入信息
    username = ''
    password = ''
    try:
        delta = sys.argv[1]
    except:
        delta = 2

    # 调用webdriver包的Chrome类，返回chrome浏览器对象
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=4000,1600')
    s = Service('/usr/bin/chromedriver')
    browser = webdriver.Chrome(service=s, options=chrome_options)

    # 正大标场
    browser.get("https://elife.fudan.edu.cn/public/front/loadOrderForm_ordinary2.htm?type=resource&serviceContent.id=2c9c486e4f821a19014f82418a900004")
    # 江湾
    # browser.get("https://elife.fudan.edu.cn/public/front/loadOrderForm_ordinary2.htm?type=resource&serviceContent.id=8aecc6ce749544fd01749a31a04332c2")

    browser.find_element(By.CLASS_NAME, 'xndl').click()
    browser.find_element(By.NAME, 'username').send_keys(username)
    browser.find_element(By.NAME, 'password').send_keys(password)
    browser.find_element(By.ID, 'idcheckloginbtn').click()

    # 几天后
    browser.switch_to.frame(0)
    reserve_day = datetime.now() + timedelta(days=int(delta))
    weekday = reserve_day.weekday()
    print('=================================\n预约日期:', reserve_day.strftime("%Y-%m-%d"))
    print('当前时间:', datetime.now())
    
    browser.execute_script("javascript:goToDate('" + reserve_day.strftime("%Y-%m-%d") + "');")

    try:
        blocks = browser.find_elements(By.XPATH, "//font[contains(text(),':00')]/../..")
    except:
        print("当天无可预约场馆")
        print(datetime.now())
        browser.quit()
        sys.exit(0)

    flag = True
    for block in blocks[::-1]:
        date_data = block.text
        try:
            block.find_element(By.TAG_NAME, 'img').click()
            browser.find_element(By.ID, 'verify_button').click()
        except:
            continue
        
        flag = False
        while True:
            pass_captcha()
            try:
                btn = WebDriverWait(browser, 1000).until(EC.element_to_be_clickable((By.ID, 'btn_sub')))
                btn.click()
                try:
                    browser.switch_to.alert.accept()
                except:
                    pass
                WebDriverWait(browser, 1000).until(EC.staleness_of(btn))
                print("<<< 预约成功 >>>")

                EMAILS = [""]  # Receive error notifications by email
                YOUR_EMAIL = ""  # Account to send email from
                EMAIL_PASSWORD = ""  # Password for the email account
                message = "Subject: YuMaoQiu " + reserve_day.strftime("%Y-%m-%d") + ' ' + date_data[:5] + '-' + date_data[6:11]
                connection = smtplib.SMTP_SSL("smtp.qq.com", 465)
                try:
                    connection.ehlo()
                    connection.login(YOUR_EMAIL, EMAIL_PASSWORD)
                    connection.sendmail(YOUR_EMAIL, EMAILS, message)
                finally:
                    connection.quit()
                break
            except:
                print("识别失败，重新识别")
                browser.find_element(By.CLASS_NAME, 're-btn').click()
        break

    if flag:
        print("当天已约满")

    browser.quit()
