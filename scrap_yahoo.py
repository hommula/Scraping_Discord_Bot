import requests, discord, asyncio, json, os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
SEEN_AUCTION = "seen.json"
seen = set()
ITEM_TO_FIND = "ddh"
def get_auctions(keyword = ""):
    url = f"https://auctions.yahoo.co.jp/search/search?p={keyword}&auccat=2084258814&va={keyword}&fixed=2&is_postage_mode=1&dest_pref_code=13&b=1&n=100&s1=featured"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, headers = headers)
    soup = BeautifulSoup(res.text, "html.parser")

    auctions = []
    auction_list = soup.find_all(class_ = "Product")

    for item in auction_list:
        auction = item.find("a", class_ = "Product__imageLink")
        auction_title = auction.get("data-auction-title")
        auciton_link = auction.get("href")
        auction_image = auction.find("img", class_ = "Product__imageData").get("src")
        auction_id = auction.get("data-auction-id")
        auctions.append({"title": auction_title, "url": auciton_link, "image": auction_image, "id": auction_id})

    return auctions

def load_seen():
    if not os.path.exists(SEEN_AUCTION):
        return set()
    with open(SEEN_AUCTION, "r") as file:
        data = json.load(file)
        return set(data)

def save_seen(seen_set):
    with open(SEEN_AUCTION, "w") as file:
        json.dump(list(seen_set), file, ensure_ascii = False, indent = 2)


def detect_new_auctions(current_auctions):
    seen = load_seen()
    new = []
    for auction in current_auctions:
        if auction["url"] not in seen:
            new.append(auction)
            seen.add(auction["url"])

    save_seen(seen)
    return new

if __name__ == "__main__":
    load_dotenv()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
    
    client = discord.Client(intents = discord.Intents.default())
    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        channel = client.get_channel(CHANNEL_ID)
        while True:
            auctions = get_auctions(ITEM_TO_FIND)
            new = detect_new_auctions(auctions)
            if not new:
                print("There's no new auction.")
            else:
                for new_auction in new:
                    temp_img_path = "/tmp/auction_image.jpg"
                    img_data = requests.get(new_auction["image"]).content
                    with open(temp_img_path, "wb") as image:
                        image.write(img_data)
                    with open(temp_img_path, "rb") as f:
                        picture = discord.File(f)
                        await channel.send(file = picture)
                    msg = f"{new_auction['title']} \n {new_auction['url']} \n {'https://buyee.jp/item/jdirectitems/auction/' + new_auction['id']}"
                    print(f"Found a new auciton {new_auction['title']}")
                    await channel.send(msg)
            await asyncio.sleep(300)
    client.run(DISCORD_TOKEN)