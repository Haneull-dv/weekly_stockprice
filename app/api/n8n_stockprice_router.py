from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# 공통 DB 모듈 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from weekly_db.db.db_builder import get_db_session
from weekly_db.db.weekly_service import WeeklyDataService, WeeklyBatchService
from weekly_db.db.weekly_unified_model import WeeklyDataModel

# StockPrice 서비스 import
from app.domain.controller.stockprice_controller import StockPriceController

# Config 직접 정의 (import 이슈 회피)
GAME_COMPANIES = {
    "036570": "엔씨소프트",
    "251270": "넷마블", 
    "259960": "크래프톤",
    "263750": "펄어비스",
    "078340": "컴투스",
    "112040": "위메이드",
    "293490": "카카오게임즈",
    "095660": "네오위즈",
    "181710": "NHN",
    "069080": "웹젠",
    "225570": "넥슨게임즈"
}
TOTAL_COMPANIES = len(GAME_COMPANIES)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/n8n")

@router.post("/collect-stockprice")
async def collect_stockprice_for_n8n(
    week: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    🤖 n8n 자동화: 전체 게임기업 주가 데이터 수집
    
    매주 월요일 오전 7시에 n8n이 자동 호출
    config에 등록된 모든 게임기업의 주가 정보를 일괄 수집하여 weekly_data 테이블에 누적 저장
    
    수집 정보:
    - 주간 등락률
    - 시가총액
    - 주간 최고가/최저가
    - 금요일 종가 정보
    
    Args:
        week: 대상 주차 (YYYY-MM-DD, None이면 현재 주)
    
    Returns:
        {"status": "success", "updated": 8, "skipped": 3, "week": "2025-01-13"}
    """
    
    if not week:
        week = WeeklyDataModel.get_current_week_monday()
    
    logger.info(f"🤖 n8n 주가 수집 시작 - Week: {week}, Companies: {TOTAL_COMPANIES}")
    
    # 배치 작업 시작 로그
    batch_service = WeeklyBatchService(db)
    job_id = await batch_service.start_batch_job("stockprice", week)
    
    try:
        # 1. 기존 StockPrice Controller로 데이터 수집
        controller = StockPriceController(db_session=db)
        
        logger.info(f"🔍 주가 데이터 수집 시작 - {TOTAL_COMPANIES}개 기업")
        # 모든 기업 주가 수집
        stockprice_results = await controller.get_all_weekly_stock_data()
        
        logger.info(f"📊 주가 수집 완료 - {len(stockprice_results)}건")
        
        # 2. weekly_data 테이블용 데이터 변환
        weekly_items = []
        for stock in stockprice_results:
            # symbol이 기업명인 경우 그대로 사용, 종목코드인 경우 기업명 찾기
            if stock.symbol in GAME_COMPANIES.values():
                company_name = stock.symbol  # 이미 기업명
                stock_code = None
                for code, name in GAME_COMPANIES.items():
                    if name == stock.symbol:
                        stock_code = code
                        break
            else:
                company_name = GAME_COMPANIES.get(stock.symbol, f"Unknown_{stock.symbol}")
                stock_code = stock.symbol
            
            # 주가 정보를 요약한 텍스트 생성
            if stock.error:
                content = f"[오류] {stock.error}"
            else:
                change_text = "상승" if stock.changeRate > 0 else "하락" if stock.changeRate < 0 else "보합"
                content = f"주간 등락률: {stock.changeRate:.2f}% ({change_text}), "
                content += f"금요일 종가: {stock.today:,}원, "
                content += f"시가총액: {stock.marketCap:,}억원" if stock.marketCap else "시가총액: N/A"
                
                if stock.weekHigh and stock.weekLow:
                    content += f", 주간 고가: {stock.weekHigh:,}원, 주간 저가: {stock.weekLow:,}원"
            
            weekly_item = {
                "company_name": company_name,
                "content": content,
                "stock_code": stock_code or stock.symbol,
                "metadata": {
                    "market_cap": stock.marketCap,
                    "today_price": stock.today,
                    "last_week_price": stock.lastWeek,
                    "change_rate": stock.changeRate,
                    "week_high": stock.weekHigh,
                    "week_low": stock.weekLow,
                    "this_friday_date": getattr(stock, 'this_friday_date', None),
                    "last_friday_date": getattr(stock, 'last_friday_date', None),
                    "data_source": getattr(stock, 'data_source', None),
                    "error": stock.error,
                    "source": "stock_crawler"
                }
            }
            weekly_items.append(weekly_item)
        
        # 3. WeeklyDataService로 통합 테이블에 저장
        weekly_service = WeeklyDataService(db)
        result = await weekly_service.bulk_upsert_weekly_data(
            weekly_items=weekly_items,
            category="stockprice",
            week=week
        )
        
        # 4. 배치 작업 완료 로그
        await batch_service.finish_batch_job(job_id, result)
        
        logger.info(f"✅ n8n 주가 수집 완료 - {result}")
        
        # 통계 계산
        successful_stocks = [s for s in stockprice_results if not s.error]
        error_stocks = [s for s in stockprice_results if s.error]
        
        return {
            "status": result["status"],
            "updated": result["updated"],
            "skipped": result["skipped"],
            "errors": result["errors"],
            "week": result["week"],
            "total_companies": TOTAL_COMPANIES,
            "stockprice_stats": {
                "successful_count": len(successful_stocks),
                "error_count": len(error_stocks),
                "avg_change_rate": round(sum(s.changeRate for s in successful_stocks) / len(successful_stocks), 2) if successful_stocks else 0
            },
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"❌ n8n 주가 수집 실패: {str(e)}")
        
        # 배치 작업 실패 로그
        await batch_service.finish_batch_job(job_id, {}, str(e))
        
        raise HTTPException(
            status_code=500, 
            detail=f"주가 데이터 수집 중 오류 발생: {str(e)}"
        )


@router.get("/stockprice/status")
async def get_stockprice_collection_status(
    week: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    📊 주가 수집 상태 조회
    
    특정 주차의 주가 데이터 수집 현황을 반환
    """
    if not week:
        week = WeeklyDataModel.get_current_week_monday()
    
    try:
        weekly_service = WeeklyDataService(db)
        
        # 해당 주차 주가 데이터 조회
        stockprice_data = await weekly_service.get_weekly_data(
            week=week, 
            category="stockprice"
        )
        
        # 배치 작업 로그 조회
        batch_service = WeeklyBatchService(db)
        recent_jobs = await batch_service.get_recent_jobs(job_type="stockprice", limit=5)
        
        # 통계 계산
        change_rates = []
        error_count = 0
        for item in stockprice_data:
            metadata = item.get("metadata", {})
            if metadata.get("error"):
                error_count += 1
            elif metadata.get("change_rate") is not None:
                change_rates.append(metadata["change_rate"])
        
        avg_change_rate = sum(change_rates) / len(change_rates) if change_rates else 0
        positive_count = len([r for r in change_rates if r > 0])
        negative_count = len([r for r in change_rates if r < 0])
        
        return {
            "week": week,
            "stockprice_count": len(stockprice_data),
            "companies_collected": len(set(item["company_name"] for item in stockprice_data)),
            "total_target_companies": TOTAL_COMPANIES,
            "successful_count": len(change_rates),
            "error_count": error_count,
            "avg_change_rate": round(avg_change_rate, 2),
            "positive_stocks": positive_count,
            "negative_stocks": negative_count,
            "recent_jobs": recent_jobs,
            "sample_data": stockprice_data[:3] if stockprice_data else []
        }
        
    except Exception as e:
        logger.error(f"❌ 주가 수집 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"주가 수집 상태 조회 중 오류 발생: {str(e)}"
        )


@router.get("/stockprice/weeks")
async def get_available_stockprice_weeks(
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """📅 주가 데이터가 있는 주차 목록 조회"""
    try:
        weekly_service = WeeklyDataService(db)
        weeks = await weekly_service.get_available_weeks(limit=limit)
        
        return {
            "available_weeks": weeks,
            "total_weeks": len(weeks),
            "latest_week": weeks[0] if weeks else None
        }
        
    except Exception as e:
        logger.error(f"❌ 주차 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"주차 목록 조회 중 오류 발생: {str(e)}"
        ) 