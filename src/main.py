import threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from db_uploader import DbUploader

font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
resource_add_path(font_dir)

# 글꼴 출처: 네이버 글꼴 자료실(https://hangeul.naver.com/font)
LabelBase.register(name='KoreanFont', fn_regular='NanumGothic.ttf')

class WorkerThread(threading.Thread):
  def __init__(self, db_info, progress_ui_callback, finished_ui_callback):
    super().__init__()
    self.db_info = db_info
    self.progress_ui_callback = progress_ui_callback
    self.finished_ui_callback = finished_ui_callback

  def safe_progress_update(self, message):
    Clock.schedule_once(lambda dt: self.progress_ui_callback(message))

  def run(self):
    print("[Worker] 작업 시작...")
    result_message = ""

    try:
      uploader = DbUploader(self.db_info)
      
      result_message = uploader.run_upload(
        progress_callback=self.safe_progress_update
      )
      
    except Exception as e:
      print(f"[Worker] 에러 발생: {e}")
      result_message = f"작업 실패: {e}"

    print("[Worker] 작업 완료.")
    
    Clock.schedule_once(lambda dt: self.finished_ui_callback(result_message))

class ExcelDBToolLayout(BoxLayout):
  def update_status_label(self, message):
    """WorkerThread가 진행 중에 호출할 함수"""
    self.ids.status_label.text = message

  def start_upload(self):
    
    db_info = {
      'host': self.ids.db_host.text,
      'user': self.ids.db_user.text,
      'password': self.ids.db_pass.text,
      'db_name': self.ids.db_name.text,
      'file_path': self.ids.file_path.text,
      'table_name': self.ids.table_name.text
    }
    
    print(f"UI 입력값: {db_info}")
    
    self.ids.upload_button.disabled = True
    self.update_status_label("작업 시작... (UI 멈추지 않음)")

    worker = WorkerThread(
      db_info=db_info,
      progress_ui_callback=self.update_status_label,
      finished_ui_callback=self.on_upload_finished
    )
    worker.start()

  def on_upload_finished(self, result_message):
    self.ids.status_label.text = f"{result_message}"
    self.ids.upload_button.disabled = False

class ExcelDBToolApp(App):
  def build(self):
    return ExcelDBToolLayout()

if __name__ == '__main__':
  ExcelDBToolApp().run()