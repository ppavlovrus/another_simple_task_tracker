#from time import sleep
#from asyncio import sleep
import time
import asyncio
from time import sleep

from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    sleep(10)
    return "Hello World"

@app.get("/blocking-async")
def bad():
    time.sleep(10)  # ← BLOCKS THE EVENT LOOP!
    return "Blocked"

@app.get("/async-sleep")
async def good():
    # Асинхронный эндпоинт — НЕ блокирует event loop!
    await asyncio.sleep(10)  # ← ПРАВИЛЬНО!
    return "Hello World (async)"

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sync_fast_Api:app", host="0.0.0.0", port=8002, reload=True)