import requests, discord, asyncio, json, os, io
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

from translate  import translate_text

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

def get_description(url):
    driver = webdriver.Chrome()
    driver.get(url)
    description_div = driver.find_element(By.ID, "description")
    shadow_root_parent = description_div.find_element(By.XPATH, "./section/div/div")
    shadow_root_content = driver.execute_script("""
        const root = arguments[0].shadowRoot;
        const style = Array.from(root.querySelectorAll("Style"))
        .map(s => s.textContent)
        .join("");

        return root.textContent.replace(style, "").trim();
    """, shadow_root_parent)
    driver.quit()
    return shadow_root_content   

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

class AuctionButtonView(discord.ui.View):    
    def __init__(self, auction_data):
        super().__init__(timeout = None)  # No timeout so button stays active
        self.auction_data = auction_data

    @discord.ui.button(label = "Translate Description", style = discord.ButtonStyle.primary, emoji="🔁")
    async def action_button(self, interaction, button):
        # Immediately show "Translating..." and remove the button
        await interaction.response.edit_message(content = f"{interaction.message.content}\n\nTranslating...", view = None)
        try:
            description = get_description(self.auction_data["url"])
            translated_description = translate_text(description)
            await interaction.edit_original_response(content = f"{interaction.message.content}\n\n{translated_description}")
        except Exception as e:
            await interaction.edit_original_response(content = f"{interaction.message.content}\n\nTranslation error: {str(e)}")

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
                pass
            else:
                for new_auction in new:
                    img_data = requests.get(new_auction["image"]).content
                    auction_img = discord.File(io.BytesIO(img_data), filename = "auction_pic.jpg")
                    await channel.send(file = auction_img)
                    msg = f"{new_auction['title']} \n {new_auction['url']} \n {'https://buyee.jp/item/jdirectitems/auction/' + new_auction['id']}"
                    print(f"Found a new auciton {new_auction['title']}") 
                    view = AuctionButtonView(new_auction)
                    await channel.send(msg, view = view, suppress_embeds = True)
            await asyncio.sleep(300)
    client.run(DISCORD_TOKEN)