import os
import pandas as pd
import datetime
import time
import re
from ai_config import setup_gemini
from zoneinfo import ZoneInfo 

# --- CONFIGURATION ---
TIMEZONE = "America/New_York" # Change to your local timezone

# --- PERSONA & CONTEXT ---
# Update this string to match your professional role and style
PERSONA = """
CORE CONTEXT:
I am [YOUR_NAME], [YOUR_ROLE] at [YOUR_ORG].
You are my executive research assistant.

STRICT STYLE GUIDE (AGGRESSIVE SIMPLIFICATION):
1. **NO FLUFF:** Delete words like "It is important to note," "Furthermore," "In conclusion."
2. **ACTIVE VOICE:** Say "AI changes governance," not "Governance is changed by AI."
3. **SCANNABLE:** Use Emojis as visual anchors. Use bolding for key terms.
4. **SIMPLE:** Write at an 8th-grade reading level. No academic jargon.
"""

def load_matrix_data():
    try:
        if not os.path.exists('literature_matrix.csv'): return None
        df = pd.read_csv('literature_matrix.csv')
        
        if 'Priority' not in df.columns: df['Priority'] = 'Medium'
        df['Priority'] = df['Priority'].fillna('Medium').astype(str)
        df['Title'] = df['Title'].fillna('Untitled')
        df['Topic'] = df['Topic'].fillna('Uncategorized')
        df['URL'] = df['URL'].fillna('#') 
        df['Author'] = df['Author'].fillna('Unknown Author')
        df['Year'] = df['Year'].fillna('n.d.')
        
        if 'Alignment_Score' in df.columns:
            df['Alignment_Score'] = pd.to_numeric(df['Alignment_Score'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def clean_html_note(raw_note):
    if pd.isna(raw_note) or str(raw_note) == 'nan': return "No summary."
    return str(raw_note).replace('<h3>', '**').replace('</h3>', '**').replace('<p>', '').replace('</p>', '\n')

def append_bibliography(df_subset):
    if df_subset is None or df_subset.empty: return ""
    bib = "\n\n---\n### 📚 References\n"
    for index, row in df_subset.iterrows():
        title = str(row.get('Title', 'Untitled')).strip()
        url = str(row.get('URL', '#')).strip()
        author = str(row.get('Author', 'Unknown Author')).strip()
        year = str(row.get('Year', 'n.d.')).replace('.0', '') 
        bib += f"* {author}. ({year}). *{title}*. {url}\n"
    return bib

def run_ai_generation(model, prompt, report_name):
    print(f"  > Generating {report_name}...")
    try:
        time.sleep(1)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"    ERROR generating {report_name}: {e}")
        return f"FAILED to generate {report_name}. Error: {str(e)}"

# --- REPORT GENERATORS ---

def generate_linkedin_post(model, df):
    if 'Alignment_Score' in df.columns: top_papers = df.nlargest(3, 'Alignment_Score')
    else: top_papers = df.tail(3)
    papers_text = "\n".join([f"- {row['Title']} ({row['Topic']})" for i, row in top_papers.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Write a LinkedIn post sharing a key insight from my research this week.
    Input Data: {papers_text}
    FORMAT:
    - **Hook:** 1 catchy sentence.
    - **Body:** 3 short sentences on what I learned.
    - **Call to Action:** A question to my network.
    - **Hashtags:** #Research #Innovation #[YOUR_FIELD]
    """
    return run_ai_generation(model, prompt, "LinkedIn Post") + append_bibliography(top_papers)

def generate_devils_advocate(model, df):
    target_df = df[df['Priority'].str.contains('Critical|High', case=False, na=False)].tail(5)
    if target_df.empty: 
        print("    (No Critical papers found. Analyzing random recent papers.)")
        target_df = df.tail(5)
    papers_text = "\n".join([f"- {row['Title']} ({row['Year']})" for i, row in target_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Act as a harsh Critic. Critique my recent sources.
    Input Data: {papers_text}
    FORMAT:
    ### 🧐 Methodological Weaknesses
    - Are these papers too old? Biased? 
    - (Critique in 2 bullets).
    ### ⚠️ Theoretical Blindspots
    - What theories are these papers ignoring?
    ### 🛡️ Defense Prep
    - "How would you defend using [Paper X] given its limitations?"
    """
    return run_ai_generation(model, prompt, "The Critic") + append_bibliography(target_df)

def generate_synthesis(model, df):
    priority_papers = df.tail(15)
    if 'Priority' in df.columns:
        priority_papers = df[df['Priority'].str.contains('Critical|High', case=False, na=False)].tail(15)
        if priority_papers.empty: priority_papers = df.tail(15)
    papers_text = "\n".join([f"- {row['Title']} ({row['Year']}): {clean_html_note(row.get('AI_Note', ''))[:500]}\n" for i, row in priority_papers.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Write a 'Weekly Synthesis'.
    Input Data: {papers_text}
    FORMAT:
    1. **🚨 BLUF (Bottom Line Up Front):** 1 sentence summary.
    2. **🔑 Key Themes:**
       - **Theme Name:** 2 bullet points max.
    3. **🎓 Research Impact:** 1 sentence.
    """
    return run_ai_generation(model, prompt, "Weekly Synthesis") + append_bibliography(priority_papers)

def generate_practitioner_toolkit(model, df):
    relevant_df = df.tail(20)
    papers_text = "\n".join([f"- {row['Title']}: {clean_html_note(row.get('AI_Note', ''))[:300]}" for i, row in relevant_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Create a 'Practitioner Toolkit'.
    Input Data: {papers_text}
    FORMAT:
    ### 🗣️ Talking Points
    - (Max 15 words per bullet)
    ### ⚠️ Emerging Risks
    - (Max 15 words per bullet)
    ### ✅ Monday Actions
    - (Simple verbs)
    """
    return run_ai_generation(model, prompt, "Practitioner Toolkit") + append_bibliography(relevant_df)

def generate_executive_brief(model, df):
    target_df = df.tail(10)
    papers_text = "\n".join([f"- {row['Title']}" for i, row in target_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Write a 1-page Strategic Memo.
    Input Data: {papers_text}
    FORMAT:
    **To:** [LEADERSHIP ROLE] | **From:** [YOUR NAME]
    **🎯 The Headline:** (1 sentence)
    **💡 Strategic Insights:** (Bullet points)
    **📉 Recommendation:** (1 sentence).
    """
    return run_ai_generation(model, prompt, "Executive Brief") + append_bibliography(target_df)

def generate_methodology_scan(model, df):
    target_df = df.sample(min(40, len(df)))
    papers_text = "\n".join([f"- {row['Title']} (Method: {clean_html_note(row.get('AI_Note', ''))[:200]})" for i, row in target_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Analyze research methodologies.
    Input Data: {papers_text}
    FORMAT:
    ### 📊 At a Glance
    - **Dominant Method:** [Method]
    - **Missing Method:** [Method]
    ### 🧩 Method Comparison
    | Method Type | Est. Count | Best Example |
    | :--- | :--- | :--- |
    | (Fill Table) | | |
    ### 🏆 Opportunity
    - Use [Method X].
    """
    return run_ai_generation(model, prompt, "Methodology Scan") + append_bibliography(target_df)

def generate_priority_reading_list(model, df):
    if 'Alignment_Score' not in df.columns: return "No alignment data available."
    top = df.nlargest(20, 'Alignment_Score')
    papers_text = "\n".join([f"- {row['Title']} (Score: {row['Alignment_Score']})" for i, row in top.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Create a Reading Plan.
    Input Data: {papers_text}
    FORMAT:
    | 🔥 Priority | 📄 Paper Title | 🧠 Why I should read this (10 words max) |
    """
    return run_ai_generation(model, prompt, "Reading List") + append_bibliography(top)

def generate_lit_review_outline(model, df):
    target_df = df.sample(min(50, len(df)))
    papers_text = "\n".join([f"- {row['Title']} ({row['Topic']})" for i, row in target_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Outline a Literature Review Chapter.
    Input Data: {papers_text}
    FORMAT:
    Use Roman Numerals (I, II, III).
    """
    return run_ai_generation(model, prompt, "Lit Review Outline") + append_bibliography(target_df)

def generate_gap_analysis(model, df):
    topic_counts = df['Topic'].value_counts().to_string()
    prompt = f"""{PERSONA}
    TASK: Identify gaps.
    Input Data: {topic_counts}
    FORMAT:
    - 🟩 **Well Covered:** [Topics]
    - 🟥 **Critical Gaps:** [Topics]
    - 🔭 **Next Search:** [Search Query]
    """
    return run_ai_generation(model, prompt, "Gap Analysis")

def generate_connect_the_dots(model, df):
    sample_df = df.sample(n=min(15, len(df)))
    papers_text = "\n".join([f"- {row['Title']} ({row['Topic']})" for i, row in sample_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Find 3 unexpected connections.
    FORMAT:
    - 🔗 **[Topic A] + [Topic B]:** (1 sentence explanation).
    """
    return run_ai_generation(model, prompt, "Connect the Dots") + append_bibliography(sample_df)

def generate_deep_dive(model, df, keyword, search_columns=['Topic', 'Title']):
    mask = pd.Series([False] * len(df))
    for col in search_columns:
        if col in df.columns: mask = mask | df[col].str.contains(keyword, case=False, na=False)
    topic_df = df[mask].tail(10)
    if topic_df.empty: return f"No papers found matching '{keyword}'."
    papers_text = "\n".join([f"- {row['Title']}: {clean_html_note(row.get('AI_Note', ''))[:500]}" for i, row in topic_df.iterrows()])
    prompt = f"""{PERSONA}
    TASK: Deep Dive on '{keyword}'.
    FORMAT:
    ### 📘 Definition
    ### ⚔️ Key Debate
    ### 🏛️ Implications
    """
    return run_ai_generation(model, prompt, f"Deep Dive: {keyword}") + append_bibliography(topic_df)

def update_main_readme(exec_brief, weekly_syn, df):
    try:
        ny_time = datetime.datetime.now(ZoneInfo(TIMEZONE))
    except:
        ny_time = datetime.datetime.now()
        
    timestamp = ny_time.strftime('%Y-%m-%d')
    
    total_papers = len(df)
    try: top_topic = df['Topic'].mode()[0]
    except: top_topic = "N/A"
    fuel = 0
    if 'Alignment_Score' in df.columns and total_papers > 0:
        fuel = int((df['Alignment_Score'].mean() / 10) * 100)
    bar_len = int(fuel / 10)
    progress_bar = "▓" * bar_len + "░" * (10 - bar_len)
    brief_snippet = exec_brief.split('\n\n')[0] if exec_brief and "FAILED" not in exec_brief else "Update Pending."
    content = f"""# 🎓 Research Agent Dashboard
**Last Updated:** {timestamp} | **Owner:** [YOUR_NAME] 

## 📊 Research Status
| 📚 Total Papers | 🏆 Top Topic | ⛽ Alignment Fuel |
| :---: | :---: | :---: |
| **{total_papers}** | **{top_topic}** | **{fuel}%** {progress_bar} |

## 🚀 Strategic Intelligence (Latest)
{brief_snippet}
> [Read Full Executive Brief](EXECUTIVE_BRIEF.md)

## 📂 Live Reports
| Report | Purpose |
| :--- | :--- |
| [**Weekly Synthesis**](WEEKLY_SYNTHESIS.md) | State of the Union. |
| [**The Critic**](THE_CRITIC.md) | **NEW:** Devil's Advocate / Defense Prep. |
| [**Practitioner Toolkit**](PRACTITIONER_TOOLKIT.md) | Actionable advice for operations. |
| [**Methodology Scan**](METHODOLOGY_SCAN.md) | Analysis of research methods. |
| [**Lit Review Outline**](LIT_REVIEW_OUTLINE.md) | Chapter 2 Draft. |
| [**Priority Reading**](PRIORITY_READING_LIST.md) | Ranked list of what to read next. |
| [**Gap Analysis**](GAP_ANALYSIS.md) | Where is my research thin? |
| [**Draft LinkedIn Post**](LINKEDIN_DRAFT.md) | Share your journey. |

## 🔍 Deep Dives
* [**Generative AI**](DEEP_DIVE_Generative_AI.md)
* [**Class Assignments**](DEEP_DIVE_Class_Assignment.md)

## 🕸️ Knowledge Graph
[**View Interactive Map**](interactive_library_graph.html) *(Download raw file to view)*
"""
    with open("README.md", "w", encoding='utf-8') as f: f.write(content)
    print("Saved: README.md (Dashboard Updated)")

def save_file(filename, title, content):
    if not content:
        print(f"    [WARNING] No content generated for {filename}. Saving fallback.")
        content = "Generation failed or returned empty. Check logs."
    
    try:
        ny_time = datetime.datetime.now(ZoneInfo(TIMEZONE))
    except:
        ny_time = datetime.datetime.now()
        
    timestamp = ny_time.strftime('%B %d, %Y at %I:%M %p')
    
    with open(filename, "w", encoding='utf-8') as f:
        f.write(f"# {title}\n**Generated:** {timestamp}\n\n{content}")
    print(f"    [SAVED] {filename}")

if __name__ == "__main__":
    print("--- STARTING SYNTHESIZER ---")
    model = setup_gemini()
    if model:
        df = load_matrix_data()
        if df is not None and not df.empty:
            
            # --- 1. GENERATE LINKEDIN & CRITIC FIRST ---
            linkedin_post = generate_linkedin_post(model, df)
            the_critic = generate_devils_advocate(model, df)
            
            save_file("LINKEDIN_DRAFT.md", "Thought Leadership Draft", linkedin_post)
            save_file("THE_CRITIC.md", "The Critic (Defense Prep)", the_critic)

            # --- 2. GENERATE STANDARD REPORTS ---
            weekly_syn = generate_synthesis(model, df)
            exec_brief = generate_executive_brief(model, df)
            
            save_file("WEEKLY_SYNTHESIS.md", "Weekly Synthesis", weekly_syn)
            save_file("EXECUTIVE_BRIEF.md", "Strategic Memo", exec_brief)

            save_file("METHODOLOGY_SCAN.md", "Methodology Scan", generate_methodology_scan(model, df))
            save_file("PRIORITY_READING_LIST.md", "Reading Plan", generate_priority_reading_list(model, df))
            save_file("LIT_REVIEW_OUTLINE.md", "Chapter 2 Outline", generate_lit_review_outline(model, df))
            save_file("GAP_ANALYSIS.md", "Gap Analysis", generate_gap_analysis(model, df))
            save_file("PRACTITIONER_TOOLKIT.md", "Practitioner Toolkit", generate_practitioner_toolkit(model, df))
            save_file("CONNECT_THE_DOTS.md", "Unexpected Connections", generate_connect_the_dots(model, df))
            
            # Custom Deep Dives - Add/Remove as needed
            save_file("DEEP_DIVE_Generative_AI.md", "Deep Dive: GenAI", generate_deep_dive(model, df, "Generative AI", search_columns=['Topic', 'Title']))
            
            update_main_readme(exec_brief, weekly_syn, df)
            print("--- SYNTHESIS COMPLETE ---")
        else:
            print("No data to synthesize.")
