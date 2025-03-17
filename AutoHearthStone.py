import re
import sys
import time
from typing import Tuple

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


class AutoHearthStone:
    def __init__(self, size: Tuple[int, int], object_model_path: str, hand_model_path: str, card_model_path: str,
                 threshold: float = 0.5):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.screen = None
        self.size = size
        self.width, self.height = size
        self.transparent_color = (255, 0, 128)
        self.font_size = 20
        self.ocr = PaddleOCR(lang='ch')
        self.objects_model_path = object_model_path
        self.hand_model_path = hand_model_path
        self.card_model_path = card_model_path
        self.hand_model = YOLO("runs/segment/train4/weights/best.pt")
        self.objects_model = YOLO(self.objects_model_path)
        self.card_model = YOLO(self.card_model_path)
        self.threshold = threshold
        self.border_color = (0, 255, 0)
        self.border_size = 2
        self.state = None
        self.minions = None
        self.taverns = None
        self.buttons = None
        self.bob = None
        self.hero = None
        self.hands = None
        self.skills = None
        self.sequence = None
        self.drag_duration = 0.2
        self.interval = 0.8
        self.is_done = False
        self.is_paused = True
        self.is_sorted = False
        self.enable_sort = False
        self.key_map = {"pause":pynput.keyboard.KeyCode.from_char("p")}
        self.listener = keyboard.Listener(on_press=self.handle_key_pressed)


    def init_transparent_window(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)
        # 透明窗口设置
        hwnd = pygame.display.get_wm_info()['window']
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.transparent_color), 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(hwnd, -1, 0, 0, self.width, self.height, 3)

    def run(self):
        self.init_transparent_window()
        self.listener.start()
        while not self.is_done:
            time.sleep(self.interval)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            # pause
            if self.is_paused:
                self.pause()
                continue
            # 运行主逻辑
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
            self.execute_operation(operation)
            pyautogui.moveTo(10, 100)  # 鼠标复位防止遮挡

    def pause(self):
        self.screen.fill(self.transparent_color)
        surf_width = 150
        surf_height = 150
        surf = pygame.surface.Surface((surf_width, surf_height), pygame.SRCALPHA)
        w, h = 50, 150
        pygame.draw.rect(surf, (255, 255, 255),  (0,0,w,h))
        pygame.draw.rect(surf, (255, 255, 255), (100, 0, w, h))
        screen_center_x = self.width / 2
        screen_center_y = self.height / 2
        self.screen.blit(surf, (screen_center_x- surf_width /2, screen_center_y - surf_height /2))
        pygame.display.flip()

    def handle_key_pressed(self, key):
        if key == self.key_map["pause"]:
            self.is_paused = not self.is_paused
        return

    def get_state(self, results, screenshot):
        if "state" not in [i['label'] for i in results]:
            return None
        state_result = None
        for result in results:
            if result['label'] == "state":
                state_result = result
                break
        x1, y1 = state_result['top_left']
        x2, y2 = state_result['bottom_right']
        cropped_screenshot = screenshot.crop((x1, y1, x2, y2))
        ocr_results = self.ocr.ocr(numpy.array(cropped_screenshot))
        all_texts = self.extract_ocr_text(ocr_results)
        if '秒' in ''.join(all_texts):
            return "Recruit"
        return "Combat"

    @staticmethod
    def get_bob(results):
        for result in results:
            if result['label'] == "bob":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                return int((x1 + x2) / 2), int((y1 + y2) / 2)
        return None

    @staticmethod
    def get_hero(results):
        for result in results:
            if result['label'] == "hero":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                return int((x1 + x2) / 2), int((y1 + y2) / 2)
        return None

    @staticmethod
    def get_buttons(results):
        res = {"upgrade": None, "refresh": None, "freeze": None}
        for result in results:
            label = result['label']
            if label == "upgrade" or label == "refresh" or label == "freeze":
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                res[label] = ((x1 + x2) / 2, (y1 + y2) / 2)
        return res

    @staticmethod
    def get_minions(results):
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
    def get_taverns(results):
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
    def get_skills(results):
        res = []
        for result in results:
            label = result['label']
            if "skill" in label:
                x1, y1 = result['top_left']
                x2, y2 = result['bottom_right']
                res.append(((x1 + x2) / 2, (y1 + y2) / 2))
        res.sort(key=lambda x: x[0])
        return res

    def get_operation(self, results, screenshot):
        if "operation panel" not in [i['label'] for i in results]:
            return None
        op_panel_result = None
        for result in results:
            if result['label'] == "operation panel":
                op_panel_result = result
                break
        x1, y1 = op_panel_result['top_left']
        x2, y2 = op_panel_result['bottom_right']
        cropped_screenshot = screenshot.crop((x1, y1, x2, y2))
        ocr_results = self.ocr.ocr(numpy.array(cropped_screenshot))
        all_texts = self.extract_ocr_text(ocr_results)
        if "打法参考A" not in all_texts:
            return None
        start_index = all_texts.index("打法参考A")
        recommend_operation = ''
        for text in all_texts[start_index + 1:]:
            if text == "站位参考" or text == "打法参考B":
                break
            recommend_operation += text + '\n'
        # if "结束回合\n" in recommend_operation:
        #     return None
        return recommend_operation

    def get_sequence(self, results, screenshot):
        if "operation panel" not in [i['label'] for i in results]:
            return None
        op_panel_result = None
        for result in results:
            if result['label'] == "operation panel":
                op_panel_result = result
                break
        x1, y1 = op_panel_result['top_left']
        x2, y2 = op_panel_result['bottom_right']
        cropped_screenshot = screenshot.crop((x1, y1, x2, y2))
        ocr_results = self.ocr.ocr(numpy.array(cropped_screenshot))
        all_texts = self.extract_ocr_text(ocr_results)
        if "站位参考" not in all_texts:
            return None
        start_index = all_texts.index("站位参考")
        sequence = []
        for text in all_texts[start_index + 1:]:
            if "该功能" in text:
                break
            if re.match(r"^\d+$",text):
                continue
            sequence.append(text)
        # if "结束回合\n" in recommend_operation:
        #     return None
        #print(sequence)
        return sequence

    def extract_ocr_text(self, result):
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
        # 进行物体推理
        results = self.detect(self.objects_model, screenshot)
        for result in results:
            self.draw_box(result['label'] + str(result['conf']), result['top_left'] + result['bottom_right'],
                          self.border_color, self.border_size)
        pygame.display.flip()
        return results

    def detect_cards(self, screenshot):
        # 进行抉择推理
        results = []
        res = self.detect(self.card_model, screenshot)
        for i in res:
            results.append((i["top_left"] + i["bottom_right"]))
        return results

    def detect_hands(self, screenshot):
        # 进行手牌推理
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
        pygame.display.flip()
        results.sort(key=lambda x: x[0])
        return results

    def detect(self, model, screenshot):
        # 进行推理
        results = []
        raw_results = model(screenshot)
        # print(raw_results)
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

    def execute_operation(self, operation):
        print(operation)
        lines = operation.split()
        self.is_sorted = False
        try:
            if "购买" in operation:
                res = re.search(r"购买(\d)", operation)
                index = int(res.groups()[0]) - 1
                self.drag(self.taverns[index], self.hero)
            elif "打出" in operation:
                battlecry = False
                target_pos = self.hero
                res = re.search(r"打出(\d)", operation)
                index = int(res.groups()[0]) - 1
                if "目标是我方" in operation:
                    res = re.search(r"目标是我方(\d)", operation)
                    target_index = int(res.groups()[0]) - 1
                    x, y, w, h = self.minions[target_index]
                    target_pos = (x - int(float(w) / 4), y)  # 偏左，保证磁力情况
                    pyautogui.moveTo(self.hands[index][0], self.hands[index][1] + 10)
                    time.sleep(0.2)
                    texts = self.ocr_card_texts()
                    if "战吼" in texts[0] or "抉择" in texts[0]:
                        battlecry = True
                elif "目标是酒馆" in operation:
                    res = re.search(r"目标是酒馆(\d)", operation)
                    target_index = int(res.groups()[0]) - 1
                    target_pos = self.taverns[target_index]
                self.drag((self.hands[index][0], self.hands[index][1] + 10), target_pos)
                if "选择" in operation:
                    target_text = lines[-1]
                    time.sleep(0.3)
                    self.ocr_select(target_text)
                if battlecry:
                    # 战吼情况 要额外点击一下
                    res = re.search(r"目标是我方(\d)", operation)
                    target_index = int(res.groups()[0]) - 1
                    x, y, w, h = self.minions[target_index]
                    target_pos = (x + int(float(w) * 3 / 4), y)  # 战吼情况会上一只怪，所以目标位置偏右
                    time.sleep(0.3)
                    self.click(target_pos)

            elif "出售" in operation:
                res = re.search(r"出售(\d)", operation)
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
                    res = re.search(r"目标是我方(\d)", operation)
                    target_index = int(res.groups()[0]) - 1
                    x, y, w, h = self.minions[target_index]
                    target_pos = (x, y)
                    self.drag(target_skill, target_pos)
                elif "目标是酒馆" in operation:
                    res = re.search(r"目标是酒馆(\d)", operation)
                    target_index = int(res.groups()[0]) - 1
                    target_pos = self.taverns[target_index]
                    self.drag(target_skill, target_pos)
                else:
                    self.click(target_skill)
            elif "选择" in operation:
                res = re.search(r"选择(\d)", operation)
                index = int(res.groups()[0]) - 1
                self.select(index)
            elif operation.startswith("结束回合") and not self.is_sorted:
                self.sort()
        except Exception as e:
            return

    def clear(self):
        self.screen.fill(self.transparent_color)
        pygame.display.flip()

    def draw_box(self, label: str, box, color=(0, 255, 0), thickness: int = 2):
        # 画框
        x1, y1, x2, y2 = box
        # 绘制边界框
        pygame.draw.rect(self.screen, (*color, 128), (int(x1), int(y1), int(x2 - x1), int(y2 - y1)), thickness)
        # 计算文本尺寸
        font = pygame.font.Font(None, self.font_size)
        text_surface = font.render(label, True, (0, 0, 0))
        text_rect = text_surface.get_rect(topleft=(x1, y1 - text_surface.get_height() - 10))
        # 创建背景矩形
        background_rect = text_surface.get_rect(topleft=(x1, y1 - text_surface.get_height() - 10))
        background_rect.width += 10
        background_rect.height += 10
        pygame.draw.rect(self.screen, (*color, 128), background_rect)
        # 添加标签
        self.screen.blit(text_surface, text_rect)

    def draw_minions(self):
        for minion in self.minions:
            pygame.draw.circle(self.screen, (255, 105, 10), (minion[0], minion[1] - 10), 3)
        pygame.display.flip()
        return

    def draw_taverns(self):
        for tavern in self.taverns:
            pygame.draw.circle(self.screen, (255, 105, 10), (tavern[0], tavern[1] - 10), 3)
        pygame.display.flip()
        return

    def log(self):
        pass

    def click(self, pos):
        if not pos:
            return
        # pyautogui.moveTo(pos[0], pos[1])
        pyautogui.click(pos[0], pos[1])
        pygame.draw.circle(self.screen, (255, 0, 0), pos, 5)
        pygame.display.flip()

    def drag(self, start_pos, end_pos):
        if not start_pos or not end_pos:
            return
        x1, y1 = start_pos
        x2, y2 = end_pos
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=self.drag_duration)
        pygame.draw.circle(self.screen, (255, 0, 0), start_pos, 5)
        pygame.draw.circle(self.screen, (255, 0, 0), end_pos, 5)
        pygame.display.flip()

    def select(self, index):
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
        self.click(selections[index])

    def ocr_select(self, target_text: str):
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
            cropped_screenshot = screenshot.crop((x1, y1, x2, y2))
            ocr_results = self.ocr.ocr(numpy.array(cropped_screenshot))
            all_texts = self.extract_ocr_text(ocr_results)
            if target_text in all_texts:
                index = i
                break
        self.click(selections[index])

    def ocr_card_texts(self) -> list:
        self.clear()
        screenshot = pyautogui.screenshot()
        results = self.detect_cards(screenshot)
        card_texts = []
        for result in results:
            x1, y1, x2, y2 = result
            cropped_screenshot = screenshot.crop((x1, y1, x2, y2))
            ocr_results = self.ocr.ocr(numpy.array(cropped_screenshot))
            all_texts = self.extract_ocr_text(ocr_results)
            card_texts.append(''.join(all_texts))
        print(card_texts)
        return card_texts

    def sort(self):
        # 实验性功能
        target_seq = self.sequence
        original_seq = []
        for minion in self.minions:
            x,y,w,h = minion
            pyautogui.moveTo(x, y)
            time.sleep(0.5)
            texts = self.ocr_card_texts()
            pattern = re.compile(r'[^\u4e00-\u9fa5]') # 过滤中文
            filtered_text=pattern.sub('', texts[0])
            original_seq.append(filtered_text[:3])
        if original_seq == target_seq or len(original_seq) != len(target_seq):
            return
        now_seq = original_seq
        print(now_seq, target_seq)
        # 开始排序
        for i in range(len(target_seq)):
            if now_seq[i] not in target_seq[i]:
                for j in range(i+1, len(now_seq)):
                    if now_seq[j] in target_seq[i]:
                        name = now_seq[j]
                        now_seq.pop(j)
                        now_seq.insert(i, name)
                        self.drag(self.minions[j][:2],self.minions[i][:2])
                        self.clear()
                        pyautogui.moveTo(10, 100)  # 鼠标复位防止遮挡
                        #time.sleep(0.2)
        # 反向再来一遍
        # for i in range(len(target_seq)):
        #     if now_seq[i] not in target_seq[i]:
        #         for j in range(i+1, len(now_seq)):
        #             if now_seq[j] in target_seq[i]:
        #                 name = now_seq[j]
        #                 now_seq.pop(j)
        #                 now_seq.insert(i, name)
        #                 self.drag(self.minions[j][:2],self.minions[i][:2])
        #                 self.clear()
        #                 pyautogui.moveTo(10, 100)  # 鼠标复位防止遮挡
        #                 #time.sleep(0.2)
        self.is_sorted = True
        return

if __name__ == "__main__":
    AutoHearthStone((1920, 1080), "runs/detect/train/weights/best.pt", "models/hand/best.pt",
                    "runs/detect/card/weights/best.pt").run()


# 马林
# 适配不同技能使用
# sort还有问题
# 长名字随从无法识别