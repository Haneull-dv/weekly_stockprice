from typing import List, Optional
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.stockprice_model import StockPriceModel, DailyStockDataModel
from ..schema.stockprice_schema import WeeklyStockPriceCreate, WeeklyStockPriceUpdate


class StockPriceRepository:
    """주간 주가 정보 Repository 클래스"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(self, stockprice_data: WeeklyStockPriceCreate) -> StockPriceModel:
        """새로운 주가 정보 생성"""
        stockprice = StockPriceModel(
            symbol=stockprice_data.symbol,
            market_cap=stockprice_data.market_cap,
            today=stockprice_data.today,
            last_week=stockprice_data.last_week,
            change_rate=stockprice_data.change_rate,
            week_high=stockprice_data.week_high,
            week_low=stockprice_data.week_low,
            error=stockprice_data.error,
            this_friday_date=stockprice_data.this_friday_date,
            last_friday_date=stockprice_data.last_friday_date,
            data_source=stockprice_data.data_source
        )
        
        self.db.add(stockprice)
        await self.db.commit()
        await self.db.refresh(stockprice)
        return stockprice
    
    async def get_by_id(self, stockprice_id: int) -> Optional[StockPriceModel]:
        """ID로 주가 정보 조회"""
        query = select(StockPriceModel).where(StockPriceModel.id == stockprice_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[StockPriceModel]:
        """모든 주가 정보 조회 (페이징)"""
        query = (
            select(StockPriceModel)
            .order_by(desc(StockPriceModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_symbol(self, symbol: str, date: Optional[str] = None) -> Optional[StockPriceModel]:
        """
        종목 심볼로 주가 정보 조회. 특정 날짜가 주어지면 해당 날짜 또는 그 이전의 가장 최신 데이터를 조회.
        """
        query = select(StockPriceModel).where(StockPriceModel.symbol == symbol)
        
        if date:
            # SQLAlchemy는 datetime 객체를 직접 비교하는 것을 권장합니다.
            # 이 예제에서는 created_at이 이미 datetime 객체라고 가정합니다.
            # 실제로는 date 문자열을 datetime 객체로 변환해야 할 수 있습니다.
            # 예: from datetime import datetime; date_obj = datetime.strptime(date, '%Y-%m-%d')
            query = query.where(StockPriceModel.created_at <= date)
        
        query = query.order_by(desc(StockPriceModel.created_at)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_latest_prices(self, date: Optional[str] = None) -> List[StockPriceModel]:
        """
        모든 종목의 최신 주가 정보 조회. 특정 날짜가 주어지면 해당 날짜 기준 최신 데이터를 조회.
        """
        # 각 심볼별로 특정 날짜 또는 그 이전의 최신 데이터만 조회
        subquery = select(
            StockPriceModel.symbol,
            func.max(StockPriceModel.created_at).label('max_created_at')
        )
        if date:
            subquery = subquery.where(StockPriceModel.created_at <= date)
        
        subquery = subquery.group_by(StockPriceModel.symbol).subquery()
        
        query = (
            select(StockPriceModel)
            .join(
                subquery,
                and_(
                    StockPriceModel.symbol == subquery.c.symbol,
                    StockPriceModel.created_at == subquery.c.max_created_at
                )
            )
            .order_by(StockPriceModel.symbol)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_symbols(self, symbols: List[str], date: Optional[str] = None) -> List[StockPriceModel]:
        """여러 종목 심볼로 특정 날짜 기준 최신 주가 정보 조회"""
        
        subquery = (
            select(
                StockPriceModel.symbol,
                func.max(StockPriceModel.created_at).label('max_created_at')
            )
            .where(StockPriceModel.symbol.in_(symbols))
        )
        if date:
            subquery = subquery.where(StockPriceModel.created_at <= date)
            
        subquery = subquery.group_by(StockPriceModel.symbol).subquery()
        
        query = (
            select(StockPriceModel)
            .join(
                subquery,
                and_(
                    StockPriceModel.symbol == subquery.c.symbol,
                    StockPriceModel.created_at == subquery.c.max_created_at
                )
            )
            .order_by(StockPriceModel.symbol)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_change_rate_range(
        self, 
        min_rate: float, 
        max_rate: float
    ) -> List[StockPriceModel]:
        """등락률 범위로 주가 정보 조회"""
        query = (
            select(StockPriceModel)
            .where(
                and_(
                    StockPriceModel.change_rate >= min_rate,
                    StockPriceModel.change_rate <= max_rate
                )
            )
            .order_by(desc(StockPriceModel.change_rate))
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_top_gainers(self, limit: int = 10) -> List[StockPriceModel]:
        """상승률 상위 종목 조회"""
        # 최신 데이터만 대상
        latest_prices = await self.get_all_latest_prices()
        
        # 상승률 순으로 정렬하여 상위 N개 반환
        gainers = [
            price for price in latest_prices 
            if price.change_rate is not None and price.change_rate > 0
        ]
        gainers.sort(key=lambda x: x.change_rate, reverse=True)
        
        return gainers[:limit]
    
    async def get_top_losers(self, limit: int = 10) -> List[StockPriceModel]:
        """하락률 상위 종목 조회"""
        # 최신 데이터만 대상
        latest_prices = await self.get_all_latest_prices()
        
        # 하락률 순으로 정렬하여 상위 N개 반환
        losers = [
            price for price in latest_prices 
            if price.change_rate is not None and price.change_rate < 0
        ]
        losers.sort(key=lambda x: x.change_rate)
        
        return losers[:limit]
    
    async def get_market_statistics(self) -> dict:
        """시장 통계 정보 조회"""
        latest_prices = await self.get_all_latest_prices()
        
        if not latest_prices:
            return {
                "total_companies": 0,
                "positive_change": 0,
                "negative_change": 0,
                "unchanged": 0,
                "average_change_rate": 0.0,
                "max_change_rate": 0.0,
                "min_change_rate": 0.0,
                "total_market_cap": 0
            }
        
        # 통계 계산
        valid_changes = [p.change_rate for p in latest_prices if p.change_rate is not None]
        valid_market_caps = [p.market_cap for p in latest_prices if p.market_cap is not None]
        
        positive_count = len([r for r in valid_changes if r > 0])
        negative_count = len([r for r in valid_changes if r < 0])
        unchanged_count = len([r for r in valid_changes if r == 0])
        
        return {
            "total_companies": len(latest_prices),
            "positive_change": positive_count,
            "negative_change": negative_count,
            "unchanged": unchanged_count,
            "average_change_rate": round(sum(valid_changes) / len(valid_changes), 2) if valid_changes else 0.0,
            "max_change_rate": round(max(valid_changes), 2) if valid_changes else 0.0,
            "min_change_rate": round(min(valid_changes), 2) if valid_changes else 0.0,
            "total_market_cap": sum(valid_market_caps) if valid_market_caps else 0
        }
    
    async def count_total(self) -> int:
        """전체 주가 레코드 개수 조회"""
        query = select(func.count(StockPriceModel.id))
        result = await self.db.execute(query)
        return result.scalar()
    
    async def update(
        self, 
        stockprice_id: int, 
        stockprice_data: WeeklyStockPriceUpdate
    ) -> Optional[StockPriceModel]:
        """주가 정보 수정 (기존 로직 유지)"""
        stockprice = await self.get_by_id(stockprice_id)
        if stockprice:
            update_data = stockprice_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(stockprice, key, value)
            
            stockprice.updated_at = func.now()
            
            await self.db.commit()
            await self.db.refresh(stockprice)
        return stockprice
    
    async def bulk_create(self, stockprices_data: List[WeeklyStockPriceCreate]) -> List[StockPriceModel]:
        """주가 정보 대량 생성 (항상 새로 추가)"""
        stockprices = []
        for data in stockprices_data:
            stockprice = StockPriceModel(
                symbol=data.symbol,
                market_cap=data.market_cap,
                today=data.today,
                last_week=data.last_week,
                change_rate=data.change_rate,
                week_high=data.week_high,
                week_low=data.week_low,
                error=data.error,
                this_friday_date=data.this_friday_date,
                last_friday_date=data.last_friday_date,
                data_source=data.data_source
            )
            stockprices.append(stockprice)
        
        self.db.add_all(stockprices)
        await self.db.commit()
        
        # 새로 생성된 ID로 다시 조회
        for stockprice in stockprices:
            await self.db.refresh(stockprice)
        
        return stockprices
    
    async def delete(self, stockprice_id: int) -> bool:
        """주가 정보 삭제"""
        stockprice = await self.get_by_id(stockprice_id)
        if stockprice:
            await self.db.delete(stockprice)
            await self.db.commit()
            return True
        return False
