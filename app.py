from flask import Flask, request, jsonify
from amazon_paapi import AmazonApi
import os, re, time

app = Flask(__name__)

# Leggi variabili ambiente
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
ASSOCIATE_TAG = os.getenv("AWS_ASSOCIATE_TAG")
REGION = os.getenv("AMAZON_REGION", "IT")

# Verifica credenziali
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, ASSOCIATE_TAG]):
    raise EnvironmentError("⚠️ Imposta AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY e AWS_ASSOCIATE_TAG")

# Inizializza client con delay per evitare throttling
amazon = AmazonApi(AWS_ACCESS_KEY, AWS_SECRET_KEY, ASSOCIATE_TAG, REGION, throttling=1.5)


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
        # Usa la firma singola
        products = amazon.get_items(asin)

        if not products:
            return jsonify({"error": "Prodotto non trovato"}), 404

        product = products[0] if isinstance(products, list) else products

        # Estrai i campi richiesti
        title = product.item_info.title.display_value if product.item_info and product.item_info.title else ""
        description = product.item_info.features.display_values[0] \
            if product.item_info and product.item_info.features and product.item_info.features.display_values else ""
        img_url = product.images.primary.large.url \
            if product.images and product.images.primary and product.images.primary.large else ""
        price = ""
        if product.offers and product.offers.listings:
            offer = product.offers.listings[0]
            if offer.price:
                price = f"{offer.price.amount} {offer.price.currency}"

        return jsonify({
            "title": title,
            "description": description,
            "img_url": img_url,
            "price": price,
            "old_price": "",   # Non disponibile via PA API
            "coupon": ""       # Non disponibile via PA API
        })

    except Exception as e:
        return jsonify({"error": f"Errore Amazon PA API: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
