from sqlalchemy import Integer, String, Text, Date, func
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class WOOP(Base):
    """WOOP表模型"""

    __tablename__ = "woop"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="名称")
    wish: Mapped[str] = mapped_column(Text, nullable=False, comment="愿望")
    obstacle: Mapped[str] = mapped_column(Text, nullable=False, comment="障碍")
    plan: Mapped[str] = mapped_column(Text, nullable=False, comment="行动")
    outcome: Mapped[str] = mapped_column(Text, nullable=False, comment="结果")
    # 新记录默认填充当前日期，且允许为空以兼容历史数据
    datetime: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
        default=date.today,  # Python 端默认值，适用于旧表结构
        server_default=func.current_date(),  # 数据库端默认值（新建表时生效）
        comment="日期",
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="排名")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    def __repr__(self) -> str:
        return f"<WOOP(id={self.id}, name='{self.name}', date='{self.datetime}')>"
