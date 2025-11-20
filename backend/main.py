from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from sqlalchemy.orm import Session
from typing import Optional

import models
from database import engine, get_db
from schema import (
    WOOPCreate,
    WOOPUpdate,
    WOOPResponse,
    WOOPList,
    MessageResponse,
    AIChatInput,
)
from crud import woop_crud
from agentset import useagent

# MCP 通过 agentset 以 stdio 方式使用，无需挂载 HTTP 子应用
# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="WOOP Management API",
    description="WOOP目标管理系统API",
    version="0.1.0",
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
def create_woop(woop: WOOPCreate, db: Session = Depends(get_db)) -> WOOPResponse:
    """创建新的WOOP记录"""
    try:
        return woop_crud.create(db=db, woop_data=woop)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")


@app.get("/woops/{woop_id}", response_model=WOOPResponse)
async def get_woop(woop_id: int, db: Session = Depends(get_db)) -> WOOPResponse:
    """根据ID获取WOOP记录"""
    woop = woop_crud.get_by_id(db=db, woop_id=woop_id)
    if woop is None:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return woop  # type: ignore


@app.get("/woops/", response_model=WOOPList)
async def get_woops(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    name_filter: Optional[str] = Query(None, description="名称过滤"),
    db: Session = Depends(get_db),
) -> WOOPList:
    """获取WOOP记录列表，支持分页和过滤"""
    skip: int = (page - 1) * size
    woops: list[models.WOOP] = woop_crud.get_all(
        db=db, skip=skip, limit=size, name_filter=name_filter
    )
    total: int = woop_crud.get_count(db=db, name_filter=name_filter)

    return WOOPList(
        items=woops,  # type: ignore
        total=total,
        page=page,
        size=size,
    )


@app.put("/woops/{woop_id}", response_model=WOOPResponse)
async def update_woop(
    woop_id: int, woop_update: WOOPUpdate, db: Session = Depends(get_db)
) -> WOOPResponse:
    """更新WOOP记录"""
    updated_woop: Optional[models.WOOP] = woop_crud.update(
        db=db, woop_id=woop_id, woop_data=woop_update
    )
    if updated_woop is None:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return updated_woop  # type: ignore


@app.delete("/woops/{woop_id}", response_model=MessageResponse)
async def delete_woop(woop_id: int, db: Session = Depends(get_db)) -> MessageResponse:
    """删除WOOP记录"""
    success: bool = woop_crud.delete(db=db, woop_id=woop_id)
    if not success:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return MessageResponse(message="WOOP记录删除成功")


@app.get("/woops/rank/{rank}", response_model=list[WOOPResponse])
async def get_woops_by_rank(
    rank: int, db: Session = Depends(get_db)
) -> list[WOOPResponse]:
    """根据排名获取WOOP记录"""
    woops: list[models.WOOP] = woop_crud.get_by_rank(db=db, rank=rank)
    return woops  # type: ignore


@app.get("/woops/search/{keyword}", response_model=list[WOOPResponse])
async def search_woops(
    keyword: str, db: Session = Depends(get_db)
) -> list[WOOPResponse]:
    """全文搜索WOOP记录"""
    woops: list[models.WOOP] = woop_crud.search(db=db, keyword=keyword)
    return woops  # type: ignore


@app.get("/woops/date-range/", response_model=list[WOOPResponse])
async def get_woops_by_date_range(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> list[WOOPResponse]:
    """根据日期范围获取WOOP记录"""
    woops: list[models.WOOP] = woop_crud.get_by_date_range(
        db=db, start_date=start_date, end_date=end_date
    )
    return woops  # type: ignore


@app.get("/health", response_model=MessageResponse)
async def health_check() -> MessageResponse:
    """健康检查"""
    return MessageResponse(message="服务运行正常")

@app.post("/ai/chat")
async def ai_chat(input_data: AIChatInput):
    """与AI助手进行对话，返回 Server-Sent Events (SSE) 流式输出"""

    async def event_generator():
        try:
            # useagent 返回一个 AsyncIterator[str]
            async for chunk in useagent(input_items=input_data.message):  # type: ignore
                # 以 SSE 格式发送数据（每个事件以两个换行结尾）
                # 这里把每个 chunk 包装为 JSON，前端解析更方便
                payload = {"text": chunk}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # 发送结束标记
            yield "event: done\ndata: [DONE]\n\n"
        except Exception as e:
            err = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
    


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
