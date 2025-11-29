import os
import pandas as pd
import google.generativeai as genai
import datetime
from collections import Counter

# --- CONFIGURATION ---
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

def setup_gemini():
    if not GEMINI_KEY:
        print("Error: Missing Gemini Key.")
        return None
    
    genai.configure(api_key=GEMINI_KEY)
    
    # --- MODEL HUNTER ---
    # Dynamically find a working model to prevent 404 errors
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

def load_weekly_data():
    """
    Reads the literature_matrix.csv.
    """
    try:
        if not os.path.exists('literature_matrix.csv'):
            print("No matrix file found. Running synthesis on empty data.")
            return None
        df = pd.read_csv('literature_matrix.csv')
        return df
    except Exception as e:
        print(f"Error reading matrix: {e}")
        return None

def clean_html_note(raw_note):
    """Helper to strip HTML for the AI prompt to save tokens."""
    if pd.isna(raw_note) or str(raw_note) == 'nan':
        return "No summary available."
    return str(raw_note).replace('<h3>', '**').replace('</h3>', '**').replace('<p>', '').replace('</p>', '\n')

def generate_synthesis(model, df):
    """
    Feeds the batch of papers to Gemini for a narrative synthesis (Academic).
    """
    papers_text = ""
    # Process top 15 rows (The "News")
    for index, row in df.head(15).iterrows():
        author = row.get('Author', 'Unknown Authors')
        if pd.isna(author): author = "Unknown Authors"
        
        note = clean_html_note(row.get('AI_Note', ''))
        
        papers_text += f"\n--- SOURCE: '{row['Title']}' by {author} ({row['Year']}) ---\nTopic: {row['Topic']}\nSetting: {row.get('Setting', 'Unknown')}\nSummary Data: {note[:1000]}\n"

    prompt = f"""
    Act as a DBA doctoral candidate. I have processed a batch of {len(df)} new academic papers this week.
    
    Here is the data for the papers:
    {papers_text}
    
    TASK:
    Write a "Weekly Synthesis" document (approx 400 words) in Markdown.
    
    CRITICAL CITATION RULES:
    1. **ALWAYS** refer to papers by **Author (Year)** format. (e.g. "Smith et al. (2025) argue that...", "Jones (2024) presents a case study...")
    2. If the author is unknown, use the Title.
    3. **NEVER** use generic labels like "Paper 1".
    
    STRUCTURE:
    1. **Executive Summary**: One paragraph relating the dominant theme of this batch to "IT Governance in Higher Ed".
    2. **Comparative Analysis**: Connect the papers. (e.g., "While Smith (2025) focuses on X, Jones (2024) contrasts this by..."). Group them by methodology or theory if possible.
    3. **Implications for Yale**: A brief bulleted list of how these findings might apply to IT leadership at a large institution.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return "Could not generate synthesis."

def generate_executive_brief(model, df):
    """
    Generates a practical, non-academic memo for a CIO/IT Leader audience.
    """
    papers_text = ""
    for index, row in df.head(10).iterrows():
        author = row.get('Author', 'Unknown')
        title = row.get('Title', 'Unknown')
        setting = row.get('Setting', 'Unknown')
        papers_text += f"- {title} ({author}) - Context: {setting}\n"

    prompt = f"""
    Act as a Chief Strategy Officer at a large university (like Yale).
    Review this list of new research papers:
    {papers_text}
    
    TASK:
    Write a 1-page "Strategic Intelligence Memo" to the CIO.
    
    TONE: Professional, concise, actionable. No academic jargon.
    
    STRUCTURE:
    1. **Headline**: The single biggest trend this week.
    2. **Strategic Risks**: What should we be worried about? (e.g. Integrity, Bias, Resistance).
    3. **Opportunities**: Where can we innovate?
    4. **Recommended Action**: One concrete step we should take based on this research.
    """
    
    try:
        return model.generate_content(prompt).text
    except: return "Could not generate brief."

def generate_deep_dive(model, df, topic):
    """
    Generates a deep dive synthesis for a specific topic using ALL historical data.
    """
    # Filter for the specific topic
    if 'Topic' not in df.columns: return None
    
    topic_df = df[df['Topic'] == topic]
    
    # If we have too many, take the top 30 most cited
    if len(topic_df) > 30:
        topic_df = topic_df.sort_values(by='Citations', ascending=False).head(30)
    
    papers_text = ""
    for index, row in topic_df.iterrows():
        author = row.get('Author', 'Unknown Authors')
        if pd.isna(author): author = "Unknown Authors"
        raw_note = clean_html_note(row.get('AI_Note', ''))[:500] 
        papers_text += f"\n- {author} ({row['Year']}): {row['Title']}\n  Note: {raw_note}\n"

    prompt = f"""
    Act as a DBA doctoral candidate writing a Literature Review Chapter.
    
    I have collected {len(topic_df)} papers on the topic: **{topic}**.
    
    Here is the cumulative data (Historical & New):
    {papers_text}
    
    TASK:
    Write a "Thematic Deep Dive" (approx 600 words) analyzing the State of the Field for {topic}.
    
    STRUCTURE:
    1. **Evolution of the Field**: How has the conversation on {topic} shifted over time (look at the years)?
    2. **Dominant Theoretical Lens**: Based on the notes, what theories are most commonly applied? (e.g., Agency Theory vs. Stewardship).
    3. **Methodological Trends**: Are these mostly case studies, quantitative, or reviews?
    4. **Gap Analysis**: What is missing from this collection? What should I research next to fill the gap?
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Deep Dive Error: {e}")
        return None

def save_file(filename, content):
    with open(filename, "w", encoding='utf-8') as f:
        f.write(content)
    print(f"Saved: {filename}")

if __name__ == "__main__":
    model = setup_gemini()
    if model:
        df = load_weekly_data()
        if df is not None and not df.empty:
            # 1. Run Weekly Synthesis (Academic)
            print("Generating Weekly Synthesis...")
            synthesis = generate_synthesis(model, df)
            save_file("WEEKLY_SYNTHESIS.md", f"# 🧠 Weekly Dissertation Synthesis\n**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n{synthesis}")
            
            # 2. Run Executive Brief (Practical)
            print("Generating Executive Brief...")
            brief = generate_executive_brief(model, df)
            save_file("EXECUTIVE_BRIEF.md", f"# 💼 CIO Strategic Memo\n**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n{brief}")

            # 3. Run Topic Deep Dive (History)
            if 'Topic' in df.columns:
                counts = Counter(df['Topic'].dropna())
                if counts:
                    top_topic = counts.most_common(1)[0][0]
                    print(f"Generating Deep Dive for top topic: {top_topic}...")
                    deep_dive = generate_deep_dive(model, df, top_topic)
                    if deep_dive:
                        safe_filename = f"DEEP_DIVE_{top_topic.replace(' ', '_')}.md"
                        save_file(safe_filename, f"# 🌊 Deep Dive: {top_topic}\n**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n{deep_dive}")
        else:
            print("No data to synthesize.")
