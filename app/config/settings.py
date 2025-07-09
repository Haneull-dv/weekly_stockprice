import os
from dotenv import load_dotenv
from pathlib import Path

"""
StockPrice 서비스 설정
"""

# 주가 데이터 수집 설정
DEFAULT_DAYS_BACK = 21  # 기본 데이터 수집 기간 (일)
TRADING_DAYS_PER_WEEK = 5  # 주당 거래일 수

# API 요청 설정
REQUEST_TIMEOUT = 10  # 초
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MAX_RETRY_COUNT = 3  # 최대 재시도 횟수

# 네이버 금융 URL 설정
NAVER_FINANCE_BASE_URL = "https://finance.naver.com"
DAILY_CHART_URL_TEMPLATE = "https://finance.naver.com/item/sise_day.naver?code={code}"
MAIN_PAGE_URL_TEMPLATE = "https://finance.naver.com/item/main.naver?code={code}"

# 데이터 파싱 설정
MARKET_CAP_PATTERNS = [
    "em#_market_sum",
    ".blind:contains('시가총액')",
    "td:contains('시가총액') + td"
]

# 캐시 설정
CACHE_DURATION = 300  # 5분 (초) 

# 현재 경로 기준, 루트 탐색
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 환경 읽기 (기본값: development)
env = os.getenv("ENV", "development")

# 분기해서 환경변수 파일 로드
if env == "production":
    load_dotenv(dotenv_path=BASE_DIR / "weekly_stockprice" / ".env.production")
else:
    load_dotenv(dotenv_path=BASE_DIR / "weekly_stockprice" / ".env.development")

# 실제 사용될 DB URL
DATABASE_URL = os.getenv("DATABASE_URL")