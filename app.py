from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Permette richieste da qualsiasi origine (per test). Poi puoi sostituire con origins=["https://www.scontify.net"]

def scrape_amazon_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/113.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {"error": "Impossibile accedere alla pagina"}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Titolo prodotto
    title = soup.select_one("#productTitle")
    title_text = title.get_text(strip=True) if title else ""

    # Descrizione breve (bullet points)
    description = ""
    bullets = soup.select("#feature-bullets ul li span")
    if bullets:
        description = " ".join(b.get_text(strip=True) for b in bullets)

    # Immagine principale
    img = soup.select_one("#landingImage")
    img_url = img.get("src") if img else ""

    # Prezzo attuale
    price = soup.select_one("#priceblock_ourprice, #priceblock_dealprice")
    price_text = price.get_text(strip=True) if price else ""

    # Prezzo vecchio / scontato (se presente)
    old_price = soup.select_one(".priceBlockStrikePriceString, .a-text-price")
    old_price_text = old_price.get_text(strip=True) if old_price else ""

    # Coupon testuale o box coupon (esempio molto base)
    coupon = ""
    coupon_box = soup.select_one(".couponBadge")
    if coupon_box:
        coupon = coupon_box.get_text(strip=True)
    else:
        coupon_text = soup.select_one("#vpcButton .a-color-base")
        if coupon_text:
            coupon = coupon_text.get_text(strip=True)

    return {
        "title": title_text,
        "description": description,
        "img_url": img_url,
        "price": price_text,
        "old_price": old_price_text,
        "coupon": coupon
    }

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url") if data else None
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    result = scrape_amazon_data(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
