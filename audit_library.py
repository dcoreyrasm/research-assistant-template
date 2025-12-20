from pyzotero import zotero
import time
import os
import requests
import google.generativeai as genai
import re
from pypdf import PdfReader
import io

# --- CONFIGURATION ---
LIBRARY_ID = os.environ.get('ZOTERO_USER_ID')
API_KEY = os.environ.get('ZOTERO_API_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LIBRARY_TYPE = 'user'

# --- FILTER SETTINGS ---
# Only process papers published in or after this year
MIN_PUBLISH_YEAR = 1900 

def setup_gemini():
    if not GEMINI_KEY: return None
    genai.configure(api_key=GEMINI_KEY)
    try: return genai.GenerativeModel('gemini-1.5-flash-001')
    except: return genai.GenerativeModel('gemini-1.5-flash')

def analyze_paper_with_ai(model, title, text_content):
    if not model or not text_content: return None
    
    # Safe truncation
    text_sample = text_content[:15000]

    prompt = f"""
    Act as a research assistant.
    Analyze the text provided below.
    
    TASK 1: Draft a "10-Point Reading Summary" (HTML format).
    TASK 2: Draft a single "Annotated Bibliography Paragraph" (Text format).
    
    Paper Title: {title}
    Source Text: {text_sample}
    
    OUTPUT FORMAT:
    <h3>1. Keywords</h3>... [Standard 10 points] ...<h3>10. Next Steps</h3>
    
    <h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>
    [Write a single coherent paragraph of approx 150-200 words. Summarize, Assess, Reflect.]
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return None

def process_library():
    if not LIBRARY_ID or not API_KEY: return
    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, API_KEY)
    ai_model = setup_gemini()
    
    # Fetch top 50 items (or use pagination for all)
    print("Scanning library for missing summaries...")
    items = zot.items(limit=50, sort='dateAdded', direction='desc')
    
    for item in items:
        data = item['data']
        title = data.get('title', 'No Title')
        item_key = item['key']
        
        # Skip non-papers
        if data['itemType'] in ['attachment', 'note']: continue
        
        # --- DATE FILTER ---
        item_date = data.get('date', '')
        # Extract year using regex (handles formats like "2025-05-12" or "May 2025")
        year_match = re.search(r'(\d{4})', item_date)
        if year_match:
            year = int(year_match.group(1))
            if year < MIN_PUBLISH_YEAR:
                continue
        else:
            pass

        # CHECK: Does it already have a 10-Point Summary?
        has_summary = False
        children = zot.children(item_key)
        for child in children:
            if child['data']['itemType'] == 'note' and "10-Point" in child['data']['note']:
                has_summary = True
                break
        
        if has_summary:
            print(f"  [Skipping] Summary exists for: {title[:20]}...")
            continue
            
        print(f"  [Processing] Missing summary: {title[:30]}...")
        
        # SOURCE 1: Abstract from Metadata
        text_content = data.get('abstractNote', '')
        
        # SOURCE 2: If abstract is empty, try Semantic Scholar Lookup by Title
        if not text_content:
            print("    - No abstract in Zotero. Checking Semantic Scholar...")
            try:
                search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
                r = requests.get(search_url, params={"query": title, "limit": 1, "fields": "abstract"}, timeout=5)
                if r.status_code == 200:
                    res = r.json()
                    if res.get('data') and res['data'][0].get('abstract'):
                        text_content = res['data'][0]['abstract']
                        print("    - Found abstract via API!")
            except: pass

        # SOURCE 3: If still empty, we are stuck (unless we download PDF, which is hard via API)
        if not text_content:
            print("    - [Failed] No text found. Skipping.")
            continue
            
        # Generate Note
        if ai_model:
            ai_note = analyze_paper_with_ai(ai_model, title, text_content)
            if ai_note:
                note_template = zot.item_template('note')
                note_template['parentItem'] = item_key
                note_template['note'] = ai_note
                note_template['tags'] = [{'tag': '10-Point-Draft'}]
                zot.create_items([note_template])
                print("    - [Success] Note created.")
                time.sleep(2) # Rate limit safety
            else:
                print("    - [Error] AI failed to generate note.")

if __name__ == "__main__":
    process_library()
