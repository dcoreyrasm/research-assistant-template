# 🤖 AI Research Assistant Template

**An autonomous research agent that automates literature discovery, synthesis, and knowledge management for academic research.**

This toolkit uses Python and Large Language Models (LLMs) to scan for new academic papers, sync them to your Zotero library, analyze their relevance to *your* specific research questions, and generate weekly synthesis reports.

![Status](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Capabilities

* **🕵️ Automatic Discovery:** Scans Semantic Scholar and RSS feeds for papers matching your keywords.
* **🧠 Intelligent Analysis:** Reads abstracts, tags papers, and scores them based on relevance to your research questions.
* **📂 Zotero Sync:** Automatically adds metadata, tags, and AI-generated summaries (10-point breakdowns) to your Zotero library.
* **📝 Report Generation:** Writes weekly synthesis reports, literature review outlines, and "Devil's Advocate" critiques.
* **🕸️ Knowledge Graphing:** Visualizes your library as an interactive network to spot clusters and connections.
* **🕵️ Gap Hunting:** Analyzes citations to find seminal papers you are missing.
* **☁️ Cloud Backup:** Syncs generated reports to Dropbox and commits them to GitHub (optional).

---

## 📂 Project Structure

| Script | Role | Description |
| :--- | :--- | :--- |
| **`scholar_sync.py`** | **The Engine** | The core collector. Scans APIs/RSS, filters by relevance, and syncs to Zotero. |
| **`synthesize.py`** | **The Writer** | Generates Markdown reports (Synthesis, Critiques, LinkedIn drafts) based on your library. |
| **`gap_hunter.py`** | **The Detective** | Scans your library's bibliographies to find "missing" seminal texts. |
| **`visualize_library.py`** | **The Mapmaker** | Generates an interactive HTML network graph of your research. |
| **`manual_import.py`** | **The Ingester** | Processes local PDFs dropped into the `manual_pdfs/` folder. |
| **`fix_metadata.py`** | **The Librarian** | Uses AI to fix "Uncategorized" papers in your tracking CSV. |
| **`dashboard.py`** | **The UI** | A Streamlit dashboard to view analytics and logs locally. |

---

## 🛠️ Prerequisites

To use this tool, you will need:

1.  **Zotero Account:** Free account + Zotero Desktop installed.
2.  **Google Gemini API Key:** (Free tier available via [Google AI Studio](https://aistudio.google.com/)).
3.  **GitHub Account:** (Optional) To run the automation in the cloud via GitHub Actions.
4.  **Dropbox API Token:** (Optional) If you want reports backed up to Dropbox.

---

## ⚙️ Setup & Configuration

### 1. Installation
Clone the repository and install dependencies:

```bash
git clone [https://github.com/your-username/research-assistant-template.git](https://github.com/your-username/research-assistant-template.git)
cd research-assistant-template
pip install -r requirements.txt

2. Environment Variables (.env)
Create a file named .env in the root directory. Do not commit this file to GitHub.

# REQUIRED
ZOTERO_USER_ID=12345678              # Found in Zotero Settings > Feeds/API
ZOTERO_API_KEY=your_zotero_key       # Create in Zotero Settings > Developer
GEMINI_API_KEY=your_gemini_key       # From Google AI Studio

# OPTIONAL (For Dropbox Sync)
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token

3. Customize Your Research (scholar_sync.py)
Open scholar_sync.py and look for the User Configuration Section. Update these lists to match your field:

MY_RESEARCH_QUESTIONS: The specific questions the AI uses to score paper relevance.

SEARCH_QUERIES: Keywords for Semantic Scholar searches.

VOCAB_* Lists: Domain-specific tags (Theories, Methods, Contexts).

4. Customize Your Persona (synthesize.py)
Open synthesize.py and edit the PERSONA string. Tell the AI who you are (e.g., "PhD Student in History") and what writing style you prefer.

🖥️ Usage
Running Locally
You can run any script manually from your terminal:
# 1. Run the collection engine
python scholar_sync.py

# 2. Generate reports
python synthesize.py

# 3. Visualize your library
python visualize_library.py

# 4. View the dashboard
streamlit run dashboard.py

Manual Imports
To process a specific PDF that wasn't found online:

Create a folder named manual_pdfs in your root directory.

Drop your PDF files into it.

Run python manual_import.py.

🤖 Automating with GitHub Actions
This repo includes a workflow (.github/workflows/zotero_automation.yml) that runs the entire suite weekly.

Push this code to a Private GitHub repository.

Go to Settings > Secrets and variables > Actions.

Add your API keys (ZOTERO_API_KEY, GEMINI_API_KEY, etc.) as Repository Secrets.

The bot will now run automatically on the schedule defined in the YAML file (default: Monday mornings).

📂 Generated Reports
The agent generates several Markdown files in your root directory:

WEEKLY_SYNTHESIS.md: High-level summary of new trends, themes, and key papers.

EXECUTIVE_BRIEF.md: A strategic, one-page memo summarizing insights for leadership.

THE_CRITIC.md: AI critique of your library's weaknesses (great for defense prep).

GAP_ANALYSIS.md: Identifies topics where your research coverage is thin.

MISSING_SEMINAL_PAPERS.md: A list of papers frequently cited by your library that you don't own yet.

interactive_library_graph.html: A network visualization file (open in any browser).

⚠️ Important Notes
Rate Limits: The scripts include time.sleep() commands to respect Semantic Scholar and Gemini API rate limits.

Privacy: If using GitHub Actions, ensure your repository is Private if you are uploading sensitive PDFs or proprietary research data.

Dependencies: This tool relies on pyzotero and google-generativeai. Keep them updated via pip install -U -r requirements.txt.

## 🧠 Choosing a Gemini Model

Model names change often, and older ones get retired. To keep this template
working, the scripts auto-detect a model from your API key by default, so you
usually do not need to set anything.

If you want to force a specific model, you have two options:

1. Edit `MODEL_NAME` in `ai_config.py`.
2. Set an environment variable, with no code change: `export GEMINI_MODEL="gemini-2.5-flash"`

All scripts read from `ai_config.py`, so this is the single place that controls
the model. For the current list of model names, see
https://ai.google.dev/gemini-api/docs/models

To see exactly which models your key can call, run a quick check:

```python
import google.generativeai as genai, os
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
```

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
