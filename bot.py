import os
import requests
import random
import time
import html
from datetime import datetime
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@LootDealsDaily2026"

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Accept-Language": "en-US,en;q=0.9",
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
# AMAZON SCRAPER (FIXED)
# -----------------------------------

def scrape_amazon_deals():

    urls = [
        "https://www.amazon.in/gp/bestsellers/electronics",
        "https://www.amazon.in/gp/bestsellers/kitchen",
        "https://www.amazon.in/gp/bestsellers/home-improvement",
        "https://www.amazon.in/gp/bestsellers/computers",
        "https://www.amazon.in/gp/bestsellers/toys"
    ]

    url = random.choice(urls)

    page = requests.get(url, headers=HEADERS, timeout=10)

    soup = BeautifulSoup(page.text, "lxml")

    items = soup.select(".zg-grid-general-faceout")

    deals = []

    for item in items:

        try:

            title_tag = item.select_one("div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1")
            link_tag = item.select_one("a.a-link-normal")

            if not title_tag or not link_tag:
                continue

            title = html.escape(title_tag.text.strip())

            link = "https://www.amazon.in" + link_tag.get("href")

            if link in posted_links:
                continue

            price_tag = item.select_one(".p13n-sc-price")

            price = "Check Price"

            if price_tag:
                price = price_tag.text.strip()

            discount = "🔥 Trending Product"

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

    if response:
        message_id = response["result"]["message_id"]
        pin_message(message_id)
        print("Deal of the day posted and pinned")
    else:
        print("Failed to send Deal of the Day")

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

            if response:
                message_id = response["result"]["message_id"]
                pin_message(message_id)
                print("New day Deal of the Day posted")
            else:
                print("Failed to send new Deal of the Day")

    else:

        deal = get_deal()

        if deal:

            msg = format_message(deal)

            send_message(msg)

            print("Posted:", deal["title"])

        else:

            print("No deal found, retrying next cycle")

    time.sleep(3600)
