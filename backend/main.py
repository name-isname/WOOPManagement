from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

import models
from database import engine, get_db
from schema import WOOPCreate, WOOPUpdate, WOOPResponse, WOOPList, MessageResponse, ChatItem, ChatHistory
from crud import woop_crud
from rtoml import load
from openai import AsyncOpenAI
import os
import re

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
        return woop_crud.create(db=db, woop_data=woop) # type: ignore
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")

@app.get("/woops/{woop_id}", response_model=WOOPResponse)
async def get_woop(woop_id: int, db: Session = Depends(get_db)) -> WOOPResponse:
    """根据ID获取WOOP记录"""
    woop = woop_crud.get_by_id(db=db, woop_id=woop_id)
    if woop is None:
        raise HTTPException(status_code=404, detail="WOOP记录不存在")
    return woop # type: ignore

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
        items=woops,  # type: ignore
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
    return updated_woop # type: ignore

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
    return woops # type: ignore

@app.get("/woops/search/{keyword}", response_model=list[WOOPResponse])
async def search_woops(keyword: str, db: Session = Depends(get_db)) -> list[WOOPResponse]:
    """全文搜索WOOP记录"""
    woops: list[models.WOOP] = woop_crud.search(db=db, keyword=keyword)
    return woops # type: ignore

@app.get("/woops/date-range/", response_model=list[WOOPResponse])
async def get_woops_by_date_range(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> list[WOOPResponse]:
    """根据日期范围获取WOOP记录"""
    woops: list[models.WOOP] = woop_crud.get_by_date_range(db=db, start_date=start_date, end_date=end_date)
    return woops # type: ignore

@app.get("/health", response_model=MessageResponse)
async def health_check() -> MessageResponse:
    """健康检查"""
    return MessageResponse(message="服务运行正常")

# （保留空位）如后续需要 HTTP 形式的 MCP 端点，可在此处挂载


# ============== AI Chat 简易接口（非流式） ==============
class ChatRequest(BaseModel):
    prompt: str
    project_name: str | None = None
    model: str | None = None  # 可选：显式指定 OpenRouter 模型 ID

class ChatResponse(BaseModel):
    text: str

@app.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """调用已配置的 OpenAI 兼容模型（通过 OpenRouter），返回简易文本回答。"""
    try:
        cfg = load(open("setting.toml", "r", encoding="utf-8")) if os.path.exists("setting.toml") else {}
        # 优先读取环境变量，其次读取 setting.toml
        api_key = os.getenv("OPENROUTER_API_KEY") or cfg.get("api_key")
        # 允许在 setting.toml 里配置 model 或 openrouter_model；否则使用一个较通用的默认模型
        default_model = cfg.get("model") or cfg.get("openrouter_model") or "openai/gpt-4o-mini"
        model = req.model or default_model

        base_url = "https://openrouter.ai/api/v1"
        if not api_key:
            raise RuntimeError("缺少 OpenRouter API Key，请在 backend/setting.toml 配置 api_key")

        client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        # 将项目名仅拼入模型上下文；保存到历史的 user 文本仍使用原始输入，避免在界面中出现“项目: xxx”前缀
        prompt = req.prompt if not req.project_name else f"项目: {req.project_name}\n{req.prompt}"

        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "请用清晰的段落回答，适当换行；如需列点，优先使用短横线或数字序号；避免输出 Markdown 标题标记(如 ###) 和过长段落。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        raw = (completion.choices[0].message.content or "").strip()

        # 后处理：去除行首 Markdown 标题（# / ## / ### ...）确保不出现 ###
        def sanitize_ai_text(s: str) -> str:
            out_lines: list[str] = []
            in_code = False
            for line in s.splitlines():
                ls = line.strip()
                if ls.startswith("```"):
                    in_code = not in_code
                    out_lines.append(line)
                    continue
                if not in_code:
                    # 移除最多 3 个前导空白后跟 1-6 个 # 的标题标记
                    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
                    out_lines.append(cleaned)
                else:
                    out_lines.append(line)
            return "\n".join(out_lines).strip()

        text = sanitize_ai_text(raw)

        # 持久化：保存 user 与 ai 的消息
        try:
            from models import ChatMessage
            # user message（保存用户原始输入，不含项目名前缀）
            db.add(ChatMessage(project_name=req.project_name, role="user", text=req.prompt))
            # ai message
            db.add(ChatMessage(project_name=req.project_name, role="ai", text=text))
            db.commit()
        except Exception:
            db.rollback()
        return ChatResponse(text=text)
    except Exception as e:
        # 更友好的错误分类与提示
        msg = str(e)
        lower = msg.lower()
        status = 500
        if "401" in msg or "unauthorized" in lower:
            status = 401
        elif "402" in msg or "payment" in lower:
            status = 402
        elif "403" in msg or "quota" in lower or "limit exceeded" in lower or "key limit" in lower:
            status = 403
        elif "429" in msg or "rate limit" in lower:
            status = 429

        if status in (402, 403, 429):
            hint = "OpenRouter Key 超额或受限，请前往 https://openrouter.ai/settings/keys 管理额度或更换 Key。也可设置环境变量 OPENROUTER_API_KEY 或在 backend/setting.toml 配置 api_key。"
            raise HTTPException(status_code=status, detail=f"AI 调用失败: {hint}")
        raise HTTPException(status_code=status, detail=f"AI 调用失败: {msg}")


# ============== AI Chat 历史接口 ==============
@app.get("/ai/history", response_model=ChatHistory)
def get_ai_history(
    project_name: Optional[str] = Query(None, description="项目名（可选）"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数上限"),
    db: Session = Depends(get_db),
) -> ChatHistory:
    from models import ChatMessage
    q = db.query(ChatMessage)
    if project_name:
        q = q.filter(ChatMessage.project_name == project_name)
    else:
        q = q.filter(ChatMessage.project_name.is_(None))
    total = q.count()
    items = q.order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc()).limit(limit).all()
    # Pydantic from_attributes 支持 ORM -> schema 直接返回
    return ChatHistory(items=items, total=total)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)