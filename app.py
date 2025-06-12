from flask import Flask, request, jsonify
from flask_cors import CORS
from amazon_paapi import AmazonApi
import os
import re

app = Flask(__name__)
CORS(app)

# Config Amazon PA API
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("AMAZON_REGION", "IT")

if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, ASSOCIATE_TAG]):
    raise EnvironmentError("Chiavi Amazon PA API mancanti.")

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

    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not match:
        return jsonify({"error": "ASIN non trovato nell'URL"}), 400
    asin = match.group(1)

    try:
        products = amazon.get_items(asin)
        if not products or len(products) == 0:
            return jsonify({"error": "Prodotto non trovato"}), 404

        product = products[0]

        title = ""
        description = ""
        img_url = ""
        price = ""
        old_price = ""
        coupon = ""  # Placeholder (non disponibile via API)

        if product.item_info:
            if product.item_info.title:
                title = product.item_info.title.display_value

            if product.item_info.product_description and product.item_info.product_description.display_value:
                description = product.item_info.product_description.display_value
            elif product.item_info.features and product.item_info.features.display_values:
                description = product.item_info.features.display_values[0]

        if product.images and product.images.primary and product.images.primary.large:
            img_url = product.images.primary.large.url

        if product.offers and product.offers.listings:
            offer = product.offers.listings[0]
            if offer.price:
                price = f"{offer.price.amount} {offer.price.currency}"
            if offer.saving_basis:
                old_price = f"{offer.saving_basis.amount} {offer.saving_basis.currency}"

        response = {
            "title": title,
            "description": description,
            "img_url": img_url,
            "price": price,
            "old_price": old_price,
            "coupon": coupon
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Errore Amazon PA API: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
