import asyncio
import atexit
import json
from collections.abc import AsyncGenerator
from enum import Enum
from typing import Any

import aiohttp

DUCK_API = "https://duckduckgo.com/duckchat/v1/{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Accept": "text/event-stream",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://duckduckgo.com/",
    "Content-Type": "application/json",
    "Origin": "https://duckduckgo.com",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class Models(Enum):
    GPT_4_MINI = "gpt-4o-mini"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    LLAMA_3_1 = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    MIXTRAL_7B = "mistralai/Mixtral-8x7B-Instruct-v0.1"


class Chat:
    def __init__(self, session: aiohttp.ClientSession, model: Models) -> None:
        self._session = session
        self._headers = HEADERS.copy()

        self.model = model
        self.messages: list[dict[str, str]] = []

    async def _init_headers(self):
        if "x-vqd-4" in self._headers:
            return
        self._headers["x-vqd-accept"] = "1"
        url = DUCK_API.format("status")

        async with self._session.get(url, headers=self._headers) as resp:
            self._headers["x-vqd-4"] = resp.headers["x-vqd-4"]

        del self._headers["x-vqd-accept"]

    def _add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def _build_paylaod(self) -> dict[str, Any]:
        return {"model": self.model.value, "messages": self.messages}

    async def send(self, msg: str) -> AsyncGenerator[str, None]:
        await self._init_headers()
        self._add_message("user", msg)

        payload = self._build_paylaod()
        url = DUCK_API.format("chat")

        full_message = ""
        async with self._session.post(url, json=payload, headers=self._headers) as resp:
            self._headers["x-vqd-4"] = resp.headers["x-vqd-4"]
            async for chunk in resp.content:
                parsed_chunk = chunk.decode()[5::].strip()
                if not parsed_chunk or parsed_chunk == "[DONE]":
                    continue

                decoded_chunk = json.loads(parsed_chunk)
                if "message" not in decoded_chunk:
                    continue

                full_message += decoded_chunk["message"]
                yield decoded_chunk["message"]

        self._add_message("assistant", full_message)


class DuckAI:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
        atexit.register(self.close)

    def create_new_chat(self, model: Models) -> Chat:
        return Chat(self.session, model)

    def close(self):
        try:
            asyncio.run(self.session.close())
        except:
            pass
