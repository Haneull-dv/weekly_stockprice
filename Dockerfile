# 1. 베이스 이미지 설정
FROM python:3.10-slim

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스코드 복사
COPY . /app

# 6. 작업 디렉토리 변경
WORKDIR /app

# 7. 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9006", "--reload"]

# 8. 포트 노출
EXPOSE 9006