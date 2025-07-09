from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.config import settings
from .db_singleton import db_singleton

DATABASE_URL = settings.DATABASE_URL

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency Injection을 위한 DB 세션 생성기
    
    사용법:
    @app.get("/api/endpoint")
    async def endpoint(db: AsyncSession = Depends(get_db_session)):
        # db 세션 사용
    """
    print("🗄️ DI: DB 세션 생성")
    
    # 새로운 세션 생성
    session = await db_singleton.get_session()
    
    try:
        yield session
        print("🗄️ DI: DB 세션 사용 완료")
    except Exception as e:
        print(f"❌ DB 세션 에러: {str(e)}")
        await session.rollback()
        raise
    finally:
        await session.close()
        print("🗄️ DI: DB 세션 종료")

# 편의를 위한 타입 별칭
DatabaseDep = Depends(get_db_session)

