import httpx
import asyncio

async def check():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get("http://127.0.0.1:4096/global/health")
        print("HEALTH:", r.text[:500])
        
        r2 = await c.get("http://127.0.0.1:4096/session")
        print("SESSIONS:", r2.text[:500])
        
        r3 = await c.get("http://127.0.0.1:4096/global/models")
        print("MODELS:", r3.text[:1000])

asyncio.run(check())
