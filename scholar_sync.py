import os
import time
import requests
import pandas as pd
import re
import feedparser
import csv
import glob
from datetime import datetime
from pypdf import PdfReader
from difflib import SequenceMatcher
from pyzotero import zotero
import google.generativeai as genai

# --- CONFIGURATION ---
LIBRARY_ID = os.environ.get('ZOTERO_USER_ID')
API_KEY = os.environ.get('ZOTERO_API_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LIBRARY_TYPE = 'user' # or 'group'

# DATE & TAGGING
CURRENT_YEAR = datetime.now().year
YEAR_RANGE = f"{CURRENT_YEAR-2}-{CURRENT_YEAR}"
TODAY_TAG = f"Imported: {datetime.now().strftime('%Y-%m-%d')}"

# --- LOGGING CONFIG ---
LOG_FILE = "research_ops_log.csv"
PROMPT_VERSION = "v1.0_Template"

# --- USER CONFIGURATION SECTION ---

# 1. Define your core research questions for the AI to align against
MY_RESEARCH_QUESTIONS = [
    "Question 1: [Insert your primary research question here?]",
    "Question 2: [Insert secondary question?]",
    "Question 3: [Insert tertiary question?]"
]

# 2. Blocklist for RSS noise (e.g., shopping deals if using tech feeds)
NOISE_BLOCKLIST = [
    "black friday", "cyber monday", "deal alert", "price drop", "limited time offer"
]

# 3. Controlled Vocabulary (Used for auto-tagging)
# Replace these examples with your domain-specific terms
VOCAB_THEORY = ["Theory A", "Theory B", "System Systems Theory"]
VOCAB_METHOD = ["Case Study", "Survey", "Mixed Methods", "Quantitative Analysis"]
VOCAB_CONTEXT = ["Industry A", "Sector B", "Context C", "Context D"]

# 4. Semantic Scholar Search Queries
SEARCH_QUERIES = [
    { "query": "your topic keyword here", "tag": "Topic A" },
    { "query": "another topic keyword", "tag": "Topic B" },
]

# 5. RSS Feeds to Monitor
RSS_FEEDS = [
    { "url": "http://export.arxiv.org/rss/cs.AI", "tag": "arXiv: AI" },
    # Add your specific journal RSS feeds here
]

# --- END USER CONFIGURATION ---

def setup_gemini():
    """Robust connection logic that hunts for a working model version."""
    if not GEMINI_KEY:
        print("  [Setup Error] GEMINI_API_KEY is missing.")
        return None
    try:
        genai.configure(api_key=GEMINI_KEY)
        candidates = [
            "gemini-1.5-flash-001", "gemini-1.5-flash", "gemini-1.5-flash-002",
            "gemini-1.5-pro", "gemini-pro"
        ]
        for model_name in candidates:
            try:
                model = genai.GenerativeModel(model_name)
                model.generate_content("Test")
                print(f"  [Setup] Success! Connected using: {model_name}")
                return model
            except Exception: continue
        print("  [Setup Error] Could not connect to ANY Gemini model.")
        return None
    except Exception as e:
        print(f"  [Setup Error] Configuration failed: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for i in range(min(10, len(reader.pages))): 
            text += reader.pages[i].extract_text() + "\n"
        return text
    except Exception as e:
        print(f"  [PDF Error] Could not read file: {e}")
        return None

def clean_abstract(text):
    if not text: return ""
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_likely_duplicate(new_title, existing_titles, threshold=0.85):
    new_clean = new_title.lower().strip()
    for existing in existing_titles:
        existing_clean = existing.lower().strip()
        similarity = SequenceMatcher(None, new_clean, existing_clean).ratio()
        if similarity > threshold:
            return True, existing
    return False, None

def calculate_priority_score(paper_data):
    score = 0
    citations = paper_data.get('citationCount', 0)
    if citations > 100: score += 40
    elif citations > 50: score += 30
    elif citations > 20: score += 20
    
    year = paper_data.get('year', 2000)
    if year >= CURRENT_YEAR: score += 30
    elif year >= CURRENT_YEAR - 2: score += 20
    
    title_lower = paper_data.get('title', '').lower()
    abstract_lower = (paper_data.get('abstract') or '').lower()
    combined_text = title_lower + " " + abstract_lower
    
    # Check against vocabulary
    all_vocab = VOCAB_THEORY + VOCAB_CONTEXT
    for term in all_vocab:
        if term.lower() in combined_text: score += 5
    return min(score, 100)

def assign_priority_tier(score):
    if score >= 70: return "Critical"
    elif score >= 50: return "High"
    elif score >= 30: return "Medium"
    else: return "Low"

def lookup_paper_details(item_data, pdf_text=None):
    url = item_data.get('url', '')
    search_title = item_data['title']
    paper_id = None
    if "doi.org/" in url: paper_id = "DOI:" + url.split("doi.org/")[1]
    elif "semanticscholar.org/paper/" in url:
        match = re.search(r'paper/.*?/([a-f0-9]+)', url)
        if match: paper_id = match.group(1)
    
    if paper_id:
        api_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        params = {"fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount,paperId"}
        try:
            r = requests.get(api_url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if not data.get('abstract') and pdf_text: data['abstract'] = pdf_text
                if not data.get('abstract'): data['abstract'] = ""
                return data
        except: pass
    
    if search_title:
        search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": search_title, "limit": 1, "fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount,paperId"}
        try:
            r = requests.get(search_url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('data'):
                    best_match = data['data'][0]
                    if not best_match.get('abstract') and pdf_text: best_match['abstract'] = pdf_text
                    if not best_match.get('abstract'): best_match['abstract'] = ""
                    return best_match
        except: pass

    if pdf_text: return {'title': search_title, 'url': url, 'year': datetime.now().year, 'abstract': pdf_text}
    return {'title': search_title, 'url': url, 'year': datetime.now().year, 'abstract': ""}

def load_library_context(df, topic, limit=5):
    if df is None or df.empty: return ""
    topic_papers = df[df['Topic'].str.contains(topic, case=False, na=False)] if 'Topic' in df.columns else df
    if topic_papers.empty: topic_papers = df
    top_papers = topic_papers.nlargest(limit, 'Citations') if 'Citations' in topic_papers.columns else topic_papers.head(limit)
    context = "EXISTING RESEARCH IN YOUR LIBRARY:\n"
    for _, row in top_papers.iterrows():
        context += f"- {row.get('Author', 'Unknown')} ({row.get('Year', 'N/A')}): {row.get('Title', 'Untitled')}\n"
    return context

def analyze_paper_with_ai(model, title, abstract, authors, year, library_context=""):
    if not model: return None
    abstract = clean_abstract(abstract)
    context_instruction = f"Source Text: {abstract[:20000]}"
    if not abstract or len(abstract) < 100:
        context_instruction = f"NOTE: No abstract provided. Summarize based on training data: '{title}' by {authors} ({year})."

    rq_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(MY_RESEARCH_QUESTIONS)])
    
    # GENERIC PROMPT
    prompt = f"""
    Act as a research assistant.
    {library_context}
    NEW PAPER TO ANALYZE:
    Title: {title}
    Authors: {authors}
    Year: {year}
    {context_instruction}
    Draft a "10-Point Reading Summary".
    TONE: Professional, academic, but concise.
    OUTPUT FORMAT:
    <h3>1. Keywords</h3>
    ...
    <h3>11. Alignment with Research</h3>
    Rate relevance to the following questions (0-10):
    {rq_text}
    <h3>12. Connection to Existing Literature</h3>
    <h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>
    [150-200 words summary]
    <h3>DATA EXTRACTION</h3>
    Setting: [Context/Country]
    Tags: [THEORIES, METHODS, CONTEXTS]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if "429" in str(e):
            time.sleep(60)
            return None
        print(f"  [AI Error] {e}")
        return None

def parse_ai_response(ai_text):
    if not ai_text: return [], "", "Unknown", "", 0
    tags, setting, clean_note, annotated_bib, alignment_score = [], "Unknown", "", "", 0
    if "<h3>1. Keywords</h3>" in ai_text: ai_text = ai_text[ai_text.find("<h3>1. Keywords</h3>"):]
    
    parts = ai_text.split("<h3>DATA EXTRACTION</h3>")
    main_content = parts[0]
    
    if "<h3>11. Alignment with Research</h3>" in main_content:
        alignment_section = main_content.split("<h3>11. Alignment with Research</h3>")[1].split("<h3>")[0]
        scores = re.findall(r'(\d+)/10', alignment_section)
        if scores: alignment_score = sum(int(s) for s in scores) / len(scores)
    
    if "<h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>" in main_content:
        bib_parts = main_content.split("<h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>")
        clean_note = bib_parts[0]
        annotated_bib = bib_parts[1].replace("<p>", "").replace("</p>", "").strip()
    else: clean_note = main_content
    
    if len(parts) > 1:
        data_section = parts[1]
        setting_match = re.search(r"Setting:\s*(.*)", data_section)
        if setting_match: setting = setting_match.group(1).strip().replace("[", "").replace("]", "")
        all_vocab = VOCAB_THEORY + VOCAB_METHOD + VOCAB_CONTEXT
        for vocab_word in all_vocab:
            if vocab_word in data_section: tags.append(vocab_word)
            
    return tags, clean_note, setting, annotated_bib, alignment_score

def search_semantic_scholar(query_text):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query_text, "year": YEAR_RANGE, "limit": 10, "fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount,paperId"}
    try:
        time.sleep(1)
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200: return r.json().get('data', [])
        return []
    except: return []

def fetch_rss_feed(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        normalized_entries = []
        for entry in feed.entries[:3]:
            title = entry.get('title', '')
            if any(x in title.lower() for x in NOISE_BLOCKLIST): continue
            pub_year = entry.published_parsed.tm_year if hasattr(entry, 'published_parsed') else CURRENT_YEAR
            abstract = clean_abstract(getattr(entry, 'summary', getattr(entry, 'description', '')))[:1500]
            normalized_entries.append({'title': title, 'abstract': abstract, 'year': pub_year, 'url': entry.link, 'citationCount': 0, 'authors': [{'name': getattr(entry, 'author', 'RSS Feed')}], 'is_industry_report': True})
        return normalized_entries
    except: return []

def get_sliding_scale_rules(paper_year):
    try: p_year = int(paper_year)
    except: return (0, "Unknown Year")
    if p_year >= CURRENT_YEAR: return (0, "🔥 Trending (New)")
    elif p_year == CURRENT_YEAR - 1: return (15, "💎 Proven (Recent)")
    else: return (50, "🏛️ High Impact")

def load_zotero_titles(zot):
    print("  [Memory] Creating local map of existing library...")
    titles = set()
    try:
        items = zot.items(limit=300, sort='dateAdded', direction='desc')
        for item in items:
            t = item['data'].get('title', '')
            if t: titles.add(t.lower().strip())
    except: pass
    print(f"  [Memory] Indexed {len(titles)} existing papers.")
    return titles

def save_matrix_csv(items, existing_df=None):
    data_for_csv = []
    for item in items:
        citations, year, title, topic, url, smart_tag, ai_note, author, setting, priority, alignment = item
        data_for_csv.append({"Year": year, "Author": author, "Title": title, "Topic": topic, "Setting": setting, "Citations": citations, "URL": url, "Tag": smart_tag, "AI_Note": ai_note, "Priority": priority, "Alignment_Score": alignment})
    new_df = pd.DataFrame(data_for_csv)
    final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Title'], keep='last') if existing_df is not None and not existing_df.empty else new_df
    final_df.to_csv("literature_matrix.csv", index=False)
    print("  [Matrix Saved] literature_matrix.csv updated.")

def update_readme_dashboard(items):
    filename = "LAST_RUN_LOG.md" 
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(filename, "w", encoding='utf-8') as f:
        f.write(f"# 📊 Research Ops Log\n**Run Date:** {timestamp}\n\n")
        if not items: f.write(f"No new papers added this run.\n")
        else:
            f.write(f"Processed **{len(items)}** new papers:\n\n| Priority | Citations | Type | Topic | Title |\n| :---: | :---: | :--- | :--- | :--- |\n")
            for item in items:
                citations, year, title, topic, url, smart_tag, ai_note, author, setting, priority, alignment = item
                f.write(f"| {priority} | {citations} | 📄 | {topic} | [{title}]({url}) |\n")
    print(f"  [Log Updated]")

def process_searches():
    if not LIBRARY_ID or not API_KEY: return
    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, API_KEY)
    ai_model = setup_gemini()
    report_data = []
    zotero_memory = load_zotero_titles(zot)
    existing_df = pd.read_csv("literature_matrix.csv") if os.path.exists("literature_matrix.csv") else None
    if existing_df is not None:
        for t in existing_df['Title']: 
            if pd.notna(t): zotero_memory.add(str(t).lower().strip())

    print(f"Starting Enhanced Analyst Engine. Batch: {TODAY_TAG}")

    manual_papers = []
    if os.path.exists("manual_pdfs"):
        for pdf in glob.glob("manual_pdfs/*.pdf"):
             manual_papers.append(lookup_paper_details({'title': os.path.splitext(os.path.basename(pdf))[0], 'url': ''}, extract_text_from_pdf(pdf)))
    
    if manual_papers: process_batch(manual_papers, zot, ai_model, "Manual Import", report_data, zotero_memory, existing_df, is_academic=True, is_manual=True)

    for search in SEARCH_QUERIES:
        papers = search_semantic_scholar(search['query'])
        if papers: process_batch(papers, zot, ai_model, search['tag'], report_data, zotero_memory, existing_df, is_academic=True)

    for feed in RSS_FEEDS:
        papers = fetch_rss_feed(feed['url'])
        if papers: process_batch(papers, zot, ai_model, feed['tag'], report_data, zotero_memory, existing_df, is_academic=False)

    update_readme_dashboard(report_data)
    save_matrix_csv(report_data, existing_df)

def process_batch(papers, zot, ai_model, tag_name, report_data, zotero_memory, existing_df, is_academic, is_manual=False):
    for paper in papers:
        title = paper.get('title', 'No Title')
        is_dup, _ = is_likely_duplicate(title, zotero_memory)
        if is_dup and not is_manual: continue

        citations = paper.get('citationCount', 0)
        p_year = paper.get('year', CURRENT_YEAR)
        priority_score = calculate_priority_score(paper)
        priority_tier = assign_priority_tier(priority_score)

        if is_academic and not is_manual:
            required_citations, smart_tag = get_sliding_scale_rules(p_year)
            if citations < required_citations: continue
        elif is_manual: smart_tag = "📥 Manual Import"
        else: smart_tag = "🌐 Industry Insight"

        library_context = load_library_context(existing_df, tag_name)
        ai_tags, ai_note_content, setting, annotated_bib, alignment_score = [], "", "Unknown", "", 0
        
        if ai_model:
            print(f"  [AI] Analyzing: {title[:30]}...")
            ai_text = analyze_paper_with_ai(ai_model, title, paper.get('abstract', ''), "Unknown", p_year, library_context)
            ai_tags, ai_note_content, setting, annotated_bib, alignment_score = parse_ai_response(ai_text)
            if not ai_note_content and not is_manual: continue
            time.sleep(1)

        template = zot.item_template('journalArticle' if is_academic else 'webpage')
        template['title'] = title
        template['abstractNote'] = paper.get('abstract', '')
        template['date'] = str(p_year)
        template['extra'] = f"Citations: {citations}\nPriority: {priority_tier} ({priority_score}/100)\nAlignment Score: {alignment_score:.1f}/10"
        if annotated_bib: template['extra'] += f"\n\nAnnotation:\n{annotated_bib}"
        template['url'] = paper.get('url', '')
        template['publicationTitle'] = paper.get('venue', 'Semantic Scholar')
        template['creators'] = [{'creatorType': 'author', 'firstName': '', 'lastName': 'Unknown'}] 
        template['tags'] = [{'tag': '_NEW_ARRIVAL'}, {'tag': smart_tag}, {'tag': TODAY_TAG}, {'tag': tag_name}, {'tag': f'Priority: {priority_tier}'}]
        for t in ai_tags: template['tags'].append({'tag': f"#{t}"})

        try:
            resp = zot.create_items([template])
            if resp and 'successful' in resp:
                print(f"  [Success] Added [{priority_tier}]: {title[:20]}...")
                parent_key = resp['successful']['0']['key']
                if ai_note_content:
                    zot.create_items([{'parentItem': parent_key, 'itemType': 'note', 'note': ai_note_content, 'tags': [{'tag': '10-Point-Draft'}]}])
                report_data.append((citations, p_year, title, tag_name, template['url'], smart_tag, ai_note_content, "Unknown", setting, priority_tier, alignment_score))
                zotero_memory.add(title.lower().strip())
        except Exception as e: 
            print(f"  [Upload Error] {e}")

if __name__ == "__main__":
    process_searches()
