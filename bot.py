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
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
"Accept-Language": "en-US,en;q=0.9",
"Accept-Encoding": "gzip, deflate, br",
"Connection": "keep-alive"
}

posted_links = set()
deal_queue = []
current_day = datetime.now().day


categories = [

"https://www.amazon.in/s?i=shoes&s=price-asc-rank",
"https://www.amazon.in/s?i=fashion&s=price-asc-rank",
"https://www.amazon.in/s?i=stripbooks&s=price-asc-rank",
"https://www.amazon.in/s?i=beauty&s=price-asc-rank",
"https://www.amazon.in/s?i=kitchen&s=price-asc-rank",
"https://www.amazon.in/s?i=electronics&s=price-asc-rank"

]

category_index = 0


# -----------------------------------
# TELEGRAM
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

    print("Telegram response:", data)

    if not data.get("ok"):
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
# SCRAPER
# -----------------------------------

def scrape_amazon_deals():

    global category_index

    url = categories[category_index]
    category_index = (category_index + 1) % len(categories)

    page = requests.get(url, headers=HEADERS, timeout=10)

    soup = BeautifulSoup(page.text, "lxml")

    items = soup.select("div.s-result-item")

    deals = []

    for item in items:

        try:

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
                "image": image
            })

        except:
            continue

    return deals


# -----------------------------------
# DEAL QUEUE
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

    price_block = f"💰 <b>Price:</b> {deal['price']}"

    if deal["mrp"]:

        price_block += f"\n🏷 <b>MRP:</b> {deal['mrp']}"

    if deal["discount"]:

        price_block += f"\n🔥 <b>{deal['discount']}% OFF</b>"

    hashtags = "\n\n#AmazonDeal #LootDeal #Discount"

    if deal_of_day:

        message = f"""
🔥 <b>DEAL OF THE DAY</b> 🔥

<b>{deal['title']}</b>

{price_block}

🛒 <b>Buy Now 👉</b>
{deal['link']}

{hashtags}
"""

    else:

        message = f"""
🔥 <b>HOT DEAL ALERT</b>

<b>{deal['title']}</b>

{price_block}

🛒 <b>Grab Deal 👉</b>
{deal['link']}

{hashtags}
"""

    return message


# -----------------------------------
# MAIN LOOP
# -----------------------------------

print("Bot started...")


# Deal of the Day
deal = get_deal()

if deal:

    msg = format_message(deal, True)

    response = send_photo(deal["image"], msg)

    if response:
        pin_message(response["result"]["message_id"])


# Second post
deal = get_deal()

if deal:

    msg = format_message(deal)

    send_photo(deal["image"], msg)


while True:

    deal = get_deal()

    if deal:

        msg = format_message(deal)

        send_photo(deal["image"], msg)

        print("Hourly deal posted:", deal["title"])

    else:

        print("No deal found")

    time.sleep(3600)
