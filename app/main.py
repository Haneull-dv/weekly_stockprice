from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 공통 DB 모듈 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# DB 테이블 생성을 위한 import 추가
from app.config.db.db_singleton import db_singleton
from app.domain.model.stockprice_model import Base

# 라우터 import
from app.api.stockprice_router import router as stockprice_router
from app.api.n8n_stockprice_router import router as n8n_stockprice_router
from app.api.cqrs_stockprice_router import router as cqrs_stockprice_router

load_dotenv()
app = FastAPI(title="Weekly Stock Price Service")

# 앱 시작 시 테이블 생성
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 데이터베이스 테이블 생성"""
    async with db_singleton.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🗄️ StockPrice 테이블 생성 완료")

ENV = os.getenv("ENV", "development")  # 기본값 development

if ENV == "production":
    allow_origins = [
        "https://haneull.com",  # 커스텀 도메인
        "https://conan.ai.kr",
        "https://portfolio-v0-02-git-main-haneull-dvs-projects.vercel.app",  # vercel 공식 도메인(운영/테스트용)
        # 필요하다면 다른 공식 도메인 추가
    ]
else:
    allow_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://portfolio-v0-02-git-main-haneull-dvs-projects.vercel.app",  # vercel 미리보기
        "https://portfolio-v0-02-1hkt...g4n-haneull-dvs-projects.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 라우터 등록
app.include_router(stockprice_router, prefix="/stockprice", tags=["주가 정보"])
app.include_router(n8n_stockprice_router, tags=["n8n 자동화"])
app.include_router(cqrs_stockprice_router, tags=["CQRS 주가"])

print(f"🤍0. 메인 진입 - 주가 서비스 시작 (DI 기반)")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9006))  # 로컬은 9006, 배포는 8080
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)