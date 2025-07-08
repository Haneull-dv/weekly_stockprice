# 1. 베이스 이미지 설정
FROM python:3.10-slim 

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 먼저 복사 및 설치
# 이제 빌드 기준이 ./weekly_stockprice 이므로, 바로 requirements.txt를 복사합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 필요한 소스코드 복사
# 공통 모듈인 weekly_db를 상위 폴더(..)에서 가져옵니다.
COPY ../weekly_db /app/weekly_db

# 현재 서비스(weekly_stockprice)의 모든 코드를 복사합니다.
COPY . .

# 6. 최종 작업 디렉토리 변경 (불필요)
# 모든 코드가 이미 /app 에 있으므로 이 라인은 삭제합니다.

# 7. 애플리케이션 실행
# uvicorn은 WORKDIR(/app) 기준으로 실행되므로 경로 수정이 필요 없습니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9006"]

# 8. 포트 노출
EXPOSE 9006