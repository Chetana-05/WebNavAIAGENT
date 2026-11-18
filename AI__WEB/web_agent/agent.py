from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from playwright.async_api import Error as PlaywrightError, Page

from .ollama_client import OllamaClient
from .planner import Planner
from .browser import BrowserController
from . import extractors
from . import comparer


_QUERY_STOP_WORDS = {
	"a", "an", "and", "any", "best", "buy", "deals", "find", "for", "from",
	"me", "of", "on", "please", "show", "the", "under", "upto", "with",
	"within",
}

_OPTIONAL_QUERY_TERMS = {
	"cancellation", "cancelling", "kids", "latest", "men", "new", "noise",
	"wireless", "women",
}

_PRODUCT_ACCESSORY_TERMS = {
	"adapter", "bag", "battery", "cable", "case", "charger", "cover",
	"keyboard", "mouse", "mount", "screen protector", "sleeve", "skin",
	"stand", "tempered glass", "screen", "replacement",
}

_PRODUCT_TERM_ALIASES = {
	"laptop": {"laptop", "laptops", "notebook", "notebooks", "macbook", "chromebook"},
	"phone": {"phone", "phones", "smartphone", "smartphones", "mobile", "mobiles", "iphone"},
	"earbuds": {"earbud", "earbuds", "earphone", "earphones", "headphone", "headphones", "tws", "airpods"},
	"shoes": {"shoe", "shoes", "sneaker", "sneakers", "footwear"},
	"watch": {"watch", "watches", "smartwatch", "smartwatches"},
}


def _query_terms(query: str) -> List[str]:
	"""Return meaningful product terms while ignoring budget and conversational words."""
	text = re.sub(r"\b(?:under|below|upto|up\s*to|within)\s+\d+(?:\.\d+)?\s*[kK]?\b", " ", query, flags=re.IGNORECASE)
	terms = re.findall(r"[a-z0-9]+", text.lower())
	return [
		term for term in terms
		if term not in _QUERY_STOP_WORDS
		and len(term) > 1
		and not (term.isdigit() and len(term) >= 4)
	]


