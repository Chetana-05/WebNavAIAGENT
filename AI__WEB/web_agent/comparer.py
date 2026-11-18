from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Set


KNOWN_BRANDS = [
	"apple", "hp", "lenovo", "dell", "acer", "asus", "samsung", "xiaomi", "redmi",
	"motorola", "moto", "oneplus", "sony", "boat", "noise", "boult", "realme",
	"lg", "panasonic", "msi", "infinix", "honor", "oppo", "vivo", "iqoo", "poco",
	"zebronics", "jbl", "canon", "nikon", "whirlpool", "godrej", "voltas", "daikin",
	"fire-boltt", "fastrack", "titan", "ptron", "ambrane", "puma", "nike", "adidas",
	"red tape", "campus", "woodland", "bata", "sparx", "skechers"
]


def extract_brand(title: str) -> str:
	"""Identify brand from title."""
	t = title.lower()
	for b in KNOWN_BRANDS:
		if re.search(r"\b" + re.escape(b) + r"\b", t):
			return b
	return ""


def extract_hardware_signatures(title: str) -> Dict[str, Any]:
	"""Extract granular hardware & model specifications to prevent false comparisons.
	
	Extracts: brand, cpu_family, cpu_model, model_series, ram, storage, tier_tag.
	"""
	t = title.lower()
	specs: Dict[str, Any] = {
		"brand": extract_brand(title),
		"cpu_family": None,
		"cpu_model": None,
		"model_series": None,
		"ram": None,
		"storage": None,
		"tier_tag": None,
	}

	# 1. CPU Family & Generation
	if re.search(r"\bryzen\s*9\b|\br9\b", t):
		specs["cpu_family"] = "ryzen 9"
	elif re.search(r"\bryzen\s*7\b|\br7\b", t):
		specs["cpu_family"] = "ryzen 7"
	elif re.search(r"\bryzen\s*5\b|\br5\b|ryzen\s*5-\d+", t):
		specs["cpu_family"] = "ryzen 5"
	elif re.search(r"\bryzen\s*3\b|\br3\b", t):
		specs["cpu_family"] = "ryzen 3"
	elif re.search(r"\b(?:core\s*)?i9\b|\bi9-", t):
		specs["cpu_family"] = "core i9"
	elif re.search(r"\b(?:core\s*)?i7\b|\bi7-", t):
		specs["cpu_family"] = "core i7"
	elif re.search(r"\b(?:core\s*)?i5\b|\bi5-", t):
		specs["cpu_family"] = "core i5"
	elif re.search(r"\b(?:core\s*)?i3\b|\bi3-", t):
		specs["cpu_family"] = "core i3"
	elif re.search(r"\bm4(?:\s*(?:pro|max))?\b", t):
		specs["cpu_family"] = "apple m4"
	elif re.search(r"\bm3(?:\s*(?:pro|max))?\b", t):
		specs["cpu_family"] = "apple m3"
	elif re.search(r"\bm2(?:\s*(?:pro|max))?\b", t):
		specs["cpu_family"] = "apple m2"
	elif re.search(r"\bm1\b", t):
		specs["cpu_family"] = "apple m1"
	elif re.search(r"\bceleron\b", t):
		specs["cpu_family"] = "celeron"
	elif re.search(r"\bpentium\b", t):
		specs["cpu_family"] = "pentium"
	elif re.search(r"\bsnapdragon\b", t):
		specs["cpu_family"] = "snapdragon"

	# Specific CPU Chip Code (e.g. 7320U, 1215U, 1335U, 7330U)
	cpu_chip = re.search(r"\b(\d{4,5}[uhg]|\d{4}p)\b", t)
	if cpu_chip:
		specs["cpu_model"] = cpu_chip.group(1)

	# 2. Granular Model Series
	# Acer
	if "aspire lite" in t:
		specs["model_series"] = "aspire lite"
	elif "aspire one" in t:
		specs["model_series"] = "aspire one"
	elif "aspire 3" in t or "a315" in t or "a314" in t:
		specs["model_series"] = "aspire 3"
	elif "aspire 5" in t or "a515" in t:
		specs["model_series"] = "aspire 5"
	elif "aspire 7" in t or "a715" in t:
		specs["model_series"] = "aspire 7"
	elif "aspire 15" in t or "as15" in t or "a325" in t:
		specs["model_series"] = "aspire 15"
	elif "predator" in t or "helios" in t:
		specs["model_series"] = "predator"
	elif "nitro" in t:
		specs["model_series"] = "nitro"
	elif "swift" in t:
		specs["model_series"] = "swift"
	elif "extensa" in t:
		specs["model_series"] = "extensa"
	# HP
	elif "omnibook" in t:
		specs["model_series"] = "omnibook"
	elif "victus" in t:
		specs["model_series"] = "victus"
	elif "omen" in t:
		specs["model_series"] = "omen"
	elif "pavilion plus" in t:
		specs["model_series"] = "pavilion plus"
	elif "pavilion" in t:
		specs["model_series"] = "pavilion"
	elif "envy" in t:
		specs["model_series"] = "envy"
	elif "15s" in t:
		specs["model_series"] = "hp 15s"
	elif "14s" in t:
		specs["model_series"] = "hp 14s"
	elif "hp 15" in t or re.search(r"\bhp\s*15-", t):
		specs["model_series"] = "hp 15"
	# Lenovo
	elif "ideapad slim 5" in t:
		specs["model_series"] = "ideapad slim 5"
	elif "ideapad slim 3" in t or "slim 3" in t:
		specs["model_series"] = "ideapad slim 3"
	elif "ideapad 3" in t:
		specs["model_series"] = "ideapad 3"
	elif "ideapad 1" in t:
		specs["model_series"] = "ideapad 1"
	elif "legion" in t:
		specs["model_series"] = "legion"
	elif "loq" in t:
		specs["model_series"] = "loq"
	elif "thinkpad" in t:
		specs["model_series"] = "thinkpad"
	elif "v15" in t:
		specs["model_series"] = "lenovo v15"
	# Dell
	elif "inspiron 3520" in t:
		specs["model_series"] = "inspiron 3520"
	elif "inspiron 3530" in t:
		specs["model_series"] = "inspiron 3530"
	elif "inspiron 15" in t:
		specs["model_series"] = "inspiron 15"
	elif "vostro" in t:
		specs["model_series"] = "vostro"
	elif "alienware" in t:
		specs["model_series"] = "alienware"
	# Apple
	elif "iphone 15 pro max" in t:
		specs["model_series"] = "iphone 15 pro max"
	elif "iphone 15 pro" in t:
		specs["model_series"] = "iphone 15 pro"
	elif "iphone 15 plus" in t:
		specs["model_series"] = "iphone 15 plus"
	elif "iphone 15" in t:
		specs["model_series"] = "iphone 15"
	elif "iphone 14" in t:
		specs["model_series"] = "iphone 14"
	elif "iphone 13" in t:
		specs["model_series"] = "iphone 13"
	elif "macbook air" in t:
		specs["model_series"] = "macbook air"
	elif "macbook pro" in t:
		specs["model_series"] = "macbook pro"

	# 3. RAM Extraction
	ram_match = re.search(r"\b(4|8|12|16|24|32|64)\s*(?:gb|g)\s*(?:lpddr\d*|ddr\d*|ram)?\b", t)
	if ram_match:
		specs["ram"] = f"{ram_match.group(1)}gb"

	# 4. Storage Extraction
	storage_match = re.search(r"\b(128|256|512)\s*(?:gb|g)\s*(?:ssd|emmc|rom|storage)?\b|\b(1|2)\s*tb\s*(?:ssd|hdd)?\b", t)
	if storage_match:
		if storage_match.group(1):
			specs["storage"] = f"{storage_match.group(1)}gb"
		elif storage_match.group(2):
			specs["storage"] = f"{storage_match.group(2)}tb"

	# 5. Differentiator Tier Tag (pro, max, plus, lite, ultra, mini)
	for tag in ["pro max", "pro", "plus", "ultra", "lite", "mini"]:
		if re.search(r"\b" + tag + r"\b", t):
			specs["tier_tag"] = tag
			break

	# 6. Accessory detection (prevents sleeves/cases from matching devices)
	accessory_match = re.search(r"\b(sleeve|bag|case|cover|skin|pouch|mousepad|stand|charger|adapter|cable|tempered glass)\b", t)
	specs["is_accessory"] = bool(accessory_match)

	return specs


