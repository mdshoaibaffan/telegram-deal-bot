import os
import requests
import time
import html
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@LootDealsDaily2026"

AFFILIATE_TAG = "dailykitchenh-21"

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
"Accept-Language": "en-US,en;q=0.9"
}

posted_links = set()
last_pinned_message = None

categories = [

"https://www.amazon.in/gp/bestsellers",
"https://www.amazon.in/gp/bestsellers/electronics",
"https://www.amazon.in/gp/bestsellers/books",
"https://www.amazon.in/gp/bestsellers/kitchen",
"https://www.amazon.in/gp/bestsellers/shoes",
"https://www.amazon.in/gp/bestsellers/beauty",
"https://www.amazon.in/gp/bestsellers/toys",
"https://www.amazon.in/gp/bestsellers/sports"

]


# TELEGRAM

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

    print("Telegram:", data)

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

            items = soup.select(".zg-grid-general-faceout")

            for item in items:

                title_tag = item.select_one(
                    "div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1"
                )

                if not title_tag:
                    continue

                title = html.escape(title_tag.text.strip())

                link_tag = item.select_one("a.a-link-normal")

                if not link_tag:
                    continue

                product_link = "https://www.amazon.in" + link_tag.get("href")

                if product_link in posted_links:
                    continue

                image_tag = item.select_one("img")

                image = image_tag.get("src") if image_tag else None


                # OPEN PRODUCT PAGE

                product_page = requests.get(product_link, headers=HEADERS, timeout=10)

                product_soup = BeautifulSoup(product_page.text, "lxml")

                price_tag = product_soup.select_one(
                    "#priceblock_dealprice, #priceblock_ourprice, .a-price .a-offscreen"
                )

                mrp_tag = product_soup.select_one(
                    ".priceBlockStrikePriceString, .a-text-price .a-offscreen"
                )

                if not price_tag:
                    continue

                price = price_tag.text.strip()

                mrp = mrp_tag.text.strip() if mrp_tag else None

                discount = None

                try:

                    price_num = float(price.replace("₹","").replace(",",""))

                    if mrp:

                        mrp_num = float(mrp.replace("₹","").replace(",",""))

                        discount = int(((mrp_num - price_num) / mrp_num) * 100)

                except:
                    pass

                deals.append({
                    "title": title,
                    "price": price,
                    "mrp": mrp,
                    "discount": discount,
                    "link": product_link + f"?tag={AFFILIATE_TAG}",
                    "image": image
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

    message = f"""
🔥 <b>HOT DEAL</b>

<b>{deal['title']}</b>

{price_block}

🛒 <b>Buy Now 👉</b>
{deal['link']}

#AmazonDeal #LootDeal
"""

    return message


# MAIN LOOP

print("Bot started")

while True:

    deals = scrape_deals()

    print("Deals found:", len(deals))

    for deal in deals:

        posted_links.add(deal["link"])

        msg = format_message(deal)

        response = send_photo(deal["image"], msg)

        if response and deal["discount"] and deal["discount"] >= 90:

            pin_message(response["result"]["message_id"])

        break

    time.sleep(1800)
