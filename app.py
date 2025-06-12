from flask import Flask, request, jsonify
from amazon_paapi import AmazonApi
import os
import re

app = Flask(__name__)

# Carica variabili d’ambiente
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("AMAZON_REGION", "IT")

# Verifica credenziali
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, ASSOCIATE_TAG]):
    raise EnvironmentError("⚠️  Devi impostare le variabili AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY e AWS_ASSOCIATE_TAG")

# Inizializza client Amazon PA API
amazon = AmazonApi(AWS_ACCESS_KEY, AWS_SECRET_KEY, ASSOCIATE_TAG, REGION)


@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    # Estrai ASIN
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    if not match:
        return jsonify({"error": "URL non valido o ASIN non trovato"}), 400

    asin = match.group(1)

    try:
        products = amazon.get_items([asin])  # ATTENZIONE: get_items richiede una lista

        if not products:
            return jsonify({"error": "Prodotto non trovato"}), 404

        product = products[0]

        # Estratti con controlli
        title = product.item_info.title.display_value if product.item_info and product.item_info.title else ""
        description = (
            product.item_info.features.display_values[0]
            if product.item_info and product.item_info.features and product.item_info.features.display_values
            else ""
        )
        img_url = (
            product.images.primary.large.url
            if product.images and product.images.primary and product.images.primary.large
            else ""
        )
        price = (
            f"{product.offers.listings[0].price.amount} {product.offers.listings[0].price.currency}"
            if product.offers and product.offers.listings and product.offers.listings[0].price
            else ""
        )

        return jsonify({
            "title": title,
            "description": description,
            "img_url": img_url,
            "price": price,
            "old_price": "",  # Non disponibile via PA API
            "coupon": ""      # Non disponibile via PA API
        })

    except Exception as e:
        return jsonify({"error": f"Errore Amazon PA API: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
