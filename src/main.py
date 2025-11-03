import threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from db_uploader import DbUploader
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty

font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
resource_add_path(font_dir)

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
  selected_file_path = StringProperty('')
  _popup = None

  def show_file_chooser_popup(self):
    if not self._popup:
      home_dir = os.path.expanduser('~')
      
      # TODO: 한글 자음 및 모음 분리 문제 해결하기(macOS 한정)
      chooser = FileChooserListView(
        path=home_dir,
        filters=['*.csv', '*.xlsx', '*.xlsm'],
        font_name='KoreanFont'
      )
      
      content = BoxLayout(orientation='vertical', spacing=5, padding=10)
      content.add_widget(chooser)
      
      btn_box = BoxLayout(size_hint_y=None, height=40, spacing=5)
      btn_select = Button(text='선택', font_name='KoreanFont')
      btn_cancel = Button(text='취소', font_name='KoreanFont')
      btn_box.add_widget(btn_select)
      btn_box.add_widget(btn_cancel)
      content.add_widget(btn_box)

      self._popup = Popup(
        title='파일 선택',
        title_font='KoreanFont',
        content=content,
        size_hint=(0.9, 0.9)
      )
      
      btn_select.bind(on_press=self._on_file_selected_button)
      btn_cancel.bind(on_press=self._popup.dismiss)
      
    self._popup.open()

  def _on_file_selected_button(self, instance):
    chooser = self._popup.content.children[1] 
    
    if chooser.selection:
      file_path = chooser.selection[0]
      self.selected_file_path = file_path
      self.ids.file_path_label.text = os.path.basename(file_path)
      print(f"파일 선택됨: {file_path}")
      
    self._popup.dismiss()

  def update_status_label(self, message):
    self.ids.status_label.text = message

  def start_upload(self):
    db_info = {
      'host': self.ids.db_host.text,
      'port': self.ids.db_port.text,
      'user': self.ids.db_user.text,
      'password': self.ids.db_pass.text,
      'db_name': self.ids.db_name.text,
      'file_path': self.selected_file_path,
      'table_name': self.ids.table_name.text
    }
    
    print(f"UI 입력값: {db_info}")
    
    if not self.selected_file_path or not os.path.exists(self.selected_file_path):
      self.update_status_label("오류: 유효한 파일을 먼저 선택하세요.")
      return

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