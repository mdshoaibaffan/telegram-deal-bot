import os
import requests
import random
import time
import html
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@LootDealsDaily2026"

AFFILIATE_TAG = "dailykitchenh-21"

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Accept-Language": "en-US,en;q=0.9",
"Accept-Encoding": "gzip, deflate, br",
"Connection": "keep-alive"
}

posted_links = set()
current_day = datetime.now().day

# Sequential deal queue
deal_queue = []


# -----------------------------------
# TELEGRAM FUNCTIONS
# -----------------------------------

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

    print("Telegram API response:", data)

    if not data.get("ok"):
        print("Telegram Error:", data)
        return None

    return data


def pin_message(message_id):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage"

    payload = {
        "chat_id": CHANNEL,
        "message_id": message_id,
        "disable_notification": True
    }

    requests.post(url, data=payload)


# -----------------------------------
# AMAZON SCRAPER
# -----------------------------------

def scrape_amazon_deals():

    urls = [

        "https://www.amazon.in/s?i=electronics&s=price-asc-rank",
        "https://www.amazon.in/s?i=kitchen&s=price-asc-rank",
        "https://www.amazon.in/s?i=computers&s=price-asc-rank",
        "https://www.amazon.in/s?i=home-improvement&s=price-asc-rank",
        "https://www.amazon.in/s?i=toys&s=price-asc-rank"

    ]

    url = random.choice(urls)

    page = requests.get(url, headers=HEADERS, timeout=10)

    soup = BeautifulSoup(page.text, "lxml")

    items = soup.select("div.s-result-item")

    deals = []

    for item in items:

        try:

            asin = item.get("data-asin")

            if asin is None or asin == "":
                continue

            title_tag = item.select_one("h2 span")

            if not title_tag:
                continue

            title = html.escape(title_tag.text.strip())

            link = f"https://www.amazon.in/dp/{asin}?tag={AFFILIATE_TAG}"

            img_tag = item.select_one("img.s-image")

            image = None
            if img_tag:
                image = img_tag.get("src")

            price_tag = item.select_one("span.a-price span.a-offscreen")

            price = None
            if price_tag:
                price = price_tag.text.strip()

            mrp_tag = item.select_one("span.a-price.a-text-price span.a-offscreen")

            mrp = None
            if mrp_tag:
                mrp = mrp_tag.text.strip()

            discount = ""

            if price and mrp:

                try:

                    price_num = float(price.replace("₹","").replace(",",""))
                    mrp_num = float(mrp.replace("₹","").replace(",",""))

                    off = int(((mrp_num - price_num) / mrp_num) * 100)

                    discount = f"🔥 {off}% OFF"

                except:

                    discount = "🔥 Trending Product"

            else:

                discount = "🔥 Trending Product"

            deals.append({
                "title": title,
                "price": price if price else "Check Price",
                "mrp": mrp,
                "discount": discount,
                "link": link,
                "image": image
            })

        except:
            continue

    return deals


# -----------------------------------
# SEQUENTIAL DEAL PICKER
# -----------------------------------

def get_deal():

    global deal_queue

    if not deal_queue:
        deal_queue = scrape_amazon_deals()

    while deal_queue:

        deal = deal_queue.pop(0)

        if deal["link"] not in posted_links:

            posted_links.add(deal["link"])
            return deal

    return None


# -----------------------------------
# MESSAGE FORMAT
# -----------------------------------

def format_message(deal, deal_of_day=False):

    if deal["mrp"]:

        price_block = f"""
💰 <b>Deal Price:</b> {deal['price']}
🏷 <b>MRP:</b> {deal['mrp']}
"""

    else:

        price_block = f"💰 <b>Price:</b> {deal['price']}"

    if deal_of_day:

        message = f"""
🔥 <b>DEAL OF THE DAY</b> 🔥

<b>{deal['title']}</b>

{price_block}

{deal['discount']}

⚡ Limited Time Offer

🛒 <b>Buy Now 👉</b>
{deal['link']}
"""

    else:

        message = f"""
🔥 <b>HOT DEAL ALERT</b>

<b>{deal['title']}</b>

{price_block}

{deal['discount']}

⚠️ Price may increase anytime

🛒 <b>Grab Deal 👉</b>
{deal['link']}
"""

    return message


# -----------------------------------
# MAIN LOOP
# -----------------------------------

print("Bot started...")


deal = get_deal()

if deal:

    msg = format_message(deal, True)

    response = send_photo(deal["image"], msg)

    if response:
        message_id = response["result"]["message_id"]
        pin_message(message_id)
        print("Deal of the day posted and pinned")

else:

    print("No deal found for Deal of the Day")


deal = get_deal()

if deal:

    msg = format_message(deal)

    send_photo(deal["image"], msg)

    print("First extra deal posted")


while True:

    today = datetime.now().day

    if today != current_day:

        posted_links.clear()
        current_day = today
        deal_queue.clear()

    deal = get_deal()

    if deal:

        msg = format_message(deal)

        send_photo(deal["image"], msg)

        print("Posted:", deal["title"])

    else:

        print("No deal found")

    # 2 minute testing interval
    time.sleep(120)
