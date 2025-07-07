import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import httpx
from bs4 import BeautifulSoup
import re
from app.config.companies import GAME_COMPANIES, TOTAL_COMPANIES, COMPANY_INFO
from ..schema.stockprice_schema import WeeklyStockPriceResponse, StockDataPoint

# Settings import
from app.config.settings import (
    DAILY_CHART_URL_TEMPLATE,
    MAIN_PAGE_URL_TEMPLATE,
    REQUEST_TIMEOUT,
    USER_AGENT,
    DEFAULT_DAYS_BACK,
    MARKET_CAP_PATTERNS
)

# Config 직접 정의 (import 이슈 회피)


class StockPriceService:
    def __init__(self):
        # Config에서 설정 로드
        self.game_companies = GAME_COMPANIES
        self.timeout = REQUEST_TIMEOUT
        self.user_agent = USER_AGENT
        self.default_days = DEFAULT_DAYS_BACK
        self.market_cap_patterns = MARKET_CAP_PATTERNS
        
        print(f"⚙️ StockPrice 서비스 초기화 - 게임기업 {TOTAL_COMPANIES}개 등록")
    
    async def fetch_all_weekly_stock_data(self) -> List[WeeklyStockPriceResponse]:
        """전체 게임기업 주간 주가 데이터 조회 (controller에서 이동한 로직)"""
        print("🤍3. 전체 게임기업 주간 데이터 서비스 로직 진입")
        
        # 병렬로 모든 기업 데이터 수집
        tasks = [
            self.fetch_weekly_stock_data(code) 
            for code in self.game_companies.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리 (예외 처리된 결과 제외)
        weekly_data = []
        for result in results:
            if isinstance(result, WeeklyStockPriceResponse):
                weekly_data.append(result)
            elif isinstance(result, Exception):
                print(f"❌ 기업 데이터 수집 실패: {str(result)}")
        
        print(f"✅ 전체 게임기업 데이터 수집 완료: {len(weekly_data)}개")
        return weekly_data
    
    def get_game_companies_info(self) -> Dict[str, Any]:
        """게임기업 리스트 정보 반환 (국가 정보 포함)"""
        print("🤍3. 게임기업 리스트 서비스 로직 진입")
        companies = []
        for symbol, info in COMPANY_INFO.items():
            companies.append({
                "symbol": symbol,
                "name": info["name"],
                "country": info["country"]
            })
        return {
            "companies": companies,
            "total_count": len(companies)
        }
        
    def _get_friday_dates(self) -> tuple[str, str]:
        """실제 달력 기준으로 이번 주/전주 금요일 날짜 계산"""
        today = datetime.now()
        
        # 이번 주 금요일 계산 (금요일 = 4)
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.weekday() == 4:
            # 오늘이 금요일이면 오늘
            this_friday = today
        elif days_until_friday == 0:
            # 토요일/일요일이면 지난 금요일
            this_friday = today - timedelta(days=today.weekday() + 1)
        else:
            # 이번 주 금요일이 아직 오지 않았으면 지난 금요일
            if today.weekday() > 4:  # 토요일(5), 일요일(6)
                this_friday = today - timedelta(days=today.weekday() - 4)
            else:  # 월-목요일
                this_friday = today - timedelta(days=today.weekday() + 3)
        
        # 전주 금요일 = 이번 주 금요일 - 7일
        last_friday = this_friday - timedelta(days=7)
        
        # 날짜 형식을 일별시세 페이지와 맞춤 (예: "2024.01.12")
        this_friday_str = this_friday.strftime("%Y.%m.%d")
        last_friday_str = last_friday.strftime("%Y.%m.%d")
        
        print(f"📅 계산된 날짜: 이번 주 금요일={this_friday_str}, 전주 금요일={last_friday_str}")
        return this_friday_str, last_friday_str
    
    def _find_closest_trading_day(self, target_date: str, daily_data: List[StockDataPoint]) -> Optional[StockDataPoint]:
        """목표 날짜에서 가장 가까운 거래일 데이터 찾기"""
        target_dt = datetime.strptime(target_date, "%Y.%m.%d")
        
        # 정확한 날짜 먼저 찾기
        for data in daily_data:
            if data.date == target_date:
                print(f"✅ 정확한 날짜 매칭: {target_date} -> {data.close:,}원")
                return data
        
        # 정확한 날짜가 없으면 가장 가까운 이전 거래일 찾기
        closest_data = None
        min_diff = float('inf')
        
        for data in daily_data:
            try:
                data_dt = datetime.strptime(data.date, "%Y.%m.%d")
                # 목표 날짜 이전의 거래일만 고려
                if data_dt <= target_dt:
                    diff = (target_dt - data_dt).days
                    if diff < min_diff:
                        min_diff = diff
                        closest_data = data
            except:
                continue
        
        if closest_data:
            print(f"📍 가장 가까운 거래일: {target_date} -> {closest_data.date} ({closest_data.close:,}원)")
            return closest_data
        
        print(f"❌ {target_date}에 해당하는 거래일을 찾을 수 없음")
        return None
        
    async def fetch_weekly_stock_data(self, symbol: str) -> WeeklyStockPriceResponse:
        """주간 주가 데이터 수집 메인 메서드 (실제 달력 기준)"""
        stock_code = self._get_stock_code(symbol)
        company_name = COMPANY_INFO.get(stock_code, {}).get('name', symbol)
        
        print(f"🤍[주간 데이터 수집 시작] {company_name}({stock_code})")
        
        try:
            # 기업명 확인 (symbol이 기업명인 경우 코드로 변환)
            
            print(f"📊 처리 중: {company_name} ({stock_code})")
            
            # 실제 달력 기준 금요일 날짜 계산
            this_friday, last_friday = self._get_friday_dates()
            
            # 1. 시가총액 수집
            market_cap = await self._fetch_market_cap(stock_code)
            
            # 2. 일별시세 데이터 수집 (최근 3주치)
            daily_data = await self._fetch_daily_data(stock_code, days=21)
            
            if not daily_data:
                return WeeklyStockPriceResponse(
                    symbol=stock_code,
                    companyName=company_name,
                    error="일별시세 데이터를 가져올 수 없습니다",
                    thisFridayDate=this_friday,
                    lastFridayDate=last_friday
                )
            
            # 3. 실제 금요일 날짜로 주간 데이터 계산
            weekly_stats = self._calculate_weekly_stats_by_date(daily_data, this_friday, last_friday)
            
            return WeeklyStockPriceResponse(
                symbol=stock_code,
                companyName=company_name,
                marketCap=market_cap,
                today=weekly_stats.get("today"),
                lastWeek=weekly_stats.get("lastWeek"),
                changeRate=weekly_stats.get("changeRate"),
                weekHigh=weekly_stats.get("weekHigh"),
                weekLow=weekly_stats.get("weekLow"),
                thisFridayDate=this_friday,
                lastFridayDate=last_friday
            )
            
        except Exception as e:
            print(f"❌ [주간 데이터 수집 실패] {company_name}({stock_code}): {str(e)}")
            # 실패 시에도 날짜 필드를 None으로 포함하여 반환
            this_friday, last_friday = self._get_friday_dates()
            return WeeklyStockPriceResponse(
                symbol=stock_code,
                companyName=company_name,
                error=f"데이터 수집 실패: {str(e)}",
                thisFridayDate=this_friday,
                lastFridayDate=last_friday
            )
    
    def _get_stock_code(self, symbol: str) -> str:
        """기업명을 종목코드로 변환 또는 종목코드 검증"""
        # 이미 종목코드인 경우
        if symbol in self.game_companies:
            return symbol
            
        # 기업명으로 검색
        for code, name in self.game_companies.items():
            if symbol in name or name in symbol:
                return code
                
        # 기본값으로 크래프톤 반환
        return "259960"
    
    async def _fetch_market_cap(self, stock_code: str) -> Optional[int]:
        """시가총액 수집"""
        url = MAIN_PAGE_URL_TEMPLATE.format(code=stock_code)
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=self.timeout)
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 시가총액 찾기 - 여러 패턴 시도                
                for pattern in self.market_cap_patterns:
                    try:
                        element = soup.select_one(pattern)
                        if element:
                            text = element.get_text().strip()
                            # 숫자와 단위 추출
                            numbers = re.findall(r'[\d,]+', text)
                            if numbers:
                                market_cap_str = numbers[0].replace(',', '')
                                market_cap = int(market_cap_str)
                                
                                # 단위 확인 (조, 억)
                                if '조' in text:
                                    market_cap *= 10000  # 조 -> 억
                                    
                                print(f"💰 시가총액: {market_cap}억원")
                                return market_cap
                    except:
                        continue
                        
                # 대안: 테이블에서 찾기
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for i, cell in enumerate(cells):
                            if '시가총액' in cell.get_text():
                                if i + 1 < len(cells):
                                    cap_text = cells[i + 1].get_text().strip()
                                    numbers = re.findall(r'[\d,]+', cap_text)
                                    if numbers:
                                        cap_value = int(numbers[0].replace(',', ''))
                                        if '조' in cap_text:
                                            cap_value *= 10000
                                        return cap_value
                
                print(f"⚠️ 시가총액 파싱 실패: {stock_code}")
                return None
                
        except Exception as e:
            print(f"❌ 시가총액 수집 실패 {stock_code}: {str(e)}")
            return None
    
    async def _fetch_daily_data(self, stock_code: str, days: int = None) -> List[StockDataPoint]:
        """일별시세 데이터 수집"""
        if days is None:
            days = self.default_days
            
        url = DAILY_CHART_URL_TEMPLATE.format(code=stock_code)
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=self.timeout)
                soup = BeautifulSoup(response.text, "html.parser")
                
                daily_data = []
                
                # 일별시세 테이블 찾기
                table = soup.find('table', {'class': 'type2'})
                if not table:
                    print(f"❌ 일별시세 테이블을 찾을 수 없음: {stock_code}")
                    return []
                
                rows = table.find_all('tr')[1:]  # 헤더 제외
                
                for row in rows[:days]:  # 요청한 일수만큼
                    cells = row.find_all('td')
                    if len(cells) >= 6:
                        try:
                            date = cells[0].get_text().strip()
                            close = cells[1].get_text().strip().replace(',', '')
                            high = cells[4].get_text().strip().replace(',', '')
                            low = cells[5].get_text().strip().replace(',', '')
                            volume = cells[6].get_text().strip().replace(',', '') if len(cells) > 6 else "0"
                            
                            # 빈 데이터 체크
                            if not close or close == '' or close == '-':
                                continue
                                
                            daily_data.append(StockDataPoint(
                                date=date,
                                close=int(close),
                                high=int(high),
                                low=int(low),
                                volume=int(volume) if volume.isdigit() else 0
                            ))
                            
                        except (ValueError, IndexError) as e:
                            print(f"⚠️ 데이터 파싱 실패: {row.get_text()[:50]}... - {str(e)}")
                            continue
                
                print(f"📈 일별데이터 수집: {len(daily_data)}개")
                return daily_data
                
        except Exception as e:
            print(f"❌ 일별시세 수집 실패 {stock_code}: {str(e)}")
            return []
    
    def _calculate_weekly_stats_by_date(self, daily_data: List[StockDataPoint], this_friday: str, last_friday: str) -> Dict[str, Any]:
        """실제 날짜 기준 주간 통계 계산"""
        if not daily_data:
            return {}
        
        try:
            # 이번 주 금요일과 전주 금요일 데이터 찾기
            this_friday_data = self._find_closest_trading_day(this_friday, daily_data)
            last_friday_data = self._find_closest_trading_day(last_friday, daily_data)
            
            if not this_friday_data or not last_friday_data:
                print(f"❌ 필요한 날짜 데이터를 찾을 수 없음")
                return {}
            
            today = this_friday_data.close
            last_week = last_friday_data.close
            
            # 이번 주 고점/저점 계산 (이번 주 금요일 기준으로 최근 5거래일)
            this_friday_dt = datetime.strptime(this_friday, "%Y.%m.%d")
            this_week_data = []
            
            for data in daily_data:
                try:
                    data_dt = datetime.strptime(data.date, "%Y.%m.%d")
                    # 이번 주 금요일로부터 5일 이내의 거래일
                    if (this_friday_dt - data_dt).days <= 4 and data_dt <= this_friday_dt:
                        this_week_data.append(data)
                except:
                    continue
            
            if this_week_data:
                week_high = max(day.high for day in this_week_data)
                week_low = min(day.low for day in this_week_data)
            else:
                week_high = today
                week_low = today
            
            # 주간 등락률 계산
            change_rate = ((today - last_week) / last_week) * 100 if last_week != 0 else 0
            
            stats = {
                "today": today,
                "lastWeek": last_week,
                "changeRate": round(change_rate, 2),
                "weekHigh": week_high,
                "weekLow": week_low
            }
            
            print(f"📊 실제 주간통계: 금주({this_friday})={today:,}원, 전주({last_friday})={last_week:,}원, 등락률={change_rate:.2f}%")
            return stats
            
        except Exception as e:
            print(f"❌ 주간통계 계산 실패: {str(e)}")
            return {}

    # 하위 호환성을 위한 기존 메서드 (삭제하고 새로운 로직 사용)
    def _calculate_weekly_stats(self, daily_data: List[StockDataPoint]) -> Dict[str, Any]:
        """기존 방식 (사용 안함)"""
        return self._calculate_weekly_stats_by_date(daily_data, *self._get_friday_dates())

    # 하위 호환성을 위한 기존 메서드
    async def fetch_stock_price(self, symbol: str):
        """기존 API 호환성 유지"""
        weekly_data = await self.fetch_weekly_stock_data(symbol)
        
        # 기존 형식으로 변환
        if weekly_data.error:
            return {"symbol": symbol, "error": weekly_data.error}
        
        return {
            "symbol": weekly_data.symbol,
            "today": weekly_data.today,
            "yesterday": weekly_data.lastWeek,  # 전주 금요일을 yesterday로 매핑
            "changeRate": f"{weekly_data.changeRate}%" if weekly_data.changeRate else "0%",
            "marketCap": weekly_data.marketCap,
            "weekHigh": weekly_data.weekHigh,
            "weekLow": weekly_data.weekLow
        }
