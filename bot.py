import os
import requests
import time
import json
import html
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@LootDealsDaily2026"

AFFILIATE_TAG = "dailykitchenh-21"

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
"Accept-Language": "en-US,en;q=0.9"
}

price_file = "price_history.json"

posted_links = set()
last_pinned_message = None


categories = [

"https://www.amazon.in/gp/bestsellers",
"https://www.amazon.in/gp/bestsellers/electronics",
"https://www.amazon.in/gp/bestsellers/kitchen",
"https://www.amazon.in/gp/bestsellers/books",
"https://www.amazon.in/gp/bestsellers/shoes",
"https://www.amazon.in/gp/movers-and-shakers",
"https://www.amazon.in/deals"

]


# -------------------------
# PRICE DATABASE
# -------------------------

def load_prices():

    try:
        with open(price_file,"r") as f:
            return json.load(f)
    except:
        return {}

def save_prices(data):

    with open(price_file,"w") as f:
        json.dump(data,f)


price_db = load_prices()


# -------------------------
# TELEGRAM
# -------------------------

def send_photo(photo,caption):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    payload={
    "chat_id":CHANNEL,
    "photo":photo,
    "caption":caption,
    "parse_mode":"HTML"
    }

    r=requests.post(url,data=payload)

    data=r.json()

    print(data)

    if not data.get("ok"):
        return None

    return data


def pin_message(message_id):

    global last_pinned_message

    if last_pinned_message:

        requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/unpinChatMessage",
        data={"chat_id":CHANNEL,"message_id":last_pinned_message}
        )

    requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage",
    data={"chat_id":CHANNEL,"message_id":message_id}
    )

    last_pinned_message=message_id


# -------------------------
# SCRAPER
# -------------------------

def scrape_products():

    products=[]

    for url in categories:

        try:

            page=requests.get(url,headers=HEADERS,timeout=10)

            soup=BeautifulSoup(page.text,"lxml")

            items=soup.select("a.a-link-normal")

            for link in items:

                href=link.get("href")

                if not href:
                    continue

                if "/dp/" not in href:
                    continue

                asin=href.split("/dp/")[1][:10]

                product_link=f"https://www.amazon.in/dp/{asin}"

                if product_link in posted_links:
                    continue

                products.append(product_link)

        except:
            continue

    return list(set(products))


# -------------------------
# PRODUCT DETAILS
# -------------------------

def get_product_details(url):

    try:

        page=requests.get(url,headers=HEADERS,timeout=10)

        soup=BeautifulSoup(page.text,"lxml")

        title_tag=soup.select_one("#productTitle")

        if not title_tag:
            return None

        title=html.escape(title_tag.text.strip())

        price_tag=soup.select_one(".a-price .a-offscreen")

        if not price_tag:
            return None

        price=price_tag.text.strip()

        price_num=float(price.replace("₹","").replace(",",""))

        mrp_tag=soup.select_one(".priceBlockStrikePriceString")

        mrp=None
        discount=None

        if mrp_tag:

            mrp=mrp_tag.text.strip()

            try:

                mrp_num=float(mrp.replace("₹","").replace(",",""))

                discount=int(((mrp_num-price_num)/mrp_num)*100)

            except:
                pass

        img=soup.select_one("#landingImage")

        image=img.get("src") if img else None

        return {
        "title":title,
        "price":price,
        "price_num":price_num,
        "mrp":mrp,
        "discount":discount,
        "image":image,
        "link":url+f"?tag={AFFILIATE_TAG}",
        "asin":url.split("/dp/")[1]
        }

    except:

        return None


# -------------------------
# DEAL DETECTION
# -------------------------

def detect_best_deal():

    links=scrape_products()

    deals=[]

    for link in links[:20]:

        data=get_product_details(link)

        if not data:
            continue

        asin=data["asin"]

        price=data["price_num"]

        old_price=price_db.get(asin)

        drop=None

        if old_price:

            drop=int(((old_price-price)/old_price)*100)

        price_db[asin]=price

        save_prices(price_db)


        score=0

        if data["discount"]:
            score=data["discount"]

        if drop:
            score=max(score,drop)

        if score>=40:
            deals.append((score,data))

    if not deals:
        return None

    deals.sort(reverse=True,key=lambda x:x[0])

    return deals[0][1]


# -------------------------
# MESSAGE FORMAT
# -------------------------

def format_message(deal):

    price_block=f"💰 <b>Price:</b> {deal['price']}"

    if deal["mrp"]:
        price_block+=f"\n🏷 <b>MRP:</b> {deal['mrp']}"

    if deal["discount"]:
        price_block+=f"\n🔥 <b>{deal['discount']}% OFF</b>"

    message=f"""
🔥 <b>HOT DEAL</b>

<b>{deal['title']}</b>

{price_block}

🛒 <b>Buy Now 👉</b>
{deal['link']}

#AmazonDeal #LootDeal
"""

    return message


# -------------------------
# MAIN LOOP
# -------------------------

print("Deal bot started")

while True:

    deal=detect_best_deal()

    if deal:

        posted_links.add(deal["link"])

        msg=format_message(deal)

        response=send_photo(deal["image"],msg)

        if response and deal["discount"] and deal["discount"]>=90:

            pin_message(response["result"]["message_id"])

    else:

        print("No strong deal found")

    time.sleep(1800)
