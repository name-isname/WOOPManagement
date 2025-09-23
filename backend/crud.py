from sqlalchemy.orm import Session
from sqlalchemy import func, select, or_
from typing import Optional
from models import WOOP
from schema import WOOPCreate, WOOPUpdate

class WOOPCrud:
    """WOOP数据库操作类"""
    
    @staticmethod
    def create(db: Session, woop_data: WOOPCreate) -> WOOP:
        """创建新的WOOP记录"""
        db_woop = WOOP(**woop_data.model_dump())
        db.add(db_woop)
        db.commit()
        db.refresh(db_woop)
        return db_woop
    
    @staticmethod
    def get_by_id(db: Session, woop_id: int) -> Optional[WOOP]:
        """根据ID获取WOOP记录"""
        return db.execute(select(WOOP).where(WOOP.id == woop_id)).scalar()
    
    @staticmethod
    def get_all(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        name_filter: Optional[str] = None
    ) -> list[WOOP]:
        """获取所有WOOP记录,支持分页和名称过滤"""
        stmt = select(WOOP)
        
        if name_filter:
            stmt = stmt.where(WOOP.name.contains(name_filter))
        
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
    
    @staticmethod
    def get_count(db: Session, name_filter: Optional[str] = None) -> int:
        """获取WOOP记录总数"""
        stmt = select(func.count(WOOP.id))
        
        if name_filter:
            stmt = stmt.where(WOOP.name.contains(name_filter))
        
        return db.scalar(stmt) or 0
    
    @staticmethod
    def update(db: Session, woop_id: int, woop_data: WOOPUpdate) -> Optional[WOOP]:
        """更新WOOP记录"""
        db_woop = db.execute(select(WOOP).where(WOOP.id == woop_id)).scalar()
        
        if not db_woop:
            return None
        
        # 只更新非None的字段
        update_data = woop_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_woop, field, value)
        
        db.commit()
        db.refresh(db_woop)
        return db_woop
    
    @staticmethod
    def delete(db: Session, woop_id: int) -> bool:
        """删除WOOP记录"""
        db_woop = db.execute(select(WOOP).where(WOOP.id == woop_id)).scalar()
        
        if not db_woop:
            return False
        
        db.delete(db_woop)
        db.commit()
        return True
    
    @staticmethod
    def get_by_rank(db: Session, rank: int) -> list[WOOP]:
        """根据排名获取WOOP记录"""
        stmt = select(WOOP).where(WOOP.rank == rank)
        return list(db.scalars(stmt).all())
    
    @staticmethod
    def get_by_date_range(
        db: Session, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> list[WOOP]:
        """根据日期范围获取WOOP记录"""
        stmt = select(WOOP)
        
        if start_date:
            stmt = stmt.where(WOOP.datetime >= start_date)
        if end_date:
            stmt = stmt.where(WOOP.datetime <= end_date)
        
        stmt = stmt.order_by(WOOP.datetime.desc())
        return list(db.scalars(stmt).all())
    
    @staticmethod
    def search(db: Session, keyword: str) -> list[WOOP]:
        """全文搜索WOOP记录"""
        stmt = select(WOOP).where(
            or_(
                WOOP.name.contains(keyword),
                WOOP.wish.contains(keyword),
                WOOP.obstacle.contains(keyword),
                WOOP.action.contains(keyword),
                WOOP.result.contains(keyword),
                WOOP.description.contains(keyword)
            )
        )
        return list(db.scalars(stmt).all())

# 创建CRUD实例
woop_crud = WOOPCrud()