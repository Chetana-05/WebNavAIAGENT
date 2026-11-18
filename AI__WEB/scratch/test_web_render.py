import json
from web_agent.web import _render_page

sample_result = {
    "status": "success",
    "result": {
        "goal": "laptops under 50000",
        "amazon_products": [
            {
                "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U (8 GB RAM/512 GB SSD/Windows 11 Home)",
                "price": "₹31,990",
                "numeric_price": 31990.0,
                "mrp": "₹52,990",
                "discount": "40% off",
                "rating": "4.0",
                "numeric_rating": 4.0,
                "reviews": "1,245",
                "image": "https://m.media-amazon.com/images/I/71czGb00k5L._AC_UY218_.jpg",
                "url": "https://amazon.in/dp/B0C46DW5F9",
                "site": "Amazon",
                "brand": "Acer"
            }
        ],
        "flipkart_products": [
            {
                "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U - (8 GB/512 GB SSD/Windows 11 Home) AL15-52",
                "price": "₹29,790",
                "numeric_price": 29790.0,
                "mrp": "₹50,990",
                "discount": "41% off",
                "rating": "4.2",
                "numeric_rating": 4.2,
                "reviews": "820",
                "image": "https://rukminim2.flixcart.com/image/312/312/xif0q/computer/u/9/s/-original-imaguyyfgq8hszhz.jpeg",
                "url": "https://flipkart.com/p/itm123",
                "site": "Flipkart",
                "brand": "Acer"
            }
        ],
        "croma_products": [
            {
                "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U (8GB RAM, 512GB SSD, Windows 11 Home)",
                "price": "₹30,990",
                "numeric_price": 30990.0,
                "mrp": "₹52,990",
                "discount": "41% off",
                "rating": "4.1",
                "numeric_rating": 4.1,
                "reviews": "1,120",
                "image": "https://m.media-amazon.com/images/I/71czGb00k5L._AC_UY218_.jpg",
                "url": "https://croma.com/p/123",
                "site": "Croma",
                "brand": "Acer"
            }
        ],
        "ajio_products": [
            {
                "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U (8GB RAM, 512GB SSD, Reliance Edition)",
                "price": "₹31,490",
                "numeric_price": 31490.0,
                "mrp": "₹52,990",
                "discount": "41% off",
                "rating": "4.1",
                "numeric_rating": 4.1,
                "reviews": "720",
                "image": "https://m.media-amazon.com/images/I/71czGb00k5L._AC_UY218_.jpg",
                "url": "https://ajio.com/p/123",
                "site": "Ajio",
                "brand": "Acer"
            }
        ],
        "comparison": {
            "cheaper_store_overall": "Flipkart",
            "avg_price_gap": "₹2,200",
            "same_product_matches": [
                {
                    "brand": "Acer",
                    "verified_specs": "Acer · Core i3 · 8GB RAM · 512GB SSD",
                    "amazon": {
                        "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U (8 GB RAM/512 GB SSD/Windows 11 Home)",
                        "price": "₹31,990",
                        "numeric_price": 31990.0,
                        "mrp": "₹52,990",
                        "discount": "40% off",
                        "rating": "4.0",
                        "numeric_rating": 4.0,
                        "reviews": "1,245",
                        "image": "https://m.media-amazon.com/images/I/71czGb00k5L._AC_UY218_.jpg",
                        "url": "https://amazon.in/dp/B0C46DW5F9",
                        "site": "Amazon",
                        "brand": "Acer"
                    },
                    "flipkart": {
                        "title": "Acer Aspire Lite 12th Gen Intel Core i3-1215U - (8 GB/512 GB SSD/Windows 11 Home) AL15-52",
                        "price": "₹29,790",
                        "numeric_price": 29790.0,
                        "mrp": "₹50,990",
                        "discount": "41% off",
                        "rating": "4.2",
                        "numeric_rating": 4.2,
                        "reviews": "820",
                        "image": "https://rukminim2.flixcart.com/image/312/312/xif0q/computer/u/9/s/-original-imaguyyfgq8hszhz.jpeg",
                        "url": "https://flipkart.com/p/itm123",
                        "site": "Flipkart",
                        "brand": "Acer"
                    },
                    "similarity": 82.5,
                    "price_difference": "₹2,200",
                    "numeric_difference": 2200.0,
                    "percent_difference": "6.9%",
                    "winner": "Flipkart",
                    "savings_text": "Save ₹2,200 (6.9%) on Flipkart"
                }
            ],
            "cross_site_matches": []
        },
        "products": [
            {"title": "Acer Aspire Lite", "site": "Amazon", "price": "₹31,990", "numeric_price": 31990.0, "numeric_rating": 4.0},
            {"title": "Acer Aspire Lite", "site": "Flipkart", "price": "₹29,790", "numeric_price": 29790.0, "numeric_rating": 4.2},
            {"title": "Acer Aspire Lite", "site": "Croma", "price": "₹30,990", "numeric_price": 30990.0, "numeric_rating": 4.1},
            {"title": "Acer Aspire Lite", "site": "Ajio", "price": "₹31,490", "numeric_price": 31490.0, "numeric_rating": 4.1}
        ]
    }
}

html = _render_page(sample_result, selected_limit="all")
assert "Compare Same Product (1)" in html, "Compare Same Product tab missing!"
assert "Croma" in html, "Croma missing!"
assert "Ajio" in html, "Ajio missing!"
assert "Amazon" in html, "Amazon missing!"
assert "Flipkart" in html, "Flipkart missing!"
assert "Core i3 · 8GB RAM · 512GB SSD" in html, "Verified specs missing!"
print("SUCCESS: 4-Store web rendering tested and passed cleanly!")
