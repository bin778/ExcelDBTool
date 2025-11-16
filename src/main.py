import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from app import ExcelDBToolApp
except ImportError as e:
    print(f"Error: 모듈을 임포트할 수 없습니다. 'src' 경로가 올바른지 확인하세요.")
    print(f"Details: {e}")
    sys.exit(1)

if __name__ == '__main__':
    ExcelDBToolApp().run()