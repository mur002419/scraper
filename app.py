from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

def scrape_amazon_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    def extract(selector):
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    return {
        "title": extract("#productTitle"),
        "description": extract("#feature-bullets"),
        "img_url": (soup.select_one("#landingImage") or {}).get("src", ""),
        "price": extract(".a-price .a-offscreen"),
        "old_price": extract(".priceBlockStrikePriceString"),
        "coupon": extract(".couponBadge, .coupon, .savingsBadgeMessage")
    }

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        result = scrape_amazon_data(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
