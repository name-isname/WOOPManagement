# 软件架构
数据库，SQlite
后端，python，FastAPI，SQLalchemy，pydantic，uv
前端，vue3，tailwindcss，vite

## 表设计
WOOP表
id(primary key),name,wish,obstacle,action,result,date,rank,discription。

## 文件分层
main.py 绑定路由
schema.py 数据检验dto模型
crud.py 操作数据库
models.py 数据库表模型
database.py 数据库连接