import httpx
import asyncio

async def check():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get("http://127.0.0.1:4096/doc")
        print(r.text[:3000])

asyncio.run(check())
