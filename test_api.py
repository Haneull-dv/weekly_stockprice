#!/usr/bin/env python3
"""
FastAPI 엔드포인트 테스트 스크립트
"""
import requests
import json
import time

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    base_url = "http://localhost:8080"
    
    print("🧪 FastAPI 엔드포인트 테스트 시작")
    print("=" * 60)
    
    # 서버 시작 대기
    print("⏳ 서버 시작 대기 중...")
    time.sleep(3)
    
    # 1. 헬스체크
    try:
        print("\n1️⃣ 헬스체크 테스트")
        response = requests.get(f"{base_url}/stockprice/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 헬스체크: {response.json()}")
        else:
            print(f"❌ 헬스체크 실패: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("   서버가 시작되지 않았을 수 있습니다.")
        return
    
    # 2. 게임기업 리스트 조회
    try:
        print("\n2️⃣ 게임기업 리스트 조회")
        response = requests.get(f"{base_url}/stockprice/companies", timeout=5)
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ 게임기업 수: {companies['total_count']}개")
            for code, name in list(companies['companies'].items())[:3]:
                print(f"   - {name} ({code})")
        else:
            print(f"❌ 게임기업 리스트 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 게임기업 리스트 조회 오류: {e}")
    
    # 3. 기존 API (하위 호환성)
    try:
        print("\n3️⃣ 기존 API 테스트 (하위 호환성)")
        response = requests.get(f"{base_url}/stockprice/price?symbol=259960", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 기존 API 응답:")
            for key, value in data.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ 기존 API 실패: {response.status_code}")
            print(f"   응답: {response.text}")
    except Exception as e:
        print(f"❌ 기존 API 오류: {e}")
    
    # 4. 새로운 주간 데이터 API (단일 기업)
    try:
        print("\n4️⃣ 주간 데이터 API 테스트 (크래프톤)")
        response = requests.get(f"{base_url}/stockprice/weekly/259960", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("✅ 주간 데이터 응답:")
            print(f"   기업명: {data.get('symbol')}")
            print(f"   시가총액: {data.get('marketCap'):,}억원" if data.get('marketCap') else "   시가총액: 정보 없음")
            print(f"   금주 종가: {data.get('today'):,}원" if data.get('today') else "   금주 종가: 정보 없음")
            print(f"   전주 종가: {data.get('lastWeek'):,}원" if data.get('lastWeek') else "   전주 종가: 정보 없음")
            print(f"   주간 등락률: {data.get('changeRate')}%" if data.get('changeRate') else "   주간 등락률: 정보 없음")
            print(f"   금주 고점: {data.get('weekHigh'):,}원" if data.get('weekHigh') else "   금주 고점: 정보 없음")
            print(f"   금주 저점: {data.get('weekLow'):,}원" if data.get('weekLow') else "   금주 저점: 정보 없음")
            if data.get('error'):
                print(f"   ❌ 오류: {data.get('error')}")
        else:
            print(f"❌ 주간 데이터 API 실패: {response.status_code}")
            print(f"   응답: {response.text}")
    except Exception as e:
        print(f"❌ 주간 데이터 API 오류: {e}")
    
    # 5. 전체 게임기업 주간 데이터 (시간이 오래 걸릴 수 있음)
    try:
        print("\n5️⃣ 전체 게임기업 주간 데이터 테스트 (최대 30초)")
        response = requests.get(f"{base_url}/stockprice/weekly", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 전체 게임기업 주간 데이터: {len(data)}개 수집")
            
            # 상위 3개만 출력
            for item in data[:3]:
                if not item.get('error'):
                    print(f"   📊 {item.get('symbol')}: {item.get('today'):,}원 ({item.get('changeRate'):+.2f}%)")
                else:
                    print(f"   ❌ {item.get('symbol')}: {item.get('error')}")
                    
        else:
            print(f"❌ 전체 데이터 API 실패: {response.status_code}")
            print(f"   응답: {response.text}")
    except requests.exceptions.Timeout:
        print("⏰ 전체 데이터 요청 타임아웃 (30초 초과)")
    except Exception as e:
        print(f"❌ 전체 데이터 API 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 API 테스트 완료!")

if __name__ == "__main__":
    test_api_endpoints() 