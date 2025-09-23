from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
from typing import Generator

# SQLite数据库URL
SQLALCHEMY_DATABASE_URL = "sqlite:///" + str(Path.cwd() / "woop_management.db")

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite特有配置
)

# 创建会话工厂
SessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类 - 使用现代写法
class Base(DeclarativeBase):
    pass

# 数据库依赖函数
def get_db() -> Generator:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()