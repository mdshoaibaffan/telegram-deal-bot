import os
import requests
import random
import time
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@LootDealsDaily2026"

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Accept-Language": "en-US,en;q=0.9",
"Accept-Encoding": "gzip, deflate, br",
"Connection": "keep-alive"
}

posted_links = set()
current_day = datetime.now().day


# -----------------------------------
# TELEGRAM FUNCTIONS
# -----------------------------------

def send_message(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    response = requests.post(url, data=payload)

    return response.json()


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
        "https://www.amazon.in/s?k=electronics&tag=dailykitchenh-21",
        "https://www.amazon.in/s?k=kitchen+gadgets&tag=dailykitchenh-21",
        "https://www.amazon.in/s?k=home+utility&tag=dailykitchenh-21",
        "https://www.amazon.in/s?k=mobile+accessories&tag=dailykitchenh-21",
        "https://www.amazon.in/s?k=summer+products&tag=dailykitchenh-21"
    ]

    url = random.choice(urls)

    page = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(page.text, "lxml")

    items = soup.select("div[data-component-type='s-search-result']")

    deals = []

    for item in items:

        try:

            title_tag = item.select_one("h2 span")
            link_tag = item.select_one("h2 a")

            price_tag = item.select_one(".a-price-whole")
            mrp_tag = item.select_one(".a-price.a-text-price span.a-offscreen")

            if not title_tag or not link_tag:
                continue

            title = title_tag.text.strip()

            link = "https://www.amazon.in" + link_tag.get("href")

            if link in posted_links:
                continue

            price = "Check Price"

            if price_tag:
                price = "₹" + price_tag.text.strip()

            discount = ""

            if price_tag and mrp_tag:

                try:

                    price_val = float(price_tag.text.replace(",", ""))
                    mrp_val = float(mrp_tag.text.replace("₹","").replace(",", ""))

                    if mrp_val > price_val:

                        percent = int((mrp_val - price_val) / mrp_val * 100)

                        discount = f"🔥 {percent}% OFF"

                except:
                    pass

            deals.append({
                "title": title,
                "price": price,
                "discount": discount,
                "link": link
            })

        except:
            continue

    return deals


# -----------------------------------
# PICK BEST DEAL
# -----------------------------------

def get_deal():

    deals = scrape_amazon_deals()

    if not deals:
        return None

    deal = random.choice(deals)

    posted_links.add(deal["link"])

    return deal


# -----------------------------------
# MESSAGE FORMAT
# -----------------------------------

def format_message(deal, deal_of_day=False):

    if not deal:
        return None

    if deal_of_day:

        message = f"""
🔥 <b>DEAL OF THE DAY</b> 🔥

<b>{deal['title']}</b>

💰 Price: {deal['price']}

{deal['discount']}

⚡ Limited Time Offer

🛒 <b>Buy Now</b>
{deal['link']}
"""

    else:

        message = f"""
🔥 <b>HOT DEAL ALERT</b>

<b>{deal['title']}</b>

💰 Price: {deal['price']}

{deal['discount']}

⚠️ Price may increase anytime

🛒 Grab Deal 👇
{deal['link']}
"""

    return message


# -----------------------------------
# MAIN LOOP
# -----------------------------------

print("Bot started...")


# Deal of the day first
deal = get_deal()

if deal:

    msg = format_message(deal, True)

    response = send_message(msg)

    message_id = response["result"]["message_id"]

    pin_message(message_id)

    print("Deal of the day posted and pinned")

else:

    print("No deal found for Deal of the Day")


# first extra deal
deal = get_deal()

if deal:

    msg = format_message(deal)

    send_message(msg)

    print("First extra deal posted")

else:

    print("No deal found for First extra post")


# hourly deals
while True:

    today = datetime.now().day

    if today != current_day:

        posted_links.clear()

        current_day = today

        deal = get_deal()

        if deal:

            msg = format_message(deal, True)

            response = send_message(msg)

            message_id = response["result"]["message_id"]

            pin_message(message_id)

            print("New day Deal of the Day posted")

    else:

        deal = get_deal()

        if deal:

            msg = format_message(deal)

            send_message(msg)

            print("Posted:", deal["title"])

        else:

            print("No deal found, retrying next cycle")

    time.sleep(3600)