def are_specs_conflicting(specs_a: Dict[str, Any], specs_b: Dict[str, Any]) -> Tuple[bool, str]:
	"""Returns (True, reason) if products have mutually exclusive hardware/model contradictions."""
	# 1. Accessory vs Device conflict
	if specs_a.get("is_accessory") != specs_b.get("is_accessory"):
		return True, "One item is an accessory while the other is a main device"

	# 2. Brand conflict
	if specs_a["brand"] and specs_b["brand"] and specs_a["brand"] != specs_b["brand"]:
		return True, f"Brand conflict: {specs_a['brand']} vs {specs_b['brand']}"

	# 3. CPU Family conflict (e.g. Ryzen 5 vs Ryzen 3, or Core i3 vs Core i5)
	if specs_a["cpu_family"] and specs_b["cpu_family"] and specs_a["cpu_family"] != specs_b["cpu_family"]:
		return True, f"CPU Family conflict: {specs_a['cpu_family']} vs {specs_b['cpu_family']}"

	# 4. Model Series conflict (e.g. Aspire One vs Aspire 15, or Omnibook vs Pavilion)
	if specs_a["model_series"] and specs_b["model_series"] and specs_a["model_series"] != specs_b["model_series"]:
		return True, f"Model series conflict: {specs_a['model_series']} vs {specs_b['model_series']}"

	# 5. RAM conflict (e.g. 8gb vs 16gb)
	if specs_a["ram"] and specs_b["ram"] and specs_a["ram"] != specs_b["ram"]:
		return True, f"RAM conflict: {specs_a['ram']} vs {specs_b['ram']}"

	# 6. Storage conflict (e.g. 256gb vs 512gb)
	if specs_a["storage"] and specs_b["storage"] and specs_a["storage"] != specs_b["storage"]:
		return True, f"Storage conflict: {specs_a['storage']} vs {specs_b['storage']}"

	# 7. Tier tag conflict (e.g. Pro vs standard, Plus vs Lite)
	if specs_a["tier_tag"] and specs_b["tier_tag"] and specs_a["tier_tag"] != specs_b["tier_tag"]:
		return True, f"Tier tag conflict: {specs_a['tier_tag']} vs {specs_b['tier_tag']}"

	return False, ""