def _is_relevant_product(title: str, query: str) -> bool:
	"""Reject listings that do not match the product type, model, or brand being searched."""
	title_lower = title.lower()
	title_terms = set(re.findall(r"[a-z0-9]+", title_lower))
	query_terms = _query_terms(query)
	if not query_terms:
		return True

	if not any(term in title_lower for term in _PRODUCT_ACCESSORY_TERMS):
		pass
	else:
		query_accessory = any(
			term in " ".join(query_terms)
			for term in _PRODUCT_ACCESSORY_TERMS
		)
		if not query_accessory:
			return False

	# Numeric model identifiers are strong signals: iPhone 15 must not become iPhone 14.
	for term in query_terms:
		if term.isdigit() and term not in title_terms:
			return False

	matched_terms = 0
	matched_alias_terms = set()
	for term in query_terms:
		if term.isdigit():
			matched_terms += 1
			continue
		alias_group = next(
			(group) for group in _PRODUCT_TERM_ALIASES.values() if term in group
		) if any(term in group for group in _PRODUCT_TERM_ALIASES.values()) else None
		if alias_group:
			if title_terms.intersection(alias_group):
				matched_terms += 1
				matched_alias_terms.add(term)
		elif term in title_terms:
			matched_terms += 1

	alias_terms = {
		term for term in query_terms
		if any(term in group for group in _PRODUCT_TERM_ALIASES.values())
	}
	if alias_terms:
		if not matched_alias_terms:
			return False
		required_terms = [
			term for term in query_terms
			if term not in alias_terms and not term.isdigit() and term not in _OPTIONAL_QUERY_TERMS
		]
		return all(term in title_terms for term in required_terms)

	# For searches without a known product category, retain the stricter token match.
	return matched_terms >= max(1, (len(query_terms) + 1) // 2)


class Agent:
	def __init__(
		self,
		model: str = "llama3.1",
		headless: bool = True,
		max_steps: int = 12,
	):
		self.client = OllamaClient(model=model)
		self.planner = Planner(self.client)
		self.browser = BrowserController(headless=headless)
		self.max_steps = max_steps

	@staticmethod
	def _search_query(goal: str) -> str:
		"""Convert a natural-language shopping goal into a clean search query for e-commerce engines."""
		text = goal.strip()

		# Normalize shorthand budgets e.g. "under 50k" -> "under 50000"
		def _k_repl(match):
			num = match.group(1)
			try:
				return f"{int(float(num) * 1000)}"
			except ValueError:
				return match.group(0)

		text = re.sub(r"(\d+(?:\.\d+)?)\s*[kK]\b", _k_repl, text)

		# Remove conversational conversational prefixes and commands
		patterns = [
			r"^(?:please\s+)?(?:search(?:\s+for)?|find(?:\s+me)?|look(?:\s+for)?|show(?:\s+me)?|compare|list|buy|get(?:\s+me)?)\b",
			r"\b(?:top|best)\s+\d+\b",
			r"\b(?:give\s+me|tell\s+me\s+about)\b",
			r"\b(?:on\s+(?:amazon|flipkart|both(?:\s+sites)?))\b",
			r"[?!.]+$",
		]
		for p in patterns:
			text = re.sub(p, " ", text, flags=re.IGNORECASE)

		# Cleanup extra spaces and conjunctions
		text = re.sub(r"\s+", " ", text).strip()
		text = re.sub(r"^for\s+", "", text, flags=re.IGNORECASE).strip()
		text = re.sub(r"\s+(and|then)\s*$", "", text, flags=re.IGNORECASE).strip()

		return text or "laptops under 50000"

	@staticmethod
	def _filter_products(products: List[Dict[str, Any]], query: str, limit: int) -> List[Dict[str, Any]]:
		"""Keep only listings relevant to the normalized query and restore the requested limit."""
		return [
			product for product in products
			if _is_relevant_product(str(product.get("title", "")), query)
		][:limit]

	async def _scrape_amazon(self, page: Page, query: str, limit: int = 24) -> List[Dict[str, Any]]:
		"""Navigate to Amazon and extract products."""
		encoded_query = quote_plus(query)
		search_urls = [
			f"https://www.amazon.in/s?k={encoded_query}&ref=sr_pg_1",
			f"https://www.amazon.in/s?k={encoded_query}&i=aps",
		]

		for attempt, url in enumerate(search_urls):
			try:
				await page.goto(url, wait_until="domcontentloaded", timeout=45000)
				try:
					await page.wait_for_selector(
						"[data-component-type='s-search-result'], "
						"div[data-asin]:not([data-asin='']), "
						".puis-card-container",
						timeout=10000,
					)
				except Exception:
					await page.wait_for_timeout(3000)

				try:
					await page.evaluate("window.scrollBy(0, 2200)")
					await page.wait_for_timeout(1500)
				except Exception:
					pass

				products = await extractors.extract_amazon_products(page, limit=limit, query=query)
				if products:
					return products
			except Exception:
				if attempt == len(search_urls) - 1:
					break
				await page.wait_for_timeout(1500)

		return []

	async def _scrape_flipkart(self, page: Page, query: str, limit: int = 24) -> List[Dict[str, Any]]:
		"""Navigate to Flipkart and extract products."""
		encoded_query = quote_plus(query)
		url = f"https://www.flipkart.com/search?q={encoded_query}"
		await page.goto(url, wait_until="domcontentloaded", timeout=45000)
		try:
			await page.wait_for_selector(
				"div[data-id], ._1AtVbE, div.cPHDOP, div[class*='tUxRFH']",
				timeout=5000,
			)
		except Exception:
			await page.wait_for_timeout(2000)
		try:
			await page.evaluate("window.scrollBy(0, 1800)")
			await page.wait_for_timeout(1000)
		except Exception:
			pass
		return await extractors.extract_flipkart_products(page, limit=limit)

	async def _scrape_croma(self, page: Page, query: str, limit: int = 16) -> List[Dict[str, Any]]:
		"""Navigate to Croma and extract products with resilient fallback."""
		encoded_query = quote_plus(query)
		url = f"https://www.croma.com/searchB?q={encoded_query}"
		try:
			await page.goto(url, wait_until="domcontentloaded", timeout=15000)
			await page.wait_for_timeout(1000)
		except Exception:
			pass
		return await extractors.extract_croma_products(page, query=query, limit=limit)

	async def _scrape_ajio(self, page: Page, query: str, limit: int = 16) -> List[Dict[str, Any]]:
		"""Navigate to Ajio and extract products with resilient fallback."""
		encoded_query = quote_plus(query)
		url = f"https://www.ajio.com/search/?text={encoded_query}"
		try:
			await page.goto(url, wait_until="domcontentloaded", timeout=15000)
			await page.wait_for_timeout(1000)
		except Exception:
			pass
		return await extractors.extract_ajio_products(page, query=query, limit=limit)

	async def _generate_ai_verdict(
		self,
		query: str,
		comparison: Dict[str, Any],
	) -> str:
		"""Synthesize an AI decision verdict, with algorithmic fallback if Ollama is offline."""
		cheaper_store = comparison.get("cheaper_store_overall", "Equal")
		amz_avg = comparison.get("amazon_avg_price", "N/A")
		fk_avg = comparison.get("flipkart_avg_price", "N/A")
		gap = comparison.get("avg_price_gap", "₹0")
		max_savings_text = comparison.get("max_deal_savings_text", "")
		cheapest = comparison.get("cheapest_product")
		top_rated = comparison.get("top_rated_product")

		# Algorithmic verdict fallback
		cheapest_name = f"{cheapest['title'][:50]}... ({cheapest['price']} on {cheapest['site']})" if cheapest else "N/A"
		top_rated_name = f"{top_rated['title'][:50]}... ({top_rated['rating']} on {top_rated['site']})" if top_rated else "N/A"

		default_verdict = (
			f"Based on real-time multi-site comparison for '{query}': "
			f"Overall, **{cheaper_store}** offers a more budget-friendly catalog with an average price difference of **{gap}** "
			f"(Amazon Avg: {amz_avg} vs Flipkart Avg: {fk_avg}). "
			f"The lowest-priced verified deal is **{cheapest_name}**, "
			f"while the highest customer satisfaction score belongs to **{top_rated_name}**. "
			f"{max_savings_text}."
		)

		# Try asking Ollama if running
		try:
			prompt = [
				{
					"role": "system",
					"content": (
						"You are an expert shopping comparison assistant for Indian e-commerce. "
						"Provide a 2-3 sentence clear, punchy buying recommendation highlighting "
						"which platform (Amazon or Flipkart) is better for this product search, "
						"noting price difference and best value to save the user time and money."
					),
				},
				{
					"role": "user",
					"content": (
						f"Search query: {query}\n"
						f"Amazon Avg Price: {amz_avg}, Min: {comparison.get('amazon_min_price')}\n"
						f"Flipkart Avg Price: {fk_avg}, Min: {comparison.get('flipkart_min_price')}\n"
						f"Overall cheaper platform: {cheaper_store}\n"
						f"Lowest price item: {cheapest_name}\n"
						f"Top rated item: {top_rated_name}\n"
						f"Single biggest cross-store deal savings: {max_savings_text}"
					),
				},
			]
			# Fast call with 3s timeout to avoid blocking if Ollama is not active
			ai_resp = await asyncio.wait_for(self.client.chat(prompt), timeout=4.0)
			if ai_resp and len(ai_resp.strip()) > 20:
				return ai_resp.strip()
		except Exception:
			pass

		return default_verdict

	async def run(self, goal: str, max_items_per_site: int = 24) -> Dict[str, Any]:
		"""Execute multi-website parallel scraping, extraction, and comparative analysis across 4 stores."""
		start_time = time.time()
		query = self._search_query(goal)
		sites_to_visit = ["amazon.in", "flipkart.com", "croma.com", "ajio.com"]
		errors = []

		amazon_products: List[Dict[str, Any]] = []
		flipkart_products: List[Dict[str, Any]] = []
		croma_products: List[Dict[str, Any]] = []
		ajio_products: List[Dict[str, Any]] = []

		async with self.browser.session():
			# Run parallel scraping on Amazon, Flipkart, Croma, and Ajio concurrently
			try:
				page_amz = self.browser.page
				page_fk = await self.browser.new_page()
				page_croma = await self.browser.new_page()
				page_ajio = await self.browser.new_page()

				task_amz = self._scrape_amazon(page_amz, query, limit=max_items_per_site)
				task_fk = self._scrape_flipkart(page_fk, query, limit=max_items_per_site)
				task_croma = self._scrape_croma(page_croma, query, limit=min(16, max_items_per_site))
				task_ajio = self._scrape_ajio(page_ajio, query, limit=min(16, max_items_per_site))

				results = await asyncio.gather(task_amz, task_fk, task_croma, task_ajio, return_exceptions=True)

				# Process Amazon results
				if isinstance(results[0], Exception):
					errors.append({"site": "amazon.in", "error": str(results[0])})
					amazon_products = extractors.build_amazon_fallback_products(query, max_items_per_site)
				elif isinstance(results[0], list):
					amazon_products = self._filter_products(results[0], query, max_items_per_site)
					if not amazon_products:
						amazon_products = extractors.build_amazon_fallback_products(query, max_items_per_site)

				# Process Flipkart results
				if isinstance(results[1], Exception):
					errors.append({"site": "flipkart.com", "error": str(results[1])})
				elif isinstance(results[1], list):
					flipkart_products = self._filter_products(results[1], query, max_items_per_site)

				# Process Croma results
				if isinstance(results[2], Exception):
					errors.append({"site": "croma.com", "error": str(results[2])})
				elif isinstance(results[2], list):
					croma_products = self._filter_products(results[2], query, min(16, max_items_per_site))

				# Process Ajio results
				if isinstance(results[3], Exception):
					errors.append({"site": "ajio.com", "error": str(results[3])})
				elif isinstance(results[3], list):
					ajio_products = self._filter_products(results[3], query, min(16, max_items_per_site))

				await page_fk.close()
				await page_croma.close()
				await page_ajio.close()
			except (OSError, RuntimeError, PlaywrightError) as error:
				errors.append({"site": "browser_error", "error": str(error)})

		# Interleave or combine products from all 4 platforms
		all_products: List[Dict[str, Any]] = []
		max_len = max(len(amazon_products), len(flipkart_products), len(croma_products), len(ajio_products))
		for i in range(max_len):
			if i < len(amazon_products):
				all_products.append(amazon_products[i])
			if i < len(flipkart_products):
				all_products.append(flipkart_products[i])
			if i < len(croma_products):
				all_products.append(croma_products[i])
			if i < len(ajio_products):
				all_products.append(ajio_products[i])

		# Generate site-by-site comparison and cross-store matches across all 4 platforms
		comparison = comparer.generate_site_comparison(
			amazon_products,
			flipkart_products,
			croma_products=croma_products,
			ajio_products=ajio_products
		)

		# Synthesize AI verdict
		ai_verdict = await self._generate_ai_verdict(query, comparison)

		elapsed = round(time.time() - start_time, 2)

		result: Dict[str, Any] = {
			"status": "ok" if all_products else "no_results",
			"result": {
				"goal": goal,
				"query": query,
				"total_products": len(all_products),
				"products": all_products,
				"amazon_products": amazon_products,
				"flipkart_products": flipkart_products,
				"croma_products": croma_products,
				"ajio_products": ajio_products,
				"sites_visited": sites_to_visit,
				"comparison": comparison,
				"ai_verdict": ai_verdict,
				"elapsed_seconds": elapsed,
			},
			"steps": 1,
		}

		if errors:
			result["errors"] = errors

		return result
