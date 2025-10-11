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
api_key = load(open("setting.toml",'r',encoding='utf-8'))["api_key"]

custom_model = LitellmModel(
    model="openrouter/z-ai/glm-4.5-air:free",
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
    agent = Agent(name="Assistant", mcp_servers=[server], model=custom_model)
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
