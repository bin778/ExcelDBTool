import threading, traceback
from kivy.clock import Clock

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