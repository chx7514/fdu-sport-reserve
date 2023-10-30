from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.options import Options
from selenium.common import exceptions

import cv2
from PIL import Image

import base64
import re
import uuid
import os
import numpy as np

import time
import ddddocr

abs_path = os.path.abspath(__file__)

def iselement(browser, selector):
    """
    实现判断元素是否存在
    :param browser: 浏览器对象
    :param xpaths: xpaths表达式
    :param istest: 如果为True,如果元素存在返回内容将为元素文本内容
    :return: 是否存在
    """
    try:
        target = browser.find_element(By.CSS_SELECTOR, selector)
    except exceptions.NoSuchElementException:
        return False
    else:
        return target

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
    filename = abs_path + "{}.{}".format(uuid.uuid4(), ext)
    with open(filename, "wb") as f:
        f.write(img)

    return filename

def ele_coor(ele):   #定义了一个方法，此方法的作用是传入一个元素，返回此元素左上角和右下角的坐标
    elem_posi = ele.location   #将元素左上角的位置赋值给 elem_posi
    elem_size = ele.size       #将元素的大小赋值给elem_size
    right = elem_posi["x"] + elem_size["width"]  # 元素左上角x + 元素宽 = 元素右下角x坐标
    bottom = elem_posi["y"] + elem_size["height"] #元素左上角y + 元素搞 = 元素右下角y坐标
    coor=(elem_posi["x"],elem_posi["y"],right,bottom) #将左上角x，y，右下角x，y 写成一个元组
    return coor   # 将元组返回给调用者

def pass_image_captcha(browser):
    url = abs_path + 'captcha.png'
    # img_block = WebDriverWait(browser, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#captchaImg")))
    img_block = browser.find_element(By.CSS_SELECTOR, "#captchaImg")
    browser.save_screenshot(url)
    img = Image.open(url)  
    img = img.crop(ele_coor(img_block))  
    img.save(url)
    
    ocr = ddddocr.DdddOcr()
    with open(url, 'rb') as f:
        img_byte = f.read()
    result = ocr.classification(img_byte)
    
    browser.find_element(By.CSS_SELECTOR, '#captchaResponse').send_keys(result)
    browser.find_element(By.CSS_SELECTOR, '#casLoginForm > p:nth-child(4) > button').click()
    
    os.remove(url)

def pass_block_captcha(browser):
    bg_block = WebDriverWait(browser, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservation-step-two > div.mask > div > div.verifybox-bottom > div > div.verify-img-out > div > img")))
    tp_block = browser.find_element(By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservation-step-two > div.mask > div > div.verifybox-bottom > div > div.verify-bar-area > div > div > div > img")
    url_bg = bg_block.get_attribute("src")
    url_tp = tp_block.get_attribute("src")

    path_bg = decode_image(url_bg)
    path_tp = decode_image(url_tp)

    bg = cv2.imread(path_bg)
    tp = cv2.imread(path_tp)

    tp_range = np.where(tp[:,:,0].sum(1) > 0)
    up, down = tp_range[0][0], tp_range[0][-1] + 1

    # res = cv2.matchTemplate(bg[up:down,:,:], tp[up:down,:,:], cv2.TM_CCOEFF_NORMED)
    # c1, c2, (dx1, _), (dx2, _) = cv2.minMaxLoc(res)
    # dx = dx1 if abs(c1) > abs(c2) else dx2
    canny = cv2.Canny(bg[up:down, :, :], 300, 300)

    contours, _ = cv2.findContours(canny, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    dx = 0
    min_d = 50
    for _, contour in enumerate(contours):
        x, _, w, h = cv2.boundingRect(contour)
        if max(abs(w - 50), abs(h - down + up)) < min_d:
            min_d = max(abs(w - 50), abs(h - down + up))
            dx = x
                
    # print(dx)

    btn = browser.find_element(By.CSS_SELECTOR, 'body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservation-step-two > div.mask > div > div.verifybox-bottom > div > div.verify-bar-area > div > div > i')
    move = ActionChains(browser)
    move.drag_and_drop_by_offset(btn, dx+5, 0)
    move.perform()

    os.remove(path_bg)
    os.remove(path_tp)


if __name__ == '__main__':
    # print(os.path.abspath(__file__))
    # 调用webdriver包的Edge类，返回edge浏览器对象
    # user_data_dir
    edge_options = Options()
    # edge_options.add_argument('--headless')
    # edge_options.add_argument('--no-sandbox')
    # edge_options.add_argument('--disable-dev-shm-usage')
    # edge_options.add_argument('--window-size=4000,1600')
    edge_options.add_argument(f'user-data-dir={user_data_dir}')
    browser = webdriver.Edge(options=edge_options)
    browser.maximize_window()
    
    # 登录
    browser.get("https://ggtypt.nju.edu.cn/venue-server/loginto")
    time.sleep(1)
    pass_image_captcha(browser)
    # 四组团羽毛球场
    browser.get("https://ggtypt.nju.edu.cn/venue/venue-reservation/126")
    # for test
    # browser.get("https://ggtypt.nju.edu.cn/venue/venue-reservation/132")
    btn = iselement(browser, "#scrollTable > div > table > thead > tr > td:nth-child(6) > div > span > i")
    if btn:
        btn.click()
    blocks = browser.find_elements(By.XPATH, '//*[@id="scrollTable"]/div/table/tbody/tr')
    # blocks = browser.find_elements(By.CLASS_NAME, 'freeBorder')
    for block in blocks[-2::-1]:
        last = block.find_elements(By.TAG_NAME, 'td')
        if last[-1].get_attribute('class') != 'freeBorder':
            continue
        last[-1].click()
        
        browser.find_element(By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservationStep1 > div:nth-child(5) > label > span > input").click()
        browser.find_element(By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservationStep1 > div.checkStep > div > div:nth-child(2)").click()            
            
        # 跳到选择同伴
        btn = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservation-step-two > form > div > div.ivu-form-item > div > div > label > span:nth-child(2)")))
        btn.click()
        browser.find_element(By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservation-step-two > div.checkStep > div > div:nth-child(2)").click()
           
        pass_block_captcha(browser)
        time.sleep(1)
        while iselement(browser, 'body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div.reservation-step-two > div.mask > div > div.verifybox-bottom > div > div.verify-bar-area > div > div > i'):
            pass_block_captcha(browser)
            time.sleep(1)
            
        btn = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.fullHeight > div > div > div.coach > div.venueSiteWrap > div > div:nth-child(3) > div.payHandle > div:nth-child(2) > button")))
        btn.click()
        break
    # time.sleep(4)
    browser.quit()
