import re
from typing import Dict, Any, List, Tuple, Optional

# Test data replicating user's exact case
p_amz_ryzen5 = {
    "title": "Acer Smartchoice Aspire One, AMD Ryzen 5-40, Office 2024 + M365 Basic, 8GB LPDDR5 RAM/ 512GB SSD,...",
    "price": "₹49,990",
    "numeric_price": 49990.0,
    "site": "Amazon",
    "rating": "3.6 ★",
    "numeric_rating": 3.6,
}

p_fk_ryzen3 = {
    "title": "Acer Aspire 15 AMD Ryzen 3 Quad Core 7330U - (8 GB/512 GB SSD/Windows 11 Home) AS15 42 / A325 42 Thin...",
    "price": "₹49,990",
    "numeric_price": 49990.0,
    "site": "Flipkart",
    "rating": "4.1 ★",
    "numeric_rating": 4.1,
}

p_amz_i3 = {
    "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U (8 GB RAM/512 GB SSD/Windows 11 Home)",
    "price": "₹31,990",
    "numeric_price": 31990.0,
    "site": "Amazon",
    "rating": "4.0 ★",
    "numeric_rating": 4.0,
}

p_fk_i3 = {
    "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U - (8 GB/512 GB SSD/Windows 11 Home) AL15-52",
    "price": "₹29,790",
    "numeric_price": 29790.0,
    "site": "Flipkart",
    "rating": "4.2 ★",
    "numeric_rating": 4.2,
}

p_croma_i3 = {
    "title": "Acer Aspire Lite Intel Core i3 12th Gen (8GB RAM, 512GB SSD, Windows 11 Home)",
    "price": "₹30,990",
    "numeric_price": 30990.0,
    "site": "Croma",
    "rating": "4.1 ★",
    "numeric_rating": 4.1,
}

p_fk_ryzen5 = {
    "title": "Acer Aspire One AMD Ryzen 5 Hexa Core 7430U - (8 GB/512 GB SSD/Windows 11 Home)",
    "price": "₹47,990",
    "numeric_price": 47990.0,
    "site": "Flipkart",
    "rating": "4.3 ★",
    "numeric_rating": 4.3,
}

print("Test script initialized.")
