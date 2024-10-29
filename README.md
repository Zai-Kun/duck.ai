# Python wrapper for duck.ai API

A python lib that allows you to chat with AI models through [duck.ai](https://duck.ai)

## Example Usage
```python
import asyncio

from duck_ai import DuckAI, Models


async def main():
    duck = DuckAI()

    chat = duck.create_new_chat(Models.GPT_4_MINI)

    while True:
        msg = input("User: ")
        print("\nAssistant: ", end="")
        async for chunk in chat.send(msg):
            print(chunk, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
```
