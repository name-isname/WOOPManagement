from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class WOOPBase(BaseModel):
    """WOOP基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="名称")
    wish: str = Field(..., min_length=1, description="愿望")
    obstacle: str = Field(..., min_length=1, description="障碍")
    plan: str = Field(..., min_length=1, description="行动")
    outcome: str = Field(..., min_length=1, description="结果")
    description: Optional[str] = Field(None, description="备注")

    class Config:
        from_attributes = True

class WOOPCreate(WOOPBase):
    """创建WOOP时的请求模型"""
    pass

class WOOPUpdate(BaseModel):
    """更新WOOP时的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="名称")
    wish: Optional[str] = Field(None, min_length=1, description="愿望")
    obstacle: Optional[str] = Field(None, min_length=1, description="障碍")
    plan: Optional[str] = Field(None, min_length=1, description="行动")
    outcome: Optional[str] = Field(None, min_length=1, description="结果")
    datetime: Optional[date] = Field(None, description="日期")
    rank: Optional[int] = Field(None, ge=1, description="排名")
    description: Optional[str] = Field(None, description="备注")

    class Config:
        from_attributes = True

class WOOPdelete(BaseModel):
    """删除WOOP时的请求模型"""
    id: int = Field(..., description="ID")

    class Config:
        from_attributes = True

class WOOPResponse(WOOPBase):
    """WOOP响应模型"""
    id: int = Field(..., description="ID")
    datetime: date = Field(..., description="日期")
    rank: Optional[int] = Field(None, ge=1, description="排名")
    

class WOOPList(BaseModel):
    """WOOP列表响应模型"""
    items: list[WOOPResponse]
    total: int = Field(..., description="总数量")
    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页数量")

    class Config:
        from_attributes = True
    
class MessageResponse(BaseModel):
    """通用消息响应模型"""
    message: str = Field(..., description="响应消息")

    class Config:
        from_attributes = True