from __future__ import annotations

import asyncio
import sys
from typing import Optional

import orjson
import typer

from .agent import Agent


app = typer.Typer(add_completion=False)


@app.command()
def main(
	goal: str = typer.Option(..., "--goal", help="Natural language instruction for the agent"),
	limit: int = typer.Option(5, "--limit", "-l", help="Number of items to display per store"),
	model: str = typer.Option("llama3.1", "--model", help="Ollama model name"),
	headless: bool = typer.Option(True, "--headless/--headed", help="Run browser headless"),
	max_steps: int = typer.Option(12, "--max-steps", min=1, max=50, help="Max planning steps"),
	json_output: bool = typer.Option(False, "--json", help="Output raw JSON instead of formatted report"),
):
	async def run():
		if hasattr(sys.stdout, "reconfigure"):
			sys.stdout.reconfigure(encoding="utf-8")

		print(f"\n🔍 [Web Navigator AI Agent] Searching multi-store catalog for: '{goal}' (Limit: {limit} per store)...")
		agent = Agent(model=model, headless=headless, max_steps=max_steps)
		result = await agent.run(goal)

		data = result.get("result", {})
		comparison = data.get("comparison", {})
		all_products = data.get("products", [])
		same_matches = comparison.get("same_product_matches", [])
		matches = comparison.get("cross_site_matches", [])

		if json_output:
			print(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode())
			return

		print("\n" + "=" * 80)
		print(f"🛍️  MULTI-STORE PRODUCT & PRICE COMPARISON REPORT")
		print("=" * 80)
		print(f"🎯 Target Query       : {data.get('query')}")
		print(f"🏪 Stores Compared     : Amazon.in, Flipkart.com, Croma.com, Ajio.com")
		print(f"📦 Total Extracted     : {len(all_products)} Items across 4 platforms")
		print("-" * 80)

		# Platform Analytics
		print("📊 SITE-BY-SITE PRICE SUMMARY:")
		print(f"  • Amazon Avg Price   : {comparison.get('amazon_avg_price')} (Lowest: {comparison.get('amazon_min_price')})")
		print(f"  • Flipkart Avg Price  : {comparison.get('flipkart_avg_price')} (Lowest: {comparison.get('flipkart_min_price')})")
		print(f"  • Croma Avg Price     : {comparison.get('croma_avg_price')} (Lowest: {comparison.get('croma_min_price')})")
		print(f"  • Ajio Avg Price      : {comparison.get('ajio_avg_price')} (Lowest: {comparison.get('ajio_min_price')})")
		print(f"  • Cheaper Store Overall: {comparison.get('cheaper_store_overall').upper()} (Avg spread: {comparison.get('avg_price_gap')})")
		print(f"  • Biggest Deal Savings: {comparison.get('max_deal_savings_text')}")
		print("-" * 80)

		# Compare Same Product (Strict Brand & Hardware Match)
		if same_matches:
			print(f"\n🎯 STRICT SAME PRODUCT MATCHES ({len(same_matches)} verified identical pairs):")
			for idx, m in enumerate(same_matches[:limit], 1):
				amz = m["amazon"]
				fk = m["flipkart"]
				print(f"\n  [Item #{idx}] {m['brand']} | ✓ Exact Same Model | {m.get('verified_specs', 'Hardware Verified')}")
				print(f"    🛒 Amazon  : {amz['title'][:55]}... | {amz['price']} | {amz['rating']}")
				print(f"    🛍️ Flipkart : {fk['title'][:55]}... | {fk['price']} | {fk['rating']}")
				print(f"    🏆 Winner   : {m['winner']} -> {m['savings_text']}")
			print("-" * 80)
		elif matches:
			print("\n🥊 CROSS-STORE EQUIVALENT MATCHES:")
			for idx, m in enumerate(matches[:limit], 1):
				amz = m["amazon"]
				fk = m["flipkart"]
				print(f"\n  [Match #{idx}] {m['savings_text']} (Similarity: {m['similarity']}%)")
				print(f"    🛒 Amazon  : {amz['title'][:55]}... | {amz['price']} | {amz['rating']}")
				print(f"    🛍️ Flipkart : {fk['title'][:55]}... | {fk['price']} | {fk['rating']}")
				print(f"    💰 Difference: {m['price_difference']} ({m['percent_difference']}) -> Winner: {m['winner']}")
			print("-" * 80)

		# Top Ranked Products Table
		print("\n🏆 TOP RANKED PRODUCTS BY VALUE:")
		header = f"{'Site':<10} | {'Price':<10} | {'MRP':<10} | {'Disc':<8} | {'Rating':<8} | {'Score':<6} | {'Title'}"
		print(header)
		print("-" * len(header))
		for p in all_products[:limit * 2]:
			site = p.get("site", "N/A")
			price = p.get("price", "N/A")
			mrp = p.get("mrp", "N/A")
			disc = p.get("discount", "N/A")
			rating = p.get("rating", "N/A")
			score = p.get("value_score", "N/A")
			title = p.get("title", "N/A")[:40]
			print(f"{site:<10} | {price:<10} | {mrp:<10} | {disc:<8} | {rating:<8} | {score:<6} | {title}...")

		# AI Verdict
		verdict = data.get("ai_verdict")
		if verdict:
			print("\n" + "=" * 80)
			print("🤖 AI AGENT VERDICT & TIME-SAVING RECOMMENDATION:")
			print(verdict)
			print("=" * 80)

		print("\n💡 Open http://127.0.0.1:8000 in your browser to view the interactive web dashboard!\n")

	asyncio.run(run())


if __name__ == "__main__":
	app()
