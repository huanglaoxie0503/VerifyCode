# -*- coding: utf-8 -*-
import time
import json
import os
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

THRESHOLD = 60
LEFT = 60
BORDER = 6
Location = {}


class Crack(object):
    def __init__(self):
        self.keywords = "中国平安保险（集团）股份有限公司"
        self.base_url = 'https://www.cods.org.cn/'
        self.browser = webdriver.Chrome()
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, 20)

    # def __del__(self):
    #     self.browser.close()
    #     self.browser.quit()

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        return slider

    def get_position(self, is_full):
        full_bg = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "geetest_canvas_fullbg")))
        # time.sleep(2)

        if is_full:
            self.browser.execute_script("arguments[0].setAttribute(arguments[1], arguments[2])", full_bg, "style", "")
            location = full_bg.location
            global Location
            Location = location
        else:
            self.browser.execute_script("arguments[0].setAttribute(arguments[1], arguments[2])", full_bg, "style",
                                        "display: none")
            location = Location

        # 获取验证码x,y轴坐标
        location = location
        # {'x': 553, 'y': 173}
        # 获取验证码的长宽
        size = full_bg.size
        # 写成我们需要截取的位置坐标
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']

        return (top, bottom, left, right)

    def get_screenshot(self):
        """
         获取网页截图
        :return: 返回截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        return Image.open(BytesIO(screenshot))

    def get_geetest_image(self, name, is_full):
        top, bottom, left, right = self.get_position(is_full)
        print("{0}:验证码位置".format(name), top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save(name)
        return captcha

    def get_geetest_image_02(self):
        # image = self.browser.find_element_by_class_name('geetest_canvas_fullbg')
        image = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "geetest_canvas_fullbg")))
        # 获取验证码x,y轴坐标
        location = {'x': 553, 'y': 173}  # image.location
        # {'x': 553, 'y': 173}
        # 获取验证码的长宽
        size = image.size
        # 写成我们需要截取的位置坐标
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        print((left, top, right, bottom))
        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save("captcha2.png")
        return captcha

    def get_gap(self, image1, image2):
        for i in range(LEFT, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    return i
        return LEFT

    def is_pixel_equal(self, image1, image2, x, y):
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        if abs(pixel1[0] - pixel2[0]) < THRESHOLD and abs(pixel1[1] - pixel2[1]) < THRESHOLD and abs(
                pixel1[2] - pixel2[2]) < THRESHOLD:
            return True
        else:
            return False

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 1 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正50
                a = 50
            else:
                # 加速度为负-10
                a = -10
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def search_open(self):
        """
        打开网页，进入搜索界面，通过搜索打开验证码
        """
        self.browser.get(self.base_url)
        time.sleep(3)
        self.browser.find_element_by_id('checkContent_index').clear()
        self.browser.find_element_by_id('checkContent_index').send_keys(self.keywords)
        time.sleep(5)
        self.browser.find_element_by_id('checkBtn').click()

    def run(self):
        # 输入搜索关键词、打开验证码页面
        self.search_open()
        # 获取验证码图片
        print('开始获取验证码')
        # 获取带缺口的验证码图片
        # image2 = self.get_geetest_image_02()
        # 获取不带缺口的验证码图片
        image1 = self.get_geetest_image("captcha1.png", True)
        image2 = self.get_geetest_image("captcha2.png", False)
        gap = self.get_gap(image1, image2)
        print("缺口位置", gap)
        # 减去缺口位移
        gap -= BORDER
        # 获取移动轨迹
        track = self.get_track(gap)
        print('滑动轨迹', track)
        # 拖动滑块
        slider = self.get_slider()
        self.move_to_gap(slider, track)
        time.sleep(3)
        # 判断验证码是否识别成功的标志是url里是否包含参数geetest_challenge
        post = {}
        if "geetest_challenge" in self.browser.current_url:
            print("验证码识别成功")
            cookie_items = self.browser.get_cookies()

            # 获取到的cookies是列表形式，将cookies转成json形式并存入本地名为cookie的文本中
            for cookie_item in cookie_items:
                post[cookie_item['name']] = cookie_item['value']
            cookie_str = json.dumps(post)
            with open(r"../cookie/cookie.txt", 'w+', encoding='utf-8') as f:
                f.write(cookie_str)
            self.browser.quit()
        else:
            print("验证码识别失败")
            self.run()


if __name__ == '__main__':
    crack = Crack()
    crack.run()
