from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WeeklyStockPriceResponse(BaseModel):
    """주간 주가 데이터 응답 모델"""
    symbol: str = Field(..., description="종목 코드", example="036570")
    companyName: str = Field(..., description="기업명", example="엔씨소프트")
    marketCap: Optional[int] = Field(None, description="시가총액 (억원 단위)", example=89500)
    today: Optional[int] = Field(None, description="이번 주 금요일 종가", example=361500)
    lastWeek: Optional[int] = Field(None, description="전주 금요일 종가", example=367500)
    changeRate: Optional[float] = Field(None, description="주간 등락률 (%)", example=-1.63)
    weekHigh: Optional[int] = Field(None, description="금주 고점", example=375000)
    weekLow: Optional[int] = Field(None, description="금주 저점", example=359000)
    error: Optional[str] = Field(None, description="오류 메시지")
    thisFridayDate: Optional[str] = Field(None, description="이번 주 금요일 날짜 (YYYY.MM.DD)", example="2024.12.27")
    lastFridayDate: Optional[str] = Field(None, description="전주 금요일 날짜 (YYYY.MM.DD)", example="2024.12.20")

class StockDataPoint(BaseModel):
    """일별 주가 데이터 포인트"""
    date: str = Field(..., description="거래일 (YYYY-MM-DD)", example="2024-12-20")
    close: int = Field(..., description="종가", example=361500)
    high: int = Field(..., description="고가", example=365000)
    low: int = Field(..., description="저가", example=359000)
    volume: int = Field(..., description="거래량", example=123456)

class WeeklyStockPriceBase(BaseModel):
    """주간 주가 기본 스키마"""
    symbol: str = Field(..., description="종목 심볼/코드")
    market_cap: Optional[int] = Field(None, description="시가총액 (억원 단위)")
    today: Optional[int] = Field(None, description="이번 주 금요일 종가")
    last_week: Optional[int] = Field(None, description="전주 금요일 종가")
    change_rate: Optional[float] = Field(None, description="주간 등락률 (%)")
    week_high: Optional[int] = Field(None, description="금주 고점")
    week_low: Optional[int] = Field(None, description="금주 저점")

class WeeklyStockPriceCreate(WeeklyStockPriceBase):
    """주간 주가 생성 스키마"""
    error: Optional[str] = Field(None, description="오류 메시지")
    this_friday_date: Optional[str] = Field(None, description="이번 주 금요일 날짜")
    last_friday_date: Optional[str] = Field(None, description="전주 금요일 날짜")
    data_source: Optional[str] = Field("naver_finance", description="데이터 소스")

class WeeklyStockPriceUpdate(BaseModel):
    """주간 주가 수정 스키마"""
    market_cap: Optional[int] = None
    today: Optional[int] = None
    last_week: Optional[int] = None
    change_rate: Optional[float] = None
    week_high: Optional[int] = None
    week_low: Optional[int] = None
    error: Optional[str] = None

class WeeklyStockPrice(WeeklyStockPriceBase):
    """주간 주가 응답 스키마 (DB 포함)"""
    id: int = Field(..., description="주가 ID")
    error: Optional[str] = Field(None, description="오류 메시지")
    this_friday_date: Optional[str] = Field(None, description="이번 주 금요일 날짜")
    last_friday_date: Optional[str] = Field(None, description="전주 금요일 날짜")
    data_source: Optional[str] = Field(None, description="데이터 소스")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    
    class Config:
        from_attributes = True

class StockPriceListResponse(BaseModel):
    """주가 목록 조회 응답 스키마"""
    status: str = Field("success", description="응답 상태")
    message: str = Field("주가 데이터 조회 완료", description="응답 메시지")
    data: List[WeeklyStockPriceResponse] = Field(..., description="주가 데이터 목록")
    total_count: int = Field(..., description="총 개수")
    companies_processed: int = Field(..., description="처리된 기업 수")
    last_updated: Optional[str] = Field(None, description="마지막 업데이트 시간")

class StockPriceBatchResponse(BaseModel):
    """배치 처리 응답 스키마"""
    status: str = Field(..., description="배치 처리 상태", example="success")
    message: str = Field(..., description="응답 메시지", example="10개 기업 주가 데이터 수집 완료")
    processed_companies: int = Field(..., description="처리된 기업 수", example=10)
    success_count: int = Field(..., description="성공한 기업 수", example=9)
    error_count: int = Field(..., description="오류 발생 기업 수", example=1)
    results: List[WeeklyStockPriceResponse] = Field(..., description="처리 결과 목록")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")

class StockPriceFetchRequest(BaseModel):
    """주가 수집 요청 스키마"""
    symbols: Optional[List[str]] = Field(None, description="종목 심볼 목록", example=["035720", "036570", "259960"])
    update_existing: bool = Field(True, description="기존 데이터 업데이트 여부")
    include_daily_data: bool = Field(False, description="일별 데이터 수집 여부")

class StockPriceSearchRequest(BaseModel):
    """주가 검색 요청 스키마"""
    symbol: Optional[str] = Field(None, description="종목 심볼")
    min_change_rate: Optional[float] = Field(None, description="최소 등락률 (%)")
    max_change_rate: Optional[float] = Field(None, description="최대 등락률 (%)")
    min_market_cap: Optional[int] = Field(None, description="최소 시가총액 (억원)")
    max_market_cap: Optional[int] = Field(None, description="최대 시가총액 (억원)")
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지 크기")

class HealthCheckResponse(BaseModel):
    """헬스체크 응답 스키마"""
    status: str = Field("healthy", description="서비스 상태")
    timestamp: str = Field(..., description="응답 시간")
    service: str = Field("weekly_stockprice", description="서비스명")
    version: str = Field("1.0.0", description="서비스 버전")
    database: str = Field("connected", description="데이터베이스 상태")
    data_source: str = Field("naver_finance", description="데이터 소스")

class StockMarketStats(BaseModel):
    """주식 시장 통계 스키마"""
    total_companies: int = Field(..., description="총 기업 수")
    positive_change: int = Field(..., description="상승 기업 수")
    negative_change: int = Field(..., description="하락 기업 수")
    unchanged: int = Field(..., description="보합 기업 수")
    average_change_rate: float = Field(..., description="평균 등락률 (%)")
    max_change_rate: float = Field(..., description="최대 등락률 (%)")
    min_change_rate: float = Field(..., description="최소 등락률 (%)")
    total_market_cap: int = Field(..., description="총 시가총액 (억원)")

class GameCompany(BaseModel):
    """게임 기업 정보 스키마"""
    symbol: str = Field(..., description="종목 코드", example="035720")
    name: str = Field(..., description="기업명", example="크래프톤")
    market: str = Field(..., description="상장 시장", example="KOSPI")
    sector: str = Field("게임", description="섹터")
    country: str = Field(..., description="국가 코드 (KR, CN, JP, US, EU 등)", example="KR")

class GameCompaniesResponse(BaseModel):
    """게임 기업 목록 응답 스키마"""
    status: str = Field("success", description="응답 상태")
    message: str = Field("게임 기업 목록 조회 완료", description="응답 메시지")
    companies: List[GameCompany] = Field(..., description="게임 기업 목록")
    total_count: int = Field(..., description="총 기업 수")

class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    status: str = Field("error", description="응답 상태")
    message: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")
    details: Optional[dict] = Field(None, description="에러 세부사항")