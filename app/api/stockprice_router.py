from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# 공통 DB 모듈 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from app.config.db.db_builder import get_db_session

# 서비스 모듈 import
from app.domain.controller.stockprice_controller import StockPriceController
from app.domain.service.fallback_service import StockPriceFallbackService
from app.domain.schema.stockprice_schema import (
    WeeklyStockPriceResponse,
    StockPriceListResponse,
    GameCompaniesResponse
)

router = APIRouter()

# ========== 주가 데이터 수집 엔드포인트 ==========

@router.get("/price")
async def get_stock_price(
    symbol: str = Query("259960", description="종목코드"),
    db: AsyncSession = Depends(get_db_session)
):
    """📈 기존 API - 하위 호환성 유지 (단순 조회용)"""
    print(f"🤍1. 라우터 진입: {symbol}")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_stock_price(symbol)
        print("🤍2. 기존 API 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ 기존 API 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"주가 조회 중 오류 발생: {str(e)}")

@router.get("/weekly/{symbol}", response_model=WeeklyStockPriceResponse)
async def get_weekly_stock_data(
    symbol: str,
    db: AsyncSession = Depends(get_db_session)
):
    """📊 주간 주가 데이터 조회 및 DB 저장"""
    print(f"🤍1. 주간 데이터 라우터 진입: {symbol}")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_weekly_stock_data(symbol)
        print("🤍2. 주간 데이터 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ 주간 데이터 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"주간 주가 조회 중 오류 발생: {str(e)}")

@router.get("/weekly", response_model=List[WeeklyStockPriceResponse])
async def get_all_weekly_stock_data(db: AsyncSession = Depends(get_db_session)):
    """📈 전체 게임기업 주간 주가 데이터 조회 및 DB 저장"""
    print("🤍1. 전체 게임기업 주간 데이터 라우터 진입")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_all_weekly_stock_data()
        print("🤍2. 전체 주간 데이터 라우터 - 컨트롤러 호출 완료")
        return result
        
    except Exception as e:
        print(f"❌ 전체 주간 데이터 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"전체 주간 주가 조회 중 오류 발생: {str(e)}")

@router.get("/companies")
async def get_game_companies(db: AsyncSession = Depends(get_db_session)):
    """🎮 게임기업 리스트 조회 (단순 조회용)"""
    print("🤍1. 게임기업 리스트 라우터 진입")
    
    try:
        controller = StockPriceController(db_session=db)
        result = controller.get_game_companies()
        print("🤍2. 게임기업 리스트 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ 게임기업 리스트 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"게임기업 리스트 조회 중 오류 발생: {str(e)}")

# ========== DB 조회 전용 엔드포인트 ==========

@router.get("/db/all", response_model=StockPriceListResponse)
async def get_all_stocks_from_db(
    page: int = Query(1, description="페이지 번호"),
    page_size: int = Query(20, description="페이지 크기"),
    db: AsyncSession = Depends(get_db_session)
):
    """📊 DB에서 모든 주가 정보 조회 (DB 실패 시 fallback 데이터 제공)"""
    print(f"🤍1. DB 주가 조회 라우터 진입 - 페이지: {page}")
    
    # Fallback 서비스 초기화
    fallback_service = StockPriceFallbackService()
    
    try:
        # 1. DB 연결 상태 확인 (1초 timeout)
        db_available = await fallback_service.check_db_connection(db)
        
        if db_available:
            # 2. DB 연결 성공 시 정상 로직 실행
            print("✅ [DB] 연결 성공 - 정상 데이터 제공")
            controller = StockPriceController(db_session=db)
            result = await controller.get_all_stocks_from_db(page=page, page_size=page_size)
            print("🤍2. DB 주가 조회 라우터 - 컨트롤러 호출 완료")
            return result
        else:
            # 3. DB 연결 실패 시 fallback 데이터 제공
            print("📁 [Fallback] DB 연결 실패 - fallback 데이터 제공")
            fallback_result = await fallback_service.get_fallback_stock_list(page=page, page_size=page_size)
            print("📁 [Fallback] fallback 데이터 제공 완료")
            return fallback_result
            
    except Exception as e:
        print(f"❌ DB 주가 조회 라우터 에러: {str(e)}")
        
        # 4. 예외 발생 시에도 fallback 시도
        try:
            print("📁 [Fallback] 예외 발생으로 fallback 데이터 시도")
            fallback_result = await fallback_service.get_fallback_stock_list(page=page, page_size=page_size)
            print("📁 [Fallback] 예외 시 fallback 데이터 제공 완료")
            return fallback_result
        except Exception as fallback_error:
            print(f"❌ [Fallback] fallback도 실패: {str(fallback_error)}")
            raise HTTPException(status_code=500, detail=f"DB 및 fallback 모두 실패: 원본 오류={str(e)}, fallback 오류={str(fallback_error)}")

@router.get("/db/top-gainers", response_model=List[WeeklyStockPriceResponse])
async def get_top_gainers_from_db(
    limit: int = Query(5, description="조회할 개수"),
    db: AsyncSession = Depends(get_db_session)
):
    """📈 DB에서 상승률 상위 종목 조회"""
    print(f"🤍1. DB 상승률 상위 {limit}개 조회 라우터 진입")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_top_gainers_from_db(limit)
        print("🤍2. DB 상승률 조회 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ DB 상승률 조회 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB 상승률 조회 중 오류 발생: {str(e)}")

@router.get("/db/top-losers", response_model=List[WeeklyStockPriceResponse])
async def get_top_losers_from_db(
    limit: int = Query(5, description="조회할 개수"),
    db: AsyncSession = Depends(get_db_session)
):
    """📉 DB에서 하락률 상위 종목 조회"""
    print(f"🤍1. DB 하락률 상위 {limit}개 조회 라우터 진입")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_top_losers_from_db(limit)
        print("🤍2. DB 하락률 조회 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ DB 하락률 조회 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB 하락률 조회 중 오류 발생: {str(e)}")

@router.get("/db/companies", response_model=GameCompaniesResponse)
async def get_game_companies_from_db(db: AsyncSession = Depends(get_db_session)):
    """🎮 DB에서 게임기업 정보 조회"""
    print("🤍1. DB 게임기업 정보 조회 라우터 진입")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_game_companies_from_db()
        print("🤍2. DB 게임기업 정보 조회 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ DB 게임기업 정보 조회 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB 게임기업 정보 조회 중 오류 발생: {str(e)}")

@router.get("/db/{symbol}", response_model=WeeklyStockPriceResponse)
async def get_stock_by_symbol_from_db(
    symbol: str,
    db: AsyncSession = Depends(get_db_session)
):
    """🔍 DB에서 특정 종목 주가 조회"""
    print(f"🤍1. DB 특정 종목 조회 라우터 진입: {symbol}")
    
    try:
        controller = StockPriceController(db_session=db)
        result = await controller.get_stock_by_symbol_from_db(symbol)
        print("🤍2. DB 특정 종목 조회 라우터 - 컨트롤러 호출 완료")
        return result
    except Exception as e:
        print(f"❌ DB 특정 종목 조회 라우터 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB 특정 종목 조회 중 오류 발생: {str(e)}")

# ========== 헬스체크 엔드포인트 ==========

@router.get("/health")
async def health_check():
    """💚 헬스체크 엔드포인트"""
    print("💚 헬스체크 진입")
    return {"status": "healthy", "service": "weekly_stockprice"}

@router.get("/")
async def root():
    """📋 서비스 정보"""
    return {
        "service": "Weekly Stock Price Service",
        "version": "1.0.0",
        "description": "게임기업 주간 주가 정보 수집 및 분석 서비스",
        "endpoints": {
            "weekly_all": "/stockprice/weekly",
            "weekly_single": "/stockprice/weekly/{symbol}",
            "companies": "/stockprice/companies",
            "db_all": "/stockprice/db/all",
            "db_single": "/stockprice/db/{symbol}",
            "top_gainers": "/stockprice/db/top-gainers",
            "top_losers": "/stockprice/db/top-losers",
            "health": "/stockprice/health"
        }
    }

