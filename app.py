from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app, origins=["https://www.scontify.net"])  # Sostituisci con il tuo dominio frontend

def scrape_amazon_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {"error": "Impossibile accedere alla pagina"}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Titolo
    title = soup.select_one("#productTitle")
    title_text = title.get_text(strip=True) if title else ""

    # Descrizione: bullet points o fallback
    description = ""
    bullets = soup.select("#feature-bullets ul li span")
    if bullets:
        description = " ".join(b.get_text(strip=True) for b in bullets)
    if not description:
        alt_desc = soup.select_one("#productDescription p, #productDescription")
        if alt_desc:
            description = alt_desc.get_text(strip=True)

    # Immagine
    img = soup.select_one("#landingImage")
    img_url = img.get("src") if img else ""

    # Prezzo attuale
    price_text = ""
    price_selectors = [
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        ".a-price .a-offscreen"  # fallback
    ]
    for selector in price_selectors:
        el = soup.select_one(selector)
        if el:
            price_text = el.get_text(strip=True)
            break

    # Prezzo vecchio
    old_price_text = ""
    old_price_selectors = [
        ".priceBlockStrikePriceString",
        ".a-price.a-text-price .a-offscreen",
        ".a-price .a-text-price .a-offscreen"
    ]
    for selector in old_price_selectors:
        el = soup.select_one(selector)
        if el:
            old_price_text = el.get_text(strip=True)
            break

    # Coupon (se presente)
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
