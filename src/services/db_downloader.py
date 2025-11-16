import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

class DbDownloader:
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
            
            print(f"[DbDownloader] 연결 시도: mysql+pymysql://{db_info['user']}:***@{host}:{port}...")
            
            self.engine = create_engine(connection_string)
            
            with self.engine.connect() as conn:
                print("[DbDownloader] DB 연결 성공 (pymysql 드라이버)")
                
        except SQLAlchemyError as e:
            print(f"[DbDownloader] DB 연결 실패: {e}")
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

    def run_download(self, progress_callback):
        if not self.engine:
            raise ConnectionError("DB가 연결되지 않았습니다. __init__에서 실패했을 수 있습니다.")

        table_name = self.db_info['table_name']
        save_path = self.db_info['save_path']
        
        query = f"SELECT * FROM `{table_name}`"
        chunk_size = 10000
        total_rows = 0
        is_first_chunk = True
        
        progress_callback(f"'{table_name}' 테이블 다운로드 시작... (저장 위치: {os.path.basename(save_path)})")
        start_time = time.time()

        try:
            with self.engine.connect() as connection:
                stream = pd.read_sql_query(text(query), connection, chunksize=chunk_size)
                
                for i, chunk in enumerate(stream):
                    if not chunk.empty:
                        if is_first_chunk:
                            chunk.to_csv(save_path, index=False, encoding='utf-8-sig', mode='w')
                            is_first_chunk = False
                        else:
                            chunk.to_csv(save_path, index=False, encoding='utf-8-sig', mode='a', header=False)
                        
                        total_rows += len(chunk)
                        progress_callback(f"청크 #{i+1} 처리 중... (누적 {total_rows} 행 다운로드)")
            
            if total_rows == 0:
                if is_first_chunk:
                    progress_callback("테이블이 비어있습니다. 빈 CSV 파일을 생성합니다...")
                    header_query = f"SELECT * FROM `{table_name}` LIMIT 0"
                    df_header = pd.read_sql_query(text(header_query), connection)
                    df_header.to_csv(save_path, index=False, encoding='utf-8-sig', mode='w')
                
            end_time = time.time()
            return f"총 {total_rows} 행을 '{os.path.basename(save_path)}' 파일로 저장 완료! ({end_time - start_time:.2f}초)"

        except SQLAlchemyError as e:
            raise Exception(f"DB 쿼리/다운로드 오류: {e}")
        except Exception as e:
            raise Exception(f"파일 저장/처리 오류: {e}")