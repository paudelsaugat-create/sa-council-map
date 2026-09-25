import json
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

# All official South Australian councils
SA_COUNCILS = [
    "Adelaide Hills Council", "Adelaide Plains Council", "Alexandrina Council",
    "Barossa Council", "Barunga West Council", "Berri Barmera Council",
    "Campbelltown City Council", "City of Adelaide", "City of Burnside",
    "City of Charles Sturt", "City of Holdfast Bay", "City of Marion",
    "City of Mitcham", "City of Norwood Payneham and St Peters",
    "City of Norwood Payneham & St Peters", "City of Onkaparinga",
    "City of Playford", "City of Port Adelaide Enfield", "City of Port Lincoln",
    "City of Prospect", "City of Salisbury", "City of Tea Tree Gully",
    "City of Unley", "City of Victor Harbor", "City of West Torrens",
    "City of Whyalla", "Clare and Gilbert Valleys Council", "Cleve District Council",
    "Coorong District Council", "Copper Coast Council", "District Council of Ceduna",
    "District Council of Cleve", "District Council of Coober Pedy",
    "District Council of Elliston", "District Council of Franklin Harbour",
    "District Council of Grant", "District Council of Karoonda East Murray",
    "District Council of Kimba", "District Council of Lower Eyre Peninsula",
    "District Council of Loxton Waikerie", "District Council of Mount Remarkable",
    "District Council of Orroroo Carrieton", "District Council of Peterborough",
    "District Council of Robe", "District Council of Streaky Bay",
    "District Council of Tumby Bay", "District Council of Yankalilla",
    "Flinders Ranges Council", "Kangaroo Island Council", "Kingston District Council",
    "Light Regional Council", "Lower Eyre Council", "Mid Murray Council",
    "Mount Barker District Council", "Mount Gambier City Council", "City of Mount Gambier",
    "Municipal Council of Roxby Downs", "Naracoorte Lucindale Council",
    "Northern Areas Council", "Port Augusta City Council", "Port Pirie Regional Council",
    "Regional Council of Goyder", "Renmark Paringa Council", "Rural City of Murray Bridge",
    "Southern Limestone Coast Council", "Southern Mallee District Council",
    "Tatiara District Council", "Town of Gawler", "Town of Walkerville",
    "Wakefield Regional Council", "Wattle Range Council", "Wudinna District Council",
    "Yorke Peninsula Council"
]

BASE_URL = "https://www.localcouncils.sa.gov.au/careers/job-search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

vacancies_by_council = {}

# Query the job-search engine for all vacancies
for start in range(1, 150, 10):
    params = {
        "collection": "all-councils-employment-push",
        "current_page": "1332517",
        "fmo": "true",
        "meta_status": "live",
        "profile": "careers",
        "query": "!showall",
        "start_rank": str(start),
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    print(f"Fetching: {url}")

        try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as resp:
            status = resp.getcode()
            html = resp.read().decode("utf-8")
            print(f"Status: {status} | Response length: {len(html)} chars")
            print("First 500 chars of response:")
            print(html[:500])
            print("---")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        break

    soup = BeautifulSoup(html, "html.parser")
    found_on_page = 0

    # Every job entry is in a list item or card containing a title and council
    for item in soup.select("li, article, .search-result, .item"):
        # Look for the job title link
        title_link = item.select_one("h2 a, h3 a, h4 a, a[href*='job'], a[href*='employment'], a[target='_blank']")
        if not title_link:
            continue

        raw_title = title_link.get_text(" ", strip=True)
        clean_title = re.sub(r"-\s*opens in a new tab.*", "", raw_title, flags=re.IGNORECASE).strip()

        # Skip site menus and non-job anchors
        if len(clean_title) < 4 or any(
            skip in clean_title.lower()
            for skip in ["job search", "career pathways", "find your council", "sort:", "show:"]
        ):
            continue

        item_text = item.get_text(" ", strip=True)

        # Match against our SA council names
        matched_council = None
        for council in SA_COUNCILS:
            if council.lower() in item_text.lower():
                matched_council = council
                break

        if matched_council:
            href = title_link["href"].strip()
            job_url = href if href.startswith("http") else f"https://www.localcouncils.sa.gov.au{href}"

            if matched_council == "City of Norwood Payneham and St Peters":
                matched_council = "City of Norwood Payneham & St Peters"

            if matched_council not in vacancies_by_council:
                vacancies_by_council[matched_council] = []

            if not any(j["title"] == clean_title for j in vacancies_by_council[matched_council]):
                vacancies_by_council[matched_council].append({
                    "title": clean_title,
                    "url": job_url
                })
                found_on_page += 1

    print(f"Parsed {found_on_page} vacancies from rank {start}.")
    if found_on_page == 0:
        break

with open("sa_vacancies.json", "w", encoding="utf-8") as f:
    json.dump(vacancies_by_council, f, indent=2, ensure_ascii=False)

total = sum(len(j) for j in vacancies_by_council.values())
print(f"Saved {total} vacancies across {len(vacancies_by_council)} councils.")
