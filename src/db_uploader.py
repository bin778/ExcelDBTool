import os, time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class DbUploader:
  def __init__(self, db_info):
    self.db_info = db_info
    self.engine = None
    try:
      connection_string = (
        f"mysql+mysqlconnector://{db_info['user']}:{db_info['password']}"
        f"@{db_info['host']}:{db_info.get('port', 3306)}/{db_info['db_name']}"
        f"?local_infile=1"
      )
      self.engine = create_engine(connection_string)
      
      with self.engine.connect() as conn:
        print("[DbUploader] DB 연결 성공")
        
    except SQLAlchemyError as e:
      print(f"[DbUploader] DB 연결 실패: {e}")
      raise ConnectionError(f"DB 연결 실패: {e}")
    except ImportError:
      raise ImportError("MySQL 드라이버(mysql-connector-python)가 설치되지 않았습니다.")

  def run_upload(self, progress_callback):
    filepath = self.db_info['file_path']
    table_name = self.db_info['table_name']
    
    chunk_size = 10000
    total_rows = 0

    print(f"[DbUploader] '{filepath}' 파일 처리 시작...")

    try:
      if filepath.lower().endswith('.csv'):
        file_iterator = pd.read_csv(filepath, chunksize=chunk_size)
      elif filepath.lower().endswith(('.xlsx', '.xlsm')):
        file_iterator = pd.read_excel(filepath, chunksize=chunk_size, engine='openpyxl')
      else:
        raise ValueError("지원하지 않는 파일 형식입니다 (.csv, .xlsx, .xlsm만 지원)")
    except FileNotFoundError:
      raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")
    except Exception as e:
      raise Exception(f"파일 읽기 오류: {e}")

    for i, chunk in enumerate(file_iterator):
      chunk_start_time = time.time()
      
      temp_csv_path = "temp_chunk_for_load.csv"
      chunk.to_csv(temp_csv_path, index=False, header=False, encoding='utf-8')

      try:
        with self.engine.connect() as connection:
          absolute_path = os.path.abspath(temp_csv_path)
          absolute_path = absolute_path.replace(os.path.sep, '/')
          
          query = f"""
            LOAD DATA LOCAL INFILE '{absolute_path}'
            INTO TABLE {table_name}
            FIELDS TERMINATED BY ',' ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
          """
          connection.execute(text(query))
          connection.commit()
          
      except SQLAlchemyError as e:
        raise Exception(f"DB 삽입 오류 (청크 #{i+1}): {e}")
      finally:
        if os.path.exists(temp_csv_path):
          os.remove(temp_csv_path)

      total_rows += len(chunk)
      chunk_time = time.time() - chunk_start_time
      
      progress_message = f"청크 #{i+1} ({len(chunk)} 행) 삽입 완료... (누적: {total_rows} 행, {chunk_time:.2f}초)"
      progress_callback(progress_message)

    return f"총 {total_rows} 행을 '{table_name}' 테이블에 업로드 완료!"