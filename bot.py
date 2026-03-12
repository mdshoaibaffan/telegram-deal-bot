import os
import requests
import time
import html
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@LootDealsDaily2026"

AFFILIATE_TAG = "dailykitchenh-21"

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
"Accept-Language": "en-US,en;q=0.9"
}

posted_links = set()
last_pinned_message = None


categories = [

"https://www.amazon.in/s?i=fashion",
"https://www.amazon.in/s?i=shoes",
"https://www.amazon.in/s?i=electronics",
"https://www.amazon.in/s?i=stripbooks",
"https://www.amazon.in/s?i=beauty",
"https://www.amazon.in/s?i=kitchen",
"https://www.amazon.in/s?i=computers",
"https://www.amazon.in/s?i=toys",
"https://www.amazon.in/s?i=sports",
"https://www.amazon.in/s?i=office-products",
"https://www.amazon.in/s?i=baby",
"https://www.amazon.in/s?i=pets",
"https://www.amazon.in/s?i=grocery",
"https://www.amazon.in/s?i=tools",
"https://www.amazon.in/s?i=garden"

]


# TELEGRAM FUNCTIONS

def send_photo(photo, caption):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    payload = {
        "chat_id": CHANNEL,
        "photo": photo,
        "caption": caption,
        "parse_mode": "HTML"
    }

    response = requests.post(url, data=payload)

    data = response.json()

    print(data)

    if not data.get("ok"):
        return None

    return data


def pin_message(message_id):

    global last_pinned_message

    if last_pinned_message:

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/unpinChatMessage",
            data={"chat_id": CHANNEL, "message_id": last_pinned_message}
        )

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage",
        data={"chat_id": CHANNEL, "message_id": message_id}
    )

    last_pinned_message = message_id


# SCRAPER

def scrape_deals():

    deals = []

    for url in categories:

        try:

            page = requests.get(url, headers=HEADERS, timeout=10)

            soup = BeautifulSoup(page.text, "lxml")

            items = soup.select("div.s-result-item")

            for item in items:

                asin = item.get("data-asin")

                if not asin:
                    continue

                title_tag = item.select_one("h2 span")

                if not title_tag:
                    continue

                title = html.escape(title_tag.text.strip())

                link = f"https://www.amazon.in/dp/{asin}?tag={AFFILIATE_TAG}"

                if link in posted_links:
                    continue

                img_tag = item.select_one("img.s-image")

                image = img_tag.get("src") if img_tag else None

                price_tag = item.select_one("span.a-price span.a-offscreen")

                if not price_tag:
                    continue

                price = price_tag.text.strip()

                mrp_tag = item.select_one("span.a-price.a-text-price span.a-offscreen")

                mrp = mrp_tag.text.strip() if mrp_tag else None

                discount = None

                if mrp:

                    try:

                        price_num = float(price.replace("₹","").replace(",",""))
                        mrp_num = float(mrp.replace("₹","").replace(",",""))

                        discount = int(((mrp_num - price_num) / mrp_num) * 100)

                    except:
                        pass

                deals.append({
                    "title": title,
                    "price": price,
                    "mrp": mrp,
                    "discount": discount,
                    "link": link,
                    "image": image,
                    "category": url
                })

        except:
            continue

    return deals


# MESSAGE FORMAT

def format_message(deal):

    price_block = f"💰 <b>Price:</b> {deal['price']}"

    if deal["mrp"]:
        price_block += f"\n🏷 <b>MRP:</b> {deal['mrp']}"

    if deal["discount"]:
        price_block += f"\n🔥 <b>{deal['discount']}% OFF</b>"

    category_link = ""

    if "fashion" in deal["category"] or "shoes" in deal["category"]:

        category_link = "\n\n👕 <b>More Fashion Deals:</b>\nhttps://www.amazon.in/s?i=fashion"

    message = f"""
🔥 <b>HOT DEAL</b>

<b>{deal['title']}</b>

{price_block}

🛒 <b>Buy Now 👉</b>
{deal['link']}

{category_link}

#AmazonDeal #LootDeal
"""

    return message


# MAIN LOOP

print("Bot started")

while True:

    deals = scrape_deals()

    for deal in deals:

        posted_links.add(deal["link"])

        msg = format_message(deal)

        response = send_photo(deal["image"], msg)

        if response and deal["discount"] and deal["discount"] >= 90:

            pin_message(response["result"]["message_id"])

        break

    time.sleep(1800)
