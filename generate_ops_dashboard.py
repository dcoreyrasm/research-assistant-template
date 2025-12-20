import pandas as pd
import datetime
import os

LOG_FILE = "research_ops_log.csv"
README_FILE = "README.md"

def generate_dashboard():
    if not os.path.exists(LOG_FILE):
        print("No log file found yet.")
        return

    df = pd.read_csv(LOG_FILE)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Stats
    total_papers = len(df[df['Action'] == 'Import'])
    total_errors = len(df[df['Status'] == 'Error'])
    last_run = df['Timestamp'].max().strftime('%Y-%m-%d %H:%M')
    
    # Recent Activity (Last 5)
    recent = df.sort_values('Timestamp', ascending=False).head(5)
    recent_table = "| Time | Action | Title |\n| :--- | :--- | :--- |\n"
    for _, row in recent.iterrows():
        title_short = row['Paper_Title'][:40] + "..." if len(row['Paper_Title']) > 40 else row['Paper_Title']
        recent_table += f"| {row['Timestamp'].strftime('%m-%d %H:%M')} | {row['Action']} | {title_short} |\n"

    # Markdown Content
    dashboard = f"""
# 🎓 Research Ops Dashboard
**Status:** 🟢 Online | **Last Run:** {last_run}

## 📊 System Vital Signs
| Metric | Value |
| :--- | :--- |
| **Total Papers Captured** | {total_papers} |
| **Error Rate** | {total_errors} errors |
| **Current Brain** | {df['Model'].iloc[-1] if not df.empty else 'Unknown'} |
| **Prompt Version** | {df['Prompt_Version'].iloc[-1] if not df.empty else 'Unknown'} |

## ⚡ Recent Activity Log
{recent_table}

## 📂 Latest Intelligence
* [📄 Weekly Synthesis](WEEKLY_SYNTHESIS.md)
* [💼 Executive Brief](EXECUTIVE_BRIEF.md)
* [🔗 Connect the Dots](CONNECT_THE_DOTS.md)
* [🛠️ Practitioner Toolkit](PRACTITIONER_TOOLKIT.md)

*(Full audit log available in `research_ops_log.csv`)*
    """
    
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(dashboard)
    print("Dashboard updated.")

if __name__ == "__main__":
    generate_dashboard()
