from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


DEFAULT_USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
	"AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/124.0.0.0 Safari/537.36"
)


class BrowserController:
	def __init__(self, headless: bool = True):
		self.headless = headless
		self._browser: Optional[Browser] = None
		self._context: Optional[BrowserContext] = None
		self._page: Optional[Page] = None

	@asynccontextmanager
	async def session(self):
		async with async_playwright() as p:
			launch_options: Dict[str, Any] = {"headless": self.headless}
			executable_path = os.getenv("WEB_AGENT_BROWSER_PATH")
			if executable_path:
				launch_options["executable_path"] = executable_path

			browser = await p.chromium.launch(**launch_options)
			context = await browser.new_context(
				user_agent=DEFAULT_USER_AGENT,
				viewport={"width": 1280, "height": 800},
				device_scale_factor=1,
				locale="en-IN",
				timezone_id="Asia/Kolkata",
				extra_http_headers={
					"Accept-Language": "en-IN,en;q=0.9",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
				},
			)
			page = await context.new_page()
			self._browser = browser
			self._context = context
			self._page = page

			try:
				yield self
			finally:
				await page.close()
				await context.close()
				await browser.close()

	@property
	def page(self) -> Page:
		assert self._page is not None, "Browser session not started"
		return self._page

	@property
	def context(self) -> BrowserContext:
		assert self._context is not None, "Browser context not initialized"
		return self._context

	async def new_page(self) -> Page:
		"""Open a new tab in the active browser context for parallel scraping."""
		assert self._context is not None, "Browser session not started"
		return await self._context.new_page()

	async def navigate(self, url: str):
		await self.page.goto(url, wait_until="domcontentloaded", timeout=45000)

	async def type_text(self, selector: str, value: str, press_enter: bool = False):
		await self.page.fill(selector, value)
		if press_enter:
			await self.page.keyboard.press("Enter")

	async def click(self, selector: str):
		await self.page.click(selector)

	async def wait(self, seconds: float = 1.0):
		await self.page.wait_for_timeout(int(seconds * 1000))

	async def get_observation(self, max_text_len: int = 5000) -> Dict[str, Any]:
		title = await self.page.title()
		url = self.page.url
		text = await self.page.evaluate("() => document.body.innerText.slice(0, 10000)")
		if text and len(text) > max_text_len:
			text = text[:max_text_len]
		return {"title": title, "url": url, "text": text}
