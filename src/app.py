import os
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.lang import Builder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_DIR = os.path.join(BASE_DIR, 'assets', 'fonts')
resource_add_path(FONT_DIR)
LabelBase.register(name='KoreanFont', fn_regular='NanumGothic.ttf')

KV_FILE = os.path.join(BASE_DIR, 'ui', 'exceldbtool.kv')
Builder.load_file(KV_FILE)

class ExcelDBToolApp(App):
    def build(self):
        from ui.layout import ExcelDBToolLayout
        return ExcelDBToolLayout()