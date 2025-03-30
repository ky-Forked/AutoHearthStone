import base64
import io
import re
import sys
import threading
import time
from typing import Tuple, Literal, Union

import numpy
import pyautogui
import pygame
import pynput.keyboard
import torch
import win32api
import win32con
import win32gui
from paddleocr import PaddleOCR
from pynput import keyboard
from ultralytics import YOLO

BASE64_ICON = "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"


class AutoBattleGrounds:
    def __init__(self, size: Tuple[int, int], object_model_path: str, hand_model_path: str, card_model_path: str,
                 threshold: float = 0.5, drag_duration: int = 0.3, interval: int = 1, enable_sort: bool = False):
        # 窗口及绘制相关属性
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.screen = None
        self.size = size
        self.width, self.height = size
        self.transparent_color = (255, 0, 128)
        self.icon = None
        self.label_font_size = 20
        self.box_border_size = 2
        self.box_border_color = (0, 255, 0)
        # ui属性
        self.key_map = {"pause": pynput.keyboard.KeyCode.from_char("p")}
        self.listener = keyboard.Listener(on_press=self.handle_key_pressed)
        # 模型相关属性
        self.objects_model_path = object_model_path
        self.hand_model_path = hand_model_path
        self.card_model_path = card_model_path
        self.ocr = None
        self.hand_model = None
        self.objects_model = None
        self.card_model = None
        self.threshold = threshold
        # 自动操作相关属性
        self.drag_duration = drag_duration
        self.interval = interval
        self.enable_sort = enable_sort
        pyautogui.FAILSAFE = False
        # 处理线程
        self.process_thread = threading.Thread(target=self.process, name="ProcessThread")
        # 运行时变量
        self.state = None
        self.minions = []
        self.taverns = []
        self.buttons = None
        self.bob = None
        self.hero = None
        self.hands = []
        self.skills = None
        self.sequence = None
        self.is_done = False
        self.is_paused = True
        self.is_sorted = False


    def process(self):
        """
        逻辑处理函数，负责检测，执行操作
        :return:
        """
        self.load_models()
        self.listener.start()
        self.clear()
        while not self.is_done:
            time.sleep(self.interval)
            # pause
            if self.is_paused:
                self.pause()
                continue
            # 主逻辑
            # 识别部分
            self.clear()
            screenshot = pyautogui.screenshot()
            results = self.detect_objects(screenshot)
            results.sort(key=lambda x: x['conf'], reverse=True)
            self.state = self.get_state(results, screenshot)
            if self.state != "Recruit":
                continue
            self.minions = self.get_minions(results)
            self.taverns = self.get_taverns(results)
            self.draw_minions()
            self.draw_taverns()
            self.skills = self.get_skills(results)
            self.buttons = self.get_buttons(results)
            self.bob = self.get_bob(results)
            self.hero = self.get_hero(results)
            self.hands = self.detect_hands(screenshot)
            operation = self.get_operation(results, screenshot)
            self.sequence = self.get_sequence(results, screenshot)
            if not operation or (operation.startswith("结束回合") and self.is_sorted):
                continue
            # 执行操作
            self.execute_operation(operation)
            pyautogui.moveTo(10, 100)  # 鼠标复位防止遮挡

    def init_window(self):
        """
        初始化窗口
        :return:
        """
        global BASE64_ICON
        pygame.init()
        pygame.display.set_caption("AutoHearthStone-Battlegrounds")
        icon_data = base64.b64decode(BASE64_ICON)
        self.icon = pygame.image.load(io.BytesIO(icon_data))
        pygame.display.set_icon(pygame.transform.scale(self.icon, (64, 64)))
        self.screen = pygame.display.set_mode(self.size)
        # 透明窗口设置
        hwnd = pygame.display.get_wm_info()['window']
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.transparent_color), 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(hwnd, -1, 0, 0, self.width, self.height, 3)
        self.clear()

    def load_models(self):
        """
        加载模型
        :return:
        """
        start_time = time.time()
        self.loading_log("Loading PaddleOCR...")
        self.ocr = PaddleOCR(lang='ch')
        self.loading_log("Loading hand model...")
        self.hand_model = YOLO(self.hand_model_path)
        self.loading_log("Loading objects model...")
        self.objects_model = YOLO(self.objects_model_path)
        self.loading_log("Loading card model...")
        self.card_model = YOLO(self.card_model_path)
        end_time = time.time()
        self.loading_log(f"All models loaded! ({end_time - start_time:.2f} seconds used)")
        time.sleep(2)
        self.loading_log("Press p to pause automatic operation.")
        time.sleep(2)
        self.loading_log("Enjoy! @Joooook")
        time.sleep(2)

    def run(self):
        """
        运行主函数
        :return:
        """
        self.init_window()
        self.process_thread.start()
        while not self.is_done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_done = True
                    pygame.quit()
                    sys.exit()
            self.display_info()
            pygame.display.update()

    def pause(self):
        """
        暂停绘制
        :return:
        """
        self.screen.fill(self.transparent_color)
        surf_width = 150
        surf_height = 150
        surf = pygame.surface.Surface((surf_width, surf_height), pygame.SRCALPHA)
        w, h = 50, 150
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, w, h))
        pygame.draw.rect(surf, (255, 255, 255), (100, 0, w, h))
        screen_center_x = self.width / 2
        screen_center_y = self.height / 2
        self.screen.blit(surf, (screen_center_x - surf_width / 2, screen_center_y - surf_height / 2))

    def handle_key_pressed(self, key):
        """
        键盘事件监听处理
        :param key: pynput.keyboard.Key
        :return:
        """
        if key == self.key_map["pause"]:
            self.is_paused = not self.is_paused
        return

    def get_state(self, results, screenshot) -> Literal[None, "Recruit", "Combat"]:
        """
        获取当前酒馆状态
        :param results: 检测结果
        :param screenshot: 屏幕截图
        :return: 当前酒馆状态
        """
        if "state" not in [i['label'] for i in results]:
            return None
        state_result = None
        for result in results:
            if result['label'] == "state":
                state_result = result
                break
        x1, y1 = state_result['top_left']
        x2, y2 = state_result['bottom_right']
        all_texts = self.ocr_texts(screenshot, (x1, y1, x2, y2))
        if '秒' in ''.join(all_texts):
            return "Recruit"
        return "Combat"

    @staticmethod
    def get_bob(results) -> Union[None, tuple[int, int]]:
        """
        获取酒馆bob信息
        :param results: 检测结果
        :return: bob中心坐标
        """
        for result in results:
            if result['label'] == "bob":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                return int((x1 + x2) / 2), int((y1 + y2) / 2)
        return None

    @staticmethod
    def get_hero(results) -> Union[None, tuple[int, int]]:
        """
        获取酒馆英雄信息
        :param results: 检测结果
        :return: 英雄中心坐标
        """
        for result in results:
            if result['label'] == "hero":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                return int((x1 + x2) / 2), int((y1 + y2) / 2)
        return None

    @staticmethod
    def get_buttons(results) -> dict:
        """
        获取酒馆各类按钮信息
        :param results: 检测结果
        :return: {"upgrade": 升级按钮坐标, "refresh": 刷新按钮坐标, "freeze": 冻结按钮坐标}
        """
        res = {"upgrade": None, "refresh": None, "freeze": None}
        for result in results:
            label = result['label']
            if label == "upgrade" or label == "refresh" or label == "freeze":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                res[label] = ((x1 + x2) / 2, (y1 + y2) / 2)
        return res

    @staticmethod
    def get_minions(results) -> list[tuple[int, int, int, int]]:
        """
        获取场上随从信息
        :param results: 检测结果
        :return: 随从的xywh（中心x，中心y，宽度w，高度h）列表
        """
        res = []
        for result in results:
            label = result['label']
            if label == "minion":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                res.append(((x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1), (y2 - y1)))  # xywh
        res.sort(key=lambda x: x[0])
        return res

    @staticmethod
    def get_taverns(results) -> list[tuple[int, int]]:
        """
        获取酒馆牌信息
        :param results: 检测结果
        :return: 酒馆牌的中心坐标列表
        """
        res = []
        for result in results:
            label = result['label']
            if "tavern" in label:
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                res.append(((x1 + x2) / 2, (y1 + y2) / 2))
        res.sort(key=lambda x: x[0])
        return res

    @staticmethod
    def get_skills(results) -> list[tuple[int, int]]:
        """
        获取英雄技能
        :param results: 检测结果
        :return: 技能的中心坐标列表
        """
        res = []
        for result in results:
            label = result['label']
            if "skill" in label:
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                res.append(((x1 + x2) / 2, (y1 + y2) / 2))
        res.sort(key=lambda x: x[0])
        return res

    def get_operation(self, results, screenshot) -> Union[None, str]:
        """
        从网易炉石盒子的面板获取推荐打法
        :param results: 检测结果
        :param screenshot: 屏幕截图
        :return: 返回操作描述
        """
        all_texts = self.get_texts_from_operation_panel(results, screenshot)
        if not all_texts or "打法参考A" not in all_texts:
            return None
        start_index = all_texts.index("打法参考A")
        recommend_operation = ''
        for text in all_texts[start_index + 1:]:
            if text == "站位参考" or text == "打法参考B":
                break
            recommend_operation += text + '\n'
        return recommend_operation

    def get_sequence(self, results, screenshot) -> Union[None, list[str]]:
        """
        从网易炉石盒子的面板获取推荐站位
        :param results: 检测结果
        :param screenshot: 屏幕截图
        :return: 返回站位序列
        """
        all_texts = self.get_texts_from_operation_panel(results, screenshot)
        if not all_texts or "站位参考" not in all_texts:
            return None
        start_index = all_texts.index("站位参考")
        sequence = []
        for text in all_texts[start_index + 1:]:
            if "该功能" in text:
                break
            if re.match(r"^\d+$", text):
                continue
            sequence.append(text)
        return sequence

    def get_texts_from_operation_panel(self, results, screenshot) -> Union[None, list[str]]:
        if "operation panel" not in [i['label'] for i in results]:
            return None
        op_panel_result = None
        for result in results:
            if result['label'] == "operation panel":
                op_panel_result = result
                break
        x1, y1 = op_panel_result['top_left']
        x2, y2 = op_panel_result['bottom_right']
        all_texts = self.ocr_texts(screenshot, (x1, y1, x2, y2))
        return all_texts

    def extract_ocr_text(self, result) -> list[str]:
        """
        从ocr结果中提取文本
        :param result: ocr得到的结果
        :return: 文本结果列表
        """
        texts = []
        for item in result:
            if isinstance(item, list):
                texts.extend(self.extract_ocr_text(item))
            # 如果当前元素是包含文字信息的元组（文本，置信度）
            elif isinstance(item, tuple) and len(item) >= 2:
                if isinstance(item[0], str):  # 确保第一个元素是文本
                    texts.append(item[0])
            elif isinstance(item, list) and len(item) >= 2:
                if isinstance(item[1], tuple):
                    texts.append(item[1][0])
        return texts

    def detect_objects(self, screenshot):
        """
        场上按钮，英雄，商店等元素的检测
        :param screenshot: 屏幕截图
        :return: 返回直接返回调用detect的检测结果
        """
        results = self.detect(self.objects_model, screenshot)
        for result in results:
            self.draw_box(result['label'] + str(result['conf']), result['top_left'] + result['bottom_right'],
                          self.box_border_color, self.box_border_size)
        return results

    def detect_cards(self, screenshot) -> list[tuple[int, int, int, int]]:
        """
        卡牌检测，此检测只检测完整的卡牌，用于抉择操作中对选项的检测。
        :param screenshot: 屏幕截图
        :return: 检测到的目标左上角点与右下角点的坐标
        """
        results = []
        res = self.detect(self.card_model, screenshot)
        for i in res:
            results.append((i["top_left"] + i["bottom_right"]))
        return results

    def detect_hands(self, screenshot) -> list[tuple[int, int]]:
        """
        进行手牌检测
        :param screenshot: 屏幕截图
        :return: 返回以x从左至右排序后的手牌中心点列表
        """
        results = []
        raw_results = self.hand_model(screenshot)
        for result in raw_results:
            # 获取结果中的所有boxes
            boxes = result.boxes
            # 遍历所有boxes
            for box in boxes:
                # 获取每个box的坐标和置信度
                x, y, _, _ = box.xywh[0].cpu().numpy()  # 或者使用box.xyxy获取左上右下坐标
                # print(x,y)
                confidence = box.conf
                if confidence > self.threshold:
                    results.append((int(x), int(y)))
                    pygame.draw.circle(self.screen, (0, 255, 255), (int(x), int(y)), 5)
        results.sort(key=lambda a: a[0])
        return results

    def detect(self, model, screenshot) -> list[dict]:
        """
        执行检测
        :param model: 模型
        :param screenshot: 截图
        :return:
        """
        # 进行推理
        results = []
        raw_results = model(screenshot)
        for result in raw_results:
            # 获取结果中的所有boxes
            boxes = result.boxes.cpu().numpy()
            # 遍历所有boxes
            for box in boxes:
                tmp = {}
                x1, y1, x2, y2 = box.xyxy[0]  # 或者使用box.xyxy获取左上右下坐标
                conf, cls = box.conf, box.cls
                if conf < self.threshold:
                    continue
                label = result.names[int(cls)]
                tmp["conf"] = conf
                tmp["label"] = label
                tmp["top_left"] = (int(x1), int(y1))
                tmp["bottom_right"] = (int(x2), int(y2))
                results.append(tmp)
        return results

    def execute_operation(self, operation: str):
        """
        执行操作
        :param operation: 操作描述
        :return:
        """
        print(operation)
        lines = operation.split()
        self.is_sorted = False
        try:
            if "购买" in operation:
                res = re.search(r"购买(\d+)", operation)
                index = int(res.groups()[0]) - 1
                self.drag(self.taverns[index], self.hero)
            elif "打出" in operation:
                battlecry = False
                target_pos = self.hero
                res = re.search(r"打出(\d+)", operation)
                index = int(res.groups()[0]) - 1
                if "目标是我方" in operation:
                    res = re.search(r"目标是我方(\d+)", operation)
                    target_index = int(res.groups()[0]) - 1
                    x, y, w, h = self.minions[target_index]
                    target_pos = (x - int(float(w) / 4), y)  # 偏左，保证磁力情况
                    pyautogui.moveTo(self.hands[index][0], self.hands[index][1] + 10)
                    time.sleep(0.3)
                    texts = self.ocr_card_texts()
                    if "战吼" in texts[0] or "抉择" in texts[0]:
                        battlecry = True
                elif "目标是酒馆" in operation:
                    res = re.search(r"目标是酒馆(\d+)", operation)
                    target_index = int(res.groups()[0]) - 1
                    target_pos = self.taverns[target_index]
                self.drag((self.hands[index][0], self.hands[index][1] + 10), target_pos)
                if "选择" in operation:
                    target_text = lines[-1]
                    time.sleep(0.2)
                    self.select_by_text(target_text)
                if battlecry:
                    # 战吼情况 要额外点击一下
                    res = re.search(r"目标是我方(\d+)", operation)
                    target_index = int(res.groups()[0]) - 1
                    x, y, w, h = self.minions[target_index]
                    target_pos = (x + int(float(w) * 3 / 4), y)  # 战吼情况会上一只怪，所以目标位置偏右
                    time.sleep(0.2)
                    self.click(target_pos)

            elif "出售" in operation:
                res = re.search(r"出售(\d+)", operation)
                index = int(res.groups()[0]) - 1
                self.drag(self.minions[index][:2], self.bob)
            elif "升级" in operation:
                self.click(self.buttons['upgrade'])
            elif "刷新" in operation:
                self.click(self.buttons['refresh'])
            elif "冻结" in operation:
                self.click(self.buttons['freeze'])
            elif "使用" in operation:
                target_skill = None
                for skill in self.skills:
                    # 寻找技能
                    pyautogui.moveTo(skill[0], skill[1])
                    texts = self.ocr_card_texts()
                    target_text = lines[1]
                    if target_text in texts[0]:
                        target_skill = skill
                        break
                if not target_skill:
                    return
                if "目标是我方" in operation:
                    res = re.search(r"目标是我方(\d+)", operation)
                    target_index = int(res.groups()[0]) - 1
                    x, y, w, h = self.minions[target_index]
                    target_pos = (x, y)
                    self.drag(target_skill, target_pos)
                elif "目标是酒馆" in operation:
                    res = re.search(r"目标是酒馆(\d+)", operation)
                    target_index = int(res.groups()[0]) - 1
                    target_pos = self.taverns[target_index]
                    self.drag(target_skill, target_pos)
                else:
                    self.click(target_skill)
            elif "选择" in operation:
                res = re.search(r"选择(\d+)", operation)
                index = int(res.groups()[0]) - 1
                self.select(index)
            elif operation.startswith("结束回合") and not self.is_sorted:
                self.sort()
        except Exception as e:
            return

    def clear(self):
        """
        清空屏幕
        :return:
        """
        self.screen.fill(self.transparent_color)
        pygame.display.flip()

    def draw_box(self, label: str, box: tuple[int, int, int, int], color=(0, 255, 0), thickness: int = 2):
        """
        检测框绘制
        :param label: 标签
        :param box: 一个储存框左上角和右下角坐标的元组(x1, y1, x2, y2)
        :param color: 边框颜色
        :param thickness: 边框粗细
        :return:
        """
        x1, y1, x2, y2 = box
        # 绘制边界框
        pygame.draw.rect(self.screen, (*color, 128), (int(x1), int(y1), int(x2 - x1), int(y2 - y1)), thickness)
        # 计算文本尺寸
        font = pygame.font.Font(None, self.label_font_size)
        text_surface = font.render(label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(topleft=(x1, y1 - text_surface.get_height() - 10))
        # 创建背景矩形
        background_rect = text_surface.get_rect(topleft=(x1, y1 - text_surface.get_height() - 10))
        background_rect.width += 10
        background_rect.height += 10
        pygame.draw.rect(self.screen, (*color, 128), background_rect)
        # 渲染
        self.screen.blit(text_surface, text_rect)

    def draw_minions(self):
        """
        绘制场上随从的中心点
        :return:
        """
        for minion in self.minions:
            pygame.draw.circle(self.screen, (255, 105, 10), (minion[0], minion[1] - 10), 3)
        return

    def draw_taverns(self):
        """
        绘制酒馆牌的中心点
        :return:
        """
        for tavern in self.taverns:
            pygame.draw.circle(self.screen, (255, 105, 10), (tavern[0], tavern[1] - 10), 3)
        return

    def click(self, pos):
        """
        点击操作
        :param pos: 点击位置
        :return:
        """
        if not pos:
            return
        pyautogui.click(pos[0], pos[1])
        pygame.draw.circle(self.screen, (255, 0, 0), pos, 5)

    def drag(self, start_pos, end_pos):
        """
        拖动操作
        :param start_pos: 起点
        :param end_pos: 终点
        :return:
        """
        if not start_pos or not end_pos:
            return
        x1, y1 = start_pos
        x2, y2 = end_pos
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=self.drag_duration)
        pygame.draw.circle(self.screen, (255, 0, 0), start_pos, 5)
        pygame.draw.circle(self.screen, (255, 0, 0), end_pos, 5)

    def select(self, index):
        """
        抉择操作
        :param index: 抉择索引
        :return:
        """
        if index is None:
            return
        self.clear()
        screenshot = pyautogui.screenshot()
        results = self.detect_cards(screenshot)
        selections = []
        for result in results:
            x1, y1, x2, y2 = result
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            selections.append((cx, cy))
        selections.sort(key=lambda x: x[0])
        print(selections)
        self.click(selections[index])

    def select_by_text(self, target_text: str):
        """
        通过目标文字进行抉择
        :param target_text: 目标文字
        :return:
        """
        if not target_text:
            return
        self.clear()
        screenshot = pyautogui.screenshot()
        results = self.detect_cards(screenshot)
        selections = []
        index = None
        for i, result in enumerate(results):
            x1, y1, x2, y2 = result
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            selections.append((cx, cy))
            all_texts = self.ocr_texts(screenshot, (x1, y1, x2, y2))
            if target_text in all_texts:
                index = i
                break
        self.click(selections[index])

    def ocr_card_texts(self) -> list[str]:
        """
        OCR卡牌检测
        :return: 返回检测到的卡牌文字列表
        """
        self.clear()
        screenshot = pyautogui.screenshot()
        results = self.detect_cards(screenshot)
        card_texts = []
        for result in results:
            all_texts = self.ocr_texts(screenshot, result)
            card_texts.append(''.join(all_texts))
        print(card_texts)
        return card_texts

    def ocr_texts(self, screenshot, crop_coords: tuple[int, int, int, int] = None) -> list[str]:
        """
        ocr并返回文字
        :param screenshot: 屏幕截图
        :param crop_coords: 裁切区域，左上角与右下角坐标
        :return: 识别到的文本列表
        """
        if not crop_coords:
            cropped_screenshot = screenshot
        else:
            cropped_screenshot = screenshot.crop(crop_coords)
        ocr_results = self.ocr.ocr(numpy.array(cropped_screenshot))
        all_texts = self.extract_ocr_text(ocr_results)
        return all_texts

    def sort(self):
        """
        站位排序功能，实验性
        :return:
        """
        if not self.enable_sort or not self.sequence:
            self.is_sorted = True
            return
        target_seq = self.sequence
        original_seq = []
        for minion in self.minions:
            x, y, w, h = minion
            pyautogui.moveTo(x, y, duration=self.drag_duration)
            time.sleep(0.2)
            texts = self.ocr_card_texts()
            pattern = re.compile(r'[^\u4e00-\u9fa5]')  # 过滤中文
            filtered_text = pattern.sub('', texts[0])
            original_seq.append(filtered_text[:3])
        if original_seq == target_seq or len(original_seq) != len(target_seq):
            return
        now_seq = original_seq
        print(now_seq, target_seq)
        # 开始排序
        for i in range(len(target_seq)):
            if now_seq[i] not in target_seq[i]:
                for j in range(i + 1, len(now_seq)):
                    if now_seq[j] in target_seq[i]:
                        name = now_seq[j]
                        now_seq.pop(j)
                        now_seq.insert(i, name)
                        self.drag(self.minions[j][:2], self.minions[i][:2])
                        self.clear()
                        pyautogui.moveTo(10, 100)  # 鼠标复位防止遮挡
        # 反向再来一遍
        for i in range(len(target_seq) - 1, -1, -1):
            if now_seq[i] not in target_seq[i]:
                for j in range(i - 1, -1):
                    if now_seq[j] in target_seq[i]:
                        name = now_seq[j]
                        now_seq.pop(j)
                        now_seq.insert(i, name)
                        self.drag(self.minions[j][:2], self.minions[i][:2])
                        self.clear()
                        pyautogui.moveTo(10, 100)  # 鼠标复位防止遮挡
        self.is_sorted = True
        return

    def loading_log(self, message: str):
        """
        初始化加载时的信息显示接口
        :param message:
        :return:
        """
        self.clear()
        position = (self.width // 2, self.height // 2)
        font_size = 30
        self.draw_text(message, font_size, (236, 206, 180), position, center=True, background=True,
                       background_color=(14, 50, 101), border_size=20, border_radius=10)

    def draw_text(self, message: str, font_size: int, font_color: tuple, position: tuple[int, int],
                  center: bool = False, background: bool = False, background_color: tuple = (255, 255, 255, 128),
                  border_size: int = 10, border_radius: int = 10):
        """
        绘制文本
        :param message: 文本内容
        :param font_size: 字体大小
        :param font_color: 字体颜色
        :param position: 绘制位置
        :param center: 是否居中
        :param background: 是否开启背景
        :param background_color: 背景颜色
        :param border_size: 背景边框宽度
        :param border_radius: 背景边框圆角
        :return:
        """
        if len(background_color) == 3:
            background_color = (*background_color, 128)
        if len(font_color) == 3:
            font_color = (*font_color, 128)
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(message, True, font_color)
        text_rect = text_surface.get_rect()
        background_rect = text_rect.copy()
        if background:
            background_rect.width += border_size
            background_rect.height += border_size
            background_rect.x -= border_size // 2
            background_rect.y -= border_size // 2
        if center:
            background_rect.center = position
        else:
            background_rect.topleft = position
        pygame.draw.rect(self.screen, background_color, background_rect, border_radius=border_radius)
        text_rect.center = background_rect.center
        self.screen.blit(text_surface, text_rect)

    def display_info(self):
        """
        显示检测信息
        :return:
        """
        log_font_size = 20
        border_size = 10
        info_font_color = (29, 76, 80)
        warning_font_color = (211, 164, 136)
        background_color = (242, 231, 229)
        if self.is_paused:
            self.draw_text("Paused", log_font_size, warning_font_color, (0, 0), background=True,
                           background_color=background_color, border_size=border_size)
            return
        minion_count = len(self.minions)
        tavern_count = len(self.taverns)
        hand_count = len(self.hands)
        self.draw_text(f"AutoBattleGrounds is running, hands: {hand_count}, minions: {minion_count}, taverns: {tavern_count}", log_font_size,
                       info_font_color, (0, 0), background=True,
                       background_color=background_color, border_size=border_size)
        return


if __name__ == "__main__":
    AutoBattleGrounds((1920, 1080), "runs/detect/train/weights/best.pt", "runs/segment/train4/weights/best.pt",
                    "runs/detect/card/weights/best.pt", enable_sort=True).run()

# 马林
# 适配不同技能使用
# sort还有问题
# 长名字随从无法识别
