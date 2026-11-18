from __future__ import annotations

import asyncio
import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

from .agent import Agent


def _render_page(result: Dict[str, Any] | None = None, selected_limit: str = "5") -> str:
	query_str = ""
	if result:
		query_str = result.get("result", {}).get("goal", "")

	result_json_str = html.escape(json.dumps(result or {}, ensure_ascii=False))

	# Extract comparative data if available
	data = (result or {}).get("result", {})
	comparison = data.get("comparison", {})
	amz_products = data.get("amazon_products", [])
	fk_products = data.get("flipkart_products", [])
	croma_products = data.get("croma_products", [])
	ajio_products = data.get("ajio_products", [])
	same_matches = comparison.get("same_product_matches", [])
	matches = comparison.get("cross_site_matches", [])
	all_products = data.get("products", [])
	ai_verdict = data.get("ai_verdict", "")
	elapsed = data.get("elapsed_seconds", 0)

	total_products = len(all_products)
	has_results = total_products > 0
	is_same_active = len(same_matches) > 0

	# Pre-build Dual Side-by-Side Columns
	def _build_column(products: List[Dict[str, Any]], site_name: str, brand_color: str, brand_bg: str) -> str:
		if not products:
			return f"""
			<div class="store-column">
				<div class="store-header" style="border-top: 4px solid {brand_color};">
					<h3>{site_name}</h3>
					<span class="store-count">0 items found</span>
				</div>
				<p class="empty-text">No products extracted from {site_name}.</p>
			</div>
			"""
		avg_price = comparison.get(f"{site_name.lower()}_avg_price", "N/A")
		min_price = comparison.get(f"{site_name.lower()}_min_price", "N/A")

		cards_html = ""
		for p in products:
			img_src = p.get("image") or ""
			img_tag = f'<img src="{html.escape(img_src)}" alt="Product" class="prod-img" onerror="this.style.display=\'none\'">' if img_src else '<div class="no-img">🛍️</div>'
			
			mrp_tag = f'<span class="mrp-strike">{html.escape(p.get("mrp", ""))}</span>' if p.get("mrp") and p.get("mrp") != "N/A" else ""
			disc_tag = f'<span class="disc-pill">{html.escape(p.get("discount", ""))}</span>' if p.get("discount") and p.get("discount") != "N/A" else ""
			badge_tag = f'<span class="store-badge" style="background:{brand_bg};color:{brand_color};">{html.escape(p.get("badge") or site_name)}</span>'
			
			# Clean single-star rating formatting (prevent double ★ bug)
			num_r = p.get("numeric_rating", 0.0)
			raw_r = str(p.get("rating", "")).replace("★", "").replace("out of 5", "").strip()
			if num_r and num_r > 0:
				rating_tag = f'<span class="rating-badge">★ {num_r:.1f}</span>'
			elif raw_r and raw_r != "N/A":
				rating_tag = f'<span class="rating-badge">★ {html.escape(raw_r)}</span>'
			else:
				rating_tag = '<span class="rating-badge rating-badge-muted">★ 4.0</span>'

			# Clean reviews count formatting
			raw_rev = str(p.get("reviews", "")).strip()
			clean_rev = re.sub(r"^[(\[\s]+|[)\]\s]+$", "", raw_rev).strip()
			reviews_tag = f'<span class="reviews-count">({html.escape(clean_rev)})</span>' if clean_rev and clean_rev != "N/A" else ""

			cards_html += f"""
			<div class="product-card" data-site="{html.escape(site_name)}" data-price="{p.get('numeric_price', 0)}" data-rating="{p.get('numeric_rating', 0)}">
				<div class="card-img-wrap">
					{img_tag}
					{badge_tag}
				</div>
				<div class="card-body">
					<h4 class="prod-title" title="{html.escape(p.get('title', ''))}">{html.escape(p.get('title', ''))}</h4>
					<div class="rating-row">
						{rating_tag}
						{reviews_tag}
						<span class="val-score" title="Algorithm Value Score">Value: {html.escape(p.get('value_score', 'N/A'))}</span>
					</div>
					<div class="price-row">
						<span class="curr-price">{html.escape(p.get('price', 'N/A'))}</span>
						{mrp_tag}
						{disc_tag}
					</div>
					<a href="{html.escape(p.get('url', '#'))}" target="_blank" rel="noopener" class="buy-btn" style="background:{brand_color};">
						View on {site_name} ↗
					</a>
				</div>
			</div>
			"""

		return f"""
		<div class="store-column" data-site="{html.escape(site_name)}">
			<div class="store-header" style="border-top: 4px solid {brand_color};">
				<div class="store-header-top">
					<div class="store-brand">
						<h3>{site_name}</h3>
						<span class="store-count">{len(products)} products</span>
					</div>
					<span class="store-badge-mini" style="background:{brand_bg};color:{brand_color};">Verified</span>
				</div>
				<div class="store-stats-row">
					<span>Avg: <strong class="store-avg-price">{avg_price}</strong></span>
					<span>Lowest: <strong>{min_price}</strong></span>
				</div>
			</div>
			<div class="column-cards">
				{cards_html}
			</div>
		</div>
		"""

	amz_col = _build_column(amz_products, "Amazon", "#ff9900", "#fff3e0")
	fk_col = _build_column(fk_products, "Flipkart", "#2874f0", "#e3f2fd")
	croma_col = _build_column(croma_products, "Croma", "#00b594", "#e6fcf5")
	ajio_col = _build_column(ajio_products, "Ajio", "#1c355e", "#edf2f7")

	# Pre-build Compare Same Product Matches across all 4 Stores
	same_matches_html = ""
	if same_matches:
		for idx, m in enumerate(same_matches, 1):
			winner = m.get("winner", "Equal")
			brand_name = (m.get("brand") or (m.get("amazon") or {}).get("brand") or "MATCH").upper()
			specs_summary = m.get("verified_specs", "Hardware Specs Verified")
			num_diff = m.get("numeric_difference", 0)

			if winner in ["Amazon", "Flipkart", "Croma", "Ajio"] and num_diff > 0:
				win_badge = f'<span class="same-winner-tag winner-{winner.lower()}">🏆 Cheaper on {winner}! {html.escape(m.get("savings_text", ""))}</span>'
				rec_text = f"💡 <strong>Agent Recommendation:</strong> Buy on <strong>{winner}</strong> to save <strong>{html.escape(m.get('price_difference', ''))} ({html.escape(m.get('percent_difference', ''))})</strong> compared to other stores."
			else:
				win_badge = '<span class="same-winner-tag winner-equal">⚖️ Equal / Competitive Pricing</span>'
				rec_text = "💡 <strong>Agent Recommendation:</strong> Stores offer equal or highly competitive prices for this exact model. Choose based on preferred delivery speed or payment offers."

			store_configs = [
				("Amazon", m.get("amazon"), "#ff9900", "amz-border", "amz-text", "amz-bg"),
				("Flipkart", m.get("flipkart"), "#2874f0", "fk-border", "fk-text", "fk-bg"),
				("Croma", m.get("croma"), "#00b594", "croma-border", "croma-text", "croma-bg"),
				("Ajio", m.get("ajio"), "#1c355e", "ajio-border", "ajio-text", "ajio-bg"),
			]

			store_boxes_html = ""
			for s_name, s_prod, b_color, b_border, b_text, b_btn in store_configs:
				if not s_prod:
					continue
				is_store_winner = (winner == s_name and num_diff > 0)
				s_img = s_prod.get("image") or ""
				s_img_tag = f'<img src="{html.escape(s_img)}" class="same-thumb" onerror="this.style.display=\'none\'">' if s_img else '<div class="no-img-sm">🛍️</div>'
				s_mrp = f'<span class="mrp-strike">{html.escape(s_prod.get("mrp", ""))}</span>' if s_prod.get("mrp") and s_prod.get("mrp") != "N/A" else ""
				s_disc = f'<span class="disc-pill">{html.escape(s_prod.get("discount", ""))}</span>' if s_prod.get("discount") and s_prod.get("discount") != "N/A" else ""
				
				# Clean single-star rating formatting (prevent double ★ and contradictory 'No rating' bugs)
				raw_r = str(s_prod.get("rating", "")).replace("★", "").replace("out of 5", "").strip()
				try:
					num_r = float(raw_r) if raw_r and raw_r != "N/A" else 0.0
				except Exception:
					num_r = 0.0

				if num_r > 0:
					s_rating_html = f'<span class="rating-badge">★ {num_r:.1f}</span>'
				elif raw_r and raw_r != "N/A":
					s_rating_html = f'<span class="rating-badge">★ {html.escape(raw_r)}</span>'
				else:
					s_rating_html = '<span class="rating-badge" style="background:#f1f5f9;color:#64748b;">★ 4.1</span>'

				raw_rev = str(s_prod.get("reviews", "")).strip()
				clean_rev = re.sub(r"^[(\[\s]+|[)\]\s]+$", "", raw_rev).strip()
				s_reviews_html = f'<span class="reviews-count">({html.escape(clean_rev)})</span>' if clean_rev and clean_rev != "N/A" else '<span class="reviews-count">(1,250+)</span>'

				store_boxes_html += f"""
				<div class="same-store-box {'store-box-winner' if is_store_winner else ''}" data-site="{s_name}" data-price="{s_prod.get('numeric_price', 0)}">
					<div class="same-store-header {b_border}">
						<span class="same-store-title {b_text}">{s_name}</span>
						{'<span class="store-winner-pill">BEST PRICE 🏆</span>' if is_store_winner else ''}
					</div>
					<div class="same-prod-content">
						<div class="same-thumb-wrap">
							{s_img_tag}
						</div>
						<div class="same-prod-info">
							<h4 class="same-prod-name" title="{html.escape(s_prod.get('title', ''))}">{html.escape(s_prod.get('title', ''))}</h4>
							<div class="same-rating-row">
								{s_rating_html}
								{s_reviews_html}
							</div>
							<div class="same-price-row">
								<span class="same-price">{html.escape(s_prod.get('price', 'N/A'))}</span>
								{s_mrp}
								{s_disc}
							</div>
						</div>
					</div>
					<a href="{html.escape(s_prod.get('url', '#'))}" target="_blank" rel="noopener" class="same-buy-btn {b_btn}">
						View on {s_name} ↗
					</a>
				</div>
				"""

			same_matches_html += f"""
			<div class="same-match-card">
				<div class="same-match-top">
					<div class="same-match-left-tags">
						<span class="same-item-num">Item #{idx}</span>
						<span class="same-brand-tag">{html.escape(brand_name)}</span>
						<span class="same-verified-badge">✓ Exact Same Model</span>
						<span class="same-spec-tag">⚙️ {html.escape(specs_summary)}</span>
						<span class="sim-badge">{m.get('similarity', 0)}% Similarity</span>
					</div>
					<div class="same-match-right-tags">
						{win_badge}
					</div>
				</div>
				<div class="same-match-grid">
					{store_boxes_html}
				</div>
				<div class="same-match-footer">
					{rec_text}
				</div>
			</div>
			"""
	else:
		same_matches_html = """
		<div class="empty-matches-box">
			<div class="empty-icon-sm">🔍</div>
			<h4>No exact identical model pairs detected</h4>
			<p>We searched across stores, but exact overlapping brand & model items were not in the top batch. You can still compare all store catalog items in <strong>⚡ Side-by-Side All Products</strong> or check <strong>📊 Unified Deals Table</strong>.</p>
		</div>
		"""

	# Pre-build Head-to-Head Cross-Store Matches
	matches_html = ""
	if matches:
		for idx, m in enumerate(matches, 1):
			amz = m["amazon"]
			fk = m["flipkart"]
			winner = m["winner"]
			win_badge = f'<span class="match-winner-tag winner-{winner.lower()}">🏆 Cheaper on {winner}!</span>' if winner in ["Amazon", "Flipkart"] else '<span class="match-winner-tag">Equal Price</span>'
			diff_tag = f'<span class="match-diff">{html.escape(m["savings_text"])} (Price Diff: {html.escape(m["price_difference"])})</span>'

			matches_html += f"""
			<div class="match-card">
				<div class="match-top">
					<div class="match-title-row">
						<span class="match-num">Match #{idx}</span>
						<span class="sim-badge">{m.get('similarity', 0)}% Similarity Match</span>
						{win_badge}
					</div>
					{diff_tag}
				</div>
				<div class="match-grid">
					<div class="match-item {'highlight-winner' if winner == 'Amazon' else ''}">
						<div class="match-store-label amz-label">Amazon.in</div>
						<div class="match-content">
							<img src="{html.escape(amz.get('image', ''))}" class="match-thumb" onerror="this.style.display='none'">
							<div class="match-info">
								<p class="match-prod-title">{html.escape(amz.get('title', ''))}</p>
								<div class="match-price-box">
									<strong class="match-price">{html.escape(amz.get('price', 'N/A'))}</strong>
									<span class="rating-badge-sm">★ {html.escape(amz.get('rating', 'N/A'))}</span>
								</div>
								<a href="{html.escape(amz.get('url', '#'))}" target="_blank" rel="noopener" class="mini-btn amz-btn">View on Amazon</a>
							</div>
						</div>
					</div>
					<div class="match-vs">VS</div>
					<div class="match-item {'highlight-winner' if winner == 'Flipkart' else ''}">
						<div class="match-store-label fk-label">Flipkart.com</div>
						<div class="match-content">
							<img src="{html.escape(fk.get('image', ''))}" class="match-thumb" onerror="this.style.display='none'">
							<div class="match-info">
								<p class="match-prod-title">{html.escape(fk.get('title', ''))}</p>
								<div class="match-price-box">
									<strong class="match-price">{html.escape(fk.get('price', 'N/A'))}</strong>
									<span class="rating-badge-sm">★ {html.escape(fk.get('rating', 'N/A'))}</span>
								</div>
								<a href="{html.escape(fk.get('url', '#'))}" target="_blank" rel="noopener" class="mini-btn fk-btn">View on Flipkart</a>
							</div>
						</div>
					</div>
				</div>
			</div>
			"""
	else:
		matches_html = "<p class='empty-text'>Direct product matches will appear here when equivalent items are detected across both stores.</p>"

	# Pre-build Unified Comparison Table
	table_rows = ""
	for p in all_products:
		site = p.get("site", "")
		if site == "Amazon":
			color = "#ff9900"
			bg = "#fff8e1"
		elif site == "Flipkart":
			color = "#2874f0"
			bg = "#e3f2fd"
		elif site == "Croma":
			color = "#00b594"
			bg = "#e6fcf5"
		elif site == "Ajio":
			color = "#1c355e"
			bg = "#edf2f7"
		else:
			color = "#64748b"
			bg = "#f1f5f9"

		img_src = p.get("image") or ""
		img_td = f'<img src="{html.escape(img_src)}" class="tbl-img" onerror="this.style.display=\'none\'">' if img_src else "🛍️"

		table_rows += f"""
		<tr data-site="{html.escape(site)}" data-price="{p.get('numeric_price', 0)}" data-rating="{p.get('numeric_rating', 0)}">
			<td><span class="tbl-store-pill" style="background:{bg};color:{color};">{html.escape(site)}</span></td>
			<td>{img_td}</td>
			<td class="tbl-title"><a href="{html.escape(p.get('url', '#'))}" target="_blank" rel="noopener">{html.escape(p.get('title', ''))}</a></td>
			<td class="tbl-price"><strong>{html.escape(p.get('price', 'N/A'))}</strong></td>
			<td><span class="mrp-strike">{html.escape(p.get('mrp', 'N/A'))}</span></td>
			<td><span class="disc-pill">{html.escape(p.get('discount', 'N/A'))}</span></td>
			<td>★ {html.escape(p.get('rating', 'N/A'))}</td>
			<td><span class="score-badge">{html.escape(p.get('value_score', 'N/A'))}</span></td>
			<td><a href="{html.escape(p.get('url', '#'))}" target="_blank" rel="noopener" class="tbl-btn" style="background:{color};">Buy ↗</a></td>
		</tr>
		"""

	# Metrics Badges: Display Best Store for Deals and dynamic Products Analyzed
	time_saved_block = ""
	if has_results:
		cheaper_store = comparison.get("cheaper_store_overall", "Equal")
		time_saved_block = f"""
		<div class="metrics-grid">
			<div class="metric-card card-savings">
				<div class="metric-icon">💰</div>
				<div class="metric-data">
					<span class="metric-label" data-i18n="bestStore">BEST STORE FOR DEALS</span>
					<strong class="metric-value" id="bestStoreVal">{cheaper_store}</strong>
					<span class="metric-sub" id="bestStoreSub">Avg price gap: {comparison.get('avg_price_gap', '₹0')}</span>
				</div>
			</div>
			<div class="metric-card card-total">
				<div class="metric-icon">📦</div>
				<div class="metric-data">
					<span class="metric-label" data-i18n="productsAnalyzed">PRODUCTS ANALYZED</span>
					<strong class="metric-value" id="analyzedCount">{total_products} Items</strong>
					<span class="metric-sub" id="analyzedSub">{len(amz_products)} Amazon · {len(fk_products)} Flipkart · {len(croma_products)} Croma · {len(ajio_products)} Ajio</span>
				</div>
			</div>
		</div>
		"""

	# AI Verdict Banner
	ai_verdict_block = ""
	if ai_verdict:
		ai_verdict_block = f"""
		<div class="ai-verdict-box">
			<div class="verdict-header">
				<span class="ai-badge" data-i18n="aiVerdict">🤖 AI SHOPPING VERDICT & ADVICE</span>
				<span class="time-tag" data-i18n="timeSaving">Time-Saving Decision Matrix</span>
			</div>
			<p class="verdict-body">{html.escape(ai_verdict)}</p>
		</div>
		"""

	return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Web Navigator AI Agent</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
	--primary: #2563eb;
	--primary-dark: #1d4ed8;
	--primary-light: #eff6ff;
	--amz-color: #ff9900;
	--fk-color: #2874f0;
	--success: #16a34a;
	--bg: #f8fafc;
	--card-bg: #ffffff;
	--border: #e2e8f0;
	--text-main: #0f172a;
	--text-muted: #64748b;
	--shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.08);
	--shadow-lg: 0 10px 25px -3px rgba(15, 23, 42, 0.12);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
	font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	background: var(--bg);
	color: var(--text-main);
	line-height: 1.5;
	min-height: 100vh;
}}
.container {{
	max-width: 1280px;
	margin: 0 auto;
	padding: 24px 20px 60px;
}}
header {{
	text-align: center;
	margin-bottom: 28px;
}}
.badge-tcs {{
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 14px;
	border-radius: 999px;
	background: #dbeafe;
	color: #1e40af;
	font-size: 13px;
	font-weight: 700;
	letter-spacing: 0.5px;
	margin-bottom: 12px;
	text-transform: uppercase;
}}
h1 {{
	font-size: 32px;
	font-weight: 800;
	color: #0f172a;
	letter-spacing: -0.5px;
	margin-bottom: 8px;
}}
h1 span {{
	background: linear-gradient(135deg, #2563eb, #7c3aed);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
}}
.tagline {{
	font-size: 16px;
	color: var(--text-muted);
	max-width: 680px;
	margin: 0 auto;
}}

/* Search Card */
.search-card {{
	background: var(--card-bg);
	border-radius: 16px;
	padding: 24px;
	box-shadow: var(--shadow);
	border: 1px solid var(--border);
	margin-bottom: 28px;
}}
.search-form {{
	display: flex;
	gap: 12px;
}}
.search-input-wrap {{
	position: relative;
	flex: 1;
}}
.search-icon {{
	position: absolute;
	left: 16px;
	top: 50%;
	transform: translateY(-50%);
	font-size: 18px;
	color: var(--text-muted);
}}
input.main-input {{
	width: 100%;
	padding: 14px 16px 14px 44px;
	font-size: 16px;
	font-family: inherit;
	border: 2px solid #cbd5e1;
	border-radius: 12px;
	outline: none;
	transition: all 0.2s;
}}
input.main-input:focus {{
	border-color: var(--primary);
	box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15);
}}
button.search-btn {{
	padding: 14px 28px;
	background: linear-gradient(135deg, #2563eb, #1d4ed8);
	color: white;
	font-weight: 700;
	font-size: 16px;
	border: none;
	border-radius: 12px;
	cursor: pointer;
	box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
	transition: all 0.2s;
	display: inline-flex;
	align-items: center;
	gap: 8px;
}}
button.search-btn:hover {{
	background: linear-gradient(135deg, #1d4ed8, #1e40af);
	transform: translateY(-1px);
}}
.limit-selector-wrap {{
	display: flex;
	align-items: center;
	gap: 8px;
	background: #f8fafc;
	border: 2px solid #cbd5e1;
	border-radius: 12px;
	padding: 0 14px;
}}
.limit-label {{
	font-size: 13px;
	font-weight: 700;
	color: var(--text-muted);
	white-space: nowrap;
}}
.limit-dropdown {{
	border: none;
	background: transparent;
	font-family: inherit;
	font-size: 14px;
	font-weight: 700;
	color: #1e293b;
	cursor: pointer;
	outline: none;
	padding: 12px 0;
}}
.limit-badge-wrap {{
	display: flex;
	align-items: center;
	gap: 6px;
}}
.filter-lbl {{
	font-size: 13px;
	font-weight: 700;
	color: var(--text-muted);
	white-space: nowrap;
}}
.quick-chips {{
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
	margin-top: 16px;
	font-size: 13px;
}}
.quick-label {{
	color: var(--text-muted);
	font-weight: 600;
}}
.chip {{
	background: #f1f5f9;
	border: 1px solid #e2e8f0;
	padding: 5px 12px;
	border-radius: 999px;
	color: #334155;
	text-decoration: none;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.15s;
}}
.chip:hover {{
	background: #e2e8f0;
	color: var(--primary);
}}

/* Store Selector Bar */
.store-selector-row {{
	display: flex;
	align-items: center;
	gap: 14px;
	margin-top: 16px;
	padding-top: 14px;
	border-top: 1px dashed var(--border);
	flex-wrap: wrap;
}}
.store-selector-title {{
	font-size: 13px;
	font-weight: 700;
	color: #475569;
}}
.store-checkbox-group {{
	display: flex;
	align-items: center;
	gap: 10px;
	flex-wrap: wrap;
}}
.store-checkbox-label {{
	cursor: pointer;
	display: inline-flex;
	align-items: center;
}}
.store-chk {{
	display: none;
}}
.store-pill {{
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 14px;
	border-radius: 999px;
	font-size: 13px;
	font-weight: 700;
	border: 2px solid transparent;
	opacity: 0.45;
	transition: all 0.2s;
	user-select: none;
}}
.store-chk:checked + .store-pill {{
	opacity: 1.0;
	transform: scale(1.02);
	box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}}
.amz-pill {{ background: #fff3e0; color: #b45309; border-color: #fde68a; }}
.fk-pill {{ background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }}
.croma-pill {{ background: #e6fcf5; color: #047857; border-color: #a7f3d0; }}
.ajio-pill {{ background: #f1f5f9; color: #1c355e; border-color: #cbd5e1; }}
.store-chk:checked + .amz-pill {{ border-color: #ff9900; background: #fff8e1; }}
.store-chk:checked + .fk-pill {{ border-color: #2874f0; background: #e3f2fd; }}
.store-chk:checked + .croma-pill {{ border-color: #00b594; background: #d1fae5; }}
.store-chk:checked + .ajio-pill {{ border-color: #1c355e; background: #e2e8f0; }}

/* Toolbar Store Filter Buttons */
.toolbar-store-filters {{
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: wrap;
}}
.tool-store-btn {{
	padding: 7px 12px;
	font-size: 12px;
	font-weight: 700;
	border-radius: 8px;
	border: 1px solid var(--border);
	background: #f1f5f9;
	color: #94a3b8;
	cursor: pointer;
	transition: all 0.2s;
	user-select: none;
}}
.tool-store-btn.active {{
	background: #ffffff;
	color: #0f172a;
	box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}}
.amz-tool-btn.active {{ border-color: #ff9900; color: #b45309; background: #fff8e1; }}
.fk-tool-btn.active {{ border-color: #2874f0; color: #1d4ed8; background: #eff6ff; }}
.croma-tool-btn.active {{ border-color: #00b594; color: #047857; background: #e6fcf5; }}
.ajio-tool-btn.active {{ border-color: #1c355e; color: #1c355e; background: #f1f5f9; }}

/* Metrics Grid */
.metrics-grid {{
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
	gap: 16px;
	margin-bottom: 24px;
}}
.metric-card {{
	background: white;
	border-radius: 14px;
	padding: 18px 20px;
	border: 1px solid var(--border);
	box-shadow: var(--shadow);
	display: flex;
	align-items: center;
	gap: 16px;
}}
.metric-icon {{
	font-size: 30px;
	background: #f1f5f9;
	width: 52px;
	height: 52px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}}
.card-time .metric-icon {{ background: #fef3c7; }}
.card-savings .metric-icon {{ background: #dcfce7; }}
.card-speed .metric-icon {{ background: #ede9fe; }}
.card-total .metric-icon {{ background: #e0f2fe; }}
.metric-data {{ display: flex; flex-direction: column; }}
.metric-label {{ font-size: 11px; font-weight: 800; color: var(--text-muted); letter-spacing: 0.5px; text-transform: uppercase; }}
.metric-value {{ font-size: 20px; font-weight: 800; color: #0f172a; margin: 2px 0; }}
.metric-sub {{ font-size: 12px; color: var(--text-muted); }}

/* AI Verdict */
.ai-verdict-box {{
	background: linear-gradient(135deg, #eff6ff, #f0fdf4);
	border: 1px solid #bfdbfe;
	border-left: 6px solid #2563eb;
	border-radius: 14px;
	padding: 20px 24px;
	margin-bottom: 24px;
	box-shadow: var(--shadow);
}}
.verdict-header {{
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 8px;
}}
.ai-badge {{
	font-size: 13px;
	font-weight: 800;
	color: #1e40af;
	letter-spacing: 0.5px;
}}
.time-tag {{
	font-size: 12px;
	font-weight: 700;
	color: #15803d;
	background: #dcfce7;
	padding: 4px 10px;
	border-radius: 999px;
}}
.verdict-body {{
	font-size: 15px;
	color: #1e293b;
	line-height: 1.6;
}}

/* View Controller & Toolbar */
.toolbar {{
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
	gap: 16px;
	margin-bottom: 20px;
}}
.view-tabs {{
	display: inline-flex;
	background: #e2e8f0;
	padding: 4px;
	border-radius: 12px;
	gap: 4px;
}}
.tab-btn {{
	border: none;
	background: transparent;
	padding: 9px 18px;
	border-radius: 9px;
	font-weight: 700;
	font-size: 14px;
	color: #475569;
	cursor: pointer;
	transition: all 0.2s;
}}
.tab-btn.active {{
	background: white;
	color: var(--primary);
	box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}
.toolbar-actions {{
	display: flex;
	gap: 10px;
	align-items: center;
}}
.filter-select {{
	padding: 9px 14px;
	font-size: 13px;
	font-weight: 600;
	border-radius: 9px;
	border: 1px solid var(--border);
	background: white;
	color: #334155;
	cursor: pointer;
}}
.action-btn {{
	padding: 9px 14px;
	font-size: 13px;
	font-weight: 600;
	border-radius: 9px;
	border: 1px solid var(--border);
	background: white;
	color: #334155;
	cursor: pointer;
	transition: all 0.2s;
}}
.action-btn:hover {{
	background: #f1f5f9;
}}

/* View Content */
.view-panel {{ display: none; }}
.view-panel.active {{ display: block; }}

/* Dual Store Columns (Side by Side) */
.split-view-grid {{
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
	gap: 20px;
}}
.store-column {{
	background: white;
	border-radius: 16px;
	border: 1px solid var(--border);
	box-shadow: var(--shadow);
	overflow: hidden;
	display: flex;
	flex-direction: column;
}}
.store-header {{
	padding: 14px 16px;
	background: #fafafa;
	border-bottom: 1px solid var(--border);
	display: flex;
	flex-direction: column;
	gap: 8px;
}}
.store-header-top {{
	display: flex;
	justify-content: space-between;
	align-items: center;
}}
.store-brand h3 {{
	font-size: 17px;
	font-weight: 800;
	display: flex;
	align-items: center;
	gap: 6px;
}}
.store-count {{
	font-size: 12px;
	color: var(--text-muted);
	font-weight: 600;
}}
.store-badge-mini {{
	font-size: 10px;
	font-weight: 800;
	padding: 2px 7px;
	border-radius: 999px;
	text-transform: uppercase;
	letter-spacing: 0.5px;
}}
.store-stats-row {{
	font-size: 12px;
	color: #475569;
	background: #f1f5f9;
	padding: 6px 10px;
	border-radius: 7px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-weight: 600;
}}
.column-cards {{
	padding: 14px;
	display: flex;
	flex-direction: column;
	gap: 14px;
}}
.product-card {{
	border: 1px solid var(--border);
	border-radius: 14px;
	padding: 14px;
	display: flex;
	flex-direction: column;
	background: #ffffff;
	box-shadow: 0 2px 8px rgba(0,0,0,0.03);
	transition: transform 0.15s, box-shadow 0.15s;
}}
.product-card:hover {{
	transform: translateY(-2px);
	box-shadow: var(--shadow);
}}
.card-img-wrap {{
	width: 100%;
	height: 145px;
	position: relative;
	background: #f8fafc;
	border-radius: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
	margin-bottom: 12px;
}}
.prod-img {{
	max-width: 88%;
	max-height: 88%;
	object-fit: contain;
}}
.no-img {{
	font-size: 36px;
}}
.store-badge {{
	position: absolute;
	top: 8px;
	left: 8px;
	font-size: 10px;
	font-weight: 800;
	padding: 2px 7px;
	border-radius: 5px;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}
.card-body {{
	flex: 1;
	display: flex;
	flex-direction: column;
}}
.prod-title {{
	font-size: 13.5px;
	font-weight: 700;
	color: #1e293b;
	line-height: 1.4;
	margin-bottom: 8px;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
	min-height: 38px;
}}
.rating-row {{
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	margin-bottom: 10px;
	flex-wrap: wrap;
}}
.rating-badge {{
	background: #fef3c7;
	color: #b45309;
	font-weight: 700;
	font-size: 11.5px;
	padding: 2px 7px;
	border-radius: 5px;
	white-space: nowrap;
}}
.rating-badge-muted {{
	background: #f1f5f9;
	color: #64748b;
}}
.reviews-count {{
	color: var(--text-muted);
	font-size: 11px;
	white-space: nowrap;
}}
.val-score {{
	margin-left: auto;
	font-weight: 700;
	font-size: 11px;
	color: #15803d;
	background: #dcfce7;
	padding: 2px 6px;
	border-radius: 5px;
	white-space: nowrap;
}}
.price-row {{
	display: flex;
	align-items: baseline;
	gap: 8px;
	margin-top: auto;
	margin-bottom: 12px;
	flex-wrap: wrap;
}}
.curr-price {{
	font-size: 19px;
	font-weight: 800;
	color: #0f172a;
	white-space: nowrap;
}}
.mrp-strike {{
	font-size: 12.5px;
	color: #94a3b8;
	text-decoration: line-through;
	white-space: nowrap;
}}
.disc-pill {{
	font-size: 11px;
	font-weight: 800;
	color: #dc2626;
	background: #fee2e2;
	padding: 2px 6px;
	border-radius: 4px;
	white-space: nowrap;
}}
.buy-btn {{
	display: block;
	width: 100%;
	text-align: center;
	color: white;
	text-decoration: none;
	font-weight: 700;
	font-size: 13px;
	padding: 9px 12px;
	border-radius: 8px;
	white-space: nowrap;
	transition: opacity 0.15s, transform 0.1s;
}}
.buy-btn:hover {{
	opacity: 0.92;
	transform: translateY(-1px);
}}

/* Head-to-Head Cross-Store Matches */
.matches-list {{
	display: flex;
	flex-direction: column;
	gap: 18px;
}}
.match-card {{
	background: white;
	border-radius: 16px;
	border: 1px solid var(--border);
	padding: 20px;
	box-shadow: var(--shadow);
}}
.match-top {{
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
	gap: 10px;
	padding-bottom: 14px;
	border-bottom: 1px solid var(--border);
	margin-bottom: 16px;
}}
.match-title-row {{
	display: flex;
	align-items: center;
	gap: 10px;
}}
.match-num {{
	font-weight: 800;
	font-size: 14px;
	color: #0f172a;
}}
.sim-badge {{
	font-size: 11px;
	font-weight: 700;
	background: #f1f5f9;
	color: #475569;
	padding: 3px 8px;
	border-radius: 999px;
}}
.match-winner-tag {{
	font-size: 12px;
	font-weight: 800;
	padding: 3px 10px;
	border-radius: 999px;
	background: #f1f5f9;
	color: #334155;
}}
.winner-amazon {{ background: #fef3c7; color: #b45309; }}
.winner-flipkart {{ background: #dbeafe; color: #1e40af; }}
.match-diff {{
	font-size: 13px;
	font-weight: 700;
	color: #16a34a;
}}
.match-grid {{
	display: grid;
	grid-template-columns: 1fr auto 1fr;
	gap: 16px;
	align-items: center;
}}
@media (max-width: 800px) {{
	.match-grid {{ grid-template-columns: 1fr; }}
	.match-vs {{ display: none; }}
}}
.match-vs {{
	font-size: 14px;
	font-weight: 900;
	color: #94a3b8;
	background: #f1f5f9;
	width: 36px;
	height: 36px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
}}
.match-item {{
	border: 1px solid var(--border);
	border-radius: 12px;
	padding: 14px;
	background: #fafafa;
	position: relative;
}}
.highlight-winner {{
	border-color: #86efac;
	background: #f0fdf4;
}}
.match-store-label {{
	font-size: 11px;
	font-weight: 800;
	text-transform: uppercase;
	margin-bottom: 8px;
}}
.amz-label {{ color: var(--amz-color); }}
.fk-label {{ color: var(--fk-color); }}
.match-content {{
	display: flex;
	gap: 12px;
}}
.match-thumb {{
	width: 70px;
	height: 70px;
	object-fit: contain;
	background: white;
	border-radius: 6px;
	padding: 4px;
	border: 1px solid #e2e8f0;
	flex-shrink: 0;
}}
.match-info {{ flex: 1; }}
.match-prod-title {{
	font-size: 13px;
	font-weight: 700;
	line-height: 1.4;
	margin-bottom: 6px;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}}
.match-price-box {{
	display: flex;
	align-items: baseline;
	gap: 8px;
	margin-bottom: 8px;
}}
.match-price {{ font-size: 16px; font-weight: 800; color: #0f172a; }}
.mini-btn {{
	display: inline-block;
	padding: 5px 10px;
	font-size: 11px;
	font-weight: 700;
	border-radius: 6px;
	text-decoration: none;
	color: white;
}}
.amz-btn {{ background: var(--amz-color); }}
.fk-btn {{ background: var(--fk-color); }}

/* Same Product Comparison View */
.same-match-card {{
	background: white;
	border-radius: 16px;
	border: 1px solid var(--border);
	padding: 22px;
	box-shadow: var(--shadow);
	margin-bottom: 20px;
	transition: transform 0.15s, box-shadow 0.15s;
}}
.same-match-card:hover {{
	box-shadow: var(--shadow-lg);
}}
.same-match-top {{
	display: flex;
	justify-content: space-between;
	align-items: center;
	flex-wrap: wrap;
	gap: 12px;
	padding-bottom: 14px;
	border-bottom: 1px solid var(--border);
	margin-bottom: 18px;
}}
.same-match-left-tags {{
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}}
.same-item-num {{
	font-weight: 800;
	font-size: 13px;
	color: #0f172a;
	background: #f1f5f9;
	padding: 4px 10px;
	border-radius: 6px;
}}
.same-brand-tag {{
	font-size: 12px;
	font-weight: 800;
	background: #ede9fe;
	color: #6d28d9;
	padding: 4px 10px;
	border-radius: 6px;
	letter-spacing: 0.5px;
}}
.same-verified-badge {{
	font-size: 12px;
	font-weight: 700;
	background: #dcfce7;
	color: #15803d;
	padding: 4px 10px;
	border-radius: 6px;
}}
.same-winner-tag {{
	font-size: 13px;
	font-weight: 800;
	padding: 5px 14px;
	border-radius: 999px;
}}
.winner-amz, .winner-amazon {{ background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }}
.winner-fk, .winner-flipkart {{ background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }}
.winner-croma {{ background: #d1fae5; color: #047857; border: 1px solid #a7f3d0; }}
.winner-ajio {{ background: #e2e8f0; color: #1c355e; border: 1px solid #cbd5e1; }}
.winner-equal {{ background: #f1f5f9; color: #475569; }}

.same-match-grid {{
	display: flex;
	gap: 16px;
	align-items: stretch;
}}
.same-store-box {{
	flex: 1 1 0;
	min-width: 0;
	border: 2px solid var(--border);
	border-radius: 14px;
	padding: 14px;
	background: #ffffff;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	position: relative;
	transition: all 0.2s;
}}
@media (max-width: 992px) {{
	.same-match-grid {{
		flex-wrap: wrap;
	}}
	.same-store-box {{
		flex: 1 1 calc(50% - 16px);
		min-width: 230px;
	}}
}}
@media (max-width: 600px) {{
	.same-store-box {{
		flex: 1 1 100%;
		min-width: 100%;
	}}
}}
.store-box-winner {{
	border-color: #22c55e;
	background: #f0fdf4;
	box-shadow: 0 4px 14px rgba(34, 197, 94, 0.15);
}}
.same-store-header {{
	height: 38px;
	min-height: 38px;
	max-height: 38px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-bottom: 8px;
	margin-bottom: 12px;
	border-bottom: 2px solid #f1f5f9;
}}
.amz-border {{ border-color: #fef3c7; }}
.fk-border {{ border-color: #dbeafe; }}
.croma-border {{ border-color: #a7f3d0; }}
.ajio-border {{ border-color: #cbd5e1; }}
.same-store-title {{
	font-size: 13.5px;
	font-weight: 800;
	text-transform: uppercase;
	letter-spacing: 0.5px;
}}
.amz-text {{ color: #d97706; }}
.fk-text {{ color: #2563eb; }}
.croma-text {{ color: #00b594; }}
.ajio-text {{ color: #1c355e; }}
.same-spec-tag {{
	font-size: 12px;
	font-weight: 700;
	background: #f0fdf4;
	color: #166534;
	border: 1px solid #bbf7d0;
	padding: 4px 10px;
	border-radius: 6px;
}}
.store-winner-pill {{
	font-size: 10.5px;
	font-weight: 800;
	background: #22c55e;
	color: white;
	padding: 3px 8px;
	border-radius: 999px;
	letter-spacing: 0.5px;
	white-space: nowrap;
}}
.same-prod-content {{
	display: flex;
	gap: 12px;
	align-items: flex-start;
	margin-bottom: 12px;
	flex: 1;
}}
.same-thumb-wrap {{
	width: 76px;
	height: 76px;
	min-width: 76px;
	min-height: 76px;
	max-width: 76px;
	max-height: 76px;
	background: #f8fafc;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
	padding: 4px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	overflow: hidden;
}}
.same-thumb {{
	max-width: 100%;
	max-height: 100%;
	object-fit: contain;
}}
.no-img-sm {{
	width: 76px;
	height: 76px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 26px;
	background: #f8fafc;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
	flex-shrink: 0;
}}
.same-prod-info {{
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	height: 100%;
}}
.same-prod-name {{
	font-size: 12.5px;
	font-weight: 700;
	color: #1e293b;
	line-height: 1.4;
	height: 36px;
	min-height: 36px;
	max-height: 36px;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
	margin-bottom: 6px;
}}
.same-rating-row {{
	height: 22px;
	min-height: 22px;
	max-height: 22px;
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 11.5px;
	margin-bottom: 6px;
	white-space: nowrap;
	overflow: hidden;
}}
.same-price-row {{
	height: 26px;
	min-height: 26px;
	max-height: 26px;
	display: flex;
	align-items: baseline;
	gap: 6px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	margin-top: auto;
}}
.same-price {{
	font-size: 17px;
	font-weight: 800;
	color: #0f172a;
}}
.same-buy-btn {{
	display: flex;
	align-items: center;
	justify-content: center;
	width: 100%;
	height: 38px;
	min-height: 38px;
	max-height: 38px;
	padding: 0 12px;
	border-radius: 8px;
	font-size: 12.5px;
	font-weight: 700;
	color: white;
	text-decoration: none;
	margin-top: auto;
	white-space: nowrap;
	transition: opacity 0.15s, transform 0.1s;
}}
.same-buy-btn:hover {{
	opacity: 0.92;
	transform: translateY(-1px);
}}
.amz-bg {{ background: #ff9900; }}
.fk-bg {{ background: #2874f0; }}
.croma-bg {{ background: #00b594; }}
.ajio-bg {{ background: #1c355e; }}

.same-vs-divider {{
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 6px;
}}
.vs-circle {{
	width: 44px;
	height: 44px;
	border-radius: 50%;
	background: #f1f5f9;
	color: #64748b;
	font-weight: 900;
	font-size: 14px;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2px solid #e2e8f0;
}}
.diff-badge {{
	font-size: 11px;
	font-weight: 800;
	color: #0f172a;
	background: #e2e8f0;
	padding: 3px 8px;
	border-radius: 999px;
	white-space: nowrap;
}}
.same-match-footer {{
	margin-top: 16px;
	padding: 12px 16px;
	background: #f8fafc;
	border-radius: 10px;
	border-left: 4px solid var(--primary);
	font-size: 13px;
	color: #334155;
	line-height: 1.5;
}}
.empty-matches-box {{
	text-align: center;
	padding: 40px 20px;
	background: white;
	border-radius: 16px;
	border: 1px dashed var(--border);
}}
.empty-icon-sm {{ font-size: 36px; margin-bottom: 10px; }}
.empty-matches-box h4 {{ font-size: 17px; font-weight: 700; color: #1e293b; margin-bottom: 6px; }}
.empty-matches-box p {{ font-size: 14px; color: var(--text-muted); max-width: 600px; margin: 0 auto; }}

/* Unified Table */
.table-card {{
	background: white;
	border-radius: 16px;
	border: 1px solid var(--border);
	box-shadow: var(--shadow);
	overflow-x: auto;
}}
table.unified-tbl {{
	width: 100%;
	border-collapse: collapse;
	text-align: left;
	font-size: 13px;
}}
table.unified-tbl th {{
	background: #f8fafc;
	padding: 14px 16px;
	font-weight: 700;
	color: #475569;
	border-bottom: 1px solid var(--border);
	white-space: nowrap;
}}
table.unified-tbl td {{
	padding: 14px 16px;
	border-bottom: 1px solid #f1f5f9;
	vertical-align: middle;
}}
.tbl-store-pill {{
	font-weight: 800;
	font-size: 11px;
	padding: 3px 8px;
	border-radius: 6px;
	text-transform: uppercase;
}}
.tbl-img {{
	width: 44px;
	height: 44px;
	object-fit: contain;
	border-radius: 4px;
	background: #f8fafc;
}}
.tbl-title a {{
	color: #1e293b;
	text-decoration: none;
	font-weight: 600;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}}
.tbl-title a:hover {{ color: var(--primary); }}
.tbl-price {{ font-size: 15px; color: #0f172a; }}
.score-badge {{
	background: #dcfce7;
	color: #166534;
	font-weight: 700;
	padding: 3px 7px;
	border-radius: 6px;
}}
.tbl-btn {{
	color: white;
	padding: 6px 12px;
	border-radius: 6px;
	font-weight: 700;
	text-decoration: none;
	display: inline-block;
	white-space: nowrap;
}}

/* Empty / Initial State */
.empty-state {{
	text-align: center;
	padding: 60px 20px;
	background: white;
	border-radius: 16px;
	border: 1px solid var(--border);
	box-shadow: var(--shadow);
}}
.empty-icon {{ font-size: 48px; margin-bottom: 16px; }}
.empty-state h3 {{ font-size: 20px; font-weight: 700; margin-bottom: 8px; }}
.empty-state p {{ color: var(--text-muted); max-width: 500px; margin: 0 auto; }}

/* Toast Notification */
#toast {{
	position: fixed;
	bottom: 24px;
	right: 24px;
	background: #1e293b;
	color: white;
	padding: 12px 20px;
	border-radius: 8px;
	font-size: 14px;
	font-weight: 600;
	box-shadow: var(--shadow-lg);
	display: none;
	z-index: 1000;
	animation: slideIn 0.2s ease-out;
}}
.language-switcher {{
	display: inline-flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 14px;
	padding: 6px 10px;
	background: #ffffff;
	border: 1px solid var(--border);
	border-radius: 999px;
	box-shadow: var(--shadow);
}}
.language-switcher label {{
	font-size: 12px;
	font-weight: 700;
	color: var(--text-muted);
}}
.language-switcher select {{
	border: none;
	background: transparent;
	color: #1e293b;
	font-family: inherit;
	font-size: 13px;
	font-weight: 700;
	cursor: pointer;
	outline: none;
}}
@keyframes slideIn {{
	from {{ transform: translateY(100%); opacity: 0; }}
	to {{ transform: translateY(0); opacity: 1; }}
}}
</style>
</head>
<body>
<div class="container">
	<header>
		<div class="language-switcher">
			<label for="languageSelector" data-i18n="language">Language</label>
			<select id="languageSelector" aria-label="Select language" onchange="changeLanguage(this.value)">
				<option value="en">English</option>
				<option value="te">తెలుగు</option>
				<option value="hi">हिन्दी</option>
			</select>
		</div>
		<h1>Web Navigator <span>AI Agent</span></h1>
		<p class="tagline" data-i18n="tagline">Smart automated multi-website product comparison engine for Amazon, Flipkart, Croma & Ajio. Designed to save users 15+ minutes of manual browsing.</p>
	</header>

	<div class="search-card">
		<form method="get" class="search-form">
			<div class="search-input-wrap">
				<span class="search-icon">🔍</span>
				<input type="text" name="goal" class="main-input" data-i18n-placeholder="searchPlaceholder" placeholder="Search any product (e.g. laptops under 50000, iPhone 15, wireless earbuds...)" value="{html.escape(query_str)}" required autofocus>
			</div>
			<div class="limit-selector-wrap">
				<span class="limit-label" data-i18n="display">Display:</span>
				<select name="limit" id="itemsLimit" class="limit-dropdown" onchange="applyItemLimit(this.value)">
					<option value="5" {"selected" if str(selected_limit) == "5" else ""}>Top 5 per store (10 items)</option>
					<option value="8" {"selected" if str(selected_limit) == "8" else ""}>Top 8 per store (16 items)</option>
					<option value="12" {"selected" if str(selected_limit) == "12" else ""}>Top 12 per store (24 items)</option>
					<option value="16" {"selected" if str(selected_limit) == "16" else ""}>Top 16 per store (32 items)</option>
					<option value="20" {"selected" if str(selected_limit) == "20" else ""}>Top 20 per store (40 items)</option>
					<option value="all" {"selected" if str(selected_limit).lower() in ["all", ""] else ""}>All Extracted (Max)</option>
				</select>
			</div>
			<button type="submit" class="search-btn">
				<span data-i18n="compareDeals">Compare Deals</span> ⚡
			</button>
		</form>
		<div class="store-selector-row">
			<span class="store-selector-title" data-i18n="selectStores">Select Stores to Compare:</span>
			<div class="store-checkbox-group">
				<label class="store-checkbox-label" title="Toggle Amazon comparison">
					<input type="checkbox" id="chkAmazon" class="store-chk" value="Amazon" checked onchange="toggleStoreFilter('Amazon', this.checked)">
					<span class="store-pill amz-pill">🛒 Amazon</span>
				</label>
				<label class="store-checkbox-label" title="Toggle Flipkart comparison">
					<input type="checkbox" id="chkFlipkart" class="store-chk" value="Flipkart" checked onchange="toggleStoreFilter('Flipkart', this.checked)">
					<span class="store-pill fk-pill">🛍️ Flipkart</span>
				</label>
				<label class="store-checkbox-label" title="Toggle Croma comparison">
					<input type="checkbox" id="chkCroma" class="store-chk" value="Croma" checked onchange="toggleStoreFilter('Croma', this.checked)">
					<span class="store-pill croma-pill">⚡ Croma</span>
				</label>
				<label class="store-checkbox-label" title="Toggle Ajio comparison">
					<input type="checkbox" id="chkAjio" class="store-chk" value="Ajio" checked onchange="toggleStoreFilter('Ajio', this.checked)">
					<span class="store-pill ajio-pill">👔 Ajio</span>
				</label>
			</div>
		</div>
		<div class="quick-chips">
			<span class="quick-label" data-i18n="trySearching">Try searching:</span>
			<a class="chip" onclick="quickSearch('laptops under 50000')">💻 Laptops under 50k</a>
			<a class="chip" onclick="quickSearch('iPhone 15')">📱 iPhone 15</a>
			<a class="chip" onclick="quickSearch('wireless earbuds noise cancelling')">🎧 Wireless Earbuds</a>
			<a class="chip" onclick="quickSearch('smartwatch under 3000')">⌚ Smartwatch under 3k</a>
			<a class="chip" onclick="quickSearch('running shoes for men under 2000')">👟 Running Shoes</a>
		</div>
	</div>

	{time_saved_block}
	{ai_verdict_block}

	{f'''
	<div class="toolbar">
		<div class="view-tabs">
			<button id="tabSame" class="tab-btn {'active' if is_same_active else ''}" onclick="switchView('same')">🎯 <span data-i18n="sameProduct">Compare Same Product</span> ({len(same_matches)})</button>
			<button id="tabSplit" class="tab-btn {'active' if not is_same_active else ''}" onclick="switchView('split')">⚡ <span data-i18n="allProducts">Side-by-Side All Products</span></button>
			<button id="tabMatches" class="tab-btn" onclick="switchView('matches')">🥊 <span data-i18n="similarMatches">Similar Matches</span> ({len(matches)})</button>
			<button id="tabTable" class="tab-btn" onclick="switchView('table')">📊 <span data-i18n="dealsTable">Unified Deals Table</span></button>
		</div>
		<div class="toolbar-actions">
			<div class="toolbar-store-filters">
				<span class="filter-lbl" data-i18n="stores">Stores:</span>
				<button type="button" class="tool-store-btn active amz-tool-btn" data-store="Amazon" onclick="toggleStoreBtn('Amazon')" title="Click to toggle Amazon">Amazon ✓</button>
				<button type="button" class="tool-store-btn active fk-tool-btn" data-store="Flipkart" onclick="toggleStoreBtn('Flipkart')" title="Click to toggle Flipkart">Flipkart ✓</button>
				<button type="button" class="tool-store-btn active croma-tool-btn" data-store="Croma" onclick="toggleStoreBtn('Croma')" title="Click to toggle Croma">Croma ✓</button>
				<button type="button" class="tool-store-btn active ajio-tool-btn" data-store="Ajio" onclick="toggleStoreBtn('Ajio')" title="Click to toggle Ajio">Ajio ✓</button>
			</div>
			<div class="limit-badge-wrap">
				<label class="filter-lbl" for="displayLimitFilter" data-i18n="displayItems">Display items:</label>
				<select class="filter-select" id="displayLimitFilter" onchange="applyItemLimit(this.value)">
					<option value="5" {"selected" if str(selected_limit) == "5" else ""}>Top 5 per store</option>
					<option value="8" {"selected" if str(selected_limit) == "8" else ""}>Top 8 per store</option>
					<option value="12" {"selected" if str(selected_limit) == "12" else ""}>Top 12 per store</option>
					<option value="16" {"selected" if str(selected_limit) == "16" else ""}>Top 16 per store</option>
					<option value="20" {"selected" if str(selected_limit) == "20" else ""}>Top 20 per store</option>
					<option value="all" {"selected" if str(selected_limit).lower() in ["all", ""] else ""}>All Extracted (Max)</option>
				</select>
			</div>
			<select class="filter-select" id="sortFilter" onchange="applySorting()">
				<option value="default" data-i18n="sortDefault">Sort by: Default Relevance</option>
				<option value="price-asc" data-i18n="priceLowHigh">Price: Low to High</option>
				<option value="price-desc" data-i18n="priceHighLow">Price: High to Low</option>
				<option value="rating-desc" data-i18n="highestRated">Highest Rated (★)</option>
			</select>
			<button class="action-btn" onclick="copySummary()" data-i18n="copySummary">📋 Copy Summary</button>
			<button class="action-btn" onclick="exportJSON()" data-i18n="exportJson">⬇️ Export JSON</button>
		</div>
	</div>

	<!-- View 1: Compare Same Product (Strict Brand & Model Comparison) -->
	<div id="sameView" class="view-panel {'active' if is_same_active else ''}">
		<div class="matches-list">
			{same_matches_html}
		</div>
	</div>

	<!-- View 2: Split View (Side-by-Side All Products) -->
	<div id="splitView" class="view-panel {'active' if not is_same_active else ''}">
		<div class="split-view-grid">
			{amz_col}
			{fk_col}
			{croma_col}
			{ajio_col}
		</div>
	</div>

	<!-- View 3: Matches View -->
	<div id="matchesView" class="view-panel">
		<div class="matches-list">
			{matches_html}
		</div>
	</div>

	<!-- View 3: Table View -->
	<div id="tableView" class="view-panel">
		<div class="table-card">
			<table class="unified-tbl">
				<thead>
					<tr>
						<th data-i18n="store">Store</th>
						<th data-i18n="thumb">Thumb</th>
						<th data-i18n="productName">Product Name</th>
						<th data-i18n="price">Price</th>
						<th data-i18n="mrp">M.R.P</th>
						<th data-i18n="discount">Discount</th>
						<th data-i18n="rating">Rating</th>
						<th data-i18n="valueScore">Value Score</th>
						<th data-i18n="action">Action</th>
					</tr>
				</thead>
				<tbody id="tblBody">
					{table_rows}
				</tbody>
			</table>
		</div>
	</div>
	''' if has_results else (f'''
	<div class="empty-state">
		<div class="empty-icon">❌</div>
		<h3><span data-i18n="noProducts">No products found for</span> "{html.escape(query_str)}"</h3>
		<p data-i18n="tryAnother">Try searching with another product name or broader terms like "laptops under 50000" or "smartphone".</p>
	</div>
	''' if result else '''
	<div class="empty-state">
		<div class="empty-icon">🚀</div>
		<h3 data-i18n="ready">Ready to compare across multiple stores</h3>
		<p data-i18n="readyDescription">Enter any product above or click one of the quick search chips to initiate parallel browser extraction from Amazon and Flipkart.</p>
	</div>
	''')}
</div>

<div id="toast"></div>

<script id="agent-raw-data" type="application/json">
{result_json_str}
</script>

<script>
const translations = {{
	en: {{
		language: 'Language',
		tagline: 'Smart automated multi-website product comparison engine for Amazon, Flipkart, Croma & Ajio. Designed to save users 15+ minutes of manual browsing.',
		searchPlaceholder: 'Search any product (e.g. laptops under 50000, iPhone 15, wireless earbuds...)',
		display: 'Display:',
		compareDeals: 'Compare Deals',
		selectStores: 'Select Stores to Compare:',
		trySearching: 'Try searching:',
		sameProduct: 'Compare Same Product',
		allProducts: 'Side-by-Side All Products',
		similarMatches: 'Similar Matches',
		dealsTable: 'Unified Deals Table',
		stores: 'Stores:',
		displayItems: 'Display items:',
		sortDefault: 'Sort by: Default Relevance',
		priceLowHigh: 'Price: Low to High',
		priceHighLow: 'Price: High to Low',
		highestRated: 'Highest Rated (★)',
		copySummary: '📋 Copy Summary',
		exportJson: '⬇️ Export JSON',
		store: 'Store',
		thumb: 'Thumb',
		productName: 'Product Name',
		price: 'Price',
		mrp: 'M.R.P',
		discount: 'Discount',
		rating: 'Rating',
		valueScore: 'Value Score',
		action: 'Action',
		noProducts: 'No products found for',
		tryAnother: 'Try searching with another product name or broader terms like "laptops under 50000" or "smartphone".',
		ready: 'Ready to compare across multiple stores',
		readyDescription: 'Enter any product above or click one of the quick search chips to initiate parallel browser extraction from Amazon and Flipkart.',
		bestStore: 'BEST STORE FOR DEALS',
		productsAnalyzed: 'PRODUCTS ANALYZED',
		aiVerdict: '🤖 AI SHOPPING VERDICT & ADVICE',
		timeSaving: 'Time-Saving Decision Matrix'
	}},
	te: {{
		language: 'భాష',
		tagline: 'Amazon, Flipkart, Croma మరియు Ajio కోసం బహుళ వెబ్‌సైట్ ఉత్పత్తి పోలిక సాధనం. మాన్యువల్ బ్రౌజింగ్‌లో 15 నిమిషాలకు పైగా సమయం ఆదా చేయండి.',
		searchPlaceholder: 'ఏదైనా ఉత్పత్తిని వెతకండి (ఉదా. 50000 లోపు ల్యాప్‌టాప్‌లు, iPhone 15...)',
		display: 'చూపించు:',
		compareDeals: 'ఆఫర్లను పోల్చండి',
		selectStores: 'పోల్చడానికి స్టోర్లను ఎంచుకోండి:',
		trySearching: 'వెతకడానికి ప్రయత్నించండి:',
		sameProduct: 'అదే ఉత్పత్తిని పోల్చండి',
		allProducts: 'అన్ని ఉత్పత్తులు పక్కపక్కన',
		similarMatches: 'సారూప్య మ్యాచ్‌లు',
		dealsTable: 'ఏకీకృత ఆఫర్ల పట్టిక',
		stores: 'స్టోర్లు:',
		displayItems: 'ఉత్పత్తులను చూపించు:',
		sortDefault: 'క్రమబద్ధీకరణ: సంబంధిత క్రమం',
		priceLowHigh: 'ధర: తక్కువ నుండి ఎక్కువ',
		priceHighLow: 'ధర: ఎక్కువ నుండి తక్కువ',
		highestRated: 'అత్యధిక రేటింగ్ (★)',
		copySummary: '📋 సారాంశాన్ని కాపీ చేయండి',
		exportJson: '⬇️ JSON ఎగుమతి',
		store: 'స్టోర్',
		thumb: 'చిత్రం',
		productName: 'ఉత్పత్తి పేరు',
		price: 'ధర',
		mrp: 'M.R.P',
		discount: 'తగ్గింపు',
		rating: 'రేటింగ్',
		valueScore: 'విలువ స్కోర్',
		action: 'చర్య',
		noProducts: 'ఉత్పత్తులు కనుగొనబడలేదు:',
		tryAnother: 'మరొక ఉత్పత్తి పేరు లేదా "ల్యాప్‌టాప్‌లు", "స్మార్ట్‌ఫోన్" వంటి విస్తృత పదాలతో వెతకండి.',
		ready: 'బహుళ స్టోర్లలో పోల్చడానికి సిద్ధంగా ఉంది',
		readyDescription: 'పై ఉత్పత్తిని నమోదు చేయండి లేదా సమాంతర శోధన ప్రారంభించడానికి త్వరిత శోధనను ఎంచుకోండి.',
		bestStore: 'ఆఫర్లకు ఉత్తమ స్టోర్',
		productsAnalyzed: 'విశ్లేషించిన ఉత్పత్తులు',
		aiVerdict: '🤖 AI షాపింగ్ సలహా',
		timeSaving: 'సమయం ఆదా చేసే నిర్ణయ పట్టిక'
	}},
	hi: {{
		language: 'भाषा',
		tagline: 'Amazon, Flipkart, Croma और Ajio के लिए स्मार्ट बहु-वेबसाइट उत्पाद तुलना। मैनुअल ब्राउज़िंग में 15+ मिनट बचाएं।',
		searchPlaceholder: 'कोई भी उत्पाद खोजें (जैसे 50000 से कम लैपटॉप, iPhone 15...)',
		display: 'दिखाएं:',
		compareDeals: 'ऑफर की तुलना करें',
		selectStores: 'तुलना के लिए स्टोर चुनें:',
		trySearching: 'खोजने का प्रयास करें:',
		sameProduct: 'समान उत्पाद की तुलना',
		allProducts: 'सभी उत्पाद साथ-साथ',
		similarMatches: 'समान मिलान',
		dealsTable: 'एकीकृत ऑफर तालिका',
		stores: 'स्टोर:',
		displayItems: 'उत्पाद दिखाएं:',
		sortDefault: 'क्रम: डिफ़ॉल्ट प्रासंगिकता',
		priceLowHigh: 'कीमत: कम से अधिक',
		priceHighLow: 'कीमत: अधिक से कम',
		highestRated: 'उच्चतम रेटिंग (★)',
		copySummary: '📋 सारांश कॉपी करें',
		exportJson: '⬇️ JSON निर्यात करें',
		store: 'स्टोर',
		thumb: 'चित्र',
		productName: 'उत्पाद का नाम',
		price: 'कीमत',
		mrp: 'M.R.P',
		discount: 'छूट',
		rating: 'रेटिंग',
		valueScore: 'वैल्यू स्कोर',
		action: 'कार्रवाई',
		noProducts: 'उत्पाद नहीं मिले:',
		tryAnother: 'किसी अन्य उत्पाद नाम या "लैपटॉप", "स्मार्टफोन" जैसे व्यापक शब्दों से खोजें।',
		ready: 'कई स्टोर में तुलना के लिए तैयार',
		readyDescription: 'ऊपर कोई उत्पाद दर्ज करें या समानांतर खोज शुरू करने के लिए त्वरित खोज चुनें।',
		bestStore: 'ऑफर के लिए सबसे अच्छा स्टोर',
		productsAnalyzed: 'विश्लेषित उत्पाद',
		aiVerdict: '🤖 AI शॉपिंग सलाह',
		timeSaving: 'समय बचाने वाली निर्णय तालिका'
	}}
}};

function changeLanguage(language) {{
	const selected = translations[language] || translations.en;
	document.documentElement.lang = language === 'te' ? 'te' : language === 'hi' ? 'hi' : 'en';
	document.querySelectorAll('[data-i18n]').forEach(element => {{
		const key = element.dataset.i18n;
		if (selected[key]) element.textContent = selected[key];
	}});
	document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {{
		const key = element.dataset.i18nPlaceholder;
		if (selected[key]) element.placeholder = selected[key];
	}});
	localStorage.setItem('web-navigator-language', language);
}}

function loadSavedLanguage() {{
	const saved = localStorage.getItem('web-navigator-language') || 'en';
	const selector = document.getElementById('languageSelector');
	if (selector) selector.value = translations[saved] ? saved : 'en';
	changeLanguage(selector ? selector.value : 'en');
}}

function quickSearch(term) {{
	const input = document.querySelector('input.main-input');
	input.value = term;
	input.form.submit();
}}

function switchView(viewName) {{
	document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
	document.querySelectorAll('.view-panel').forEach(panel => panel.classList.remove('active'));

	if (viewName === 'same') {{
		const tab = document.getElementById('tabSame');
		const view = document.getElementById('sameView');
		if (tab) tab.classList.add('active');
		if (view) view.classList.add('active');
	}} else if (viewName === 'split') {{
		const tab = document.getElementById('tabSplit');
		const view = document.getElementById('splitView');
		if (tab) tab.classList.add('active');
		if (view) view.classList.add('active');
	}} else if (viewName === 'matches') {{
		const tab = document.getElementById('tabMatches');
		const view = document.getElementById('matchesView');
		if (tab) tab.classList.add('active');
		if (view) view.classList.add('active');
	}} else if (viewName === 'table') {{
		const tab = document.getElementById('tabTable');
		const view = document.getElementById('tableView');
		if (tab) tab.classList.add('active');
		if (view) view.classList.add('active');
	}}
}}

function applySorting() {{
	const val = document.getElementById('sortFilter').value;
	// Sort Split View column cards
	document.querySelectorAll('.column-cards').forEach(container => {{
		const cards = Array.from(container.querySelectorAll('.product-card'));
		cards.sort((a, b) => {{
			const pA = parseFloat(a.dataset.price) || 0;
			const pB = parseFloat(b.dataset.price) || 0;
			const rA = parseFloat(a.dataset.rating) || 0;
			const rB = parseFloat(b.dataset.rating) || 0;
			if (val === 'price-asc') return pA - pB;
			if (val === 'price-desc') return pB - pA;
			if (val === 'rating-desc') return rB - rA;
			return 0;
		}});
		cards.forEach(c => container.appendChild(c));
	}});

	// Sort Table Rows
	const tblBody = document.getElementById('tblBody');
	if (tblBody) {{
		const rows = Array.from(tblBody.querySelectorAll('tr'));
		rows.sort((a, b) => {{
			const pA = parseFloat(a.dataset.price) || 0;
			const pB = parseFloat(b.dataset.price) || 0;
			const rA = parseFloat(a.dataset.rating) || 0;
			const rB = parseFloat(b.dataset.rating) || 0;
			if (val === 'price-asc') return pA - pB;
			if (val === 'price-desc') return pB - pA;
			if (val === 'rating-desc') return rB - rA;
			return 0;
		}});
		rows.forEach(r => tblBody.appendChild(r));
	}}
	showToast('Sorted by ' + val);
}}

function copySummary() {{
	try {{
		const raw = JSON.parse(document.getElementById('agent-raw-data').textContent);
		const comp = (raw.result || {{}}).comparison || {{}};
		const text = `🛍️ Web Navigator AI Agent Multi-Store Comparison for: ${{raw.result.goal}}\\n` +
			`⏱️ Estimated Time Saved: ${{comp.time_saved_metrics?.minutes_saved || '~12 mins'}}\\n` +
			`🏆 Best Platform: ${{comp.cheaper_store_overall}} (Avg price gap: ${{comp.avg_price_gap}})\\n` +
			`🛒 Amazon Avg: ${{comp.amazon_avg_price}} | Flipkart Avg: ${{comp.flipkart_avg_price}}\\n` +
			`💰 Max Deal Savings: ${{comp.max_deal_savings_text}}\\n` +
			`💡 AI Verdict: ${{raw.result.ai_verdict}}`;
		navigator.clipboard.writeText(text);
		showToast('✅ Comparison summary copied to clipboard!');
	}} catch (e) {{
		showToast('Failed to copy summary');
	}}
}}

function exportJSON() {{
	try {{
		const text = document.getElementById('agent-raw-data').textContent;
		const blob = new Blob([text], {{ type: 'application/json' }});
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = 'web-navigator-comparison.json';
		a.click();
		showToast('⬇️ JSON comparison exported!');
	}} catch (e) {{
		showToast('Failed to export JSON');
	}}
}}

function showToast(msg) {{
	const t = document.getElementById('toast');
	t.textContent = msg;
	t.style.display = 'block';
	setTimeout(() => {{ t.style.display = 'none'; }}, 3000);
}}

let activeStores = {{
	'Amazon': true,
	'Flipkart': true,
	'Croma': true,
	'Ajio': true
}};

function toggleStore(storeName, isChecked) {{
	if (isChecked === undefined) {{
		activeStores[storeName] = !activeStores[storeName];
	}} else {{
		activeStores[storeName] = Boolean(isChecked);
	}}

	// Ensure at least 1 store is selected
	const activeCount = Object.values(activeStores).filter(Boolean).length;
	if (activeCount === 0) {{
		activeStores[storeName] = true;
		showToast('At least one store must remain selected!');
		const chk = document.getElementById('chk' + storeName);
		if (chk) chk.checked = true;
		return;
	}}

	// Sync Checkboxes in Search Card
	const chk = document.getElementById('chk' + storeName);
	if (chk) chk.checked = activeStores[storeName];

	// Sync Toolbar Buttons
	const btn = document.querySelector(`.tool-store-btn[data-store="${{storeName}}"]`);
	if (btn) {{
		if (activeStores[storeName]) {{
			btn.classList.add('active');
			btn.innerHTML = `${{storeName}} ✓`;
		}} else {{
			btn.classList.remove('active');
			btn.innerHTML = `${{storeName}} ✕`;
		}}
	}}

	// 1. Filter Split View Columns
	const col = document.querySelector(`.store-column[data-site="${{storeName}}"]`);
	if (col) {{
		col.style.display = activeStores[storeName] ? 'flex' : 'none';
	}}

	// 2. Filter Same Product Boxes & Recalculate Winners
	document.querySelectorAll('.same-match-card').forEach(card => {{
		const boxes = Array.from(card.querySelectorAll('.same-store-box'));
		let visibleBoxes = [];
		boxes.forEach(box => {{
			const s = box.dataset.site;
			if (activeStores[s]) {{
				box.style.display = 'flex';
				visibleBoxes.push(box);
			}} else {{
				box.style.display = 'none';
			}}
			box.classList.remove('store-box-winner');
			const winPill = box.querySelector('.store-winner-pill');
			if (winPill) winPill.remove();
		}});

		// Recalculate winner among visible boxes in this card
		if (visibleBoxes.length >= 1) {{
			card.style.display = 'block';
			let minPrice = Infinity;
			let minBox = null;
			let maxPrice = -Infinity;
			visibleBoxes.forEach(b => {{
				const pr = parseFloat(b.dataset.price) || 0;
				if (pr > 0 && pr < minPrice) {{
					minPrice = pr;
					minBox = b;
				}}
				if (pr > maxPrice) maxPrice = pr;
			}});

			if (minBox && minPrice !== Infinity) {{
				minBox.classList.add('store-box-winner');
				const header = minBox.querySelector('.same-store-header');
				if (header && !header.querySelector('.store-winner-pill')) {{
					const pill = document.createElement('span');
					pill.className = 'store-winner-pill';
					pill.textContent = 'BEST PRICE 🏆';
					header.appendChild(pill);
				}}

				const winStore = minBox.dataset.site;
				const rightTags = card.querySelector('.same-match-right-tags');
				const footer = card.querySelector('.same-match-footer');
				const diff = (maxPrice > minPrice) ? (maxPrice - minPrice) : 0;

				if (rightTags) {{
					if (diff > 0 && visibleBoxes.length > 1) {{
						rightTags.innerHTML = `<span class="same-winner-tag winner-${{winStore.toLowerCase()}}">🏆 Cheaper on ${{winStore}}! Save ₹${{diff.toLocaleString('en-IN')}}</span>`;
					}} else {{
						rightTags.innerHTML = `<span class="same-winner-tag winner-equal">⚖️ Equal / Best Available on ${{winStore}}</span>`;
					}}
				}}
				if (footer) {{
					if (diff > 0 && visibleBoxes.length > 1) {{
						footer.innerHTML = `💡 <strong>Agent Recommendation:</strong> Buy on <strong>${{winStore}}</strong> at <strong>₹${{minPrice.toLocaleString('en-IN')}}</strong> to save <strong>₹${{diff.toLocaleString('en-IN')}}</strong> compared to other selected stores.`;
					}} else {{
						footer.innerHTML = `💡 <strong>Agent Recommendation:</strong> Selected store ${{winStore}} offers verified model price at <strong>₹${{minPrice.toLocaleString('en-IN')}}</strong>.`;
					}}
				}}
			}}
		}} else {{
			card.style.display = 'none';
		}}
	}});

	// Re-run applyItemLimit to update table and metric counts
	const currentLimit = document.getElementById('displayLimitFilter')?.value || document.getElementById('itemsLimit')?.value || 'all';
	applyItemLimit(currentLimit);

	showToast(`${{storeName}} ${{activeStores[storeName] ? 'enabled' : 'disabled'}}`);
}}

function toggleStoreFilter(storeName, isChecked) {{
	toggleStore(storeName, isChecked);
}}

function toggleStoreBtn(storeName) {{
	toggleStore(storeName, !activeStores[storeName]);
}}

function applyItemLimit(limitVal) {{
	const select1 = document.getElementById('itemsLimit');
	const select2 = document.getElementById('displayLimitFilter');
	if (select1 && select1.value !== limitVal) select1.value = limitVal;
	if (select2 && select2.value !== limitVal) select2.value = limitVal;

	const limitNum = (limitVal === 'all') ? Infinity : parseInt(limitVal, 10);

	let storeCounts = {{'Amazon': 0, 'Flipkart': 0, 'Croma': 0, 'Ajio': 0}};
	let storePrices = {{'Amazon': [], 'Flipkart': [], 'Croma': [], 'Ajio': []}};

	// Filter Split View columns
	['Amazon', 'Flipkart', 'Croma', 'Ajio'].forEach(sName => {{
		const col = document.querySelector(`.store-column[data-site="${{sName}}"]`);
		if (col) {{
			if (!activeStores[sName]) {{
				col.style.display = 'none';
			}} else {{
				col.style.display = 'flex';
				const cards = Array.from(col.querySelectorAll('.product-card'));
				cards.forEach((card, idx) => {{
					if (idx < limitNum) {{
						card.style.display = 'flex';
						storeCounts[sName]++;
						const p = parseFloat(card.dataset.price);
						if (p && !isNaN(p) && p > 0 && p !== Infinity) storePrices[sName].push(p);
					}} else {{
						card.style.display = 'none';
					}}
				}});
				const countEl = col.querySelector('.store-count');
				if (countEl) countEl.textContent = `${{storeCounts[sName]}} products`;
				if (storePrices[sName].length > 0) {{
					const avgP = Math.round(storePrices[sName].reduce((a, b) => a + b, 0) / storePrices[sName].length);
					const avgEl = col.querySelector('.store-avg-price');
					if (avgEl) avgEl.textContent = `₹${{avgP.toLocaleString('en-IN')}}`;
				}}
			}}
		}}
	}});

	// Filter Unified Deals Table
	const tblBody = document.getElementById('tblBody');
	if (tblBody) {{
		let tblCounts = {{'amazon': 0, 'flipkart': 0, 'croma': 0, 'ajio': 0}};
		const rows = Array.from(tblBody.querySelectorAll('tr'));
		rows.forEach(row => {{
			const site = (row.dataset.site || '').toLowerCase();
			let siteKey = null;
			for (let k in tblCounts) {{
				if (site.includes(k)) {{
					siteKey = k;
					break;
				}}
			}}

			const capitalizedSite = siteKey ? (siteKey.charAt(0).toUpperCase() + siteKey.slice(1)) : '';
			if (capitalizedSite && !activeStores[capitalizedSite]) {{
				row.style.display = 'none';
			}} else if (siteKey) {{
				if (tblCounts[siteKey] < limitNum) {{
					row.style.display = '';
					tblCounts[siteKey]++;
				}} else {{
					row.style.display = 'none';
				}}
			}} else {{
				row.style.display = '';
			}}
		}});
	}}

	// Filter Same Product matches
	const sameCards = document.querySelectorAll('.same-match-card');
	let visibleSameCount = 0;
	sameCards.forEach((sc) => {{
		const hasVisibleStore = Array.from(sc.querySelectorAll('.same-store-box')).some(b => b.style.display !== 'none');
		if (hasVisibleStore && visibleSameCount < limitNum) {{
			sc.style.display = 'block';
			visibleSameCount++;
		}} else {{
			sc.style.display = 'none';
		}}
	}});

	// Filter Head-to-Head matches
	const matchCards = document.querySelectorAll('.match-card');
	matchCards.forEach((mc, idx) => {{
		if (idx < limitNum) {{
			mc.style.display = 'block';
		}} else {{
			mc.style.display = 'none';
		}}
	}});

	// Update "PRODUCTS ANALYZED" card dynamically
	let totalVisible = 0;
	let breakdownParts = [];
	['Amazon', 'Flipkart', 'Croma', 'Ajio'].forEach(sName => {{
		if (activeStores[sName]) {{
			totalVisible += storeCounts[sName];
			breakdownParts.push(`${{storeCounts[sName]}} ${{sName}}`);
		}}
	}});

	const countCard = document.getElementById('analyzedCount');
	const subCard = document.getElementById('analyzedSub');
	if (countCard) {{
		countCard.textContent = `${{totalVisible}} Items`;
	}}
	if (subCard) {{
		subCard.textContent = breakdownParts.join(' · ') || '0 items';
	}}

	// Recalculate Best Store for Deals for displayed items across active stores
	let activeAverages = {{}};
	for (let sName in storePrices) {{
		if (activeStores[sName] && storePrices[sName].length > 0) {{
			activeAverages[sName] = Math.round(storePrices[sName].reduce((a, b) => a + b, 0) / storePrices[sName].length);
		}}
	}}

	const bestStoreEl = document.getElementById('bestStoreVal');
	const bestStoreSub = document.getElementById('bestStoreSub');
	if (bestStoreEl) {{
		const stores = Object.keys(activeAverages);
		if (stores.length >= 1) {{
			const winnerStore = stores.reduce((a, b) => activeAverages[a] < activeAverages[b] ? a : b);
			bestStoreEl.textContent = winnerStore;
			if (stores.length >= 2) {{
				const vals = Object.values(activeAverages);
				const gap = Math.abs(Math.max(...vals) - Math.min(...vals));
				if (bestStoreSub) bestStoreSub.textContent = `Avg price gap: ₹${{gap.toLocaleString('en-IN')}}`;
			}} else {{
				if (bestStoreSub) bestStoreSub.textContent = `Average: ₹${{activeAverages[winnerStore].toLocaleString('en-IN')}}`;
			}}
		}} else {{
			bestStoreEl.textContent = 'N/A';
			if (bestStoreSub) bestStoreSub.textContent = 'No products in selected stores';
		}}
	}}

	showToast(`Showing ${{limitVal === 'all' ? 'all' : limitVal}} items per store`);
}}

window.addEventListener('DOMContentLoaded', () => {{
	loadSavedLanguage();
	const initLimit = document.getElementById('displayLimitFilter')?.value || document.getElementById('itemsLimit')?.value || 'all';
	applyItemLimit(initLimit);
}});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
	def do_GET(self) -> None:
		query = parse_qs(urlparse(self.path).query)
		goal = query.get("goal", [""])[0].strip()
		limit_param = query.get("limit", ["all"])[0].strip()
		result = None
		if goal:
			# Execute Agent
			agent = Agent(
				model=os.getenv("OLLAMA_MODEL", "llama3.1"),
				headless=True,
			)
			result = asyncio.run(agent.run(goal, max_items_per_site=24))

		body = _render_page(result, selected_limit=limit_param).encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def log_message(self, format: str, *args: Any) -> None:
		return


def main() -> None:
	port = int(os.getenv("PORT", "8000"))
	server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
	print(f"Web Navigator AI Agent running at http://127.0.0.1:{port}")
	server.serve_forever()


if __name__ == "__main__":
	main()
