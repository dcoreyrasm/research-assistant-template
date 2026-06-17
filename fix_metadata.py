import pandas as pd
from ai_config import setup_gemini
import os
import time

# --- CONFIGURATION ---
INPUT_FILE = "literature_matrix.csv"

# Your Official Controlled Vocabulary
# USER: Update this list with the topics relevant to your research.
VALID_TOPICS = [
    "Topic A", "Topic B", "Topic C",
    "Methodology X", "Methodology Y",
    "Theory Z", "Theory Q"
]

def get_true_topic(model, title, abstract):
    """Asks AI to classify the paper."""
    prompt = f"""
    Act as a Research Librarian.
    Classify the following academic paper into exactly ONE of these topics:
    {VALID_TOPICS}

    Paper Title: {title}
    Abstract Snippet: {str(abstract)[:500]}

    Rules:
    1. Return ONLY the topic name.
    2. If it fits none perfectly, pick the closest one.
    3. Do not explain.
    """
    try:
        time.sleep(1.5) # Rate limiting protection
        response = model.generate_content(prompt)
        cleaned_topic = response.text.strip().replace("\n", "").replace(".", "")
        
        # Validation: Ensure AI didn't hallucinate a new topic
        for valid in VALID_TOPICS:
            if valid.lower() in cleaned_topic.lower():
                return valid
        return "Uncategorized" # Fallback
    except Exception as e:
        print(f"    [Error] AI classification failed: {e}")
        return "Manual Import" # Keep original if failed

def run_cleanup():
    if not os.path.exists(INPUT_FILE):
        print("Error: literature_matrix.csv not found.")
        return

    model = setup_gemini()
    if not model: return

    print("🧹 Starting Metadata Cleanup...")
    df = pd.read_csv(INPUT_FILE)
    
    # Check if 'Topic' column exists
    if 'Topic' not in df.columns:
        print("Error: No 'Topic' column found in CSV.")
        return

    # Count how many need fixing
    mask = df['Topic'] == "Manual Import"
    count = mask.sum()
    print(f"  Found {count} items labeled 'Manual Import'. Fixing now...")

    # Iterate and Fix
    fixed_count = 0
    for index, row in df[mask].iterrows():
        title = row['Title']
        print(f"  [{fixed_count+1}/{count}] Re-classifying: {str(title)[:30]}...")
        
        new_topic = get_true_topic(model, title, row.get('AI_Note', ''))
        
        # Apply the fix to the dataframe
        df.at[index, 'Topic'] = new_topic
        print(f"    -> New Topic: {new_topic}")
        fixed_count += 1

    # Save
    df.to_csv(INPUT_FILE, index=False)
    print(f"✅ Cleanup Complete. {fixed_count} records updated.")
    print("   Run 'visualize_library.py' next to see the corrected graph.")

if __name__ == "__main__":
    run_cleanup()
