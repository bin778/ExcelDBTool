import time, threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path

font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
resource_add_path(font_dir)

# 글꼴 출처: 네이버 글꼴 자료실(https://hangeul.naver.com/font)
LabelBase.register(name='KoreanFont', fn_regular='NanumGothic.ttf')

class WorkerThread(threading.Thread):
  def __init__(self, callback):
    super().__init__()
    self.callback = callback
  def run(self):
    print("[Worker] 작업 시작...")
    time.sleep(5)
    result = "총 50,000건 처리 완료!"
    print("[Worker] 작업 완료.")
    Clock.schedule_once(lambda dt: self.callback(result))

class ExcelDBToolLayout(BoxLayout):
  def start_upload(self):
    host = self.ids.db_host.text
    user = self.ids.db_user.text
    password = self.ids.db_pass.text
    
    self.ids.upload_button.disabled = True
    self.ids.status_label.text = "작업 시작... (UI 멈추지 않음)"

    # TODO: 나중에 WorkerThread에 이 정보들을 넘겨야 할 것!
    worker = WorkerThread(callback=self.on_upload_finished)
    worker.start()

  def on_upload_finished(self, result_message):
    self.ids.status_label.text = f"작업 완료: {result_message}"
    self.ids.upload_button.disabled = False

class ExcelDBToolApp(App):
  def build(self):
    return ExcelDBToolLayout()

if __name__ == '__main__':
  ExcelDBToolApp().run()