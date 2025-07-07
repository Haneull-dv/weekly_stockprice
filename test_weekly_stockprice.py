#!/usr/bin/env python3
"""
Weekly Stock Price Service Test Script
주간 주가 데이터 API 테스트용 스크립트
"""
import asyncio
import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domain.service.stockprice_service import StockPriceService
from app.domain.controller.stockprice_controller import StockPriceController

async def test_single_company():
    """단일 기업 주간 데이터 테스트"""
    print("🧪 단일 기업 주간 데이터 테스트 시작")
    print("=" * 60)
    
    service = StockPriceService()
    
    # 크래프톤으로 테스트
    test_symbol = "259960"  # 크래프톤
    
    print(f"📊 테스트 대상: {test_symbol}")
    
    try:
        result = await service.fetch_weekly_stock_data(test_symbol)
        
        print(f"\n✅ 테스트 결과:")
        print(f"   기업명: {result.symbol}")
        print(f"   시가총액: {result.marketCap}억원")
        print(f"   금주 종가: {result.today:,}원")
        print(f"   전주 종가: {result.lastWeek:,}원")
        print(f"   주간 등락률: {result.changeRate}%")
        print(f"   금주 고점: {result.weekHigh:,}원")
        print(f"   금주 저점: {result.weekLow:,}원")
        
        if result.error:
            print(f"   ❌ 오류: {result.error}")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")

async def test_multiple_companies():
    """여러 기업 주간 데이터 테스트"""
    print("\n🧪 여러 기업 주간 데이터 테스트 시작")
    print("=" * 60)
    
    controller = StockPriceController()
    
    try:
        # 게임기업 리스트 조회
        companies_info = controller.get_game_companies()
        print(f"📋 등록된 게임기업 수: {companies_info['total_count']}개")
        
        # 상위 3개 기업만 테스트 (시간 절약)
        test_companies = list(companies_info['companies'].keys())[:3]
        print(f"🎯 테스트 대상: {test_companies}")
        
        # 병렬로 데이터 수집
        results = []
        for company_code in test_companies:
            try:
                result = await controller.get_weekly_stock_data(company_code)
                results.append(result)
                print(f"✅ {result.symbol}: 수집 완료")
            except Exception as e:
                print(f"❌ {company_code}: 수집 실패 - {str(e)}")
        
        print(f"\n📊 수집 결과 요약:")
        for result in results:
            if not result.error:
                print(f"   {result.symbol}: 금주 {result.today:,}원 (전주 대비 {result.changeRate:+.2f}%)")
            else:
                print(f"   {result.symbol}: 오류 - {result.error}")
                
    except Exception as e:
        print(f"❌ 다중 기업 테스트 실패: {str(e)}")

async def test_api_compatibility():
    """기존 API 호환성 테스트"""
    print("\n🧪 기존 API 호환성 테스트 시작")
    print("=" * 60)
    
    service = StockPriceService()
    
    try:
        # 기존 메서드 테스트
        old_result = await service.fetch_stock_price("259960")
        
        print("✅ 기존 API 형식 결과:")
        for key, value in old_result.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ 호환성 테스트 실패: {str(e)}")

async def test_error_handling():
    """오류 처리 테스트"""
    print("\n🧪 오류 처리 테스트 시작")
    print("=" * 60)
    
    service = StockPriceService()
    
    # 잘못된 종목코드로 테스트
    invalid_symbols = ["000000", "abc123", "invalid"]
    
    for symbol in invalid_symbols:
        try:
            result = await service.fetch_weekly_stock_data(symbol)
            print(f"🔍 {symbol}: {result.error if result.error else '예상과 다른 결과'}")
        except Exception as e:
            print(f"❌ {symbol}: 예외 발생 - {str(e)}")

async def main():
    """메인 테스트 실행"""
    print("🚀 Weekly Stock Price Service 테스트 시작")
    print("=" * 80)
    
    await test_single_company()
    await test_multiple_companies()
    await test_api_compatibility()
    await test_error_handling()
    
    print("\n" + "=" * 80)
    print("🎉 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main()) 