import threading, os, traceback
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
        is_error = False
        try:
            result_message = self.target_callable(
                progress_callback=self.safe_progress_update
            )
        except Exception as e:
            print(f"[Worker] 에러 발생: {e}")
            traceback.print_exc()
            result_message = e
            is_error = True
            
        print("[Worker] 작업 완료.")
        Clock.schedule_once(lambda dt: self.finished_ui_callback(result_message, is_error))

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
            try:
                import unicodedata
                file_path = unicodedata.normalize('NFC', file_path)
            except ImportError:
                pass
            
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
        
        try:
            import unicodedata
            save_dir = unicodedata.normalize('NFC', save_dir)
            file_name = unicodedata.normalize('NFC', file_name)
        except ImportError:
            pass

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

    def _parse_error_message(self, error_obj):
        error_str = str(error_obj).lower()
        print(f"[Error Parser] 원본 오류: {error_str}")

        if "access denied" in error_str:
            user = self.ids.db_user.text
            return f"DB 접속 실패: '{user}' 사용자의 비밀번호가 틀렸거나 접속 권한이 없습니다."
        
        if "unknown database" in error_str:
            db_name = self.ids.db_name.text
            return f"DB 접속 실패: '{db_name}' 데이터베이스를 찾을 수 없습니다."

        if "(2003," in error_str or "can't connect to mysql server" in error_str:
            host = self.ids.db_host.text
            port = self.ids.db_port.text or '3306'
            return f"DB 연결 실패: 서버({host}:{port})에 연결할 수 없습니다. (호스트/포트 확인)"

        if isinstance(error_obj, ImportError):
            if "pymysql" in error_str:
                return "환경 오류: 'PyMySQL' 라이브러리가 없습니다. (터미널에서 pip install PyMySQL)"
            if "cryptography" in error_str:
                return "환경 오류: 'cryptography' 라이브러리가 필요합니다. (터미널에서 pip install cryptography)"
            if "openpyxl" in error_str:
                return "환경 오류: 'openpyxl' 라이브러리가 필요합니다. (터미널에서 pip install openpyxl)"
            return f"환경 오류: 필요한 라이브러리를 찾을 수 없습니다. ({error_obj})"

        if "table" in error_str and "doesn't exist" in error_str:
            table_name = self.ids.table_name.text
            return f"작업 실패: DB에 '{table_name}' 테이블이 존재하지 않습니다."

        if "file not found" in error_str or isinstance(error_obj, FileNotFoundError):
            return "작업 실패: 선택한 파일을 찾을 수 없습니다. (파일이 삭제되었거나 경로 오류)"

        if "파일에 헤더(컬럼)가 없습니다" in error_str:
            return "업로드 실패: 파일이 비어있거나, 헤더(컬럼)가 정의되지 않았습니다."
        
        if "syntax error" in error_str:
            return f"DB 오류: SQL 문법 오류가 발생했습니다. (테이블명/컬럼명에 특수문자 확인)"
        
        if ("data local infile" in error_str and "is not allowed" in error_str) or \
            ("loading local data is disabled" in error_str) or \
            "(3948," in error_str:
            return "DB 설정 오류: 'LOAD DATA LOCAL INFILE'이 비활성화되어 있습니다. (DB 서버 설정 변경 필요)"

        error_snippet = (error_str[:120] + '...') if len(error_str) > 120 else error_str
        return f"알 수 없는 오류: {error_snippet}"

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
            traceback.print_exc()
            self.on_task_finished(e, is_error=True)

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
            traceback.print_exc()
            self.on_task_finished(e, is_error=True)

    
    def on_task_finished(self, result, is_error=False):
        if is_error:
            friendly_message = self._parse_error_message(result)
            self.ids.status_label.text = f"오류: {friendly_message}"
        else:
            self.ids.status_label.text = f"{result}"
            
        self.ids.upload_button.disabled = False
        self.ids.download_button.disabled = False

class ExcelDBToolApp(App):
    def build(self):
        return ExcelDBToolLayout()

if __name__ == '__main__':
    ExcelDBToolApp().run()