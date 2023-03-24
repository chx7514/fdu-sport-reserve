from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

import cv2
import base64
import re
import uuid
import os
import sys

def decode_image(src):
    """
    解码图片
    :param src: 图片编码
        eg:
            src="data:image/gif;base64,R0lGODlhMwAxAIAAAAAAAP///
                yH5BAAAAAAALAAAAAAzADEAAAK8jI+pBr0PowytzotTtbm/DTqQ6C3hGX
                ElcraA9jIr66ozVpM3nseUvYP1UEHF0FUUHkNJxhLZfEJNvol06tzwrgd
                LbXsFZYmSMPnHLB+zNJFbq15+SOf50+6rG7lKOjwV1ibGdhHYRVYVJ9Wn
                k2HWtLdIWMSH9lfyODZoZTb4xdnpxQSEF9oyOWIqp6gaI9pI1Qo7BijbF
                ZkoaAtEeiiLeKn72xM7vMZofJy8zJys2UxsCT3kO229LH1tXAAAOw=="

    :return: str 保存到本地的文件名
    """
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
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # plt.imshow(image)
    # plt.show()

    canny = cv2.Canny(image, 300, 300)
    # plt.imshow(canny)
    # plt.show()

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
    
    print(dx, dy)
    
    # plt.imshow(image)
    # plt.show()

    btn = browser.find_element(By.CLASS_NAME, 'slider-btn')
    move = ActionChains(browser)
    move.click_and_hold(btn)
    move.move_by_offset((dx-5)/1.75, 0)
    move.release(btn)
    move.perform()
    os.remove(path)


if __name__ == '__main__':
    env_dist = os.environ

    username = env_dist.get('USER_ID')
    password = env_dist.get('PASSWORD')
    reserve_time = sys.argv[1]
    weekday = sys.argv[2]
    
    print(username)
    print(password)

    # 调用webdriver包的Chrome类，返回chrome浏览器对象
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)

    # 正大标场
    browser.get("https://elife.fudan.edu.cn/public/front/loadOrderForm_ordinary2.htm?type=resource&serviceContent.id=2c9c486e4f821a19014f82418a900004")

    browser.find_element(By.CLASS_NAME, 'xndl').click()
    browser.find_element(By.NAME, 'username').send_keys(username)
    browser.find_element(By.NAME, 'password').send_keys(password)
    browser.find_element(By.ID, 'idcheckloginbtn').click()

    # 星期几
    browser.switch_to.frame(0)
    browser.find_element(By.ID, 'one' + weekday).click()

    block = browser.find_element(By.XPATH, "//font[text()='" + reserve_time + "']/../..")
    
    block.find_element(By.TAG_NAME, 'img').click()
    browser.find_element(By.ID, 'verify_button').click()

    error = True
    while error:
        try:
            pass_captcha()
            browser.implicitly_wait(1)
            browser.find_element(By.ID, 'btn_sub').click()
            error = False
            print("预约成功")
        except:
            print("识别失败，重新识别")

    browser.quit()
