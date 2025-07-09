from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from app.config.db.base import Base

Base = declarative_base()

class StockPriceModel(Base):
    """주간 주가 정보 SQLAlchemy 모델"""
    __tablename__ = "weekly_stock_prices"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 주가 데이터
    symbol = Column(String(20), nullable=False, comment="종목 심볼/코드")
    market_cap = Column(BigInteger, nullable=True, comment="시가총액 (억원 단위)")
    today = Column(Integer, nullable=True, comment="이번 주 금요일 종가")
    last_week = Column(Integer, nullable=True, comment="전주 금요일 종가")
    change_rate = Column(Float, nullable=True, comment="주간 등락률 (%)")
    week_high = Column(Integer, nullable=True, comment="금주 최고가")
    week_low = Column(Integer, nullable=True, comment="금주 최저가")
    
    # 메타데이터
    error = Column(String, nullable=True, comment="오류 메시지")
    this_friday_date = Column(String, nullable=True, comment="이번 주 금요일 날짜")
    last_friday_date = Column(String, nullable=True, comment="지난 주 금요일 날짜")
    data_source = Column(String, nullable=True, comment="데이터 출처 (예: naver_finance)")
    
    # 시스템 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정 시간")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_stockprice_symbol_date', 'symbol', 'this_friday_date'),
        Index('idx_stockprice_symbol', 'symbol'),
        Index('idx_stockprice_created_at', 'created_at'),
        Index('idx_stockprice_change_rate', 'change_rate'),
    )
    
    def __repr__(self):
        return f"<StockPriceModel(id={self.id}, symbol='{self.symbol}', change_rate={self.change_rate}%)>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "market_cap": self.market_cap,
            "today": self.today,
            "last_week": self.last_week,
            "change_rate": self.change_rate,
            "week_high": self.week_high,
            "week_low": self.week_low,
            "error": self.error,
            "this_friday_date": self.this_friday_date,
            "last_friday_date": self.last_friday_date,
            "data_source": self.data_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class DailyStockDataModel(Base):
    """일별 주가 데이터 SQLAlchemy 모델 (주간 통계 계산용)"""
    __tablename__ = "daily_stock_data"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 일별 데이터
    symbol = Column(String(20), nullable=False, comment="종목 심볼/코드")
    date = Column(String(10), nullable=False, comment="거래일 (YYYY-MM-DD)")
    close = Column(Integer, nullable=False, comment="종가")
    high = Column(Integer, nullable=False, comment="고가")
    low = Column(Integer, nullable=False, comment="저가")
    volume = Column(BigInteger, nullable=True, comment="거래량")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_daily_symbol_date', 'symbol', 'date'),
        Index('idx_daily_date', 'date'),
    )
    
    def __repr__(self):
        return f"<DailyStockDataModel(symbol='{self.symbol}', date='{self.date}', close={self.close})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "date": self.date,
            "close": self.close,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }