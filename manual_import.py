from pyzotero import zotero
import time
import os
import requests
import google.generativeai as genai
import pandas as pd
import re
import glob
import csv
from datetime import datetime
from pypdf import PdfReader

# --- CONFIGURATION ---
LIBRARY_ID = os.environ.get('ZOTERO_USER_ID')
API_KEY = os.environ.get('ZOTERO_API_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LIBRARY_TYPE = 'user'

# --- LOGGING CONFIG ---
LOG_FILE = "research_ops_log.csv"
PROMPT_VERSION = "v2.3_Manual_Bib"
CURRENT_MODEL = "gemini-1.5-flash-001"

# --- TARGET ARTICLES (Pre-Filled) ---
# USER: Add specific URLs/DOIs you want to force-import here.
TARGET_DATA = [
    # {"url": "https://doi.org/10.xxxx/xxxx", "title": "Example Paper Title"},
]

# --- VOCABULARY ---
# USER: Update these lists with your domain-specific terms.
VOCAB_THEORY = [
    "Theory A", "Theory B", "Theory C"
]

VOCAB_METHOD = [
    "Case Study", "Survey", "Mixed Methods", "Quantitative Analysis",
    "Qualitative Interview", "Systematic Review"
]

VOCAB_CONTEXT = [
    "Context A", "Context B", "Context C"
]

def setup_gemini():
    if not GEMINI_KEY: return None
    genai.configure(api_key=GEMINI_KEY)
    try:
        return genai.GenerativeModel('gemini-1.5-flash-001')
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

def log_operation(action, title, details, status):
    """Writes a permanent record of every robot action to a CSV."""
    file_exists = os.path.isfile(LOG_FILE)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Action', 'Status', 'Paper_Title', 'Prompt_Version', 'Model', 'Details'])
        writer.writerow([timestamp, action, status, title, PROMPT_VERSION, CURRENT_MODEL, details])

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for i in range(min(5, len(reader.pages))):
            text += reader.pages[i].extract_text() + "\n"
        return text
    except Exception as e:
        print(f"  [PDF Error] Could not read file: {e}")
        return None

def analyze_paper_with_ai(model, title, abstract, authors, year):
    if not model: return None
    
    # Context instruction handles missing abstracts
    context_instruction = f"Source Text: {abstract[:15000]}"
    if not abstract or len(abstract) < 50:
        context_instruction = f"NOTE: No abstract provided. Please summarize this famous work based on your internal training data: '{title}' by {authors} ({year})."

    theory_str = ", ".join(VOCAB_THEORY)
    method_str = ", ".join(VOCAB_METHOD)
    context_str = ", ".join(VOCAB_CONTEXT)

    prompt = f"""
    Act as a research assistant.
    
    {context_instruction}
    
    TASK 1: Draft a "10-Point Reading Summary" (HTML format).
    TASK 2: Draft a single "Annotated Bibliography Paragraph" (Text format).
    
    OUTPUT FORMAT:
    
    <h3>1. Keywords</h3>
    ... [Standard 10 points] ...
    <h3>10. Next Steps</h3>
    
    <h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>
    [Write a single coherent paragraph of approx 150-200 words.
    Structure:
    - Sentences 1-2: SUMMARIZE the content/argument.
    - Sentences 3-4: ASSESS the methodology and reliability.
    - Sentences 5-6: REFLECT on its relevance.
    Do NOT use bullet points here. Use complete sentences.]
    
    <h3>DATA EXTRACTION</h3>
    Setting: [Extract Country/Context]
    Tags: [Select from lists: {theory_str}, {method_str}, {context_str}]
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  [AI Error] {e}")
        return None

def parse_ai_response(ai_text):
    if not ai_text: return [], "", "Unknown", ""
    
    tags = []
    setting = "Unknown"
    clean_note = ""
    annotated_bib = ""
    
    parts = ai_text.split("<h3>DATA EXTRACTION</h3>")
    main_content = parts[0]
    
    if "<h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>" in main_content:
        bib_parts = main_content.split("<h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>")
        clean_note = bib_parts[0]
        annotated_bib = bib_parts[1].replace("<p>", "").replace("</p>", "").strip()
    else:
        clean_note = main_content
    
    if len(parts) > 1:
        data_section = parts[1]
        setting_match = re.search(r"Setting:\s*(.*)", data_section)
        if setting_match: setting = setting_match.group(1).strip().replace("[", "").replace("]", "")
        
        all_vocab = VOCAB_THEORY + VOCAB_METHOD + VOCAB_CONTEXT
        for vocab_word in all_vocab:
            if vocab_word in data_section: tags.append(vocab_word)
            
    return tags, clean_note, setting, annotated_bib

def lookup_paper_details(item_data, pdf_text=None):
    url = item_data.get('url', '')
    search_title = item_data['title']
    
    paper_id = None
    if "doi.org/" in url:
        paper_id = "DOI:" + url.split("doi.org/")[1]
    elif "semanticscholar.org/paper/" in url:
        match = re.search(r'paper/.*?/([a-f0-9]+)', url)
        if match: paper_id = match.group(1)
    
    if paper_id:
        api_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        params = {"fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount"}
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
        params = {"query": search_title, "limit": 1, "fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount"}
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

    if pdf_text:
        return {'title': search_title, 'url': url, 'year': datetime.now().year, 'abstract': pdf_text}

    return {'title': search_title, 'url': url, 'year': datetime.now().year, 'abstract': ""}

def save_matrix_csv(items):
    data_for_csv = []
    for item in items:
        citations, year, title, topic, url, smart_tag, ai_note, author, setting = item
        data_for_csv.append({
            "Year": year, "Author": author, "Title": title, "Topic": topic,
            "Setting": setting, "Citations": citations, "URL": url,
            "Tag": smart_tag, "AI_Note": ai_note
        })
    new_df = pd.DataFrame(data_for_csv)
    if os.path.exists("literature_matrix.csv"):
        existing_df = pd.read_csv("literature_matrix.csv")
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Title'], keep='last')
    else: final_df = new_df
    final_df.to_csv("literature_matrix.csv", index=False)
    print("  [Matrix Saved] literature_matrix.csv updated.")

def save_summary_file(year, title, note_content, bib_content):
    os.makedirs("summaries", exist_ok=True)
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    filename = f"summaries/{year} - {safe_title}.md"
    
    md_content = note_content.replace("<h3>", "### ").replace("</h3>", "\n").replace("<p>", "").replace("</p>", "\n\n").replace("<b>", "**").replace("</b>", "**").replace("<br>", "\n")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("## Annotated Bibliography Entry\n")
        f.write(bib_content + "\n\n")
        f.write("## 10-Point Summary\n")
        f.write(md_content)
    print(f"  [File Saved] {filename}")

def process_manual_list():
    if not LIBRARY_ID or not API_KEY: return
    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, API_KEY)
    ai_model = setup_gemini()
    report_data = []
    
    process_queue = []
    for item in TARGET_DATA: process_queue.append(item)
    
    if os.path.exists("manual_pdfs"):
        pdf_files = glob.glob("manual_pdfs/*.pdf")
        for pdf in pdf_files:
             clean_title = os.path.splitext(os.path.basename(pdf))[0]
             pdf_content = extract_text_from_pdf(pdf)
             process_queue.append({"url": pdf, "title": clean_title, "pdf_text": pdf_content})
    
    print(f"Starting Manual Import for {len(process_queue)} items...")

    for item_data in process_queue:
        print(f"\nProcessing: {item_data['title']}")
        pdf_text = item_data.get('pdf_text')
        paper = lookup_paper_details(item_data, pdf_text)
        
        title = paper.get('title', 'No Title')
        citations = paper.get('citationCount', 0)
        p_year = paper.get('year', datetime.now().year)
        abstract = paper.get('abstract') or ""
        
        if abstract: abstract = re.sub(r'\s+', ' ', abstract).strip()
        
        author_str = "Unknown"
        zotero_creators = []
        if paper.get('authors'):
            author_str = ", ".join([a['name'] for a in paper['authors'][:3]])
            for auth in paper['authors']:
                if 'name' in auth:
                    parts = auth['name'].split()
                    if len(parts) > 1: zotero_creators.append({'creatorType': 'author', 'firstName': " ".join(parts[:-1]), 'lastName': parts[-1]})
                    else: zotero_creators.append({'creatorType': 'author', 'firstName': '', 'lastName': auth['name']})

        ai_tags, ai_note_content, setting, annotated_bib = [], "", "Unknown", ""
        
        # PERMISSIVE MODE: Always try AI, even with no abstract (fallback to internal knowledge)
        if ai_model:
            print(f"  [AI] Analyzing: {title[:30]}...")
            ai_text = analyze_paper_with_ai(ai_model, title, abstract, author_str, p_year)
            ai_tags, ai_note_content, setting, annotated_bib = parse_ai_response(ai_text)
            time.sleep(1)

        template = zot.item_template('journalArticle')
        template['title'] = title
        template['abstractNote'] = (abstract[:2000] + "...") if len(abstract) > 2000 else abstract
        template['date'] = str(p_year)
        template['url'] = paper.get('url', item_data['url'] if "http" in item_data['url'] else "")
        template['creators'] = zotero_creators
        if paper.get('venue'): template['publicationTitle'] = paper['venue']
        
        # Save Annotation to Extra
        if annotated_bib:
            template['extra'] = annotated_bib
        
        tag_list = [{'tag': 'Manual Import'}]
        for t in ai_tags: tag_list.append({'tag': f"#{t}"})
        template['tags'] = tag_list

        try:
            resp = zot.create_items([template])
            if resp and 'successful' in resp:
                print(f"  [Success] Added: {title[:20]}...")
                log_operation("Import", title, "Manual", "Success")

                parent_key = resp['successful']['0']['key']
                
                if ai_note_content:
                    note_template = zot.item_template('note')
                    note_template['parentItem'] = parent_key
                    note_template['note'] = ai_note_content
                    note_template['tags'] = [{'tag': '10-Point-Draft'}]
                    zot.create_items([note_template])
                    
                    if annotated_bib:
                        bib_note = zot.item_template('note')
                        bib_note['parentItem'] = parent_key
                        # FIX: Unique title for Word plugin search
                        bib_note['note'] = f"<h3>Annotated Bib: {author_str} ({p_year})</h3><p>{annotated_bib}</p>"
                        bib_note['tags'] = [{'tag': 'Annotated Bib'}]
                        zot.create_items([bib_note])

                    save_summary_file(p_year, title, ai_note_content, annotated_bib)
                
                report_data.append((citations, p_year, title, "Class Assignment", template['url'], "Manual", ai_note_content, author_str, setting))
        except Exception as e: 
            print(f"  [Upload Error] {e}")
            log_operation("Zotero Upload", title, str(e), "Error")

    if report_data:
        save_matrix_csv(report_data)

if __name__ == "__main__":
    process_manual_list()
