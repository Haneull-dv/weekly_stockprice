from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Index, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from app.config.db.base import Base  # Base 경로만 이걸로 바꾸면 됨


class WeeklyDataModel(Base):
    __tablename__ = "weekly_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    week = Column(String(10), nullable=False)
    week_year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    stock_code = Column(String(10), nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('company_name', 'category', 'week', name='uq_weekly_data_unique'),
        Index('idx_weekly_company_category_week', 'company_name', 'category', 'week'),
        Index('idx_weekly_week', 'week'),
        Index('idx_weekly_category', 'category'),
        Index('idx_weekly_company', 'company_name'),
        Index('idx_weekly_collected_at', 'collected_at'),
    )

    def __repr__(self):
        return f"<WeeklyData(id={self.id}, company='{self.company_name}', category='{self.category}', week='{self.week}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "content": self.content,
            "category": self.category,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "week": self.week,
            "week_year": self.week_year,
            "week_number": self.week_number,
            "stock_code": self.stock_code,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def get_current_week_monday() -> str:
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        return monday.strftime('%Y-%m-%d')

    @staticmethod
    def get_week_info(date_str: str = None) -> tuple:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        year, week_num, _ = date_obj.isocalendar()
        return year, week_num


class WeeklyBatchJobModel(Base):
    __tablename__ = "weekly_batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False)
    week = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    total_companies = Column(Integer, nullable=True)
    updated_count = Column(Integer, nullable=True)
    skipped_count = Column(Integer, nullable=True)
    error_count = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_batch_job_type_week', 'job_type', 'week'),
        Index('idx_batch_started_at', 'started_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "job_type": self.job_type,
            "week": self.week,
            "status": self.status,
            "total_companies": self.total_companies,
            "updated_count": self.updated_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
        }
