# 1. 베이스 이미지 설정
FROM python:3.10-slim

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 먼저 복사 및 설치
# 빌드 기준이 루트(.)이므로, weekly_stockprice 폴더 안의 파일을 지정해야 합니다.
COPY ./weekly_stockprice/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 필요한 소스코드 복사
# 루트에서 weekly_db와 weekly_stockprice 폴더를 각각 복사합니다.
COPY ./weekly_db /app/weekly_db
COPY ./weekly_stockprice /app/weekly_stockprice

# 6. 최종 작업 디렉토리 변경
# CMD 명령어를 실행할 위치를 /app/weekly_stockprice 로 지정합니다.
WORKDIR /app/weekly_stockprice

# 7. 애플리케이션 실행
# uvicorn은 현재 작업 디렉토리(/app/weekly_stockprice) 기준으로 app.main을 찾습니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9006"]

# 8. 포트 노출
EXPOSE 9006