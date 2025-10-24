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
  def __init__(self, callback, db_info):
    super().__init__()
    self.callback = callback
    self.db_info = db_info

  def run(self):
    print("[Worker] 작업 시작...")
    
    try:
      print(f"[Worker] 호스트: {self.db_info['host']}")
      print(f"[Worker] 사용자: {self.db_info['user']}")
      print(f"[Worker] 파일 경로: {self.db_info['file_path']}")
      print(f"[Worker] 테이블: {self.db_info['table_name']}")
      
      time.sleep(5)
      
      result = f"{self.db_info['table_name']} 테이블에 업로드 완료!"
      
    except Exception as e:
      print(f"[Worker] 에러 발생: {e}")
      result = f"작업 실패: {e}"

    print("[Worker] 작업 완료.")
    Clock.schedule_once(lambda dt: self.callback(result))


class ExcelDBToolLayout(BoxLayout):
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
    self.ids.status_label.text = "작업 시작... (UI 멈추지 않음)"

    worker = WorkerThread(callback=self.on_upload_finished, db_info=db_info)
    worker.start()

  def on_upload_finished(self, result_message):
    self.ids.status_label.text = f"작업 완료: {result_message}"
    self.ids.upload_button.disabled = False

class ExcelDBToolApp(App):
  def build(self):
    return ExcelDBToolLayout()

if __name__ == '__main__':
  ExcelDBToolApp().run()