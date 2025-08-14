import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

BASE_URL = "https://en.wikipedia.org"

# ==============================
url = "https://en.wikipedia.org/wiki/List_of_Nintendo_Switch_games_(Q%E2%80%93Z)"
response = requests.get(url, timeout=10)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'lxml')

table = soup.find('table', class_='wikitable plainrowheaders sortable')
elements = []

for row in table.find_all('tr')[1:]:  # bỏ dòng tiêu đề
    try:
        game_cell = row.find('th')
        game_name = game_cell.get_text(strip=True)
        game_link = game_cell.find('a')['href'] if game_cell.find('a') else None

        cells = row.find_all('td')
        developer = cells[0].get_text(strip=True) if len(cells) > 0 else ""
        publisher = cells[1].get_text(strip=True) if len(cells) > 1 else ""
        release_jp = cells[2].get_text(strip=True) if len(cells) > 2 else ""

        elements.append([game_name, game_link, developer, publisher, release_jp])
    except Exception as e:
        print("Lỗi khi xử lý 1 dòng:", e)

# ==============================
df_games = pd.DataFrame(elements, columns=["Title", "Link", "Developer", "Publisher", "Release_JP"])

# ==============================
plots = []
for idx, row in df_games.iterrows():
    if not row["Link"]:
        plots.append(None)
        continue

    game_url = BASE_URL + row["Link"]
    try:
        r = requests.get(game_url, timeout=10)
        r.raise_for_status()
        soup_game = BeautifulSoup(r.text, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối {game_url}: {e}")
        plots.append(None)
        continue

    text = ""
    for section in soup_game.find_all('h2'):
        if section.text.strip().startswith(("Gameplay", "Plot", "Game-play")):
            for element in section.next_siblings:
                if element.name and element.name.startswith('h'):
                    break
                elif element.name == 'p':
                    text += element.get_text(" ", strip=True) + " "
    plots.append(text.strip() if text else None)

    time.sleep(0.5)

# ==============================
plots_clean = []
for t in plots:
    if t:
        t = re.sub(r'\[.*?\]', '', t)  # xóa [1], [citation needed], ...
        plots_clean.append(t.strip())
    else:
        plots_clean.append(None)

df_games["Plots"] = plots_clean

# ==============================
df_games = df_games[df_games["Title"] != "Untitled"]
df_games.to_csv("Games_dataset.csv", index=False, encoding="utf-8-sig")

print("Done")
