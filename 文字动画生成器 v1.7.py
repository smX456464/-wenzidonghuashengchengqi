import pygame
import jieba
import os
import random
import re
import json
import math
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog

# 初始化
pygame.init()
pygame.font.init()
tk.Tk().withdraw()

# 屏幕设置 - 支持拉伸
WIDTH, HEIGHT = 1400, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("文字动画生成器 v5.1 - 右键菜单增强版")
pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                          pygame.MOUSEMOTION, pygame.DROPFILE, pygame.MOUSEWHEEL, pygame.KEYDOWN])

# 全局字体缓存
FONT_CACHE = {}
def get_font(size, bold=False):
    key = (size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont('SimHei', size, bold=bold)
    return FONT_CACHE[key]

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (0, 120, 215)
RED = (255, 0, 0)
GREEN = (0, 180, 0)
LIGHT_BLUE = (100, 180, 255)
LIGHT_RED = (255, 100, 100)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
PANEL_BG = (245, 245, 245)
PLACEHOLDER = (230, 230, 230)
SCROLLBAR_BG = (220, 220, 220)
SCROLLBAR_HANDLE = (80, 80, 80)

# 预设背景颜色（扩展为12种）
BG_COLORS = [
    ("白色", (255,255,255)), ("黑色", (0,0,0)), ("浅灰", (240,240,240)), ("深灰", (30,30,30)),
    ("浅蓝", (200,230,255)), ("浅绿", (200,255,200)), ("浅粉", (255,200,230)), ("浅黄", (255,255,200)),
    ("红色", (255,0,0)), ("橙色", (255,165,0)), ("青色", (0,255,255)), ("棕色", (139,69,19))
]
# 预设文字颜色
TEXT_COLORS = [
    ("黑色", (0,0,0)), ("白色", (255,255,255)), ("红色", (255,0,0)), ("绿色", (0,255,0)),
    ("蓝色", (0,0,255)), ("黄色", (255,255,0)), ("紫色", (128,0,128)), ("橙色", (255,165,0))
]

# 字体映射
FONT_MAP = {
    'simhei': '黑体', 'microsoftyahei': '微软雅黑', 'simsun': '宋体',
    'kaiti': '楷体', 'fangsong': '仿宋'
}
REVERSE_FONT_MAP = {v: k for k, v in FONT_MAP.items()}
AVAILABLE_FONTS_CN = list(FONT_MAP.values())

# 预设字符集（无文件且无自定义字符时使用）
PRESET_NUMBERS = "0123456789"
PRESET_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
PRESET_LOWER = "abcdefghijklmnopqrstuvwxyz"
PRESET_SYMBOLS = "!@#$%^&*()_+-=[]{};:'\",.<>/?~`。，、；：？！…—·ˉ¨‘’“”『』（）【】"
PRESET_CN = "〇壹贰叁肆伍陆柒捌玖"

# ------------------------------ 基础UI组件 ------------------------------
class UIElement:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
    def get_absolute_rect(self, scroll_offset=0):
        return pygame.Rect(self.x, self.y - scroll_offset, self.width, self.height)
    def is_hovered(self, mouse_pos, offset_x=0, offset_y=0, scroll_offset=0):
        adjusted_pos = (mouse_pos[0] - offset_x, mouse_pos[1] - offset_y)
        abs_rect = self.get_absolute_rect(scroll_offset)
        return abs_rect.collidepoint(adjusted_pos)

class Button(UIElement):
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=LIGHT_BLUE, text_color=WHITE):
        super().__init__(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = get_font(14)
        self.hovered = False
        self.on_click = None
        self.normal_alpha = 120
        self.hover_alpha = 255
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=(width//2, height//2))
    def set_text(self, text):
        self.text = text
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=(self.width//2, self.height//2))
    def handle_event(self, event, offset_x=0, offset_y=0, scroll_offset=0):
        if event.type == pygame.MOUSEWHEEL:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.is_hovered(event.pos, offset_x, offset_y, scroll_offset)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered(event.pos, offset_x, offset_y, scroll_offset):
                if self.on_click:
                    self.on_click()
                return True
        return False
    def draw(self, surface, scroll_offset=0):
        abs_rect = self.get_absolute_rect(scroll_offset)
        current_color = self.hover_color if self.hovered else self.color
        alpha = self.hover_alpha if self.hovered else self.normal_alpha
        if alpha < 255:
            btn_surface = pygame.Surface((abs_rect.width, abs_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(btn_surface, (*current_color, alpha), (0,0,abs_rect.width,abs_rect.height), border_radius=4)
            pygame.draw.rect(btn_surface, (*BLACK, alpha), (0,0,abs_rect.width,abs_rect.height), 1, border_radius=4)
            btn_surface.blit(self.text_surf, self.text_rect)
            surface.blit(btn_surface, abs_rect.topleft)
        else:
            pygame.draw.rect(surface, current_color, abs_rect, border_radius=4)
            pygame.draw.rect(surface, BLACK, abs_rect, 1, border_radius=4)
            surface.blit(self.text_surf, abs_rect.topleft + self.text_rect.topleft)

class Slider(UIElement):
    def __init__(self, x, y, width, min_val, max_val, step, value, label):
        super().__init__(x, y, width, 50)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.value = value
        self.label = label
        self.track_rect = pygame.Rect(x, y+25, width, 12)
        self.handle_rect = pygame.Rect(0, y+22, 18, 18)
        self.dragging = False
        self.font = get_font(14)
        self._text_surf = None
        self._last_value = None
        self.update_handle()
    def update_handle(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.x = self.track_rect.x + ratio * (self.track_rect.width - 18)
    def get_text_surf(self):
        if self._text_surf is None or self.value != self._last_value:
            self._text_surf = self.font.render(f"{self.label}: {self.value}", True, BLACK)
            self._last_value = self.value
        return self._text_surf
    def handle_event(self, event, offset_x=0, offset_y=0, scroll_offset=0):
        if event.type == pygame.MOUSEWHEEL:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered(event.pos, offset_x, offset_y, scroll_offset):
            self.dragging = True
            return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            adjusted_x = event.pos[0] - offset_x
            x = max(self.track_rect.x, min(adjusted_x, self.track_rect.x + self.track_rect.width - 18))
            ratio = (x - self.track_rect.x) / (self.track_rect.width - 18)
            self.value = round((self.min_val + ratio * (self.max_val - self.min_val)) / self.step) * self.step
            self.update_handle()
            return True
        return False
    def draw(self, surface, scroll_offset=0):
        abs_y = self.y - scroll_offset
        track_rect = pygame.Rect(self.track_rect.x, self.track_rect.y - scroll_offset, self.track_rect.width, self.track_rect.height)
        handle_rect = pygame.Rect(self.handle_rect.x, self.handle_rect.y - scroll_offset, self.handle_rect.width, self.handle_rect.height)
        pygame.draw.rect(surface, PLACEHOLDER, (self.x, abs_y + self.height, self.width, 5))
        surface.blit(self.get_text_surf(), (self.x, abs_y))
        pygame.draw.rect(surface, GRAY, track_rect, border_radius=3)
        pygame.draw.rect(surface, BLUE, handle_rect, border_radius=3)
        pygame.draw.rect(surface, BLACK, handle_rect, 1, border_radius=3)

class RadioGroup:
    def __init__(self):
        self.buttons = []
    def add_button(self, btn):
        self.buttons.append(btn)
    def select(self, selected_btn):
        for btn in self.buttons:
            btn.checked = (btn == selected_btn)

class RadioButton(UIElement):
    def __init__(self, x, y, text, group, checked=False):
        super().__init__(x, y, 180, 30)
        self.text = text
        self.group = group
        self.checked = checked
        self.group.add_button(self)
        self.font = get_font(14)
        self.box_rect = pygame.Rect(x, y, 18, 18)
        self.text_surf = self.font.render(self.text, True, BLACK)
    def is_hovered(self, mouse_pos, offset_x=0, offset_y=0, scroll_offset=0):
        adjusted_pos = (mouse_pos[0] - offset_x, mouse_pos[1] - offset_y)
        abs_box_rect = pygame.Rect(self.box_rect.x, self.box_rect.y - scroll_offset, self.box_rect.width, self.box_rect.height)
        return abs_box_rect.collidepoint(adjusted_pos)
    def handle_event(self, event, offset_x=0, offset_y=0, scroll_offset=0):
        if event.type == pygame.MOUSEWHEEL:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered(event.pos, offset_x, offset_y, scroll_offset):
            self.group.select(self)
            return True
        return False
    def draw(self, surface, scroll_offset=0):
        abs_y = self.y - scroll_offset
        box_rect = pygame.Rect(self.box_rect.x, self.box_rect.y - scroll_offset, self.box_rect.width, self.box_rect.height)
        pygame.draw.rect(surface, WHITE, box_rect)
        pygame.draw.rect(surface, BLACK, box_rect, 1)
        if self.checked:
            pygame.draw.circle(surface, BLUE, box_rect.center, 5)
        surface.blit(self.text_surf, (box_rect.right + 7, abs_y))

class CheckBox(UIElement):
    def __init__(self, x, y, text, checked=False):
        super().__init__(x, y, 150, 30)
        self.text = text
        self.checked = checked
        self.font = get_font(14)
        self.box_rect = pygame.Rect(x, y, 18, 18)
        self.text_surf = self.font.render(self.text, True, BLACK)
    def is_hovered(self, mouse_pos, offset_x=0, offset_y=0, scroll_offset=0):
        adjusted_pos = (mouse_pos[0] - offset_x, mouse_pos[1] - offset_y)
        abs_box_rect = pygame.Rect(self.box_rect.x, self.box_rect.y - scroll_offset, self.box_rect.width, self.box_rect.height)
        return abs_box_rect.collidepoint(adjusted_pos)
    def handle_event(self, event, offset_x=0, offset_y=0, scroll_offset=0):
        if event.type == pygame.MOUSEWHEEL:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered(event.pos, offset_x, offset_y, scroll_offset):
            self.checked = not self.checked
            return True
        return False
    def draw(self, surface, scroll_offset=0):
        abs_y = self.y - scroll_offset
        box_rect = pygame.Rect(self.box_rect.x, self.box_rect.y - scroll_offset, self.box_rect.width, self.box_rect.height)
        pygame.draw.rect(surface, WHITE, box_rect)
        pygame.draw.rect(surface, BLACK, box_rect, 1)
        if self.checked:
            pygame.draw.line(surface, BLUE, (box_rect.x+3, box_rect.y+3), (box_rect.x+15, box_rect.y+15), 2)
            pygame.draw.line(surface, BLUE, (box_rect.x+15, box_rect.y+3), (box_rect.x+3, box_rect.y+15), 2)
        surface.blit(self.text_surf, (box_rect.right + 7, abs_y))

# ------------------------------ 滚动条 ------------------------------
class ScrollBar:
    def __init__(self, x, y, width, height, content_height):
        self.rect = pygame.Rect(x, y, width, height)
        self.content_height = content_height
        self.view_height = height
        self.scroll_offset = 0
        self.dragging = False
        self.handle_height = max(50, self.view_height * self.view_height / self.content_height)
        self.handle_rect = pygame.Rect(x, y, width, self.handle_height)
        self.update_handle_position()
    def update_handle_position(self):
        if self.content_height <= self.view_height:
            self.handle_rect.y = self.rect.y
            return
        ratio = self.scroll_offset / (self.content_height - self.view_height)
        self.handle_rect.y = self.rect.y + ratio * (self.view_height - self.handle_height)
    def scroll_to(self, y):
        if self.content_height <= self.view_height:
            self.scroll_offset = 0
            return
        self.scroll_offset = max(0, min(y, self.content_height - self.view_height))
        self.update_handle_position()
    def handle_event(self, event, offset_x=0, offset_y=0):
        if self.content_height <= self.view_height:
            return False
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            adjusted_pos = (event.pos[0] - offset_x, event.pos[1] - offset_y)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.handle_rect.collidepoint(adjusted_pos):
                    self.dragging = True
                    self.drag_start_y = adjusted_pos[1]
                    self.drag_start_offset = self.scroll_offset
                    return True
                elif self.rect.collidepoint(adjusted_pos):
                    click_y = adjusted_pos[1] - self.rect.y
                    ratio = click_y / self.view_height
                    self.scroll_to(ratio * (self.content_height - self.view_height))
                    return True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                delta_y = adjusted_pos[1] - self.drag_start_y
                ratio = delta_y / (self.view_height - self.handle_height)
                self.scroll_to(self.drag_start_offset + ratio * (self.content_height - self.view_height))
                return True
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_to(self.scroll_offset - event.y * 30)
            return True
        return False
    def draw(self, surface):
        if self.content_height <= self.view_height:
            return
        pygame.draw.rect(surface, SCROLLBAR_BG, self.rect, border_radius=5)
        pygame.draw.rect(surface, SCROLLBAR_HANDLE, self.handle_rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.handle_rect, 1, border_radius=5)

# ------------------------------ 右键菜单 ------------------------------
class ContextMenu:
    def __init__(self):
        self.items = []
        self.visible = False
        self.x = 0
        self.y = 0
        self.width = 160
        self.item_height = 28
        self.font = get_font(14)
    def add_item(self, text, callback):
        self.items.append((text, callback))
    def show(self, pos):
        self.x, self.y = pos
        self.visible = True
    def hide(self):
        self.visible = False
    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 只响应左键
            mx, my = event.pos
            if self.x <= mx <= self.x + self.width:
                idx = (my - self.y) // self.item_height
                if 0 <= idx < len(self.items):
                    self.items[idx][1]()
                    self.visible = False
                    return True
            self.visible = False
            return True
        return False
    def draw(self, surface):
        if not self.visible:
            return
        menu_rect = pygame.Rect(self.x, self.y, self.width, self.item_height * len(self.items))
        pygame.draw.rect(surface, WHITE, menu_rect)
        pygame.draw.rect(surface, BLACK, menu_rect, 1)
        for i, (text, _) in enumerate(self.items):
            item_y = self.y + i * self.item_height
            item_rect = pygame.Rect(self.x, item_y, self.width, self.item_height)
            hover = item_rect.collidepoint(pygame.mouse.get_pos())
            if hover:
                pygame.draw.rect(surface, LIGHT_BLUE, item_rect)
            text_surf = self.font.render(text, True, BLACK)
            surface.blit(text_surf, (self.x + 10, item_y + 4))

# ------------------------------ 弹出选择窗口（文本列表）------------------------------
class PopupSelectWindow:
    def __init__(self, x, y, width, height, title, options, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.options = options
        self.callback = callback
        self.font = get_font(14)
        self.title_font = get_font(16, bold=True)
        self.item_height = 30
        self.scrollbar = ScrollBar(width-15, 35, 10, height-40, len(options)*self.item_height)
        self.active = True
        self.title_surf = self.title_font.render(self.title, True, BLACK)
    def handle_event(self, event):
        if not self.active:
            return False
        if self.scrollbar.handle_event(event, self.rect.x, self.rect.y):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.active = False
                return True
            for i, option in enumerate(self.options):
                item_rect = pygame.Rect(
                    self.rect.x + 10, self.rect.y + 40 + i * self.item_height - self.scrollbar.scroll_offset,
                    self.rect.width - 25, self.item_height
                )
                if item_rect.collidepoint(event.pos):
                    self.callback(option)
                    self.active = False
                    return True
        return False
    def draw(self, surface):
        if not self.active:
            return
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        surface.blit(self.title_surf, (self.rect.x + 10, self.rect.y + 10))
        pygame.draw.line(surface, BLACK, (self.rect.x, self.rect.y + 35), (self.rect.right-15, self.rect.y + 35), 1)
        for i, option in enumerate(self.options):
            item_y = self.rect.y + 40 + i * self.item_height - self.scrollbar.scroll_offset
            if item_y < self.rect.y + 35 or item_y + self.item_height > self.rect.bottom:
                continue
            item_rect = pygame.Rect(self.rect.x + 10, item_y, self.rect.width - 25, self.item_height)
            hover = item_rect.collidepoint(pygame.mouse.get_pos())
            if hover:
                pygame.draw.rect(surface, LIGHT_BLUE, item_rect)
            pygame.draw.rect(surface, BLACK, item_rect, 1)
            text_surf = self.font.render(option, True, BLACK)
            surface.blit(text_surf, (item_rect.x + 10, item_rect.y + 5))
        self.scrollbar.draw(surface)

# ------------------------------ 颜色选择弹窗（三列网格）------------------------------
class ColorPickerWindow:
    def __init__(self, x, y, width, height, title, colors, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.colors = colors  # list of (name, (r,g,b))
        self.callback = callback
        self.font = get_font(14)
        self.title_font = get_font(16, bold=True)
        self.active = True
        self.title_surf = self.title_font.render(title, True, BLACK)
        self.cols = 3
        self.item_w = (width - 40) // self.cols
        self.item_h = 50
        self.rows = math.ceil(len(colors) / self.cols)
        self.content_height = 40 + self.rows * self.item_h + 10
        self.view_height = height - 40
        if self.content_height > self.view_height:
            self.scrollbar = ScrollBar(width-15, 35, 10, height-40, self.content_height)
        else:
            self.scrollbar = None
    def handle_event(self, event):
        if not self.active:
            return False
        if self.scrollbar and self.scrollbar.handle_event(event, self.rect.x, self.rect.y):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.active = False
                return True
            mx, my = event.pos
            ox = self.rect.x + 20
            oy = self.rect.y + 40
            if self.scrollbar:
                oy -= self.scrollbar.scroll_offset
            col = (mx - ox) // self.item_w
            row = (my - oy) // self.item_h
            if 0 <= col < self.cols and row >= 0:
                idx = row * self.cols + col
                if 0 <= idx < len(self.colors):
                    self.callback(self.colors[idx])
                    self.active = False
                    return True
        return False
    def draw(self, surface):
        if not self.active:
            return
        pygame.draw.rect(surface, PANEL_BG, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        surface.blit(self.title_surf, (self.rect.x + 10, self.rect.y + 10))
        offset_y = self.rect.y + 40
        if self.scrollbar:
            offset_y -= self.scrollbar.scroll_offset
        for i, (name, rgb) in enumerate(self.colors):
            row = i // self.cols
            col = i % self.cols
            rect = pygame.Rect(self.rect.x + 20 + col * self.item_w, offset_y + row * self.item_h,
                               self.item_w - 5, self.item_h - 5)
            pygame.draw.rect(surface, rgb, rect)
            # 自适应文字颜色
            lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            text_color = BLACK if lum > 128 else WHITE
            text_surf = self.font.render(name, True, text_color)
            surface.blit(text_surf, (rect.x + 5, rect.y + 5))
            if rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surface, YELLOW, rect, 2)
        if self.scrollbar:
            self.scrollbar.draw(surface)

# ------------------------------ 文字元素（翻转+旋转）------------------------------
class TextElement:
    def __init__(self, text, x, y, speed, direction, size, color, font, alpha,
                 dir_x=0, dir_y=0, random_hflip=False, random_vflip=False,
                 rotate_enabled=False, max_rotate=0):
        self.text = text
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = direction
        self.size = size
        self.color = color
        self.font = pygame.font.SysFont(REVERSE_FONT_MAP.get(font, 'simhei'), size)
        self.alpha = alpha
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.fade = False
        self.fade_speed = 3
        self.surface = self.font.render(text, True, color)
        self.surface.set_alpha(alpha)
        self.active = True
        self.hflip = random.random() < 0.5 if random_hflip else False
        self.vflip = random.random() < 0.5 if random_vflip else False
        self.rotation = random.uniform(-max_rotate, max_rotate) if rotate_enabled else 0
    def update(self):
        if self.direction == 'explode':
            self.x += self.speed * self.dir_x
            self.y += self.speed * self.dir_y
            if self.x < -200 or self.x > WIDTH+200 or self.y < -200 or self.y > HEIGHT+200:
                self.active = False
        elif self.direction == 'implode':
            center_x, center_y = WIDTH//2, HEIGHT//2
            dx = center_x - self.x
            dy = center_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 15:
                self.fade = True
            if self.fade:
                self.alpha -= self.fade_speed
                self.surface.set_alpha(max(0, self.alpha))
                if self.alpha <= 0:
                    self.active = False
            else:
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed
        else:
            if self.direction == 'fall': self.y += self.speed
            elif self.direction == 'rise': self.y -= self.speed
            elif self.direction == 'left': self.x -= self.speed
            elif self.direction == 'right': self.x += self.speed
            if self.y > HEIGHT or self.y < -100 or self.x > WIDTH+100 or self.x < -100:
                self.active = False
    def draw(self, surface):
        img = pygame.transform.flip(self.surface, self.hflip, self.vflip)
        if self.rotation != 0:
            img = pygame.transform.rotate(img, self.rotation)
        surface.blit(img, (self.x, self.y))

# ------------------------------ 主程序 ------------------------------
class TextAnimationApp:
    def __init__(self):
        self.elements = []
        self.tokens = []
        self.raw_text = ""
        self.running = False
        self.show_settings = False
        self.spawn_timer = 0
        self.messages = []
        self.popup_window = None
        self.config_path = "config.json"
        self.load_config()
        self.last_filter_config = (
            self.config['filter_sym'], self.config['filter_num'],
            self.config['filter_upper'], self.config['filter_lower'], self.config['filter_cn']
        )
        self.last_min_length = self.config['min_token_length']
        self.context_menu = ContextMenu()
        self.init_context_menu()
        self.selected_files = []
        self.max_files = 10
        self.create_settings_window()

    def init_context_menu(self):
        self.context_menu.add_item("打开设置", lambda: setattr(self, 'show_settings', not self.show_settings))
        self.context_menu.add_item("开始", lambda: setattr(self, 'running', True))
        self.context_menu.add_item("暂停", lambda: setattr(self, 'running', False))
        self.context_menu.add_item("清除", self.clear_all)
        self.context_menu.add_item("均匀分布: " + ("开" if self.config['uniform_distribution'] else "关"), self.toggle_uniform)
        self.context_menu.add_item("退出", self.exit_game)

    def refresh_context_menu(self):
        self.context_menu.items[4] = ("均匀分布: " + ("开" if self.config['uniform_distribution'] else "关"), self.toggle_uniform)

    def show_message(self, text, color=GREEN):
        self.messages.append({'text': text, 'color': color, 'time': pygame.time.get_ticks()})
        print(f"[消息] {text}")

    def update_messages(self):
        current_time = pygame.time.get_ticks()
        self.messages = [msg for msg in self.messages if current_time - msg['time'] < 3000]

    def draw_messages(self, surface):
        font = get_font(14)
        y = 20
        for msg in reversed(self.messages):
            text_surf = font.render(msg['text'], True, msg['color'])
            bg_rect = pygame.Rect(WIDTH - text_surf.get_width() - 20, y, text_surf.get_width() + 10, 25)
            pygame.draw.rect(surface, (0,0,0,180), bg_rect, border_radius=3)
            surface.blit(text_surf, (bg_rect.x + 5, bg_rect.y + 3))
            y += 30

    def load_config(self):
        default = {
            'speed_base':3,'speed_mode':'fixed','speed_rand':200,
            'size_base':24,'size_mode':'fixed','size_rand':200,
            'spawn_per_second':100,
            'alpha_mode':'fixed','alpha_base':255,'alpha_rand':200,
            'allow_overlap':False, 'max_overlap':3,
            'anim_fall':False,'anim_rise':False,'anim_left':False,'anim_right':False,
            'anim_explode':False,'anim_implode':False,
            'filter_sym':True,'filter_num':True,'filter_upper':True,'filter_lower':True,'filter_cn':True,
            'min_token_length':1,
            'font':'黑体','bg_color':[255,255,255],
            'color_mode':'random','single_text_color':[0,0,0],
            'custom_chars': '',
            'uniform_distribution': False,
            'random_hflip': False,
            'random_vflip': False,
            'enable_rotate': False,
            'max_rotate_angle': 45
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path,'r',encoding='utf-8') as f:
                    self.config = {**default,**json.load(f)}
                self.show_message("配置加载成功")
            except:
                self.config = default
                self.show_message("配置文件损坏，使用默认配置", ORANGE)
        else:
            self.config = default
            self.show_message("创建默认配置文件")

    def save_config(self):
        with open(self.config_path,'w',encoding='utf-8') as f:
            json.dump(self.config,f,ensure_ascii=False,indent=2)
        self.show_message("配置已成功保存")

    def exit_game(self):
        self.save_config()
        pygame.quit()
        sys.exit()

    def toggle_uniform(self):
        self.config['uniform_distribution'] = not self.config['uniform_distribution']
        self.refresh_context_menu()
        self.show_message(f"均匀分布已{'开启' if self.config['uniform_distribution'] else '关闭'}")

    def process_tokens(self):
        custom_chars = self.config.get('custom_chars', '').strip()
        if custom_chars:
            self.tokens = [part.strip() for part in custom_chars.split(',') if part.strip()]
            return
        if self.raw_text:
            words = jieba.lcut(self.raw_text)
            filtered = []
            for word in words:
                if not word.strip():
                    continue
                res = []
                for c in word:
                    if self.should_include_char(c):
                        res.append(c)
                s = ''.join(res)
                if len(s) >= self.config['min_token_length']:
                    filtered.append(s)
            self.tokens = filtered
            return
        # 无文件无自定义字符：生成预设
        self.tokens = []
        if self.config['filter_num']:
            self.tokens += list(PRESET_NUMBERS)
        if self.config['filter_upper']:
            self.tokens += list(PRESET_UPPER)
        if self.config['filter_lower']:
            self.tokens += list(PRESET_LOWER)
        if self.config['filter_sym']:
            self.tokens += list(PRESET_SYMBOLS)
        if self.config['filter_cn']:
            self.tokens += list(PRESET_CN)

    def add_label(self, text, x, y):
        self.labels.append((self.font_bold.render(text, True, BLACK), x, y))

    def create_settings_window(self):
        self.win_x, self.win_y = 350, 50
        self.win_w = 700
        self.font_small = get_font(14)
        self.font_bold = get_font(14, bold=True)
        self.font_title = get_font(18, bold=True)
        self.title_label = self.font_title.render('文字动画设置', True, BLACK)
        x, y = 30, 30
        self.controls = []
        self.labels = []

        # 1. 文件管理
        self.add_label("1. 文件管理(最多10个，支持拖拽):", x, y)
        y += 35
        self.browse_btn = Button(x, y, 120, 30, "浏览文件", BLUE)
        self.browse_btn.on_click = self.browse_files
        self.clear_files_btn = Button(x+130, y, 120, 30, "清空文件", RED)
        self.clear_files_btn.on_click = self.clear_files
        self.controls.extend([self.browse_btn, self.clear_files_btn])
        y += 45
        self.file_list_rect = pygame.Rect(x, y, 640, 120)
        self.file_buttons = []
        y += 130

        # 2. 速度设置
        self.add_label("2. 运动速度设置:", x, y)
        y += 35
        self.speed_group = RadioGroup()
        self.speed_fixed = RadioButton(x,y,"固定速度",self.speed_group,self.config['speed_mode']=='fixed')
        self.speed_rand = RadioButton(x+200,y,"随机速度",self.speed_group,self.config['speed_mode']=='random')
        self.controls.extend([self.speed_fixed, self.speed_rand])
        y += 40
        self.speed_slider = Slider(x,y,300,1,20,1,self.config['speed_base'],"基础速度")
        self.speed_rand_slider = Slider(x+330,y,300,0,400,5,self.config['speed_rand'],"随机百分比(%)")
        self.controls.extend([self.speed_slider, self.speed_rand_slider])
        y += 60

        # 3. 大小设置
        self.add_label("3. 文字大小设置:", x, y)
        y += 35
        self.size_group = RadioGroup()
        self.size_fixed = RadioButton(x,y,"固定大小",self.size_group,self.config['size_mode']=='fixed')
        self.size_rand = RadioButton(x+200,y,"随机大小",self.size_group,self.config['size_mode']=='random')
        self.controls.extend([self.size_fixed, self.size_rand])
        y += 40
        self.size_slider = Slider(x,y,300,12,120,2,self.config['size_base'],"基础大小")
        self.size_rand_slider = Slider(x+330,y,300,0,400,5,self.config['size_rand'],"随机百分比(%)")
        self.controls.extend([self.size_slider, self.size_rand_slider])
        y += 60

        # 4. Token生成速度
        self.add_label("4. Token生成速度:", x, y)
        y += 35
        self.spawn_slider = Slider(x,y,640,50,3000,10,self.config['spawn_per_second'],"每秒生成数量")
        self.controls.append(self.spawn_slider)
        y += 60

        # 5. 动画方式
        self.add_label("5. 动画方式(可多选):", x, y)
        y += 35
        self.anim_fall = CheckBox(x,y,"降落",self.config['anim_fall'])
        self.anim_rise = CheckBox(x+120,y,"上升",self.config['anim_rise'])
        self.anim_left = CheckBox(x+240,y,"左入弹幕",self.config['anim_left'])
        self.anim_right = CheckBox(x+360,y,"右入弹幕",self.config['anim_right'])
        y += 45
        self.anim_explode = CheckBox(x,y,"中心炸开",self.config['anim_explode'])
        self.anim_implode = CheckBox(x+120,y,"四周聚拢",self.config['anim_implode'])
        self.controls.extend([self.anim_fall, self.anim_rise, self.anim_left, self.anim_right,
                              self.anim_explode, self.anim_implode])
        y += 45

        # 6. 透明度设置
        self.add_label("6. 文字透明度设置:", x, y)
        y += 35
        self.alpha_group = RadioGroup()
        self.alpha_fixed = RadioButton(x,y,"固定透明度",self.alpha_group,self.config['alpha_mode']=='fixed')
        self.alpha_rand = RadioButton(x+200,y,"随机透明度",self.alpha_group,self.config['alpha_mode']=='random')
        self.controls.extend([self.alpha_fixed, self.alpha_rand])
        y += 40
        self.alpha_base_slider = Slider(x,y,300,50,255,5,self.config['alpha_base'],"基础透明度")
        self.alpha_rand_slider = Slider(x+330,y,300,0,400,5,self.config['alpha_rand'],"随机百分比(%)")
        self.controls.extend([self.alpha_base_slider, self.alpha_rand_slider])
        y += 60

        # 7. 翻转与旋转
        self.add_label("7. 翻转与旋转设置:", x, y)
        y += 35
        self.random_hflip = CheckBox(x, y, "随机水平翻转", self.config.get('random_hflip', False))
        self.random_vflip = CheckBox(x+180, y, "随机垂直翻转", self.config.get('random_vflip', False))
        self.enable_rotate = CheckBox(x+360, y, "启用随机旋转", self.config.get('enable_rotate', False))
        self.controls.extend([self.random_hflip, self.random_vflip, self.enable_rotate])
        y += 40
        self.rotate_angle_slider = Slider(x, y, 640, 0, 360, 5, self.config.get('max_rotate_angle', 45), "最大旋转角度")
        self.controls.append(self.rotate_angle_slider)
        y += 60

        # 8. 字体选择
        self.add_label("8. 字体选择:", x, y)
        y += 35
        self.font_btn = Button(x, y, 200, 30, f"当前: {self.config['font']}", GRAY, DARK_GRAY, BLACK)
        self.font_btn.on_click = self.show_font_popup
        self.controls.append(self.font_btn)
        y += 50

        # 9. 文字颜色模式
        self.add_label("9. 文字颜色模式:", x, y)
        y += 35
        self.color_group = RadioGroup()
        self.color_random = RadioButton(x,y,"每个token随机颜色",self.color_group,self.config['color_mode']=='random')
        self.color_single = RadioButton(x+250,y,"整体统一颜色",self.color_group,self.config['color_mode']=='single')
        self.controls.extend([self.color_random, self.color_single])
        y += 45
        current_color_name = "黑色"
        for name, color in TEXT_COLORS:
            if list(color) == self.config['single_text_color']:
                current_color_name = name
                break
        self.text_color_btn = Button(x, y, 200, 30, f"当前颜色: {current_color_name}", GRAY, DARK_GRAY, BLACK)
        self.text_color_btn.on_click = self.show_text_color_popup
        self.controls.append(self.text_color_btn)
        y += 50

        # 10. 背景颜色切换（改为按钮弹出窗口）
        self.add_label("10. 背景颜色切换:", x, y)
        y += 35
        self.bg_color_btn = Button(x, y, 200, 30, "选择背景颜色", GRAY, DARK_GRAY, BLACK)
        self.bg_color_btn.on_click = self.show_bg_color_popup
        self.controls.append(self.bg_color_btn)
        y += 50

        # 11. 字符筛选
        self.add_label("11. 字符筛选(勾选允许显示):", x, y)
        y += 35
        self.filter_sym = CheckBox(x,y,"符号",self.config['filter_sym'])
        self.filter_num = CheckBox(x+100,y,"数字",self.config['filter_num'])
        self.filter_upper = CheckBox(x+200,y,"大写字母",self.config['filter_upper'])
        self.filter_lower = CheckBox(x+320,y,"小写字母",self.config['filter_lower'])
        self.filter_cn = CheckBox(x+440,y,"中文",self.config['filter_cn'])
        self.controls.extend([self.filter_sym, self.filter_num, self.filter_upper, self.filter_lower, self.filter_cn])
        y += 50

        # 12. 字符长度过滤
        self.add_label("12. 字符长度过滤:", x, y)
        y += 35
        self.min_length_slider = Slider(x,y,640,1,10,1,self.config['min_token_length'],"最小字符长度")
        self.controls.append(self.min_length_slider)
        y += 60

        # 13. 自选字符
        self.add_label("13. 自选字符(英文逗号分隔):", x, y)
        y += 35
        self.custom_chars_btn = Button(x, y, 200, 30, "编辑自选字符", GRAY, DARK_GRAY, BLACK)
        self.custom_chars_btn.on_click = self.show_custom_chars_popup
        self.controls.append(self.custom_chars_btn)
        y += 50

        # 底部按钮
        self.save_btn = Button(x, y, 150, 35, "保存设置", GREEN)
        self.save_btn.on_click = self.save_config
        self.close_btn = Button(self.win_w-180, y, 150, 35, "关闭窗口", RED)
        self.close_btn.on_click = lambda: setattr(self, 'show_settings', False)
        self.controls.extend([self.save_btn, self.close_btn])
        y += 50

        self.content_height = y
        self.win_h = max(500, min(self.content_height - 1000, 900))  # 确保窗口足够显示
        self.scrollbar = ScrollBar(self.win_w - 15, 0, 12, self.win_h, self.content_height)

    # ------------------------------ 弹出窗口（居中）------------------------------
    def show_font_popup(self):
        w, h = 300, 300
        x = (WIDTH - w) // 2
        y = (HEIGHT - h) // 2
        def on_select(font):
            self.config['font'] = font
            self.font_btn.set_text(f"当前: {font}")
            self.show_message(f"已选择字体: {font}")
        self.popup_window = PopupSelectWindow(x, y, w, h, "选择字体", AVAILABLE_FONTS_CN, on_select)

    def show_text_color_popup(self):
        color_names = [name for name, _ in TEXT_COLORS]
        w, h = 300, 350
        x = (WIDTH - w) // 2
        y = (HEIGHT - h) // 2
        def on_select(name):
            for n, c in TEXT_COLORS:
                if n == name:
                    self.config['single_text_color'] = list(c)
                    self.text_color_btn.set_text(f"当前颜色: {name}")
                    self.show_message(f"文字颜色已改为: {name}")
                    break
        self.popup_window = PopupSelectWindow(x, y, w, h, "选择文字颜色", color_names, on_select)

    def show_bg_color_popup(self):
        w = int(WIDTH * 0.4)
        h = int(HEIGHT * 0.4)
        x = (WIDTH - w) // 2
        y = (HEIGHT - h) // 2
        self.popup_window = ColorPickerWindow(x, y, w, h, "选择背景颜色", BG_COLORS, self.set_bg_color)

    def set_bg_color(self, color_tuple):
        # color_tuple is (name, (r,g,b))
        self.config['bg_color'] = list(color_tuple[1])
        self.show_message(f"背景颜色已切换为: {color_tuple[0]}")

    def show_custom_chars_popup(self):
        result = simpledialog.askstring("编辑自选字符", "请输入字符（英文逗号分隔）：",
                                        initialvalue=self.config.get('custom_chars', ''))
        if result is not None:
            self.config['custom_chars'] = result
            self.process_tokens()
            self.show_message(f"自选字符已保存，当前共{len(self.tokens)}个词元")

    # ------------------------------ 文件处理（不变）------------------------------
    def browse_files(self):
        if len(self.selected_files) >= self.max_files:
            self.show_message(f"最多只能添加{self.max_files}个文件", ORANGE)
            return
        files = filedialog.askopenfilenames(title="选择TXT文件", filetypes=[("文本文件", "*.txt")],
                                            initialdir=os.getcwd())
        added = 0
        for file in files:
            if file.endswith('.txt') and file not in self.selected_files and len(self.selected_files) < self.max_files:
                self.selected_files.append(file)
                added += 1
        if added > 0:
            self.update_file_buttons()
            self.load_selected_files()
            self.show_message(f"成功添加{added}个文件")
        else:
            self.show_message("没有添加新文件", ORANGE)

    def handle_drop_file(self, path):
        if path.endswith('.txt') and path not in self.selected_files and len(self.selected_files) < self.max_files:
            self.selected_files.append(path)
            self.update_file_buttons()
            self.load_selected_files()
            self.show_message(f"已添加: {os.path.basename(path)}")
        elif len(self.selected_files) >= self.max_files:
            self.show_message(f"最多只能添加{self.max_files}个文件", ORANGE)
        else:
            self.show_message("文件已存在或格式不支持", RED)

    def update_file_buttons(self):
        self.file_buttons = []
        for i, file in enumerate(self.selected_files):
            filename = os.path.basename(file)
            row = i // 2
            col = i % 2
            btn = Button(self.file_list_rect.x + 5 + col * 315,
                         self.file_list_rect.y + 5 + row * 30,
                         305, 25, filename, GRAY, DARK_GRAY, BLACK)
            btn.on_click = lambda f=file: self.remove_file(f)
            self.file_buttons.append(btn)

    def remove_file(self, file):
        if file in self.selected_files:
            self.selected_files.remove(file)
            self.update_file_buttons()
            self.load_selected_files()
            self.show_message(f"已移除: {os.path.basename(file)}")

    def clear_files(self):
        self.selected_files.clear()
        self.file_buttons.clear()
        self.raw_text = ""
        self.process_tokens()
        self.show_message("已清空所有文件")

    def load_selected_files(self):
        if not self.selected_files:
            self.raw_text = ""
            self.process_tokens()
            return
        try:
            all_content = ""
            for file in self.selected_files:
                with open(file, 'r', encoding='utf-8') as f:
                    all_content += f.read() + "\n\n"
            self.raw_text = all_content
            self.process_tokens()
            self.show_message(f"加载完成，共{len(self.tokens)}个词元")
        except Exception as e:
            self.show_message(f"加载文件失败: {str(e)}", RED)
            print(f"加载文件错误: {e}")

    def should_include_char(self, char):
        if re.match(r'[\u4e00-\u9fff]', char):
            return self.config['filter_cn']
        elif char.isupper():
            return self.config['filter_upper']
        elif char.islower():
            return self.config['filter_lower']
        elif char.isdigit():
            return self.config['filter_num']
        else:
            return self.config['filter_sym']

    def clear_all(self):
        self.elements.clear()
        self.spawn_timer = 0
        self.show_message("屏幕已清除")

    # ------------------------------ 生成文字元素 ------------------------------
    def spawn_token(self):
        if not self.tokens or not self.running:
            return
        anims = []
        if self.config['anim_fall']: anims.append('fall')
        if self.config['anim_rise']: anims.append('rise')
        if self.config['anim_left']: anims.append('left')
        if self.config['anim_right']: anims.append('right')
        if self.config['anim_explode']: anims.append('explode')
        if self.config['anim_implode']: anims.append('implode')
        if not anims:
            return
        token = random.choice(self.tokens)
        direction = random.choice(anims)
        # 速度
        if self.config['speed_mode'] == 'fixed':
            speed = self.config['speed_base']
        else:
            p = self.config['speed_rand'] / 100
            speed = random.uniform(max(1, self.config['speed_base']*(1-p)), self.config['speed_base']*(1+p))
        # 大小
        if self.config['size_mode'] == 'fixed':
            size = self.config['size_base']
        else:
            p = self.config['size_rand'] / 100
            size = int(random.uniform(max(12, self.config['size_base']*(1-p)), self.config['size_base']*(1+p)))
        # 颜色
        if self.config['color_mode'] == 'random':
            color = (random.randint(50,255), random.randint(50,255), random.randint(50,255))
        else:
            color = tuple(self.config['single_text_color'])
        # 透明度
        if self.config['alpha_mode'] == 'fixed':
            alpha = self.config['alpha_base']
        else:
            p = self.config['alpha_rand'] / 100
            alpha = random.randint(int(max(50, self.config['alpha_base']*(1-p))), int(min(255, self.config['alpha_base']*(1+p))))
        # 位置
        grid_size = 50
        dir_x, dir_y = 0, 0
        if direction == 'explode':
            x, y = WIDTH//2, HEIGHT//2
            angle = random.uniform(0, 2*math.pi)
            dir_x = math.cos(angle)
            dir_y = math.sin(angle)
        elif direction == 'implode':
            side = random.randint(0,3)
            if side == 0:
                if self.config['uniform_distribution']:
                    x = 50 + random.randint(0, (WIDTH-100)//grid_size)*grid_size
                else: x = random.randint(0, WIDTH)
                y = -size
            elif side == 1:
                if self.config['uniform_distribution']:
                    x = 50 + random.randint(0, (WIDTH-100)//grid_size)*grid_size
                else: x = random.randint(0, WIDTH)
                y = HEIGHT + size
            elif side == 2:
                x = -150
                if self.config['uniform_distribution']:
                    y = 50 + random.randint(0, (HEIGHT-100)//grid_size)*grid_size
                else: y = random.randint(0, HEIGHT)
            else:
                x = WIDTH + 150
                if self.config['uniform_distribution']:
                    y = 50 + random.randint(0, (HEIGHT-100)//grid_size)*grid_size
                else: y = random.randint(0, HEIGHT)
        elif direction == 'fall':
            if self.config['uniform_distribution']:
                x = 50 + random.randint(0, (WIDTH-100)//grid_size)*grid_size
            else: x = random.randint(100, WIDTH-100)
            y = -size
        elif direction == 'rise':
            if self.config['uniform_distribution']:
                x = 50 + random.randint(0, (WIDTH-100)//grid_size)*grid_size
            else: x = random.randint(100, WIDTH-100)
            y = HEIGHT
        elif direction == 'left':
            x = WIDTH
            if self.config['uniform_distribution']:
                y = 50 + random.randint(0, (HEIGHT-100)//grid_size)*grid_size
            else: y = random.randint(0, HEIGHT-size)
        else:
            x = -200
            if self.config['uniform_distribution']:
                y = 50 + random.randint(0, (HEIGHT-100)//grid_size)*grid_size
            else: y = random.randint(0, HEIGHT-size)
        elem = TextElement(token, x, y, speed, direction, size, color,
                           self.config['font'], alpha, dir_x, dir_y,
                           random_hflip=self.config['random_hflip'],
                           random_vflip=self.config['random_vflip'],
                           rotate_enabled=self.config['enable_rotate'],
                           max_rotate=self.config['max_rotate_angle'])
        self.elements.append(elem)

    # ------------------------------ 主循环 ------------------------------
    def run(self):
        clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT, 16)
        global screen, WIDTH, HEIGHT
        while True:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.exit_game()
                if e.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = e.w, e.h
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                if e.type == pygame.DROPFILE:
                    self.handle_drop_file(e.file)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    if not self.show_settings or not pygame.Rect(self.win_x, self.win_y, self.win_w, self.win_h).collidepoint(e.pos):
                        self.context_menu.show(e.pos)
                    continue
                if self.context_menu.handle_event(e):
                    continue
                if self.popup_window and self.popup_window.handle_event(e):
                    continue
                if self.show_settings:
                    offset_x, offset_y = self.win_x, self.win_y
                    if self.scrollbar.handle_event(e, offset_x, offset_y):
                        continue
                    for btn in self.file_buttons:
                        btn.handle_event(e, offset_x, offset_y, self.scrollbar.scroll_offset)
                    for control in self.controls:
                        control.handle_event(e, offset_x, offset_y, self.scrollbar.scroll_offset)

            # 同步配置
            self.config['speed_mode'] = 'fixed' if self.speed_fixed.checked else 'random'
            self.config['size_mode'] = 'fixed' if self.size_fixed.checked else 'random'
            self.config['alpha_mode'] = 'fixed' if self.alpha_fixed.checked else 'random'
            self.config['speed_base'] = self.speed_slider.value
            self.config['speed_rand'] = self.speed_rand_slider.value
            self.config['size_base'] = self.size_slider.value
            self.config['size_rand'] = self.size_rand_slider.value
            self.config['spawn_per_second'] = self.spawn_slider.value
            self.config['alpha_base'] = self.alpha_base_slider.value
            self.config['alpha_rand'] = self.alpha_rand_slider.value
            self.config['anim_fall'] = self.anim_fall.checked
            self.config['anim_rise'] = self.anim_rise.checked
            self.config['anim_left'] = self.anim_left.checked
            self.config['anim_right'] = self.anim_right.checked
            self.config['anim_explode'] = self.anim_explode.checked
            self.config['anim_implode'] = self.anim_implode.checked
            self.config['color_mode'] = 'random' if self.color_random.checked else 'single'
            self.config['filter_sym'] = self.filter_sym.checked
            self.config['filter_num'] = self.filter_num.checked
            self.config['filter_upper'] = self.filter_upper.checked
            self.config['filter_lower'] = self.filter_lower.checked
            self.config['filter_cn'] = self.filter_cn.checked
            self.config['min_token_length'] = self.min_length_slider.value
            self.config['random_hflip'] = self.random_hflip.checked
            self.config['random_vflip'] = self.random_vflip.checked
            self.config['enable_rotate'] = self.enable_rotate.checked
            self.config['max_rotate_angle'] = self.rotate_angle_slider.value

            current_filter = (self.config['filter_sym'], self.config['filter_num'],
                              self.config['filter_upper'], self.config['filter_lower'], self.config['filter_cn'])
            if current_filter != self.last_filter_config or self.config['min_token_length'] != self.last_min_length:
                self.last_filter_config = current_filter
                self.last_min_length = self.config['min_token_length']
                self.process_tokens()
                if self.raw_text or self.config.get('custom_chars', ''):
                    self.show_message(f"筛选已更新，当前{len(self.tokens)}个词元")

            spawn_interval = 1000 / self.config['spawn_per_second']
            self.spawn_timer += clock.tick(60)
            if self.spawn_timer >= spawn_interval:
                self.spawn_timer = 0
                self.spawn_token()

            for elem in self.elements[:]:
                elem.update()
                if not elem.active:
                    self.elements.remove(elem)

            self.update_messages()

            screen.fill(tuple(self.config['bg_color']))
            for elem in self.elements:
                elem.draw(screen)
            self.draw_messages(screen)

            if self.show_settings:
                s = pygame.Surface((self.win_w, self.win_h))
                s.fill(PANEL_BG)
                pygame.draw.rect(s, BLACK, (0,0,self.win_w,self.win_h), 2)
                s.blit(self.title_label, (260, 15))
                for label, lx, ly in self.labels:
                    s.blit(label, (lx, ly - self.scrollbar.scroll_offset))
                file_rect = pygame.Rect(self.file_list_rect.x,
                                        self.file_list_rect.y - self.scrollbar.scroll_offset,
                                        self.file_list_rect.width, self.file_list_rect.height)
                pygame.draw.rect(s, WHITE, file_rect)
                pygame.draw.rect(s, BLACK, file_rect, 1)
                for btn in self.file_buttons:
                    btn.draw(s, self.scrollbar.scroll_offset)
                for control in self.controls:
                    control.draw(s, self.scrollbar.scroll_offset)
                self.scrollbar.draw(s)
                screen.blit(s, (self.win_x, self.win_y))

            if self.popup_window:
                self.popup_window.draw(screen)
            self.context_menu.draw(screen)
            pygame.display.flip()

if __name__ == "__main__":
    app = TextAnimationApp()
    app.run()