import time, threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path

font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
resource_add_path(font_dir)

LabelBase.register(name='KoreanFont', fn_regular='NanumGothic.ttf')

class WorkerThread(threading.Thread):
  def __init__(self, callback):
    super().__init__()
    self.callback = callback

  def run(self):
    """스레드가 실제 수행하는 작업 내용"""
    print("[Worker] 작업 시작...")
    time.sleep(5)
    result = "총 50,000건 처리 완료!"
    print("[Worker] 작업 완료.")

    Clock.schedule_once(lambda dt: self.callback(result))

class ExcelDBToolLayout(BoxLayout):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.orientation = 'vertical'
    
    self.status_label = Label(
      text="대기 중...",
      size_hint_y=0.2,
      font_name='KoreanFont'
    )
    self.add_widget(self.status_label)
    
    self.upload_button = Button(
      text="업로드 시작 (5초 작업)",
      font_name='KoreanFont'
    )
    self.upload_button.bind(on_press=self.start_upload)
    self.add_widget(self.upload_button)

  def start_upload(self, instance):
    self.upload_button.disabled = True
    self.status_label.text = "작업 시작... (UI 멈추지 않음)"

    worker = WorkerThread(callback=self.on_upload_finished)
    worker.start()

  def on_upload_finished(self, result_message):
    self.status_label.text = f"작업 완료: {result_message}"
    self.upload_button.disabled = False

class ExcelDBToolApp(App):
  def build(self):
    return ExcelDBToolLayout()

if __name__ == '__main__':
  ExcelDBToolApp().run()