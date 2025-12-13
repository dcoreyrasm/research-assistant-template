from pyzotero import zotero
import time
import os
import requests
import google.generativeai as genai
import pandas as pd
import re
import feedparser
from datetime import datetime

# --- CONFIGURATION ---
LIBRARY_ID = os.environ.get('ZOTERO_USER_ID')
API_KEY = os.environ.get('ZOTERO_API_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LIBRARY_TYPE = 'user'

# DATE & TAGGING
CURRENT_YEAR = datetime.now().year
YEAR_RANGE = f"{CURRENT_YEAR-2}-{CURRENT_YEAR}"
TODAY_TAG = f"Imported: {datetime.now().strftime('%Y-%m-%d')}"

# --- NOISE FILTER (BLOCKLIST) ---
NOISE_BLOCKLIST = [
    "black friday", "cyber monday", "prime day", "deal alert", "price drop",
    "gift guide", "best buy", "promo code", "coupon", "limited time offer",
    "on sale", "clearance", "doorbuster", "shopping list", "best deals",
    "must-have", "gadget", "appliance", "vacuum", "mattress", "tv deal",
    "headphones", "laptop deal", "smart home deal", "review:", "hands-on:"
]

# --- EXPANDED CONTROLLED VOCABULARY ---
VOCAB_THEORY = [
    "Agency Theory", "Resource Dependence Theory", "Transaction Cost Economics", 
    "Stewardship Theory", "Institutional Theory", "Stakeholder Theory",
    "Diffusion of Innovation", "Disruptive Innovation", "Dynamic Capabilities",
    "Absorptive Capacity", "Organizational Learning Theory",
    "Technology Acceptance Model (TAM)", "UTAUT", "Socio-Technical Systems Theory",
    "Actor-Network Theory", "Structuration Theory"
]

VOCAB_METHOD = [
    "Case Study", "Survey", "Mixed Methods", "Action Research", "Ethnography",
    "Systematic Review", "Bibliometric Analysis", "Design Science Research",
    "Regression Analysis", "Structural Equation Modeling (SEM)", "Factor Analysis (EFA/CFA)",
    "Panel Data Analysis", "Time Series Analysis", "Difference-in-Differences",
    "Experimental Design", "ANOVA/MANOVA", "Machine Learning", "Social Network Analysis",
    "Thematic Analysis", "Grounded Theory", "Content Analysis",
    "Phenomenology", "Discourse Analysis", "Qualitative Interview"
]

VOCAB_CONTEXT = [
    "Higher Education", "IT Governance", "Public Sector Management",
    "AI in Education", "Generative AI", "Large Language Models (LLMs)",
    "Algorithmic Bias", "Responsible AI", "Human-AI Collaboration",
    "Digital Equity", "Equity Analytics", "Student Success",
    "Digital Transformation", "Data Privacy & Ethics"
]

VOCAB_STRATEGY = [
    "Strategic Alignment", "Competitive Advantage", "Value Creation",
    "Risk Management", "Business Process Reengineering", "Change Management",
    "Organizational Resilience", "Knowledge Management", "Strategic Planning"
]

VOCAB_LEADERSHIP = [
    "Transformational Leadership", "Distributed Leadership", "Servant Leadership",
    "Adaptive Leadership", "Decision-Making Styles", "Organizational Culture",
    "Faculty Resistance", "Shared Governance", "Top Management Support"
]

# SEARCH TOPICS
SEARCH_QUERIES = [
    { "query": "university IT governance", "tag": "IT Governance" },
    { "query": "AI literacy higher education", "tag": "AI Literacy" },
    { "query": "resource dependence theory higher education", "tag": "Resource Dependence Theory" },
    { "query": "student engagement equity analytics", "tag": "Equity Analytics" },
    { "query": "digital equity higher education", "tag": "Digital Equity" },
    { "query": "AI governance higher education", "tag": "AI Governance" },
    { "query": "university data governance decision making", "tag": "Data Governance" },
    { "query": "generative AI higher education", "tag": "Generative AI" },
    { "query": "AI in higher education administration", "tag": "Admin & Ops" },
    { "query": "faculty AI adoption resistance", "tag": "Change Management" },
    { "query": "generative AI academic integrity policy", "tag": "Policy & Risk" },
    { "query": "human-AI collaboration higher education", "tag": "Future of Work" }
]

# RSS FEEDS
RSS_FEEDS = [
    { "url": "https://er.educause.edu/rss", "tag": "EDUCAUSE Review" },
    { "url": "https://er.educause.edu/blogs/rss", "tag": "EDUCAUSE Blogs" },
    { "url": "https://er.educause.edu/multimedia/rss", "tag": "EDUCAUSE Multimedia" },
    { "url": "https://www.educause.edu/rss", "tag": "EDUCAUSE Policy" },
    { "url": "https://library.educause.edu/search?q=artificial+intelligence&rss=true", "tag": "EDUCAUSE Lib: AI" },
    { "url": "https://library.educause.edu/search?q=digital+transformation&rss=true", "tag": "EDUCAUSE Lib: Dx" },
    { "url": "https://library.educause.edu/search?q=student+success&rss=true", "tag": "EDUCAUSE Lib: Student Success" },
    { "url": "https://library.educause.edu/search?q=governance&rss=true", "tag": "EDUCAUSE Lib: Governance" },
    { "url": "https://www.insidehighered.com/rss/news", "tag": "IHE: News" },
    { "url": "https://www.insidehighered.com/rss/opinion", "tag": "IHE: Opinion" },
    { "url": "https://www.insidehighered.com/rss/section/student-success", "tag": "IHE: Student Success" },
    { "url": "https://www.insidehighered.com/rss/section/technology", "tag": "IHE: Tech" },
    { "url": "https://www.insidehighered.com/rss/section/careers", "tag": "IHE: Careers" },
    { "url": "https://www.chronicle.com/section/all/rss", "tag": "Chronicle: All" },
    { "url": "https://www.chronicle.com/section/opinion/rss", "tag": "Chronicle: Opinion" },
    { "url": "https://www.chronicle.com/section/teaching-learning/rss", "tag": "Chronicle: Teaching" },
    { "url": "https://www.chronicle.com/section/technology/rss", "tag": "Chronicle: Tech" },
    { "url": "https://www.highereddive.com/rss/", "tag": "Higher Ed Dive" },
    { "url": "https://www.timeshighereducation.com/rss", "tag": "Times Higher Ed" },
    { "url": "https://www.universityworldnews.com/rss/", "tag": "Univ World News" },
    { "url": "https://hechingerreport.org/feed/", "tag": "Hechinger Report" },
    { "url": "https://www.edweek.org/feeds/rss/articles/index.rss", "tag": "EdWeek" },
    { "url": "https://www.educationnext.org/feed/", "tag": "Education Next" },
    { "url": "https://www.brookings.edu/feed/", "tag": "Brookings: General" },
    { "url": "https://www.brookings.edu/topic/education/feed/", "tag": "Brookings: Education" },
    { "url": "https://www.brookings.edu/topic/artificial-intelligence/feed/", "tag": "Brookings: AI" },
    { "url": "https://www.brookings.edu/topic/governance/feed/", "tag": "Brookings: Governance" },
    { "url": "https://www.pewresearch.org/feed/", "tag": "Pew: General" },
    { "url": "https://www.pewresearch.org/internet/feed/", "tag": "Pew: Internet/Tech" },
    { "url": "https://www.pewresearch.org/topic/education/feed/", "tag": "Pew: Education" },
    { "url": "https://www.rand.org/education-and-labor.html/rss.xml", "tag": "RAND Education" },
    { "url": "https://www.newamerica.org/education-policy/feed/", "tag": "New America Ed" },
    { "url": "https://www.americanprogress.org/topic/education/feed/", "tag": "Center Am Progress" },
    { "url": "https://www.urban.org/taxonomy/term/6/feed", "tag": "Urban Institute" },
    { "url": "https://www.nber.org/feeds/working_papers.xml", "tag": "NBER Working Papers" },
    { "url": "https://technews.acm.org/backend.php", "tag": "ACM TechNews" },
    { "url": "http://feeds.arstechnica.com/arstechnica/index", "tag": "Ars Technica" },
    { "url": "https://www.wired.com/feed/rss", "tag": "Wired" },
    { "url": "https://www.theverge.com/rss/index.xml", "tag": "The Verge" },
    { "url": "https://ai.googleblog.com/feeds/posts/default", "tag": "Google AI Blog" },
    { "url": "https://www.microsoft.com/en-us/research/feed/", "tag": "Microsoft Research" },
    { "url": "https://hai.stanford.edu/news/rss.xml", "tag": "Stanford HAI" },
    { "url": "https://bair.berkeley.edu/blog/feed.xml", "tag": "Berkeley BAIR" },
    { "url": "https://www.csail.mit.edu/rss/news", "tag": "MIT CSAIL" },
    { "url": "https://www.benton.org/feed", "tag": "Benton Institute" },
    { "url": "https://datasociety.net/feed/", "tag": "Data & Society" },
    { "url": "https://montrealethics.ai/feed/", "tag": "Montreal AI Ethics" },
    { "url": "https://www.technologyreview.com/feed/", "tag": "MIT Tech Review" },
    { "url": "https://feeds.hbr.org/harvardbusiness", "tag": "Harvard Business Review" },
    { "url": "https://ssir.org/articles/rss", "tag": "Stanford Social Innovation" },
    { "url": "https://sloanreview.mit.edu/feed/", "tag": "MIT Sloan Review" },
    { "url": "https://www.mckinsey.com/insights/rss", "tag": "McKinsey Insights" },
    { "url": "https://www2.deloitte.com/global/en/insights/find-insights.html?format=rss", "tag": "Deloitte Insights" },
    { "url": "http://feeds.plos.org/plosone/LatestArticles", "tag": "PLOS ONE" },
    { "url": "https://www.frontiersin.org/journals/education/rss", "tag": "Frontiers in Ed" },
    { "url": "https://www.learntechlib.org/journal/JOLR/latest?format=rss", "tag": "JOLR Journal" },
    { "url": "https://eric.ed.gov/rss/rss.xml", "tag": "ERIC Database" },
    { "url": "https://www.oecd.org/education/publicationsdocumenttype/workingpapers/rss.xml", "tag": "OECD Education Papers" }
]

def setup_gemini():
    if not GEMINI_KEY:
        return None
    
    genai.configure(api_key=GEMINI_KEY)
    
    # --- MODEL HUNTER ---
    print("  [Setup] Hunting for valid Gemini models...")
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        priorities = ['gemini-1.5-flash', 'gemini-1.5-flash-001', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-pro']
        selected_model = None
        
        for p in priorities:
            for m in available_models:
                if p in m:
                    selected_model = m
                    break
            if selected_model:
                break
        
        if not selected_model and available_models:
            selected_model = available_models[0]

        if not selected_model:
            print("  [Setup Warning] Could not list models. Forcing 'gemini-1.5-flash'.")
            selected_model = 'gemini-1.5-flash'

        print(f"  [Setup] Locking in model: {selected_model}")
        return genai.GenerativeModel(selected_model)
            
    except Exception as e:
        print(f"  [Setup Error] Model listing failed: {e}")
        return genai.GenerativeModel('gemini-1.5-flash')

# --- LOGGING FUNCTION ---
import csv
LOG_FILE = "research_ops_log.csv"
PROMPT_VERSION = "v2.2_Annotated_Bib"
CURRENT_MODEL = "gemini-1.5-flash-001"

def log_operation(action, title, details, status):
    file_exists = os.path.isfile(LOG_FILE)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Action', 'Status', 'Paper_Title', 'Prompt_Version', 'Model', 'Details'])
        writer.writerow([timestamp, action, status, title, PROMPT_VERSION, CURRENT_MODEL, details])

def analyze_paper_with_ai(model, title, abstract, authors, year):
    if not model or not abstract:
        return None

    # We format the vocab lists into strings for the prompt
    theory_str = ", ".join(VOCAB_THEORY)
    method_str = ", ".join(VOCAB_METHOD)
    context_str = ", ".join(VOCAB_CONTEXT)
    strategy_str = ", ".join(VOCAB_STRATEGY)
    leadership_str = ", ".join(VOCAB_LEADERSHIP)

    prompt = f"""
    Act as a research assistant for a DBA student and Yale IT Leader.
    Analyze the abstract/summary provided below for a newly discovered paper.
    
    Draft a "10-Point Reading Summary" based STRICTLY on the provided text.
    
    TONE & STYLE INSTRUCTIONS (DARICE'S VOICE):
    1.  **Voice:** Write in the first person ('I', 'My'). Use a warm but grounded tone.
    2.  **Style:** Keep sentences clean, steady, and direct. No fluff. No em dashes (use periods/commas).
    3.  **Avoid:** Jargon, corporate speak, 'tech marketing' hype, or overly poetic language.
    4.  **Perspective:** Balance strategy with practical clarity.
    5.  **Prohibited:** DO NOT start with "Of course" or "Here is the summary". Start directly with the content.
    
    Paper: {title} ({year}) by {authors}
    Abstract/Context: {abstract}
    
    OUTPUT FORMAT:
    
    <h3>1. Keywords</h3>
    <p><strong>[Keyword 1]</strong>, <strong>[Keyword 2]</strong>, ...</p>

    <h3>2. Subject</h3>
    <p><strong>General:</strong> [Broad Field]<br><strong>Specific:</strong> [Narrow Focus]</p>

    <h3>3. Research Question & Takeaway</h3>
    <p><strong>Question:</strong> [Infer the question]<br><strong>Takeaway:</strong> [Significant idea]</p>

    <h3>4. Methodological Approach</h3>
    <p><strong>Method:</strong> [Infer method]<br><strong>Sample:</strong> [Population]<br><strong>Reflection:</strong> [My critique of the rigor]</p>

    <h3>5. Results / Findings</h3>
    <p><strong>Findings:</strong> [Summarize key results]<br><strong>Reflection:</strong> [How this connects to my work]</p>

    <h3>6. Limitations</h3>
    <p>[List limitations]</p>

    <h3>7. Significance</h3>
    <p><strong>Reflection:</strong> [Why this matters to my DBA research at Yale]</p>

    <h3>8. Originality</h3>
    <p><strong>Contribution:</strong> [What is new?]</p>

    <h3>9. AI Disclosure</h3>
    <p><strong>Tool:</strong> Google Gemini via Python Script.<br><strong>Reflection:</strong> Initial summary drafted by AI; verified by Darice.</p>

    <h3>10. Next Steps</h3>
    <p>[Placeholder for future references]</p>
    
    <h3>ANNOTATED BIBLIOGRAPHY ENTRY</h3>
    [Write a single coherent paragraph of approx 150-200 words.
    Structure:
    - Sentences 1-2: Summarize the content/argument in plain English.
    - Sentences 3-4: Assess the methodology and reliability critically.
    - Sentences 5-6: Reflect on its relevance to IT Governance, AI, or Equity in Higher Ed using 'I' statements.]
    
    <h3>DATA EXTRACTION</h3>
    Setting: [Extract Country or Context (e.g., "USA", "UK", "Global", "Unknown")]
    Tags: [Select relevant tags ONLY from lists below]
    
    THEORIES: {theory_str}
    METHODS: {method_str}
    CONTEXTS: {context_str}
    STRATEGY: {strategy_str}
    LEADERSHIP: {leadership_str}
    """
    
    # Retry Logic for Rate Limits (429 Errors)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                print(f"  [AI 429] Rate limit hit. Cooling down for 60s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(60)
            else:
                print(f"  [AI Error] {e}")
                return None
    return None

def parse_ai_response(ai_text):
    if not ai_text: return [], "", "Unknown", ""
    
    # --- CLEANUP FILLER ---
    if "<h3>1. Keywords</h3>" in ai_text:
        ai_text = ai_text[ai_text.find("<h3>1. Keywords</h3>"):]

    # --- ENHANCE READABILITY ---
    key_terms = VOCAB_THEORY + VOCAB_METHOD + VOCAB_CONTEXT + VOCAB_STRATEGY + VOCAB_LEADERSHIP
    for term in key_terms:
        ai_text = re.sub(f'(?<!<strong>){re.escape(term)}(?!</strong>)', f'<strong>{term}</strong>', ai_text, flags=re.IGNORECASE)

    tags, setting, clean_note, annotated_bib = [], "Unknown", "", ""
    
    parts = ai_text.split("<h3>DATA EXTRACTION</h3>")
    main_content = parts[0]
    
    # Extract Annotated Bib
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
        all_vocab = VOCAB_THEORY + VOCAB_METHOD + VOCAB_CONTEXT + VOCAB_STRATEGY + VOCAB_LEADERSHIP
        for vocab_word in all_vocab:
            if vocab_word in data_section: tags.append(vocab_word)
            
    return tags, clean_note, setting, annotated_bib

def format_abstract_for_readability(text):
    """Inserts line breaks before common structured abstract headers."""
    if not text: return ""
    headers = ["Background:", "Methods:", "Results:", "Conclusion:", "Objective:", "Discussion:", "Findings:"]
    formatted = text
    for h in headers:
        formatted = formatted.replace(h, f"\n\n{h}")
        formatted = formatted.replace(h.lower(), f"\n\n{h}") 
    return formatted.strip()

def search_semantic_scholar(query_text):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query_text, "year": YEAR_RANGE, "limit": 10, "fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf,citationCount"}
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

            pub_year = CURRENT_YEAR
            if hasattr(entry, 'published_parsed'):
                pub_year = entry.published_parsed.tm_year
            
            summary_text = getattr(entry, 'summary', '')
            description_text = getattr(entry, 'description', '')
            abstract = summary_text if len(summary_text) > len(description_text) else description_text
            
            abstract = re.sub('<[^<]+?>', '', abstract)
            abstract = re.sub(r'\s+', ' ', abstract).strip()
            abstract = abstract[:1500] 

            normalized_entries.append({
                'title': title, 'abstract': abstract, 'year': pub_year, 'url': entry.link,
                'citationCount': 0, 'authors': [{'name': getattr(entry, 'author', 'EDUCAUSE')}],
                'is_industry_report': True
            })
        return normalized_entries
    except Exception as e:
        print(f"  [RSS Error] {e}")
        return []

def get_sliding_scale_rules(paper_year):
    try: p_year = int(paper_year)
    except: return (0, "Unknown Year")
    if p_year >= CURRENT_YEAR: return (0, "🔥 Trending (New)")
    elif p_year == CURRENT_YEAR - 1: return (15, "⭐ Proven (Recent)")
    else: return (50, "🏆 High Impact")

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
        citations, year, title, topic, url, smart_tag, ai_note, author, setting = item
        data_for_csv.append({
            "Year": year, "Author": author, "Title": title, "Topic": topic,
            "Setting": setting, "Citations": citations, "URL": url,
            "Tag": smart_tag, "AI_Note": ai_note
        })
    new_df = pd.DataFrame(data_for_csv)
    if existing_df is not None and not existing_df.empty:
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Title'], keep='last')
    else: final_df = new_df
    final_df.to_csv("literature_matrix.csv", index=False)
    print("  [Matrix Saved] literature_matrix.csv updated.")

def update_readme_dashboard(items):
    filename = "LAST_RUN_LOG.md" 
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(filename, "w", encoding='utf-8') as f:
        f.write(f"# 📊 Weekly AI-Analyst Log\n**Run Date:** {timestamp} UTC\n\n")
        if not items: f.write(f"No new papers added this run.\n")
        else:
            f.write(f"Processed **{len(items)}** new papers:\n\n| Citations | Type | Topic | Title |\n| :---: | :--- | :--- | :--- |\n")
            for item in items:
                citations, year, title, topic, url, smart_tag, ai_note, author, setting = item
                title_display = f"[{title}]({url})" if url else title
                icon = "📄"
                if "Trending" in smart_tag: icon = "🔥"
                if "Proven" in smart_tag: icon = "⭐"
                f.write(f"| {citations} | {icon} | {topic} | {title_display} |\n")
    print(f"  [Log Updated]")

def process_searches():
    if not LIBRARY_ID or not API_KEY: return
    zot = zotero.Zotero(LIBRARY_ID, LIBRARY_TYPE, API_KEY)
    ai_model = setup_gemini()
    report_data = []
    zotero_memory = load_zotero_titles(zot)
    existing_df = None
    if os.path.exists("literature_matrix.csv"):
        try: existing_df = pd.read_csv("literature_matrix.csv")
        except: pass
        if existing_df is not None and not existing_df.empty:
            for t in existing_df['Title']: 
                if pd.notna(t): zotero_memory.add(str(t).lower().strip())

    print(f"Starting Analyst Engine. Batch: {TODAY_TAG}")

    # --- PROCESS 1: ACADEMIC PAPERS ---
    for search in SEARCH_QUERIES:
        query = search['query']
        tag_name = search['tag']
        print(f"\nSearching (Academic): '{query}'...")
        papers = search_semantic_scholar(query)
        if not papers: continue
        
        process_batch(papers, zot, ai_model, tag_name, report_data, zotero_memory, is_academic=True)

    # --- PROCESS 2: INDUSTRY FEEDS (RSS) ---
    for feed in RSS_FEEDS:
        url = feed['url']
        tag_name = feed['tag']
        papers = fetch_rss_feed(url)
        if not papers: continue
        process_batch(papers, zot, ai_model, tag_name, report_data, zotero_memory, is_academic=False)

    update_readme_dashboard(report_data)
    save_matrix_csv(report_data, existing_df)

def process_batch(papers, zot, ai_model, tag_name, report_data, zotero_memory, is_academic):
    for paper in papers:
        title = paper.get('title', 'No Title')
        if title.lower().strip() in zotero_memory: continue

        citations = paper.get('citationCount', 0)
        p_year = paper.get('year', CURRENT_YEAR)
        
        # Clean Abstract text
        abstract = paper.get('abstract', '')
        if abstract:
            abstract = format_abstract_for_readability(abstract)
        
        # Author Parsing
        author_str = "Unknown"
        if paper.get('authors'):
            try:
                zotero_creators = []
                for auth in paper['authors']:
                    if 'name' in auth:
                        name_parts = auth['name'].split()
                        if len(name_parts) > 1:
                            last = name_parts[-1]
                            first = " ".join(name_parts[:-1])
                            zotero_creators.append({'creatorType': 'author', 'firstName': first, 'lastName': last})
                        else:
                            zotero_creators.append({'creatorType': 'author', 'firstName': '', 'lastName': auth['name']})
                
                author_str = ", ".join([a['name'] for a in paper['authors'][:3]])
                if len(paper['authors']) > 3: author_str += " et al."
            except:
                zotero_creators = [{'creatorType': 'author', 'firstName': '', 'lastName': 'Unknown'}]
        else:
             zotero_creators = [{'creatorType': 'author', 'firstName': '', 'lastName': 'Unknown'}]

        if is_academic:
            required_citations, smart_tag = get_sliding_scale_rules(p_year)
            if citations < required_citations: continue
        else:
            smart_tag = "📢 Industry Insight"

        ai_tags, ai_note_content, setting, annotated_bib = [], "", "Unknown", ""
        
        if ai_model and abstract:
            print(f"  [AI] Drafting Note: {title[:30]}...")
            ai_text = analyze_paper_with_ai(ai_model, title, abstract, author_str, p_year)
            ai_tags, ai_note_content, setting, annotated_bib = parse_ai_response(ai_text)
            
            # STRICT MODE
            if not ai_note_content:
                print(f"  [Skipped] AI Analysis failed for: {title[:30]}")
                continue
            
            # 1 second sleep (Paid Tier)
            time.sleep(1)

        template = zot.item_template('journalArticle' if is_academic else 'webpage')
        template['title'] = title
        template['abstractNote'] = abstract
        template['date'] = str(p_year)
        template['extra'] = f"Citations: {citations}"
        
        # SAVE ANNOTATION TO EXTRA FOR CSL
        if annotated_bib:
            template['extra'] += f"\n\n{annotated_bib}"
        
        template['url'] = paper.get('url', '')
        if paper.get('venue'): template['publicationTitle'] = paper['venue']
        elif is_academic: template['publicationTitle'] = "Semantic Scholar"
        
        template['creators'] = zotero_creators
        
        tag_list = [{'tag': '_NEW_ARRIVAL'}, {'tag': smart_tag}, {'tag': TODAY_TAG}, {'tag': tag_name}]
        for t in ai_tags: tag_list.append({'tag': f"#{t}"})
        template['tags'] = tag_list

        try:
            resp = zot.create_items([template])
            if resp and 'successful' in resp:
                print(f"  [Success] Added: {title[:20]}...")
                
                # LOGGING
                log_operation("Import", title, f"Source: {tag_name}", "Success")

                parent_key = resp['successful']['0']['key']
                if ai_note_content:
                    # Note 1: 10-Point Summary
                    note_template = zot.item_template('note')
                    note_template['parentItem'] = parent_key
                    note_template['note'] = ai_note_content
                    note_template['tags'] = [{'tag': '10-Point-Draft'}]
                    zot.create_items([note_template])
                    
                    # Note 2: Annotated Bib (Renamed with Author/Year for search)
                    if annotated_bib:
                        bib_note = zot.item_template('note')
                        bib_note['parentItem'] = parent_key
                        # Use Author in title for easy Zotero search
                        bib_note['note'] = f"<h3>Annotated Bib: {author_str} ({p_year})</h3><p>{annotated_bib}</p>"
                        bib_note['tags'] = [{'tag': 'Annotated Bib'}]
                        zot.create_items([bib_note])
                
                report_data.append((citations, p_year, title, tag_name, template['url'], smart_tag, ai_note_content, author_str, setting))
                zotero_memory.add(title.lower().strip())
        except Exception as e: 
            print(f"  [Upload Error] {e}")
            log_operation("Zotero Upload", title, str(e), "Error")

if __name__ == "__main__":
    process_searches()
