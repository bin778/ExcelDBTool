# ExcelDBTool

> 대용량 엑셀/CSV 파일과 MySQL DB 간의 데이터를 초고속으로 업로드/다운로드하는 데스크톱 유틸리티

---

## 1. 프로젝트 소개 (What & Why)

### ❓ 무엇을 하는 프로젝트인가?

**ExcelDBTool**은 수십만, 수백만 건의 데이터가 담긴 대용량 엑셀 파일(`.xlsx`, `.csv`, `.numbers` 등)을 MySQL 데이터베이스에 빠르고 안정적으로 업로드하거나, 반대로 DB의 대용량 데이터를 엑셀 파일로 내려받을 수 있도록 돕는 데스크톱 애플리케이션이다.

### 💡 왜 이 프로젝트가 필요한가?

일반적으로 대용량 엑셀 파일을 MySQL Workbench 같은 GUI 툴로 임포트(Import)하면, 메모리 부족으로 프로그램이 중단되거나 응답이 멈추는 경우가 빈번하다. 또한, 작업이 완료되기까지 하염없이 기다려야 하며 진행 상황을 파악하기도 어렵다.

본 툴은 **'청킹(Chunking)'** 및 **'벌크 삽입(Bulk Insert)'** 기술을 사용하여, 파일을 작은 조각으로 나누어 순차적으로 처리한다. 이 방식을 통해 **파일 크기와 상관없이 일정한 수준의 메모리( $O(1)$ )**만 사용하므로, 1GB가 넘는 파일도 메모리 걱정 없이 안정적으로 처리할 수 있다.

사용자는 더 이상 프로그램이 멈출까 걱정할 필요 없이, 대용량 데이터를 클릭 몇 번으로 간편하게 DB에 올리거나 원하는 부분만 내려받을 수 있다.

---

## 2. 구현 목표 (Project Objectives)

본 프로젝트의 핵심 목표는 **사용자 체감 성능 극대화**이다. 이를 위해 다음과 같은 기능이 목표이다.

- **⚡ 초고속 업로드/다운로드**

  - `pandas`의 `chunksize` 옵션을 활용한 데이터 스트리밍.
  - MySQL의 `LOAD DATA INFILE` 또는 `to_sql(method='multi')`를 활용한 Bulk Insert로 DB I/O 최적화.

- **📉 최소한의 메모리 사용**

  - 파일 전체를 메모리에 로드하지 않고 스트리밍 방식으로 처리하여, 파일 크기와 상관없이 일정한 메모리( $O(1)$ ) 사용량을 유지.

- **🔄 반응형 UI (체감 성능 극대화)**

  - 멀티스레딩(Multi-Threading)을 적용하여, 데이터 업로드/다운로드 중에도 UI가 멈추지 않고(Not Responding 방지) 실시간 진행률을 표시.

- **🎯 유연한 데이터 처리**
  - **중간부터 업로드**: 지정한 행(Row) 번호부터 데이터를 읽어 업로드 가능. (조건 2)
  - **일부 데이터 다운로드**: `WHERE` 조건절, `LIMIT`, `OFFSET` 등을 사용하여 DB에서 원하는 데이터만 필터링하여 다운로드 가능. (조건 3)
  - **다양한 포맷 지원**: CSV뿐만 아니라 `.xlsx`, `.xlsm`, `.numbers` 등 다른 엑셀 파일도 CSV와 유사한 성능으로 처리. (조건 5)

---

## 3. 기술 스택 (Tech Stack)

#### Language

<p>
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/kivy-191A1B?style=for-the-badge&logo=kivy&logoColor=white">
  <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white">
</p>

#### Database

<p>
  <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
</p>

#### Tools

<p>
  <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">
  <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white">
  <img src="https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white">
</p>

---

## 4. 설치 및 실행 방법 (Installation)

```bash
# 1. 가상환경 생성 및 활성화(의존성 문제로 3.13 까지만 가능)
python -m venv venv
source venv/bin/activate # (macOS/Linux)
.\venv\Scripts\activate # (Windows CMD)

# 2. 필요 라이브러리 설치
pip install kivy pandas openpyxl sqlalchemy pymysql mysql-connector-python

# 3. 프로그램 실행
python src/main.py # (macOS/Linux)
python src\main.py # (Windows CMD)

# 4. MySQL 설정
SET GLOBAL local_infile = 'ON'; # `local_infile` 시스템 변수를 `ON`으로 설정 필수!
```

_(추후 업데이트 예정)_
