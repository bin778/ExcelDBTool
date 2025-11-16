def parse_error_message(error_obj, db_info):
    error_str = str(error_obj).lower()
    print(f"[Error Parser] 원본 오류: {error_str}")

    if "access denied" in error_str:
        user = db_info.get('user', 'N/A')
        return f"DB 접속 실패: '{user}' 사용자의 비밀번호가 틀렸거나 접속 권한이 없습니다."
    
    if "unknown database" in error_str:
        db_name = db_info.get('db_name', 'N/A')
        return f"DB 접속 실패: '{db_name}' 데이터베이스를 찾을 수 없습니다."

    if "(2003," in error_str or "can't connect to mysql server" in error_str:
        host = db_info.get('host', 'N/A')
        port = db_info.get('port', 'N/A')
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
        table_name = db_info.get('table_name', 'N/A')
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