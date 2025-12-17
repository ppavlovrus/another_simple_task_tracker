# async_demo.py
import asyncio
import time
import httpx

async def fetch(client, url):
    print(f"Запрашиваю {url}")
    response = await client.get(url)
    return response.status_code

async def main():
    urls = ["https://httpbin.org/delay/1"] * 5
    start = time.time()

    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, url) for url in urls]
        results = await asyncio.gather(*tasks)

    for status in results:
        print(f"Получен статус: {status}")

    end = time.time()
    print(f"Асинхронно: {end - start:.2f} секунд")

if __name__ == "__main__":
    asyncio.run(main())