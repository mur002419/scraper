from flask import Flask, request, jsonify
from amazon_paapi import AmazonApi
import os
import re

app = Flask(__name__)

# Config Amazon PA API
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("AMAZON_REGION", "IT")

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

    # Estrai ASIN dall'URL Amazon
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not match:
        return jsonify({"error": "URL non valido o ASIN non trovato"}), 400
    asin = match.group(1)

    try:
        products = amazon.get_items(asin)
        if not products or len(products) == 0:
            return jsonify({"error": "Prodotto non trovato"}), 404

        product = products[0]

        # Estrazione dati con check per evitare errori
        title = ""
        description = ""
        img_url = ""
        price = ""

        if product.item_info and product.item_info.title:
            title = product.item_info.title.display_value

        if product.item_info and product.item_info.features and product.item_info.features.display_values:
            description = product.item_info.features.display_values[0]

        if product.images and product.images.primary and product.images.primary.large:
            img_url = product.images.primary.large.url

        if product.offers and product.offers.listings:
            offer = product.offers.listings[0]
            if offer.price:
                price = f"{offer.price.amount} {offer.price.currency}"

        response = {
            "title": title,
            "description": description,
            "img_url": img_url,
            "price": price,
            "old_price": "",  # Non disponibile direttamente da PA API
            "coupon": ""      # Non disponibile direttamente da PA API
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Errore Amazon PA API: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
