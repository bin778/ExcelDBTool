import os, time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

class DbUploader:
  def __init__(self, db_info):
    self.db_info = db_info
    self.engine = None
    try:
      port = db_info.get('port') or 3306
      host = db_info.get('host') or 'localhost'
      
      password_encoded = quote_plus(db_info['password'])
      
      connection_string = (
        f"mysql+pymysql://{db_info['user']}:{password_encoded}"
        f"@{host}:{port}/{db_info['db_name']}"
        f"?local_infile=1&charset=utf8mb4"
      )
      
      print(f"[DbUploader] 연결 시도: mysql+pymysql://{db_info['user']}:***@{host}:{port}...")
      
      self.engine = create_engine(connection_string)
      
      with self.engine.connect() as conn:
        print("[DbUploader] DB 연결 성공 (pymysql 드라이버)")
        
    except SQLAlchemyError as e:
      print(f"[DbUploader] DB 연결 실패: {e}")
      
      err_str = str(e).lower()
      if "no module named 'pymysql'" in err_str:
        raise ImportError("PyMySQL 드라이버가 설치되지 않았습니다. (pip install PyMySQL)")
      if "'cryptography' package is required" in err_str:
        raise ImportError("MySQL 8+ 인증을 위해 'cryptography' 라이브러리가 필요합니다. (pip install cryptography)")
      
      raise ConnectionError(f"DB 연결 실패: {e}")
    except ImportError as e:
      raise e
    except Exception as e:
      raise Exception(f"알 수 없는 연결 오류: {e}")

  def _sanitize_column_name(self, col_name):
    sanitized = str(col_name).strip().replace(' ', '_').replace('-', '_')
    return f"`{sanitized}`"

  def _create_table_if_not_exists(self, filepath, table_name):
    print(f"[DbUploader] '{table_name}' 테이블 존재 여부 확인 및 생성 (필요시)...")
    try:
      if filepath.lower().endswith('.csv'):
        try:
          df_header = pd.read_csv(filepath, nrows=0, encoding='utf-8')
        except UnicodeDecodeError:
          df_header = pd.read_csv(filepath, nrows=0, encoding='cp949')
      elif filepath.lower().endswith(('.xlsx', '.xlsm')):
          df_header = pd.read_excel(filepath, nrows=0, engine='openpyxl')
      else:
        raise ValueError("지원하지 않는 파일 형식")

      column_names = [self._sanitize_column_name(col) for col in df_header.columns]
      
      if not column_names:
        raise Exception("파일에 헤더(컬럼)가 없습니다. 비어있는 파일인지 확인하세요.")

      columns_with_types = [f"{col_name} TEXT" for col_name in column_names]
      
      query_str = f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n"
      query_str += ",\n".join(columns_with_types)
      query_str += "\n) DEFAULT CHARSET=utf8mb4;"
      
      print(f"[DbUploader] 실행할 DDL:\n{query_str}")

      with self.engine.connect() as connection:
        connection.execute(text(query_str))
        connection.commit()
      print(f"[DbUploader] 테이블 준비 완료.")

    except Exception as e:
      raise Exception(f"테이블 자동 생성 실패: {e}")


  def run_upload(self, progress_callback):
    filepath = self.db_info['file_path']
    table_name = self.db_info['table_name']
    
    try:
      self._create_table_if_not_exists(filepath, table_name)
    except Exception as e:
      raise Exception(f"테이블 준비 실패: {e}")

    chunk_size = 10000
    total_rows = 0

    print(f"[DbUploader] '{filepath}' 파일 처리 시작...")

    try:
      if filepath.lower().endswith('.csv'):
        try:
          file_iterator = pd.read_csv(filepath, chunksize=chunk_size, encoding='utf-8', header=0)
        except UnicodeDecodeError:
          print("[DbUploader] UTF-8 읽기 실패. CP949(EUC-KR)로 재시도...")
          file_iterator = pd.read_csv(filepath, chunksize=chunk_size, encoding='cp949', header=0)
          
      elif filepath.lower().endswith(('.xlsx', '.xlsm')):
        file_iterator = pd.read_excel(filepath, chunksize=chunk_size, engine='openpyxl', header=0)
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
          
          sanitized_columns = [self._sanitize_column_name(col) for col in chunk.columns]
          columns_sql = f"({', '.join(sanitized_columns)})"
          
          query = f"""
            LOAD DATA LOCAL INFILE '{absolute_path}'
            INTO TABLE `{table_name}`
            CHARACTER SET utf8mb4 
            FIELDS TERMINATED BY ',' ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
            {columns_sql}
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