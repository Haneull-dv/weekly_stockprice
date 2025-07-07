"""
CQRS 패턴 적용 StockPrice Command Side API

DDD + CQRS 구조:
- Command Side: stockprice 도메인 데이터를 로컬 테이블에 저장
- Projection: 로컬 저장 완료 후 weekly_data 테이블로 projection 전송
- Event-Driven: n8n 자동화와 연동
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging
import httpx
import sys
import os

# 프로젝트 루트 추가 (weekly_db 모듈 접근)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 도메인 서비스 import
from app.domain.controller.stockprice_controller import StockPriceController
from weekly_db.db.db_builder import get_db_session

# 주차 계산 utility import
from weekly_db.db.weekly_unified_model import WeeklyDataModel

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
router = APIRouter(prefix="/cqrs-stockprice")


@router.post("/collect-and-project")
async def collect_stockprice_with_cqrs(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    [CQRS Command Side] 주가 데이터 수집 → 로컬 저장 → Projection
    
    CQRS 패턴 적용:
    1. Command Side: 주가 데이터를 stockprice 도메인의 로컬 테이블에 저장
    2. Projection: 로컬 저장 완료 후 weekly_data 테이블로 projection 전송
    3. Event-Driven: 배치 작업 로그로 다른 서비스와 동기화
    
    n8n에서 매주 자동으로 호출됩니다.
    """
    job_id = None
    week = WeeklyDataModel.get_current_week_monday()
    
    try:
        logger.info(f"🔧 [CQRS Command] StockPrice 수집 시작 - Week: {week}")
        
        # ==========================================
        # 1. 배치 작업 시작 로그 (CQRS Monitoring)
        # ==========================================
        async with httpx.AsyncClient(timeout=30.0) as client:
            batch_start_response = await client.post(
                "http://weekly_data:8091/weekly-cqrs/domain-command/stockprice",
                params={
                    "week": week,
                    "action": "start_job"
                }
            )
            batch_start_result = batch_start_response.json()
            job_id = batch_start_result.get("job_id")
            
            logger.info(f"📝 [CQRS] 배치 작업 시작 로그 - Job ID: {job_id}")
        
        # ==========================================
        # 2. Command Side: 로컬 도메인 테이블에 저장
        # ==========================================
        
        # StockPrice Controller로 데이터 수집
        controller = StockPriceController(db_session=db)
        logger.info(f"🔍 [CQRS Command] 주가 데이터 수집 - {TOTAL_COMPANIES}개 기업")
        
        # 모든 기업 주가 수집
        stockprice_results = await controller.get_all_weekly_stock_data()
        logger.info(f"📊 [CQRS Command] 주가 수집 완료 - {len(stockprice_results)}건")
        
        # 로컬 테이블 저장 통계
        local_updated = 0
        local_skipped = 0
        projection_data = []  # weekly_data로 보낼 projection 데이터
        
        # ==========================================
        # 3. 로컬 테이블 저장 및 Projection 데이터 준비
        # ==========================================
        
        for stock in stockprice_results:
            try:
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
                
                # 로컬 테이블 저장은 기존 StockPriceController에서 이미 처리됨
                # (controller.get_all_weekly_stock_data() 내부에서 저장)
                local_updated += 1
                
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
                
                # Projection용 데이터 준비 (weekly_data 테이블로 전송할 형태)
                projection_item = {
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
                        "source": "stock_crawler",
                        "cqrs_pattern": "command_to_projection"
                    }
                }
                
                projection_data.append(projection_item)
                
                logger.debug(f"✅ [CQRS Command] 로컬 저장 및 Projection 준비: {company_name}")
                
            except Exception as e:
                logger.error(f"❌ [CQRS Command] 개별 주가 처리 실패: {str(e)}")
                local_skipped += 1
        
        # ==========================================
        # 4. Projection: weekly_data 테이블로 전송
        # ==========================================
        
        logger.info(f"🔄 [CQRS Projection] weekly_data로 projection 시작 - {len(projection_data)}건")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            projection_response = await client.post(
                "http://weekly_data:8091/weekly-cqrs/project-domain-data",
                params={
                    "category": "stockprice", 
                    "week": week
                },
                json=projection_data
            )
            projection_result = projection_response.json()
            
            logger.info(f"✅ [CQRS Projection] Projection 완료 - Updated: {projection_result.get('updated', 0)}")
        
        # ==========================================
        # 5. 배치 작업 완료 로그
        # ==========================================
        
        # 통계 계산
        successful_stocks = [s for s in stockprice_results if not s.error]
        error_stocks = [s for s in stockprice_results if s.error]
        
        final_result = {
            "local_updated": local_updated,
            "local_skipped": local_skipped,
            "projection_updated": projection_result.get("updated", 0),
            "projection_skipped": projection_result.get("skipped", 0),
            "total_collected": len(stockprice_results),
            "stockprice_stats": {
                "successful_count": len(successful_stocks),
                "error_count": len(error_stocks),
                "avg_change_rate": round(sum(s.changeRate for s in successful_stocks) / len(successful_stocks), 2) if successful_stocks else 0
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                "http://weekly_data:8091/weekly-cqrs/domain-command/stockprice",
                params={
                    "week": week,
                    "action": "finish_job"
                },
                json={
                    "job_id": job_id,
                    "result": final_result
                }
            )
            
            logger.info(f"📝 [CQRS] 배치 작업 완료 로그 - Job ID: {job_id}")
        
        # ==========================================
        # 6. 최종 응답
        # ==========================================
        
        return {
            "status": "success",
            "week": week,
            "cqrs_pattern": "command_side_completed",
            "local_storage": {
                "updated": local_updated,
                "skipped": local_skipped,
                "table": "stockprices"
            },
            "projection": {
                "updated": projection_result.get("updated", 0),
                "skipped": projection_result.get("skipped", 0),
                "table": "weekly_data"
            },
            "total_companies": TOTAL_COMPANIES,
            "total_collected": len(stockprice_results),
            "stockprice_stats": final_result["stockprice_stats"],
            "job_id": job_id,
            "collected_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        error_message = f"StockPrice CQRS 처리 실패: {str(e)}"
        logger.error(f"❌ [CQRS Command] {error_message}")
        
        # 배치 작업 실패 로그
        if job_id:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(
                        "http://weekly_data:8091/weekly-cqrs/domain-command/stockprice",
                        params={
                            "week": week,
                            "action": "fail_job"
                        },
                        json={
                            "job_id": job_id,
                            "error": error_message
                        }
                    )
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=error_message
        )


@router.get("/cqrs-status")
async def get_stockprice_cqrs_status() -> Dict[str, Any]:
    """
    [CQRS Status] StockPrice 도메인 CQRS 상태 확인
    
    현재 CQRS 패턴 구현 상태와 도메인 서비스 정보를 반환합니다.
    """
    return {
        "service": "weekly_stockprice",
        "cqrs_pattern": "enabled",
        "domain": "stockprice",
        "endpoints": {
            "command_side": "/cqrs-stockprice/collect-and-project",
            "status": "/cqrs-stockprice/cqrs-status"
        },
        "table_structure": {
            "local_table": "stockprices",
            "projection_table": "weekly_data"
        },
        "supported_companies": TOTAL_COMPANIES,
        "data_source": "stock_crawler",
        "processing_pipeline": [
            "주가 데이터 수집",
            "시가총액 계산",
            "등락률 계산",
            "로컬 저장",
            "Projection"
        ]
    } 