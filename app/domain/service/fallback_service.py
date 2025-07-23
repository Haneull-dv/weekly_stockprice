import json
import os
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from ..schema.stockprice_schema import WeeklyStockPriceResponse, StockPriceListResponse
from app.config.companies import KOREAN_COMPANIES_MAP

class StockPriceFallbackService:
    """주가 데이터 Fallback 서비스 (DB 연결 실패 시 사용)"""
    
    def __init__(self):
        # fallback 파일 경로 설정
        self.fallback_file_path = Path(__file__).parent.parent.parent / "fallback" / "fallback_stockprice.jsonl"
        print(f"📁 [Fallback] 주가 fallback 파일 경로: {self.fallback_file_path}")
    
    async def load_fallback_data(self) -> List[Dict[str, Any]]:
        """JSONL 파일에서 fallback 데이터 로드"""
        try:
            print(f"📁 [Fallback] 주가 데이터 로드 시도: {self.fallback_file_path}")
            
            if not self.fallback_file_path.exists():
                print(f"❌ [Fallback] 파일이 존재하지 않음: {self.fallback_file_path}")
                return []
            
            fallback_data = []
            with open(self.fallback_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        fallback_data.append(data)
            
            print(f"📁 [Fallback] 주가 데이터 로드 성공: {len(fallback_data)}개 종목")
            return fallback_data
            
        except Exception as e:
            print(f"❌ [Fallback] 주가 데이터 로드 실패: {str(e)}")
            return []
    
    async def get_fallback_stock_list(self, page: int = 1, page_size: int = 20) -> StockPriceListResponse:
        """DB 실패 시 fallback 주가 리스트 반환"""
        print(f"📁 [Fallback] 주가 리스트 생성 시작 - 페이지: {page}, 크기: {page_size}")
        
        try:
            # 1. Fallback 데이터 로드
            fallback_data = await self.load_fallback_data()
            
            if not fallback_data:
                return StockPriceListResponse(
                    status="fallback_empty",
                    message="DB 연결 실패 및 fallback 데이터 없음",
                    data=[],
                    total_count=0,
                    page=page,
                    page_size=page_size
                )
            
            # 2. WeeklyStockPriceResponse 형식으로 변환
            stock_responses = []
            for item in fallback_data:
                # 종목코드를 기업명으로 변환
                company_name = KOREAN_COMPANIES_MAP.get(item["symbol"], item["symbol"])
                
                stock_response = WeeklyStockPriceResponse(
                    symbol=company_name,  # 기업명으로 변환
                    companyName=company_name,
                    marketCap=item.get("marketCap"),
                    today=item.get("currentPrice"),
                    lastWeek=None,  # fallback에는 없는 데이터
                    changeRate=item.get("changeRate"),
                    weekHigh=None,  # fallback에는 없는 데이터
                    weekLow=None,   # fallback에는 없는 데이터
                    thisFridayDate=None,
                    lastFridayDate=None,
                    error=None
                )
                stock_responses.append(stock_response)
            
            # 3. 시가총액 기준으로 정렬 (내림차순)
            stock_responses.sort(key=lambda x: x.marketCap or 0, reverse=True)
            
            # 4. 페이징 적용
            total_count = len(stock_responses)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_data = stock_responses[start_idx:end_idx]
            
            print(f"📁 [Fallback] 주가 리스트 생성 완료: {len(paginated_data)}개 (전체 {total_count}개)")
            
            return StockPriceListResponse(
                status="fallback_success",
                message="DB 연결 실패로 fallback 데이터 제공",
                data=paginated_data,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            print(f"❌ [Fallback] 주가 리스트 생성 실패: {str(e)}")
            return StockPriceListResponse(
                status="fallback_error",
                message=f"Fallback 데이터 처리 중 오류: {str(e)}",
                data=[],
                total_count=0,
                page=page,
                page_size=page_size
            )
    
    async def check_db_connection(self, db_session) -> bool:
        """DB 연결 상태 확인 (1초 timeout)"""
        try:
            # 1초 timeout으로 DB 연결 테스트
            await asyncio.wait_for(
                self._test_db_connection(db_session),
                timeout=1.0
            )
            return True
        except asyncio.TimeoutError:
            print("⏱️ [Fallback] DB 연결 timeout (1초)")
            return False
        except Exception as e:
            print(f"❌ [Fallback] DB 연결 실패: {str(e)}")
            return False
    
    async def _test_db_connection(self, db_session):
        """실제 DB 연결 테스트"""
        from sqlalchemy import text
        await db_session.execute(text("SELECT 1"))
        await db_session.commit() 