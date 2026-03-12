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

posted_links=set()
last_pinned=None


categories=[

"https://www.amazon.in/gp/bestsellers",
"https://www.amazon.in/gp/bestsellers/electronics",
"https://www.amazon.in/gp/bestsellers/kitchen",
"https://www.amazon.in/gp/bestsellers/books",
"https://www.amazon.in/gp/bestsellers/shoes",
"https://www.amazon.in/gp/movers-and-shakers",
"https://www.amazon.in/deals"

]


# -------------------------
# PRICE HISTORY
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

price_db=load_prices()


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


def pin_message(msg_id):

    global last_pinned

    if last_pinned:

        requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/unpinChatMessage",
        data={"chat_id":CHANNEL,"message_id":last_pinned}
        )

    requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage",
    data={"chat_id":CHANNEL,"message_id":msg_id}
    )

    last_pinned=msg_id


# -------------------------
# SCRAPE PRODUCT LINKS
# -------------------------

def scrape_products():

    links=[]

    for url in categories:

        try:

            page=requests.get(url,headers=HEADERS,timeout=10)

            soup=BeautifulSoup(page.text,"lxml")

            for a in soup.select("a.a-link-normal"):

                href=a.get("href")

                if href and "/dp/" in href:

                    asin=href.split("/dp/")[1][:10]

                    link=f"https://www.amazon.in/dp/{asin}"

                    links.append(link)

        except:
            continue

    return list(set(links))


# -------------------------
# PRODUCT DETAILS
# -------------------------

def get_product(link):

    try:

        page=requests.get(link,headers=HEADERS,timeout=10)

        soup=BeautifulSoup(page.text,"lxml")

        title=soup.select_one("#productTitle")

        if not title:
            return None

        title=html.escape(title.text.strip())

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

        asin=link.split("/dp/")[1]

        return{
        "title":title,
        "price":price,
        "price_num":price_num,
        "mrp":mrp,
        "discount":discount,
        "image":image,
        "link":link+f"?tag={AFFILIATE_TAG}",
        "asin":asin
        }

    except:
        return None


# -------------------------
# DEAL DETECTOR
# -------------------------

def detect_deal():

    links=scrape_products()

    price_drop_deals=[]
    discount_deals=[]

    for link in links[:50]:

        data=get_product(link)

        if not data:
            continue

        asin=data["asin"]

        price=data["price_num"]

        old_price=price_db.get(asin)

        drop=None

        if old_price:

            drop=int(((old_price-price)/old_price)*100)

            if drop>=25:

                price_drop_deals.append((drop,data))

        price_db[asin]=price

        if data["discount"]:

            discount_deals.append((data["discount"],data))

    save_prices(price_db)


    # PRIORITY 1 → PRICE DROP

    if price_drop_deals:

        price_drop_deals.sort(reverse=True,key=lambda x:x[0])

        return price_drop_deals[0][1]


    # PRIORITY 2 → HIGHEST DISCOUNT

    if discount_deals:

        discount_deals.sort(reverse=True,key=lambda x:x[0])

        return discount_deals[0][1]

    return None


# -------------------------
# MESSAGE FORMAT
# -------------------------

def format_message(deal):

    block=f"💰 <b>Price:</b> {deal['price']}"

    if deal["mrp"]:
        block+=f"\n🏷 <b>MRP:</b> {deal['mrp']}"

    if deal["discount"]:
        block+=f"\n🔥 <b>{deal['discount']}% OFF</b>"

    msg=f"""
🔥 <b>HOT DEAL</b>

<b>{deal['title']}</b>

{block}

🛒 <b>Buy Now 👉</b>
{deal['link']}

#AmazonDeal #LootDeal
"""

    return msg


# -------------------------
# MAIN LOOP
# -------------------------

print("Deal bot started")

while True:

    deal=detect_deal()

    if deal:

        posted_links.add(deal["link"])

        msg=format_message(deal)

        response=send_photo(deal["image"],msg)

        if response and deal["discount"] and deal["discount"]>=90:

            pin_message(response["result"]["message_id"])

    else:

        print("No deals detected")

    time.sleep(1800)
