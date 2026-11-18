import json
import urllib.request
import urllib.error

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.croma.com/",
}

# Test Croma auto-suggest or search api
test_urls = [
    "https://api.croma.com/search/v1/search?query=laptop&currentPage=0&pageSize=10",
    "https://www.croma.com/searchB?q=laptop&showFacets=true",
    "https://api.ajio.com/api/search?text=shoes",
    "https://www.ajio.com/api/search?fields=DEFAULT&currentPage=0&pageSize=10&format=json&query=shoes",
]

for url in test_urls:
    print(f"Testing {url[:60]}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            print("Status:", resp.status, "Length:", len(data))
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.reason)
    except Exception as e:
        print("Error:", e)
