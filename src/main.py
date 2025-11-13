import threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from db_uploader import DbUploader
from db_downloader import DbDownloader
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty

font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
resource_add_path(font_dir)

LabelBase.register(name='KoreanFont', fn_regular='NanumGothic.ttf')

class WorkerThread(threading.Thread):
    def __init__(self, target_callable, progress_ui_callback, finished_ui_callback):
        super().__init__()
        self.target_callable = target_callable
        self.progress_ui_callback = progress_ui_callback
        self.finished_ui_callback = finished_ui_callback

    def safe_progress_update(self, message):
        Clock.schedule_once(lambda dt: self.progress_ui_callback(message))

    def run(self):
        print("[Worker] 작업 시작...")
        result_message = ""
        try:
            result_message = self.target_callable(
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
    _save_popup = None

    def show_file_chooser_popup(self):
        if not self._popup:
            home_dir = os.path.expanduser('~')
            
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

    def show_file_save_popup(self):
        if not self._save_popup:
            home_dir = os.path.expanduser('~')
            
            content = BoxLayout(orientation='vertical', spacing=5, padding=10)
            
            chooser = FileChooserListView(
                path=home_dir,
                dirselect=True, 
                font_name='KoreanFont'
            )
            
            file_name_input = TextInput(
                text='downloaded_table.csv', 
                size_hint_y=None, 
                height=40,
                font_name='KoreanFont',
                write_tab=False
            )
            
            content.add_widget(chooser)
            content.add_widget(file_name_input)
            
            btn_box = BoxLayout(size_hint_y=None, height=40, spacing=5)
            btn_save = Button(text='저장', font_name='KoreanFont')
            btn_cancel = Button(text='취소', font_name='KoreanFont')
            btn_box.add_widget(btn_save)
            btn_box.add_widget(btn_cancel)
            content.add_widget(btn_box)

            self._save_popup = Popup(
                title='CSV로 저장',
                title_font='KoreanFont',
                content=content,
                size_hint=(0.9, 0.9)
            )
            
            btn_save.bind(on_press=lambda x: self._on_file_save_button(chooser, file_name_input))
            btn_cancel.bind(on_press=self._save_popup.dismiss)
            
        self._save_popup.open()

    def _on_file_save_button(self, chooser, file_name_input):
        save_dir = chooser.path
        file_name = file_name_input.text
        
        if not file_name:
            self.update_status_label("오류: 파일명을 입력하세요.")
            return
        
        if not file_name.lower().endswith('.csv'):
            file_name += '.csv'
            
        save_path = os.path.join(save_dir, file_name)
        print(f"저장 경로 선택됨: {save_path}")
        
        self._save_popup.dismiss()
        self.start_download(save_path)


    def update_status_label(self, message):
        self.ids.status_label.text = message

    def _get_common_db_info(self):
        return {
            'host': self.ids.db_host.text,
            'port': self.ids.db_port.text,
            'user': self.ids.db_user.text,
            'password': self.ids.db_pass.text,
            'db_name': self.ids.db_name.text,
            'table_name': self.ids.table_name.text
        }

    def start_upload(self):
        db_info = self._get_common_db_info()
        db_info['file_path'] = self.selected_file_path
        
        print(f"UI 입력값 (업로드): {db_info}")
        
        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            self.update_status_label("오류: 유효한 파일을 먼저 선택하세요.")
            return

        self.ids.upload_button.disabled = True
        self.ids.download_button.disabled = True
        self.update_status_label("업로드 작업 시작...")

        try:
            uploader = DbUploader(db_info)
            
            worker = WorkerThread(
                target_callable=uploader.run_upload,
                progress_ui_callback=self.update_status_label,
                finished_ui_callback=self.on_task_finished
            )
            worker.start()
        except Exception as e:
            self.on_task_finished(f"업로드 시작 실패: {e}")

    def start_download(self, save_path):
        db_info = self._get_common_db_info()
        db_info['save_path'] = save_path
        
        print(f"UI 입력값 (다운로드): {db_info}")

        if not db_info['table_name']:
            self.update_status_label("오류: 테이블명을 입력하세요.")
            return

        self.ids.upload_button.disabled = True
        self.ids.download_button.disabled = True
        self.update_status_label("다운로드 작업 시작...")
        
        try:
            downloader = DbDownloader(db_info)

            worker = WorkerThread(
                target_callable=downloader.run_download,
                progress_ui_callback=self.update_status_label,
                finished_ui_callback=self.on_task_finished
            )
            worker.start()
        except Exception as e:
            self.on_task_finished(f"다운로드 시작 실패: {e}")


    def on_task_finished(self, result_message):
        self.ids.status_label.text = f"{result_message}"
        self.ids.upload_button.disabled = False
        self.ids.download_button.disabled = False

class ExcelDBToolApp(App):
    def build(self):
        return ExcelDBToolLayout()

if __name__ == '__main__':
    ExcelDBToolApp().run()