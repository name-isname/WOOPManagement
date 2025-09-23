from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

import models
from database import engine, get_db
from schema import WOOPCreate, WOOPUpdate, WOOPResponse, WOOPList, MessageResponse
from crud import woop_crud

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="WOOP Management API",
    description="WOOP目标管理系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=MessageResponse)
async def root() -> MessageResponse:
    """根路径"""
    return MessageResponse(message="WOOP Management API is running!")

@app.post("/woops/", response_model=WOOPResponse, status_code=201)
async def create_woop(woop: WOOPCreate, db: Session = Depends(get_db)) -> WOOPResponse:
    """创建新的WOOP记录"""
    try:
        return woop_crud.create(db=db, woop_data=woop)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")

@app.get("/woops/{woop_id}", response_model=WOOPResponse)
async def get_woop(woop_id: int, db: Session = Depends(get_db)) -> WOOPResponse:
    """根据ID获取WOOP记录"""
    woop = woop_crud.get_by_id(db=db, woop_id=woop_id)
    if woop is None:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return woop

@app.get("/woops/", response_model=WOOPList)
async def get_woops(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    name_filter: Optional[str] = Query(None, description="名称过滤"),
    db: Session = Depends(get_db)
) -> WOOPList:
    """获取WOOP记录列表，支持分页和过滤"""
    skip: int = (page - 1) * size
    woops: list[models.WOOP] = woop_crud.get_all(db=db, skip=skip, limit=size, name_filter=name_filter)
    total: int = woop_crud.get_count(db=db, name_filter=name_filter)
    
    return WOOPList(
        items=woops, 
        total=total,
        page=page,
        size=size
    )

@app.put("/woops/{woop_id}", response_model=WOOPResponse)
async def update_woop(
    woop_id: int, 
    woop_update: WOOPUpdate, 
    db: Session = Depends(get_db)
) -> WOOPResponse:
    """更新WOOP记录"""
    updated_woop: Optional[models.WOOP] = woop_crud.update(db=db, woop_id=woop_id, woop_data=woop_update)
    if updated_woop is None:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return updated_woop

@app.delete("/woops/{woop_id}", response_model=MessageResponse)
async def delete_woop(woop_id: int, db: Session = Depends(get_db)) -> MessageResponse:
    """删除WOOP记录"""
    success: bool = woop_crud.delete(db=db, woop_id=woop_id)
    if not success:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return MessageResponse(message="WOOP记录删除成功")

@app.get("/woops/rank/{rank}", response_model=list[WOOPResponse])
async def get_woops_by_rank(rank: int, db: Session = Depends(get_db)) -> list[WOOPResponse]:
    """根据排名获取WOOP记录"""
    woops: list[models.WOOP] = woop_crud.get_by_rank(db=db, rank=rank)
    return woops

@app.get("/woops/search/{keyword}", response_model=list[WOOPResponse])
async def search_woops(keyword: str, db: Session = Depends(get_db)) -> list[WOOPResponse]:
    """全文搜索WOOP记录"""
    woops: list[models.WOOP] = woop_crud.search(db=db, keyword=keyword)
    return woops

@app.get("/woops/date-range/", response_model=list[WOOPResponse])
async def get_woops_by_date_range(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> list[WOOPResponse]:
    """根据日期范围获取WOOP记录"""
    woops: list[models.WOOP] = woop_crud.get_by_date_range(db=db, start_date=start_date, end_date=end_date)
    return woops

@app.get("/health", response_model=MessageResponse)
async def health_check() -> MessageResponse:
    """健康检查"""
    return MessageResponse(message="服务运行正常")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)