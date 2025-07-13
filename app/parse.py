import os
import time
import csv
import random
import requests
from bs4 import BeautifulSoup

# === Configuration ===
BASE_URL = "https://www.freepatentsonline.com"
OUTPUT_DIR = "parsed_patents"
MAX_DOCS = 50
MAX_FAILURES = 5  # max consecutive failed pages before exit
DELAY_BETWEEN_PATENTS = 1.5  # seconds between requests

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15',
]

os.makedirs(OUTPUT_DIR, exist_ok=True)
parsed_docs = []

# === Session Setup ===
def new_session():
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    })
    return sess

session = new_session()

# === Patent Parsing ===
def parse_patent(url, pid):
    try:
        print(f"🔍 Parsing: {url}")
        res = session.get(url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')

        data = {'pid': pid}
        for div in soup.find_all('div', class_='disp_doc2'):
            title_div = div.find('div', class_='disp_elm_title')
            text_div = div.find('div', class_='disp_elm_text')
            if not title_div or not text_div:
                continue
            title = title_div.get_text(strip=True).replace(":", "")
            text = text_div.get_text(separator=" ", strip=True)
            if title in ["Abstract", "Claims", "Description"]:
                data[title] = text
        return data if len(data) > 1 else None
    except Exception as e:
        print(f"❌ Error parsing {pid}: {e}")
        return None

# === Search Results with Retry + Session Reset ===
def get_patent_ids(query, page, retries=3):
    global session

    url = f"{BASE_URL}/result.html?p={page}&sort=relevance&srch=top&query_txt={query}&submit=&patents_us=on"
    print(f"\n📄 Fetching results: Page {page}")

    for attempt in range(retries):
        try:
            res = session.get(url, timeout=20)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'html.parser')
            td_list = soup.find_all('td', attrs={'width': '15%', 'valign': 'top'})
            return [td.get_text(strip=True) for td in td_list if td.get_text(strip=True)]
        except Exception as e:
            print(f"⚠️ Retry {attempt + 1}/{retries} failed: {e}")
            time.sleep((2 ** attempt) + 1)

    print(f"🔁 Resetting session after failure on page {page}")
    session = new_session()
    return []

# === CSV Export ===
def save_to_csv(query, data):
    filename = os.path.join(OUTPUT_DIR, f"{query}_50patents.csv")
    keys = sorted(set().union(*(d.keys() for d in data)))
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"\n✅ Saved {len(data)} patents to {filename}")

# === Main Driver ===
def main():
    query = input("Enter topic to search patents for: ").strip()
    if not query:
        print("❌ No query entered.")
        return

    page = 1
    consecutive_failures = 0

    while len(parsed_docs) < MAX_DOCS and consecutive_failures < MAX_FAILURES:
        patent_ids = get_patent_ids(query, page, retries=3)
        if not patent_ids:
            print(f"⚠️ Skipping Page {page} — No results or blocked.")
            consecutive_failures += 1
            page += 1
            continue

        consecutive_failures = 0  # reset on success

        for pid in patent_ids:
            if len(parsed_docs) >= MAX_DOCS:
                break
            if pid.startswith("US"):
                url = f"{BASE_URL}/{pid[2:6]}/{pid[6:]}.html"
                real_pid = pid[2:]
            else:
                url = f"{BASE_URL}/{pid}.html"
                real_pid = pid

            parsed = parse_patent(url, real_pid)
            if parsed:
                parsed_docs.append(parsed)
            time.sleep(DELAY_BETWEEN_PATENTS)
        page += 1

    if parsed_docs:
        save_to_csv(query, parsed_docs)
    else:
        print("❌ No documents parsed.")

if __name__ == "__main__":
    main()
