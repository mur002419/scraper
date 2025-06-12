from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def scrape_amazon_data(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    def extract_text(*selectors):
        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                return el.get_text(strip=True)
        return ""

    def extract_image_src(*selectors):
        for selector in selectors:
            el = soup.select_one(selector)
            if el and el.has_attr("src"):
                return el["src"]
            elif el and el.has_attr("data-a-dynamic-image"):
                # extract image from data-a-dynamic-image attribute
                import json
                try:
                    images = json.loads(el["data-a-dynamic-image"])
                    return list(images.keys())[0]
                except:
                    continue
        return ""

    data = {
        "title": extract_text("#productTitle", "span#title"),
        "description": extract_text("#feature-bullets", "#productDescription"),
        "img_url": extract_image_src("#landingImage", "#imgTagWrapperId img"),
        "price": extract_text("#priceblock_dealprice", "#priceblock_ourprice", ".a-price .a-offscreen"),
        "old_price": extract_text(".priceBlockStrikePriceString", ".a-text-strike"),
        "coupon": extract_text(".couponBadge", ".coupon", ".savingsBadgeMessage", ".a-color-price")
    }
    return data

@app.route("/scrape", methods=["POST"])
def scrape():
    content = request.json
    url = content.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    data = scrape_amazon_data(url)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
