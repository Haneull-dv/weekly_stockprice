# StockPrice Service

주가 정보 조회 및 분석을 위한 마이크로서비스입니다.

## 🚀 서비스 구조

```
메인(main.py) → 라우터(stockprice_router.py) → 컨트롤러(stockprice_controller.py) → 서비스(stockprice_service.py)
```

## 📋 API 엔드포인트

### 기본 주가 조회
```bash
GET /api/v1/stockprice/?symbol=005930
```

### 주가 트렌드 조회
```bash
GET /api/v1/stockprice/trend?symbol=005930&period=1y
```

### 주가 분석
```bash
GET /api/v1/stockprice/analysis?symbol=005930
```

## 🐳 Docker 사용법

### 개별 서비스 실행
```bash
# 빌드 및 실행
make build-stockprice
make up-stockprice

# 로그 확인
make logs-stockprice

# 재시작 (빌드 포함)
make restart-stockprice
```

### 🔥 개발 모드 (Live Reload)
코드 수정 시 자동으로 반영되는 개발 환경:

```bash
# 개발 모드로 시작 (빌드 없이 재시작)
make dev-stockprice

# 또는 직접 명령어
docker-compose stop stockprice
docker-compose up -d stockprice
```

**✨ 장점:**
- 코드 수정 시 즉시 반영 (빌드 불필요)
- `--reload` 옵션으로 자동 재시작
- 볼륨 마운트로 실시간 개발 가능

### 전체 시스템과 함께 실행
```bash
# 모든 서비스 시작
make up

# 주가 관련 서비스만 시작
make stock-services-up
```

## ⚙️ 환경 설정

### Docker 볼륨 설정
개발 환경을 위한 최적화된 볼륨 설정:

```yaml
volumes:
  - ./stockprice:/app          # 소스코드 실시간 반영
  - /app/__pycache__          # 캐시 파일 제외
  - /app/.pytest_cache        # 테스트 캐시 제외

environment:
  - PYTHONDONTWRITEBYTECODE=1  # .pyc 파일 생성 방지
  - PYTHONUNBUFFERED=1        # 출력 버퍼링 방지
  - PYTHONPATH=/app           # Python 경로 설정
```

### 환경변수 설정

다음 환경변수들을 `.env` 파일에 설정하세요:

```env
# StockPrice Service Configuration
SERVICE_NAME=stockprice
SERVICE_PORT=9006
SERVICE_HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://hc_user:hc_password@db:5432/hc_db

# API Keys (필요시 추가)
# STOCK_API_KEY=your_api_key_here
# FINANCIAL_DATA_API_KEY=your_api_key_here

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=development
```

## 🔗 N8N 워크플로우 연동

N8N을 통해 주가 데이터를 자동으로 수집하고 처리할 수 있습니다:

1. N8N 웹 인터페이스 접속: http://localhost:5678
   - Username: admin
   - Password: password

2. 워크플로우에서 StockPrice API 호출:
   ```
   HTTP Request Node → http://stockprice:9006/api/v1/stockprice/
   ```

## 🛠️ 개발 가이드

### 🔥 Hot Reload 개발 워크플로우

1. **서비스 시작**
```bash
make dev-stockprice
```

2. **코드 수정**
   - 파일 저장 시 자동으로 서버 재시작
   - 브라우저에서 즉시 확인 가능

3. **로그 실시간 확인**
```bash
make logs-stockprice
```

### 서비스 로직 구현
`app/domain/service/stockprice_service.py` 파일의 각 메서드에 비즈니스 로직을 구현하세요:

- `fetch_stock_price(symbol)` - 주가 조회
- `fetch_stock_trend(symbol, period)` - 트렌드 분석  
- `analyze_stock(symbol)` - 주가 분석

### 의존성 추가
새로운 패키지가 필요한 경우:

1. `requirements.txt`에 추가
2. 컨테이너 재빌드:
```bash
make restart-stockprice
```

## 📊 모니터링

### 로그 확인
```bash
# 실시간 로그
docker-compose logs -f stockprice

# 특정 시간대 로그
docker-compose logs --since="2024-01-01T10:00:00" stockprice
```

### 컨테이너 상태 확인
```bash
docker-compose ps
```

### 컨테이너 접속
```bash
docker exec -it stockprice bash
```

### API 테스트
```bash
# 주가 조회 테스트
curl http://localhost:9006/api/v1/stockprice/?symbol=005930

# API 문서 확인
curl http://localhost:9006/docs
```

## 🔧 트러블슈팅

### 코드 변경이 반영되지 않을 때
```bash
# 컨테이너 재시작
make dev-stockprice

# 또는 강제 재빌드
make restart-stockprice
```

### 포트 충돌 시
`docker-compose.yml`에서 포트를 변경하세요:
```yaml
ports:
  - "다른포트:9006"
```

### 권한 문제 (Linux/macOS)
```bash
# 볼륨 권한 수정
sudo chown -R $USER:$USER ./stockprice
```

### 빌드 실패 시
```bash
# 캐시 없이 다시 빌드
docker-compose build --no-cache stockprice
```

## 🚀 성능 최적화

### 개발 환경
- Live reload로 빠른 개발 사이클
- 볼륨 마운트로 즉시 반영
- Python 캐시 파일 제외로 깔끔한 환경

### 운영 환경
- 멀티스테이지 빌드 (필요시)
- 환경변수 최적화
- 로그 레벨 조정