import re
from typing import Dict, Any, Tuple, Optional

KNOWN_BRANDS = [
	"apple", "hp", "lenovo", "dell", "acer", "asus", "samsung", "xiaomi", "redmi",
	"motorola", "moto", "oneplus", "sony", "boat", "noise", "boult", "realme",
	"lg", "panasonic", "msi", "infinix", "honor", "oppo", "vivo", "iqoo", "poco",
	"zebronics", "jbl", "canon", "nikon", "whirlpool", "godrej", "voltas", "daikin"
]

def extract_brand(title: str) -> str:
	t = title.lower()
	for b in KNOWN_BRANDS:
		if re.search(r"\b" + re.escape(b) + r"\b", t):
			return b
	return ""

def extract_hardware_signatures(title: str) -> Dict[str, Any]:
	"""Extract granular hardware & model specifications to prevent false comparisons."""
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

	return specs


def are_specs_conflicting(specs_a: Dict[str, Any], specs_b: Dict[str, Any]) -> Tuple[bool, str]:
	"""Returns (True, reason) if products have mutually exclusive hardware/model contradictions."""
	# 1. Brand conflict
	if specs_a["brand"] and specs_b["brand"] and specs_a["brand"] != specs_b["brand"]:
		return True, f"Brand conflict: {specs_a['brand']} vs {specs_b['brand']}"

	# 2. CPU Family conflict (e.g. Ryzen 5 vs Ryzen 3, or Core i3 vs Core i5)
	if specs_a["cpu_family"] and specs_b["cpu_family"] and specs_a["cpu_family"] != specs_b["cpu_family"]:
		return True, f"CPU Family conflict: {specs_a['cpu_family']} vs {specs_b['cpu_family']}"

	# 3. Model Series conflict (e.g. Aspire One vs Aspire 15, or Omnibook vs Pavilion)
	if specs_a["model_series"] and specs_b["model_series"] and specs_a["model_series"] != specs_b["model_series"]:
		return True, f"Model series conflict: {specs_a['model_series']} vs {specs_b['model_series']}"

	# 4. RAM conflict (e.g. 8gb vs 16gb)
	if specs_a["ram"] and specs_b["ram"] and specs_a["ram"] != specs_b["ram"]:
		return True, f"RAM conflict: {specs_a['ram']} vs {specs_b['ram']}"

	# 5. Storage conflict (e.g. 256gb vs 512gb)
	if specs_a["storage"] and specs_b["storage"] and specs_a["storage"] != specs_b["storage"]:
		return True, f"Storage conflict: {specs_a['storage']} vs {specs_b['storage']}"

	# 6. Tier tag conflict (e.g. Pro vs standard, Plus vs Lite)
	if specs_a["tier_tag"] and specs_b["tier_tag"] and specs_a["tier_tag"] != specs_b["tier_tag"]:
		return True, f"Tier tag conflict: {specs_a['tier_tag']} vs {specs_b['tier_tag']}"

	return False, ""


# Test with the exact user screenshot example!
title_amz = "Acer Smartchoice Aspire One, AMD Ryzen 5-40, Office 2024 + M365 Basic, 8GB LPDDR5 RAM/ 512GB SSD,..."
title_fk = "Acer Aspire 15 AMD Ryzen 3 Quad Core 7330U - (8 GB/512 GB SSD/Windows 11 Home) AS15 42 / A325 42 Thin..."

specs_a = extract_hardware_signatures(title_amz)
specs_b = extract_hardware_signatures(title_fk)

print("Specs Amazon:", specs_a)
print("Specs Flipkart:", specs_b)

is_conflict, reason = are_specs_conflicting(specs_a, specs_b)
print("\nIs Conflict:", is_conflict)
print("Reason:", reason)
assert is_conflict, "Should have flagged conflict between Ryzen 5 Aspire One and Ryzen 3 Aspire 15!"

# Test with true identical model
title_amz_true = "Acer Aspire Lite 12th Gen Intel Core i3-1215U (8 GB RAM/512 GB SSD/Windows 11 Home)"
title_fk_true = "Acer Aspire Lite 12th Gen Intel Core i3-1215U - (8 GB/512 GB SSD/Windows 11 Home) AL15-52"

specs_true_a = extract_hardware_signatures(title_amz_true)
specs_true_b = extract_hardware_signatures(title_fk_true)
print("\nTrue match Amazon:", specs_true_a)
print("True match Flipkart:", specs_true_b)
is_conflict_true, reason_true = are_specs_conflicting(specs_true_a, specs_true_b)
print("True Match Conflict:", is_conflict_true, reason_true)
assert not is_conflict_true, "True match should have NO conflict!"

print("\nALL HARDWARE SPEC TESTS PASSED!")
