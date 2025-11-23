from pyzotero import zotero
import time
import os
import requests
from datetime import datetime

# --- CONFIGURATION ---
# These are pulled from GitHub Secrets (Safe for Public Repos)
LIBRARY_ID = os.environ.get('ZOTERO_USER_ID')
API_KEY = os.environ.get('ZOTERO_API_KEY')
LIBRARY_TYPE = 'user'

# DATE SETTINGS
CURRENT_YEAR = datetime.now().year
YEAR_RANGE = f"{CURRENT_YEAR-1}-{CURRENT_YEAR}"
TODAY_TAG = f"Imported: {datetime.now().strftime('%Y-%m-%d')}"

# --- CUSTOMIZE YOUR TOPICS HERE ---
SEARCH_QUERIES = [
    { "query": "university IT governance", "tag": "IT Governance" },
    { "query": "AI literacy higher education", "tag": "AI Literacy" },
    { "query": "resource dependence theory higher education", "tag": "Resource Dependence Theory" },
    { "query": "student engagement equity analytics", "tag": "Equity Analytics" },
    { "query": "digital equity higher education", "tag": "Digital Equity" },
    { "query": "AI governance higher education", "tag": "AI Governance" },
    { "query": "university data governance decision making", "tag": "Data Governance" },
    { "query": "generative AI higher education", "tag": "Generative AI" }
]

def search_semantic_scholar(query_text):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query_text,
        "year": YEAR_RANGE,
        "limit": 20, 
        "fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount"
    }
    
    try:
        time.sleep(2)
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get('data', [])
        return []
    except Exception as e:
        print(f"  [Connection Error] {e}")
        return []

def get_sliding_scale_rules(paper_year):
    """
    Returns a tuple: (required_citations, classification_tag)
    """
    try:
        p_year = int(paper_year)
    except:
        return (0, "Unknown Year")
    
    if p_year >= CURRENT_YEAR:
        return (0, "🔥 Trending (New)")
    elif p_year == CURRENT_YEAR - 1:
        return (15, "⭐ Proven (Recent)")
    else:
        return (50, "🏆 High Impact")

def update_readme_dashboard(items):
    filename = "README.md"
    # We append to the existing README or overwrite a status section
    # For simplicity in this template, we overwrite to show the status
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Note: In a real deployment, you might want to read the existing README content 
    # and only replace the "Status" section. 
    # For this template, we simply generate a status log.
    
    with open("LAST_RUN_LOG.md", "w", encoding='utf-8') as f:
        f.write(f"# 📊 Weekly Import Log\n")
        f.write(f"**Run Date:** {timestamp} UTC\n\n")
        
        if not items:
            f.write(f"No new papers met the criteria this week.\n")
        else:
            f.write(f"Imported **{len(items)}** papers:\n\n")
            f.write("| Citations | Type | Topic | Title |\n")
            f.write("| :---: | :--- | :--- | :--- |\n")
            for citations, year, title, topic, url, smart_tag in items:
                title_display = f"[{title}]({url})" if url else title
                icon = "📄"
                if "Trending" in smart_tag: icon = "🔥"
                if "Proven" in smart_tag: icon = "⭐"
                f.write(f"| {citations} | {icon} | {topic} | {title_display} |\n")
    
    print(f"  [Log Updated]")

def process_searches():
    if not LIBRARY_ID or not API_KEY:
        print("Error: Zotero Credentials missing. Check GitHub Secrets.")
        return

    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, API_KEY)
    report_data = []

    print(f"Starting Import for {YEAR_RANGE} (Sliding Scale). Batch Tag: {TODAY_TAG}")

    for search in SEARCH_QUERIES:
        query = search['query']
        tag_name = search['tag']
        
        print(f"\nSearching: '{query}'...")
        papers = search_semantic_scholar(query)
        
        if not papers:
            continue

        for paper in papers:
            title = paper.get('title', 'No Title')
            citations = paper.get('citationCount', 0)
            p_year = paper.get('year', CURRENT_YEAR)
            
            # SLIDING SCALE FILTER
            required_citations, smart_tag = get_sliding_scale_rules(p_year)
            if citations < required_citations:
                continue
            
            # DUPLICATE CHECK
            try:
                search_results = zot.items(q=f'title:"{title}"', limit=1)
                if len(search_results) > 0:
                    existing_title = search_results[0]['data']['title']
                    if existing_title.lower().strip() == title.lower().strip():
                        print(f"  [Skipping] Duplicate.")
                        continue
            except:
                pass 

            # PREPARE ITEM
            template = zot.item_template('journalArticle')
            template['title'] = title
            template['abstractNote'] = paper.get('abstract', '')
            template['date'] = str(p_year)
            template['extra'] = f"Citations: {citations}"
            
            final_url = paper.get('url', '')
            if paper.get('openAccessPdf'):
                final_url = paper['openAccessPdf'].get('url', final_url)
            template['url'] = final_url
            
            if paper.get('venue'):
                template['publicationTitle'] = paper['venue']

            template['tags'] = [
                {'tag': '_NEW_ARRIVAL'},
                {'tag': smart_tag},
                {'tag': TODAY_TAG},
                {'tag': tag_name}
            ]

            if paper.get('authors'):
                zotero_authors = []
                for author in paper['authors']:
                    name_parts = author['name'].split()
                    if len(name_parts) > 1:
                        last = name_parts[-1]
                        first = " ".join(name_parts[:-1])
                    else:
                        last = author['name']
                        first = ""
                    zotero_authors.append({'creatorType': 'author', 'firstName': first, 'lastName': last})
                template['creators'] = zotero_authors

            try:
                resp = zot.create_items([template])
                if resp and 'successful' in resp:
                    print(f"  [Success] Added to Zotero.")
                    report_data.append((citations, p_year, title, tag_name, final_url, smart_tag))
            except Exception as e:
                print(f"  [Upload Error] {e}")

    update_readme_dashboard(report_data)

if __name__ == "__main__":
    process_searches()
