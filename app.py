from flask import Flask, request, jsonify
from amazon_paapi import AmazonApi
import os
import traceback

app = Flask(__name__)

# Config Amazon PA API
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("AMAZON_REGION", "IT")

print(f"AWS_ACCESS_KEY: {AWS_ACCESS_KEY}")
print(f"ASSOCIATE_TAG: {ASSOCIATE_TAG}")
print(f"REGION: {REGION}")

amazon = AmazonApi(
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
    ASSOCIATE_TAG,
    REGION
)

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    import re
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not match:
        return jsonify({"error": "URL non valido o ASIN non trovato"}), 400

    asin = match.group(1)

    try:
        products = amazon.get_items(asin)
        if not products or len(products) == 0:
            return jsonify({"error": "Prodotto non trovato"}), 404

        product = products[0]

        response = {
            "title": product.title,
            "description": product.features[0] if product.features else "",
            "img_url": product.images[0].url if product.images else "",
            "price": product.price_and_currency.price if product.price_and_currency else "",
            "old_price": "",
            "coupon": ""
        }
        return jsonify(response)

    except Exception as e:
        # Stampa stacktrace completo nei log
        traceback.print_exc()
        return jsonify({"error": f"Errore Amazon PA API: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
