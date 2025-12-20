import os
import pandas as pd
import requests
import time
from collections import Counter
import csv
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILE = "literature_matrix.csv"
OUTPUT_FILE = "MISSING_SEMINAL_PAPERS.md"
# We only analyze papers that are already "High" or "Critical" priority
# to ensure we are finding foundations of GOOD research, not noise.
PRIORITY_FILTER = ['Critical', 'High'] 

def load_local_library():
    """Loads the titles we already have so we don't recommend what you own."""
    if not os.path.exists(INPUT_FILE):
        print("Error: literature_matrix.csv not found.")
        return None, set()
    
    df = pd.read_csv(INPUT_FILE)
    # Normalize titles to lowercase for comparison
    existing_titles = set(df['Title'].dropna().str.lower().str.strip())
    
    # Get high priority papers to analyze
    if 'Priority' in df.columns:
        analysis_corpus = df[df['Priority'].isin(PRIORITY_FILTER)]
        # If we don't have enough high priority, take the top 20 by citation count
        if len(analysis_corpus) < 5:
            analysis_corpus = df.nlargest(20, 'Citations')
    else:
        analysis_corpus = df.tail(20)
        
    return analysis_corpus, existing_titles

def get_citations_from_semantic_scholar(paper_title):
    """Asks API: 'What papers does THIS paper cite?'"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # 1. Find the paper ID first
    params = {"query": paper_title, "limit": 1, "fields": "paperId"}
    try:
        time.sleep(1) # Be nice to the API
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200: return None
        
        data = r.json()
        if not data.get('data'): return None
        paper_id = data['data'][0]['paperId']
        
        # 2. Get its references (Citations OUT)
        # We fetch the top 100 references for this paper
        ref_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"
        ref_params = {"limit": 100, "fields": "title,year,authors,citationCount,url,paperId"}
        
        r_ref = requests.get(ref_url, params=ref_params, timeout=10)
        if r_ref.status_code == 200:
            return r_ref.json().get('data', [])
        return []
        
    except Exception as e:
        print(f"  [API Error] {e}")
        return []

def analyze_gaps():
    print("🕵️ Starting Seminal Gap Hunter...")
    
    # 1. Load Data
    corpus, existing_titles = load_local_library()
    if corpus is None or corpus.empty:
        print("No high-priority papers found to analyze.")
        return

    print(f"  [Scope] Analyzing bibliographies of {len(corpus)} priority papers...")
    
    # 2. Build the "Mention Count"
    # This dictionary tracks: "Paper Title" -> Count of how many times it was cited
    citation_counts = Counter()
    citation_metadata = {} # Stores details like Year/Author so we can display them later

    for index, row in corpus.iterrows():
        title = row['Title']
        print(f"    -> Scanning bibliography of: '{title[:30]}...'")
        
        references = get_citations_from_semantic_scholar(title)
        if not references: continue
        
        for ref in references:
            cited_paper = ref.get('citedPaper', {})
            ref_title = cited_paper.get('title')
            
            if not ref_title: continue
            
            # Normalization
            clean_title = ref_title.lower().strip()
            
            # CRITICAL CHECK: Ignore if we already have it
            if clean_title in existing_titles:
                continue
                
            citation_counts[clean_title] += 1
            
            # Store metadata if we haven't yet
            if clean_title not in citation_metadata:
                authors = cited_paper.get('authors', [])
                author_str = authors[0]['name'] if authors else "Unknown"
                citation_metadata[clean_title] = {
                    'title': ref_title,
                    'year': cited_paper.get('year', 'N/A'),
                    'author': author_str,
                    'global_citations': cited_paper.get('citationCount', 0),
                    'url': cited_paper.get('url', '#')
                }

    # 3. Identify the "Missing Seminal"
    # Logic: If 3 or more of your high-priority papers cite the SAME missing paper,
    # that is a strong signal you are missing a foundational text.
    
    # Sort by frequency (how many of YOUR papers cited it)
    most_common = citation_counts.most_common(20)
    
    report_content = "# 🕵️ Gap Hunter: Missing Seminal Papers\n"
    report_content +=f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    report_content += "This report analyzed the bibliographies of your **High Priority** papers to find foundational texts you are missing.\n\n"
    
    found_gaps = False
    
    for clean_title, count in most_common:
        # Filter: Only show if cited by at least 2 different papers in your library
        if count < 2: continue
        
        found_gaps = True
        meta = citation_metadata[clean_title]
        
        report_content += f"### 🔥 {meta['title']} ({meta['year']})\n"
        report_content += f"**Cited by {count} papers in your library.**\n"
        report_content += f"- **Author:** {meta['author']}\n"
        report_content += f"- **Global Citations:** {meta['global_citations']}\n"
        report_content += f"- [View on Semantic Scholar]({meta['url']})\n\n"
        
        print(f"  [Found Gap] '{meta['title']}' (Cited by {count} of your papers)")

    if not found_gaps:
        report_content += "✅ Good news! Your library appears to cover the major shared citations of your current collection.\n"
        print("  [Result] No significant gaps found.")
    
    # 4. Save Report
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"  [Success] Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_gaps()