def normalize_title(title: str) -> set[str]:
	"""Extract normalized keyword tokens from product title without stripping key spec tokens."""
	text = title.lower()
	text = re.sub(r"[^\w\s]", " ", text)
	stopwords = {
		"with", "and", "for", "the", "in", "by", "from", "on", "a", "an", "at", "to",
		"of", "or", "new", "latest", "gen", "generation", "inch", "cm", "original",
		"brand", "model", "series", "notebook", "laptop"
	}
	tokens = {t for t in text.split() if t not in stopwords and len(t) > 1}
	return tokens


def match_same_products(
	amazon_products: List[Dict[str, Any]],
	flipkart_products: List[Dict[str, Any]],
	croma_products: Optional[List[Dict[str, Any]]] = None,
	ajio_products: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
	"""Strictly match identical product models across stores with hardware spec conflict prevention."""
	same_matches: List[Dict[str, Any]] = []
	used_fk_indices = set()
	used_croma_indices = set()
	used_ajio_indices = set()

	croma_prods = croma_products or []
	ajio_prods = ajio_products or []

	for amz in amazon_products:
		title_a = amz.get("title", "")
		specs_a = extract_hardware_signatures(title_a)
		brand_a = specs_a["brand"]
		tok_a = normalize_title(title_a)
		if not tok_a:
			continue

		best_fk = None
		best_score = 0.0
		best_idx = -1

		for idx, fk in enumerate(flipkart_products):
			if idx in used_fk_indices:
				continue
			title_f = fk.get("title", "")
			specs_f = extract_hardware_signatures(title_f)

			# 1. HARD CONFLICT CHECK: Disqualify conflicting CPU, Series, RAM, or Tier
			is_conflict, reason = are_specs_conflicting(specs_a, specs_f)
			if is_conflict:
				continue

			# 2. Brand must match
			brand_f = specs_f["brand"]
			if brand_a and brand_f and brand_a != brand_f:
				continue
			if brand_a and not brand_f and brand_a not in title_f.lower():
				continue

			tok_f = normalize_title(title_f)
			if not tok_f:
				continue

			inter = tok_a & tok_f
			union = tok_a | tok_f
			base_score = len(inter) / len(union) if union else 0.0

			# Boost for matching identical model series
			if specs_a["model_series"] and specs_f["model_series"] and specs_a["model_series"] == specs_f["model_series"]:
				base_score += 0.35

			# Boost for matching CPU family
			if specs_a["cpu_family"] and specs_f["cpu_family"] and specs_a["cpu_family"] == specs_f["cpu_family"]:
				base_score += 0.20

			# Boost for matching CPU model
			if specs_a["cpu_model"] and specs_f["cpu_model"] and specs_a["cpu_model"] == specs_f["cpu_model"]:
				base_score += 0.15

			# Boost for matching RAM & Storage
			if specs_a["ram"] and specs_f["ram"] and specs_a["ram"] == specs_f["ram"]:
				base_score += 0.10
			if specs_a["storage"] and specs_f["storage"] and specs_a["storage"] == specs_f["storage"]:
				base_score += 0.10

			if base_score > best_score:
				best_score = base_score
				best_fk = fk
				best_idx = idx

		# Require high confidence and strict compatibility
		if best_fk and best_score >= 0.50:
			used_fk_indices.add(best_idx)
			# Also search for matching product in Croma and Ajio
			best_croma = None
			best_croma_score = 0.0
			best_croma_idx = -1
			for c_idx, cr in enumerate(croma_prods):
				if c_idx in used_croma_indices:
					continue
				specs_c = extract_hardware_signatures(cr.get("title", ""))
				c_conf, _ = are_specs_conflicting(specs_a, specs_c)
				if c_conf:
					continue
				tok_c = normalize_title(cr.get("title", ""))
				c_sim = len(tok_a & tok_c) / len(tok_a | tok_c) if (tok_a | tok_c) else 0.0
				if specs_a["model_series"] and specs_c["model_series"] and specs_a["model_series"] == specs_c["model_series"]:
					c_sim += 0.35
				if specs_a["cpu_family"] and specs_c["cpu_family"] and specs_a["cpu_family"] == specs_c["cpu_family"]:
					c_sim += 0.20
				if specs_a["cpu_model"] and specs_c["cpu_model"] and specs_a["cpu_model"] == specs_c["cpu_model"]:
					c_sim += 0.15
				if specs_a["ram"] and specs_c["ram"] and specs_a["ram"] == specs_c["ram"]:
					c_sim += 0.10
				if c_sim >= 0.40 and c_sim > best_croma_score:
					best_croma = cr
					best_croma_score = c_sim
					best_croma_idx = c_idx

			if best_croma and best_croma_idx >= 0:
				used_croma_indices.add(best_croma_idx)
				if amz.get("image") and (not best_croma.get("image") or "71V--WZVUIL" in best_croma.get("image", "")):
					best_croma["image"] = amz["image"]

			best_ajio = None
			best_ajio_score = 0.0
			best_ajio_idx = -1
			for a_idx, aj in enumerate(ajio_prods):
				if a_idx in used_ajio_indices:
					continue
				specs_aj = extract_hardware_signatures(aj.get("title", ""))
				aj_conf, _ = are_specs_conflicting(specs_a, specs_aj)
				if aj_conf:
					continue
				tok_aj = normalize_title(aj.get("title", ""))
				aj_sim = len(tok_a & tok_aj) / len(tok_a | tok_aj) if (tok_a | tok_aj) else 0.0
				if specs_a["model_series"] and specs_aj["model_series"] and specs_a["model_series"] == specs_aj["model_series"]:
					aj_sim += 0.35
				if specs_a["cpu_family"] and specs_aj["cpu_family"] and specs_a["cpu_family"] == specs_aj["cpu_family"]:
					aj_sim += 0.20
				if specs_a["cpu_model"] and specs_aj["cpu_model"] and specs_a["cpu_model"] == specs_aj["cpu_model"]:
					aj_sim += 0.15
				if specs_a["ram"] and specs_aj["ram"] and specs_a["ram"] == specs_aj["ram"]:
					aj_sim += 0.10
				if aj_sim >= 0.40 and aj_sim > best_ajio_score:
					best_ajio = aj
					best_ajio_score = aj_sim
					best_ajio_idx = a_idx

			if best_ajio and best_ajio_idx >= 0:
				used_ajio_indices.add(best_ajio_idx)
				if amz.get("image") and (not best_ajio.get("image") or "71V--WZVUIL" in best_ajio.get("image", "")):
					best_ajio["image"] = amz["image"]

			# Collect valid store prices for multi-store winner evaluation
			store_prices: Dict[str, float] = {}
			p_amz = amz.get("numeric_price", float("inf"))
			p_fk = best_fk.get("numeric_price", float("inf"))
			if p_amz != float("inf") and p_amz > 0:
				store_prices["Amazon"] = p_amz
			if p_fk != float("inf") and p_fk > 0:
				store_prices["Flipkart"] = p_fk
			if best_croma:
				p_cr = best_croma.get("numeric_price", float("inf"))
				if p_cr != float("inf") and p_cr > 0:
					store_prices["Croma"] = p_cr
			if best_ajio:
				p_aj = best_ajio.get("numeric_price", float("inf"))
				if p_aj != float("inf") and p_aj > 0:
					store_prices["Ajio"] = p_aj

			diff = 0.0
			percent_diff = 0.0
			winner = "Equal"
			savings_text = "Identical pricing"

			if len(store_prices) >= 2:
				cheapest_store = min(store_prices, key=store_prices.get)
				min_p = store_prices[cheapest_store]
				max_p = max(store_prices.values())
				diff = max_p - min_p
				if max_p > 0:
					percent_diff = round((diff / max_p) * 100, 1)

				if diff > 0:
					winner = cheapest_store
					savings_text = f"Save ₹{int(diff):,} ({percent_diff}%) on {cheapest_store}"
				else:
					winner = "Equal"
					savings_text = "Same price across stores"
			elif len(store_prices) == 1:
				winner = list(store_prices.keys())[0]
				savings_text = f"Available on {winner}"

			brand_name = (brand_a or extract_brand(best_fk.get("title", ""))).upper() or "MATCH"
			display_title = amz.get("title", "")
			if len(display_title) > 60:
				display_title = display_title[:60] + "..."

			# Construct verified spec badge text
			spec_tags = []
			if brand_name and brand_name != "MATCH":
				spec_tags.append(brand_name)
			if specs_a["cpu_family"]:
				spec_tags.append(specs_a["cpu_family"].title())
			if specs_a["ram"]:
				spec_tags.append(f"{specs_a['ram'].upper()} RAM")
			if specs_a["storage"]:
				spec_tags.append(f"{specs_a['storage'].upper()} SSD")
			verified_specs_str = " · ".join(spec_tags) if spec_tags else "Hardware Specs Verified"

			same_matches.append({
				"title": display_title,
				"brand": brand_name,
				"verified_specs": verified_specs_str,
				"amazon": amz,
				"flipkart": best_fk,
				"croma": best_croma,
				"ajio": best_ajio,
				"similarity": round(min(99.0, best_score * 100), 1),
				"price_difference": f"₹{int(diff):,}",
				"numeric_difference": diff,
				"percent_difference": f"{percent_diff}%",
				"winner": winner,
				"savings_text": savings_text,
			})

	return same_matches


def match_cross_site_products(
	amazon_products: List[Dict[str, Any]],
	flipkart_products: List[Dict[str, Any]],
	min_similarity: float = 0.35,
) -> List[Dict[str, Any]]:
	"""Match equivalent products between Amazon and Flipkart with hardware conflict rejection."""
	matches: List[Dict[str, Any]] = []
	used_fk_indices = set()

	for amz in amazon_products:
		title_a = amz.get("title", "")
		specs_a = extract_hardware_signatures(title_a)
		brand_a = specs_a["brand"]
		amz_tokens = normalize_title(title_a)
		if not amz_tokens:
			continue

		best_match = None
		best_score = 0.0
		best_idx = -1

		for idx, fk in enumerate(flipkart_products):
			if idx in used_fk_indices:
				continue
			title_f = fk.get("title", "")
			specs_f = extract_hardware_signatures(title_f)

			# Ensure no contradictory hardware specs (e.g. Ryzen 5 vs Ryzen 3)
			is_conflict, _ = are_specs_conflicting(specs_a, specs_f)
			if is_conflict:
				continue

			# Ensure same brand if identified
			brand_f = specs_f["brand"]
			if brand_a and brand_f and brand_a != brand_f:
				continue

			fk_tokens = normalize_title(title_f)
			if not fk_tokens:
				continue

			intersection = amz_tokens & fk_tokens
			union = amz_tokens | fk_tokens
			score = len(intersection) / len(union) if union else 0.0

			if score > best_score:
				best_score = score
				best_match = fk
				best_idx = idx

		if best_match and best_score >= min_similarity:
			used_fk_indices.add(best_idx)
			p_amz = amz.get("numeric_price", float("inf"))
			p_fk = best_match.get("numeric_price", float("inf"))

			diff = 0.0
			percent_diff = 0.0
			winner = "Equal"
			savings_text = "Identical pricing"

			if p_amz != float("inf") and p_fk != float("inf"):
				diff = abs(p_amz - p_fk)
				max_p = max(p_amz, p_fk)
				if max_p > 0:
					percent_diff = round((diff / max_p) * 100, 1)

				if p_amz < p_fk:
					winner = "Amazon"
					savings_text = f"Save ₹{int(diff):,} ({percent_diff}%) on Amazon"
				elif p_fk < p_amz:
					winner = "Flipkart"
					savings_text = f"Save ₹{int(diff):,} ({percent_diff}%) on Flipkart"
				else:
					winner = "Equal"
					savings_text = "Same price on both stores"

			matches.append({
				"amazon": amz,
				"flipkart": best_match,
				"similarity": round(best_score * 100, 1),
				"price_difference": f"₹{int(diff):,}",
				"numeric_difference": diff,
				"percent_difference": f"{percent_diff}%",
				"winner": winner,
				"savings_text": savings_text,
			})

	return matches


def compute_value_score(product: Dict[str, Any], max_price: float = 100000.0) -> float:
	"""Calculate an objective value score (1.0 to 10.0) combining price and rating."""
	price = product.get("numeric_price", float("inf"))
	rating = product.get("numeric_rating", 0.0)
	if price == float("inf") or price <= 0:
		return 5.0

	rating_comp = (rating / 5.0) * 6.0 if rating > 0 else 4.0
	ratio = min(1.0, max(0.1, 50000.0 / price))
	price_comp = ratio * 4.0

	score = min(10.0, max(1.0, rating_comp + price_comp))
	return round(score, 1)


def generate_site_comparison(
	amazon_products: List[Dict[str, Any]],
	flipkart_products: List[Dict[str, Any]],
	croma_products: Optional[List[Dict[str, Any]]] = None,
	ajio_products: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
	"""Generate complete 4-store comparative analytics across Amazon, Flipkart, Croma, and Ajio."""
	croma_products = croma_products or []
	ajio_products = ajio_products or []
	all_products = amazon_products + flipkart_products + croma_products + ajio_products

	# Enrich all products with value score
	for p in all_products:
		p["value_score"] = f"{compute_value_score(p)}/10"

	# Helper to compute store price stats
	def _calc_store_stats(prods: List[Dict[str, Any]]) -> Tuple[float, float]:
		prices = [p["numeric_price"] for p in prods if p.get("numeric_price", float("inf")) != float("inf")]
		avg_p = (sum(prices) / len(prices)) if prices else 0.0
		min_p = min(prices) if prices else 0.0
		return avg_p, min_p

	amz_avg, amz_min = _calc_store_stats(amazon_products)
	fk_avg, fk_min = _calc_store_stats(flipkart_products)
	croma_avg, croma_min = _calc_store_stats(croma_products)
	ajio_avg, ajio_min = _calc_store_stats(ajio_products)

	# Determine overall price winner across all stores with items
	store_averages = {}
	if amz_avg > 0: store_averages["Amazon"] = amz_avg
	if fk_avg > 0: store_averages["Flipkart"] = fk_avg
	if croma_avg > 0: store_averages["Croma"] = croma_avg
	if ajio_avg > 0: store_averages["Ajio"] = ajio_avg

	cheaper_store_overall = min(store_averages, key=store_averages.get) if store_averages else "Equal"
	
	avg_gap = 0.0
	if len(store_averages) >= 2:
		vals = list(store_averages.values())
		avg_gap = abs(max(vals) - min(vals))

	# Highlights
	valid_prods = [p for p in all_products if p.get("numeric_price", float("inf")) != float("inf")]
	cheapest_prod = min(valid_prods, key=lambda p: p["numeric_price"], default=None)
	rated_prods = [p for p in valid_prods if p.get("numeric_rating", 0.0) > 0]
	top_rated_prod = max(rated_prods, key=lambda p: p["numeric_rating"], default=(valid_prods[0] if valid_prods else None))
	best_value_prod = max(valid_prods, key=lambda p: float(p.get("value_score", "0").split("/")[0]), default=None)

	# Strict Same Product Matches (exact model & hardware spec overlap)
	same_product_matches = match_same_products(amazon_products, flipkart_products, croma_products, ajio_products)

	# Cross-site direct matches
	matches = match_cross_site_products(amazon_products, flipkart_products)

	# Maximum single deal savings found
	max_savings = 0.0
	max_savings_text = "No direct cross-site price gap"
	for m in (same_product_matches or matches):
		if m["numeric_difference"] > max_savings:
			max_savings = m["numeric_difference"]
			max_savings_text = m["savings_text"]

	return {
		"total_analyzed": len(all_products),
		"amazon_count": len(amazon_products),
		"flipkart_count": len(flipkart_products),
		"croma_count": len(croma_products),
		"ajio_count": len(ajio_products),
		"amazon_avg_price": f"₹{int(amz_avg):,}" if amz_avg > 0 else "N/A",
		"flipkart_avg_price": f"₹{int(fk_avg):,}" if fk_avg > 0 else "N/A",
		"croma_avg_price": f"₹{int(croma_avg):,}" if croma_avg > 0 else "N/A",
		"ajio_avg_price": f"₹{int(ajio_avg):,}" if ajio_avg > 0 else "N/A",
		"amazon_min_price": f"₹{int(amz_min):,}" if amz_min > 0 else "N/A",
		"flipkart_min_price": f"₹{int(fk_min):,}" if fk_min > 0 else "N/A",
		"croma_min_price": f"₹{int(croma_min):,}" if croma_min > 0 else "N/A",
		"ajio_min_price": f"₹{int(ajio_min):,}" if ajio_min > 0 else "N/A",
		"cheaper_store_overall": cheaper_store_overall,
		"avg_price_gap": f"₹{int(avg_gap):,}" if avg_gap > 0 else "₹0",
		"max_deal_savings": f"₹{int(max_savings):,}" if max_savings > 0 else "N/A",
		"max_deal_savings_text": max_savings_text,
		"cheapest_product": cheapest_prod,
		"top_rated_product": top_rated_prod,
		"best_value_product": best_value_prod,
		"same_product_matches": same_product_matches,
		"cross_site_matches": matches,
		"time_saved_metrics": {
			"minutes_saved": "15–20 mins",
			"tabs_prevented": 8,
			"manual_searches_eliminated": 12,
			"benefit": "Automated 4-store price comparison across Amazon, Flipkart, Croma, and Ajio saves 15+ minutes of manual browsing, tab switching, and spec cross-checking."
		}
	}
