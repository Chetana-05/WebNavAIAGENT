import asyncio
from playwright.async_api import async_playwright

async def test_sites():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Test Croma
        page1 = await context.new_page()
        print("Testing Croma search...")
        try:
            await page1.goto("https://www.croma.com/searchB?q=laptops%20under%2050000", timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            croma_title = await page1.title()
            print("Croma page title:", croma_title)
            croma_content = await page1.content()
            print("Croma content length:", len(croma_content))
            # Check for product selectors
            cards = await page1.query_selector_all(".product-item, .cp-product, li.product-item, .product-card")
            print("Croma cards found:", len(cards))
        except Exception as e:
            print("Croma error:", e)
        await page1.close()

        # Test Ajio
        page2 = await context.new_page()
        print("\nTesting Ajio search...")
        try:
            await page2.goto("https://www.ajio.com/search/?text=shoes", timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            ajio_title = await page2.title()
            print("Ajio page title:", ajio_title)
            ajio_content = await page2.content()
            print("Ajio content length:", len(ajio_content))
            cards2 = await page2.query_selector_all(".item, .rilrtl-products-list__item, .preview")
            print("Ajio cards found:", len(cards2))
        except Exception as e:
            print("Ajio error:", e)
        await page2.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sites())
