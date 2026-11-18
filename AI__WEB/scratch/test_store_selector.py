from web_agent.comparer import match_same_products, generate_site_comparison
from web_agent.web import _render_page

amz = [{'title': 'Acer Aspire Lite 13th Gen Intel Core i3-1305U (8GB RAM/512GB SSD)', 'price': '₹31,990', 'numeric_price': 31990, 'rating': '4.1', 'numeric_rating': 4.1, 'site': 'Amazon'}]
fk = [{'title': 'Acer Aspire Lite Intel Core i3 13th Gen - (8 GB/512 GB SSD)', 'price': '₹32,990', 'numeric_price': 32990, 'rating': '4.2', 'numeric_rating': 4.2, 'site': 'Flipkart'}]
croma = [{'title': 'Acer Aspire Lite Intel Core i3 13th Gen Laptop (8GB RAM, 512GB SSD)', 'price': '₹30,990', 'numeric_price': 30990, 'rating': '4.3', 'numeric_rating': 4.3, 'site': 'Croma'}]
ajio = [{'title': 'Acer Aspire Lite Laptop Sleeve Bag', 'price': '₹999', 'numeric_price': 999, 'rating': '4.0', 'numeric_rating': 4.0, 'site': 'Ajio'}]

matches = match_same_products(amz, fk, croma, ajio)
print('Matches found:', len(matches))
if matches:
    m = matches[0]
    print('Winner:', m['winner'])
    print('Savings text:', m['savings_text'].encode('ascii', errors='replace').decode('ascii'))
    print('Croma matched:', m.get('croma') is not None)
    print('Ajio accessory matched:', m.get('ajio') is not None)

comp = generate_site_comparison(amz, fk, croma, ajio)
result = {'result': {'goal': 'Acer Aspire Lite i3', 'products': amz + fk + croma, 'amazon_products': amz, 'flipkart_products': fk, 'croma_products': croma, 'ajio_products': [], 'comparison': comp}}
html_out = _render_page(result)
print('HTML length:', len(html_out))

assert 'chkAmazon' in html_out, "chkAmazon missing"
assert 'chkCroma' in html_out, "chkCroma missing"
assert 'chkAjio' in html_out, "chkAjio missing"
assert 'tool-store-btn' in html_out, "tool-store-btn missing"
assert 'data-site="Croma"' in html_out, "data-site Croma missing"
assert '🏆 Cheaper on Croma!' in html_out, "Winner badge for Croma missing"
assert 'toggleStoreFilter' in html_out, "toggleStoreFilter function missing"
assert 'toggleStoreBtn' in html_out, "toggleStoreBtn function missing"
assert 'activeStores' in html_out, "activeStores state missing"

print('SUCCESS: All assertions passed flawlessly!')
