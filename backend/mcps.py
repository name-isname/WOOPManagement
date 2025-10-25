from mcp.server.fastmcp import FastMCP
from schema import WOOPCreate
from crud import woop_crud
from database import SessionLocal
from sqlalchemy.orm import Session
from models import WOOP

mcp = FastMCP("WOOPManagement")

@mcp.tool()
def mcp_create_woop(
    name : str,
    wish : str,
    outcome : str,
    obstacle : str,
    plan : str):
    '''利用MCP帮助创建一个WOOP'''
    with SessionLocal() as db:
        woop_crud.create(db=db, woop_data=WOOPCreate(
            name=name,
            wish=wish,
            outcome=outcome,
            obstacle=obstacle,
            plan=plan,
            description=None
            )
        )

@mcp.resource(uri="woops://all",name="Get all WOOP items")
def mcp_get_woops() -> list[WOOP]:
    '''查看所有的WOOP'''
    with SessionLocal() as db:
        return woop_crud.get_all(db=db, skip=0, limit=100) # type: ignore

# FastMCP 通过 stdio 方式运行（见 agentset.py），无需在 FastAPI 中挂载 HTTP 子应用

if __name__ == "__main__":
    mcp.run(transport="stdio")