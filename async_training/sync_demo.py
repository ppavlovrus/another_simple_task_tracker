# sync_demo.py
import time
import requests

def fetch(url):
    print(f"Запрашиваю {url}")
    response = requests.get(url)
    return response.status_code

def main():
    urls = ["https://httpbin.org/delay/1"] * 5
    start = time.time()

    for url in urls:
        status = fetch(url)
        print(f"Получен статус: {status}")

    end = time.time()
    print(f"Синхронно: {end - start:.2f} секунд")

if __name__ == "__main__":
    main()