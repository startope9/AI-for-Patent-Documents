# utils/patent_parser.py
import os
import time
import csv
import random
import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    # 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
    # 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15',
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
]


BASE_URL = "https://www.freepatentsonline.com"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "parsed_patents")
MAX_DOCS = 50
DELAY_BETWEEN_PATENTS = 1.5
MAX_FAILURES = 5

def new_session():
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    })
    return sess

def parse_patent(url, pid, session):
    try:
        print(f"🔎 Fetching patent {pid} from URL: {url}")
        res = session.get(url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        data = {'pid': pid}

        for block in soup.find_all('div', class_='disp_doc2'):
            title_div = block.find('div', class_='disp_elm_title')
            text_div = block.find('div', class_='disp_elm_text')
            if not title_div or not text_div:
                continue

            section = title_div.get_text(strip=True).strip(':')
            content = text_div.get_text(separator=' ', strip=True)

            # Only keep relevant patent sections
            if section in {"Abstract", "Claims", "Description"}:
                data[section] = content

        if not {"Abstract", "Claims", "Description"} & data.keys():
            print(f"⚠️ No core sections found for {pid}, skipping.")
            return None

        return data

    except Exception as e:
        print(f"❌ Failed to parse patent {pid}: {e}")
        return None


def get_patent_ids(query, page, session):
    url = f"{BASE_URL}/result.html?p={page}&sort=relevance&srch=top&query_txt={query}&submit=&patents_us=on"
    try:
        print(f"📄 Fetching patent ID list for topic '{query}', page {page}...")
        res = session.get(url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        td_list = soup.find_all('td', attrs={'width': '15%', 'valign': 'top'})
        ids = [td.get_text(strip=True) for td in td_list if td.get_text(strip=True)]
        print(f"✅ Found {len(ids)} patent IDs on page {page}")
        return ids
    except Exception as e:
        print(f"⚠️ Failed to fetch patent IDs on page {page}: {e}")
        return []

def parse_and_save_topic(query: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, f"{query}_50patents.csv")
    if os.path.exists(filename):
        print(f"📂 File already exists: {filename}")
        return filename  # Already parsed

    print(f"🚀 Starting parsing for topic: {query}")
    parsed_docs = []
    session = new_session()
    page = 1
    failures = 0

    while len(parsed_docs) < MAX_DOCS and failures < MAX_FAILURES:
        ids = get_patent_ids(query, page, session)
        if not ids:
            failures += 1
            print(f"❌ No IDs found on page {page}. Consecutive failures: {failures}")
            page += 1
            continue

        for pid in ids:
            print(f"parsing {pid}....")
            if len(parsed_docs) >= MAX_DOCS:
                break
            if pid.startswith("US"):
                url = f"{BASE_URL}/{pid[2:6]}/{pid[6:]}.html"
                real_pid = pid[2:]
            else:
                url = f"{BASE_URL}/{pid}.html"
                real_pid = pid
            parsed = parse_patent(url, real_pid, session)
            if parsed:
                parsed_docs.append(parsed)
                print(f"✅ Parsed {real_pid}. Total parsed: {len(parsed_docs)} / {MAX_DOCS}")
            time.sleep(DELAY_BETWEEN_PATENTS)
        page += 1

    if parsed_docs:
        print(f"💾 Saving {len(parsed_docs)} patents to CSV: {filename}")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=sorted(set().union(*(d.keys() for d in parsed_docs))),
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            for row in parsed_docs:
                writer.writerow(row)
    else:
        print("⚠️ No patents were successfully parsed.")

    return filename
