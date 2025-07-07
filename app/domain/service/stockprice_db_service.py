from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.companies import GAME_COMPANIES, TOTAL_COMPANIES
from ..repository.stockprice_repository import StockPriceRepository
from ..model.stockprice_model import StockPriceModel
from ..schema.stockprice_schema import (
    WeeklyStockPriceCreate,
    WeeklyStockPriceResponse,
    StockPriceListResponse,
    StockPriceBatchResponse,
    StockMarketStats,
    GameCompaniesResponse,
    GameCompany
)


class StockPriceDbService:
    """주간 주가 정보 DB 접근 전용 서비스"""
    
    def __init__(self, db_session: AsyncSession):
        self.repository = StockPriceRepository(db_session)
        
        # Config에서 게임기업 정보 로드
        self.game_companies = GAME_COMPANIES
        
        print(f"⚙️ StockPriceDB 서비스 초기화 - 게임기업 {TOTAL_COMPANIES}개 등록")
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> StockPriceListResponse:
        """모든 주가 정보 조회 (페이징)"""
        print("🗄️ [DB] 모든 주가 정보 조회")
        
        stock_prices = await self.repository.get_all(skip=skip, limit=limit)
        total_count = await self.repository.count_total()
        
        # WeeklyStockPriceResponse 형태로 변환
        stock_data = []
        for stock in stock_prices:
            stock_data.append(WeeklyStockPriceResponse(
                symbol=stock.symbol,
                companyName=stock.symbol,
                marketCap=stock.market_cap,
                today=stock.today,
                lastWeek=stock.last_week,
                changeRate=stock.change_rate,
                weekHigh=stock.week_high,
                weekLow=stock.week_low,
                error=stock.error,
                thisFridayDate=stock.this_friday_date,
                lastFridayDate=stock.last_friday_date
            ))
        
        return StockPriceListResponse(
            status="success",
            message="주가 데이터 조회 완료",
            data=stock_data,
            total_count=total_count,
            companies_processed=len(set(s.symbol for s in stock_prices)),
            last_updated=max(s.updated_at for s in stock_prices).isoformat() if stock_prices else None
        )
    
    async def get_by_id(self, stockprice_id: int) -> Optional[WeeklyStockPriceResponse]:
        """ID로 주가 정보 조회"""
        print(f"🗄️ [DB] 주가 정보 조회 - ID: {stockprice_id}")
        
        stock = await self.repository.get_by_id(stockprice_id)
        if not stock:
            return None
        
        return WeeklyStockPriceResponse(
            symbol=stock.symbol,
            companyName=stock.symbol,
            marketCap=stock.market_cap,
            today=stock.today,
            lastWeek=stock.last_week,
            changeRate=stock.change_rate,
            weekHigh=stock.week_high,
            weekLow=stock.week_low,
            error=stock.error,
            thisFridayDate=stock.this_friday_date,
            lastFridayDate=stock.last_friday_date
        )
    
    async def get_by_symbol(self, symbol: str) -> Optional[WeeklyStockPriceResponse]:
        """종목 심볼로 최신 주가 정보 조회"""
        print(f"🗄️ [DB] 주가 정보 조회 - 심볼: {symbol}")
        
        stock = await self.repository.get_by_symbol(symbol)
        if not stock:
            return None
        
        return WeeklyStockPriceResponse(
            symbol=stock.symbol,
            companyName=stock.symbol,
            marketCap=stock.market_cap,
            today=stock.today,
            lastWeek=stock.last_week,
            changeRate=stock.change_rate,
            weekHigh=stock.week_high,
            weekLow=stock.week_low,
            error=stock.error,
            thisFridayDate=stock.this_friday_date,
            lastFridayDate=stock.last_friday_date
        )
    
    async def get_all_latest_prices(self) -> List[WeeklyStockPriceResponse]:
        """모든 종목의 최신 주가 정보 조회"""
        print("🗄️ [DB] 모든 종목 최신 주가 조회")
        
        stocks = await self.repository.get_all_latest_prices()
        return [
            WeeklyStockPriceResponse(
                symbol=stock.symbol,
                companyName=stock.symbol,
                marketCap=stock.market_cap,
                today=stock.today,
                lastWeek=stock.last_week,
                changeRate=stock.change_rate,
                weekHigh=stock.week_high,
                weekLow=stock.week_low,
                error=stock.error,
                thisFridayDate=stock.this_friday_date,
                lastFridayDate=stock.last_friday_date
            )
            for stock in stocks
        ]
    
    async def get_by_symbols(self, symbols: List[str]) -> List[WeeklyStockPriceResponse]:
        """여러 종목 심볼로 최신 주가 정보 조회"""
        print(f"🗄️ [DB] 복수 종목 주가 조회 - {len(symbols)}개")
        
        stocks = await self.repository.get_by_symbols(symbols)
        return [
            WeeklyStockPriceResponse(
                symbol=stock.symbol,
                companyName=stock.symbol,
                marketCap=stock.market_cap,
                today=stock.today,
                lastWeek=stock.last_week,
                changeRate=stock.change_rate,
                weekHigh=stock.week_high,
                weekLow=stock.week_low,
                error=stock.error,
                thisFridayDate=stock.this_friday_date,
                lastFridayDate=stock.last_friday_date
            )
            for stock in stocks
        ]
    
    async def get_top_gainers(self, limit: int = 10) -> List[WeeklyStockPriceResponse]:
        """상승률 상위 종목 조회"""
        print(f"🗄️ [DB] 상승률 상위 {limit}개 종목 조회")
        
        stocks = await self.repository.get_top_gainers(limit)
        return [
            WeeklyStockPriceResponse(
                symbol=stock.symbol,
                companyName=stock.symbol,
                marketCap=stock.market_cap,
                today=stock.today,
                lastWeek=stock.last_week,
                changeRate=stock.change_rate,
                weekHigh=stock.week_high,
                weekLow=stock.week_low,
                error=stock.error,
                thisFridayDate=stock.this_friday_date,
                lastFridayDate=stock.last_friday_date
            )
            for stock in stocks
        ]
    
    async def get_top_losers(self, limit: int = 10) -> List[WeeklyStockPriceResponse]:
        """하락률 상위 종목 조회"""
        print(f"🗄️ [DB] 하락률 상위 {limit}개 종목 조회")
        
        stocks = await self.repository.get_top_losers(limit)
        return [
            WeeklyStockPriceResponse(
                symbol=stock.symbol,
                companyName=stock.symbol,
                marketCap=stock.market_cap,
                today=stock.today,
                lastWeek=stock.last_week,
                changeRate=stock.change_rate,
                weekHigh=stock.week_high,
                weekLow=stock.week_low,
                error=stock.error,
                thisFridayDate=stock.this_friday_date,
                lastFridayDate=stock.last_friday_date
            )
            for stock in stocks
        ]
    
    async def get_by_change_rate_range(
        self, 
        min_rate: float, 
        max_rate: float
    ) -> List[WeeklyStockPriceResponse]:
        """등락률 범위로 주가 정보 조회"""
        print(f"🗄️ [DB] 등락률 범위 조회 - {min_rate}% ~ {max_rate}%")
        
        stocks = await self.repository.get_by_change_rate_range(min_rate, max_rate)
        return [
            WeeklyStockPriceResponse(
                symbol=stock.symbol,
                companyName=stock.symbol,
                marketCap=stock.market_cap,
                today=stock.today,
                lastWeek=stock.last_week,
                changeRate=stock.change_rate,
                weekHigh=stock.week_high,
                weekLow=stock.week_low,
                error=stock.error,
                thisFridayDate=stock.this_friday_date,
                lastFridayDate=stock.last_friday_date
            )
            for stock in stocks
        ]
    
    async def get_summary_statistics(self) -> StockMarketStats:
        """주식 시장 요약 통계"""
        print("🗄️ [DB] 주식 시장 통계 조회")
        
        stats = await self.repository.get_market_statistics()
        return StockMarketStats(
            total_companies=stats["total_companies"],
            positive_change=stats["positive_change"],
            negative_change=stats["negative_change"],
            unchanged=stats["unchanged"],
            average_change_rate=stats["average_change_rate"],
            max_change_rate=stats["max_change_rate"],
            min_change_rate=stats["min_change_rate"],
            total_market_cap=stats["total_market_cap"]
        )
    
    async def get_game_companies(self) -> GameCompaniesResponse:
        """게임 기업 목록 조회"""
        print("🗄️ [DB] 게임 기업 목록 조회")
        
        from app.config.companies import COMPANY_INFO
        companies = []
        for symbol, name in self.game_companies.items():
            country = COMPANY_INFO[symbol]["country"] if symbol in COMPANY_INFO else "Unknown"
            companies.append(GameCompany(
                symbol=symbol,
                name=name,
                market="KOSPI" if symbol in ["036570", "259960"] else "KOSDAQ",
                sector="게임",
                country=country
            ))
        
        return GameCompaniesResponse(
            status="success",
            message="게임 기업 목록 조회 완료",
            companies=companies,
            total_count=len(companies)
        )
    
    async def count_total(self) -> int:
        """전체 주가 레코드 개수 조회"""
        print("🗄️ [DB] 전체 주가 레코드 개수 조회")
        return await self.repository.count_total()
    
    async def create(self, stockprice_data: WeeklyStockPriceCreate) -> WeeklyStockPriceResponse:
        """새로운 주가 정보 생성"""
        print(f"🗄️ [DB] 주가 정보 생성 - 심볼: {stockprice_data.symbol}")
        
        stock = await self.repository.create(stockprice_data)
        return WeeklyStockPriceResponse(
            symbol=stock.symbol,
            companyName=stock.symbol,
            marketCap=stock.market_cap,
            today=stock.today,
            lastWeek=stock.last_week,
            changeRate=stock.change_rate,
            weekHigh=stock.week_high,
            weekLow=stock.week_low,
            error=stock.error,
            thisFridayDate=stock.this_friday_date,
            lastFridayDate=stock.last_friday_date
        )
    
    async def bulk_create(
        self, 
        stockprices_data: List[WeeklyStockPriceCreate]
    ) -> StockPriceBatchResponse:
        """주가 정보 대량 생성"""
        print(f"🗄️ [DB] 주가 정보 대량 생성 - {len(stockprices_data)}건")
        
        start_time = __import__('time').time()
        
        try:
            stocks = await self.repository.bulk_create(stockprices_data)
            
            from app.config.companies import COMPANY_INFO
            results = [
                WeeklyStockPriceResponse(
                    symbol=stock.symbol,
                    companyName=stock.symbol,
                    marketCap=stock.market_cap,
                    today=stock.today,
                    lastWeek=stock.last_week,
                    changeRate=stock.change_rate,
                    weekHigh=stock.week_high,
                    weekLow=stock.week_low,
                    error=stock.error,
                    thisFridayDate=stock.this_friday_date,
                    lastFridayDate=stock.last_friday_date
                )
                for stock in stocks
            ]
            
            processing_time = __import__('time').time() - start_time
            
            return StockPriceBatchResponse(
                status="success",
                message=f"{len(stocks)}개 주가 데이터 대량 생성 완료",
                processed_companies=len(stockprices_data),
                success_count=len(stocks),
                error_count=len(stockprices_data) - len(stocks),
                results=results,
                processing_time=processing_time
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # 에러의 전체 traceback을 출력
            processing_time = __import__('time').time() - start_time
            
            return StockPriceBatchResponse(
                status="error",
                message=f"대량 생성 실패: {str(e)}",
                processed_companies=len(stockprices_data),
                success_count=0,
                error_count=len(stockprices_data),
                results=[],
                processing_time=processing_time
            )
    
    async def upsert_by_symbol(
        self, 
        stockprice_data: WeeklyStockPriceCreate
    ) -> WeeklyStockPriceResponse:
        """종목 심볼 기준으로 업서트 (있으면 업데이트, 없으면 생성)"""
        print(f"🗄️ [DB] 주가 정보 업서트 - 심볼: {stockprice_data.symbol}")
        
        stock = await self.repository.upsert_by_symbol(stockprice_data)
        return WeeklyStockPriceResponse(
            symbol=stock.symbol,
            companyName=stock.symbol,
            marketCap=stock.market_cap,
            today=stock.today,
            lastWeek=stock.last_week,
            changeRate=stock.change_rate,
            weekHigh=stock.week_high,
            weekLow=stock.week_low,
            error=stock.error,
            thisFridayDate=stock.this_friday_date,
            lastFridayDate=stock.last_friday_date
        )
    
    async def update(
        self, 
        stockprice_id: int, 
        stockprice_data: dict
    ) -> Optional[WeeklyStockPriceResponse]:
        """주가 정보 수정"""
        print(f"🗄️ [DB] 주가 정보 수정 - ID: {stockprice_id}")
        
        from ..schema.stockprice_schema import WeeklyStockPriceUpdate
        update_schema = WeeklyStockPriceUpdate(**stockprice_data)
        
        stock = await self.repository.update(stockprice_id, update_schema)
        if not stock:
            return None
        
        return WeeklyStockPriceResponse(
            symbol=stock.symbol,
            companyName=stock.symbol,
            marketCap=stock.market_cap,
            today=stock.today,
            lastWeek=stock.last_week,
            changeRate=stock.change_rate,
            weekHigh=stock.week_high,
            weekLow=stock.week_low,
            error=stock.error,
            thisFridayDate=stock.this_friday_date,
            lastFridayDate=stock.last_friday_date
        )
    
    async def delete(self, stockprice_id: int) -> bool:
        """주가 정보 삭제"""
        print(f"🗄️ [DB] 주가 정보 삭제 - ID: {stockprice_id}")
        return await self.repository.delete(stockprice_id)
