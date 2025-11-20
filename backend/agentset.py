from agents.mcp import MCPServerStdio
import asyncio
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_tracing_disabled,
    set_default_openai_client,
    run_demo_loop,
)
from agents.extensions.models.litellm_model import LitellmModel
from agents.items import TResponseInputItem
from os import getcwd

from openai import AsyncOpenAI


from typing import AsyncIterator
from openai.types.responses import ResponseTextDeltaEvent

from rtoml import load


filepath = getcwd()

base_url = "https://openrouter.ai/api/v1"
api_key = load(open("setting.toml", "r", encoding="utf-8"))["api_key"]

custom_model = LitellmModel(
    model="openrouter/x-ai/grok-4.1-fast",
    base_url=base_url,
    api_key=api_key,
)

set_default_openai_client(
    AsyncOpenAI(base_url=base_url, api_key=api_key), use_for_tracing=False
)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=False)


def create_agent():
    server = MCPServerStdio(
        name="read woops Server via uv",
        params={
            "command": "uv",
            "args": ["--directory", filepath, "run", "mcps.py"],
        },
    )
    agent = Agent(
        name="Assistant",
        instructions="你是一个帮助用户建立WOOP的助手，你需要一步一步地引导用户去完成WOOP的建立过程" \
        "你需要通过不断地对话来引导用户完成WOOP的建立，每次只问一个问题，等待用户回答后再进行下一个问题。" \
        "1. 首先，问用户他们的愿望是什么（wish）。" \
        "2. 然后，问用户他们认为实现这个愿望的障碍是什么（obstacle）。" \
        "3. 接着，问用户他们打算如何克服这些障碍（plan）。" \
        "4. 最后，问用户他们期望实现这个愿望后的结果是什么（outcome）。" \
        "在整个过程中，确保你的问题简洁明了，并且每次只关注一个方面。" \
        "在用户回答后，确认他们的回答，并引导他们进入下一个问题。" \
        "当用户完成所有四个步骤后，总结他们的WOOP，并鼓励他们开始行动。" ,
        mcp_servers=[server],
        model=custom_model,
    )
    return agent, server


# def create_agent_v2():
#     server = MCPServerSse(
#         name="read woops Server via uv",
#         params={
#              "url": "http://localhost:8000/sse",
#              "headers": {"X-Workspace": workspace_id},
#         },
#     )
#     agent = Agent(
#         name="Assistant",
#         mcp_servers=[server],
#         model=custom_model
#     )
#     return agent, server


async def test():
    agent, server = create_agent()
    async with server:
        await run_demo_loop(agent)


async def useagent(input_items: list[TResponseInputItem]) -> AsyncIterator[str]:
    agent, server = create_agent()
    async with server:
        result = Runner.run_streamed(agent, input=input_items)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                yield event.data.delta


if __name__ == "__main__":
    asyncio.run(test())
