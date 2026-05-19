import httpx
import asyncio
import json

async def check():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get("http://127.0.0.1:4096/doc")
        doc = r.json()
        
        # Find session message endpoint
        for path, methods in doc.get("paths", {}).items():
            if "message" in path.lower():
                print(f"\n=== {path} ===")
                print(json.dumps(methods, indent=2)[:3000])
        
        # Find components schemas
        schemas = doc.get("components", {}).get("schemas", {})
        for name in schemas:
            print(f"\n=== Schema: {name} ===")
            print(json.dumps(schemas[name], indent=2)[:2000])

asyncio.run(check())
