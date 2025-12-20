# 🤖 AI Research Assistant Template

**An autonomous research agent that automates literature discovery, synthesis, and knowledge management for academic research.**

This toolkit uses Python and Large Language Models (LLMs) to scan for new academic papers, sync them to your Zotero library, analyze their relevance to your specific research questions, and generate weekly synthesis reports.

![Status](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Capabilities

* **🕵️ Automatic Discovery:** Scans Semantic Scholar and RSS feeds for papers matching your specific keywords.
* **🧠 Intelligent Analysis:** Reads abstracts, tags papers, and scores them based on relevance to *your* research questions.
* **📂 Zotero Sync:** Automatically adds metadata, tags, and AI-generated summaries to your Zotero library.
* **📝 Report Generation:** Writes weekly synthesis reports, literature review outlines, and "Devil's Advocate" critiques.
* **🕸️ Knowledge Graphing:** Visualizes your library as an interactive network to spot clusters and connections.
* **☁️ Cloud Backup:** Syncs generated reports to Dropbox (optional).

---

## 🛠️ Prerequisites

To use this tool, you will need:

1.  **Zotero Account:** Free account + Zotero Desktop installed.
2.  **Google Gemini API Key:** (Free tier available via Google AI Studio).
3.  **GitHub Account:** (Optional) To run the automation in the cloud via GitHub Actions.
4.  **Dropbox API Token:** (Optional) If you want reports backed up to Dropbox.

---

## ⚙️ Configuration Guide

### 1. Environment Variables (`.env`)
Create a `.env` file in the root directory (or set these as Secrets in GitHub Actions):

```bash
# REQUIRED
ZOTERO_USER_ID=12345678              # Found in Zotero Settings > Feeds/API
ZOTERO_API_KEY=your_zotero_key       # Create in Zotero Settings > Developer
GEMINI_API_KEY=your_gemini_key       # From Google AI Studio

# OPTIONAL (For Dropbox Sync)
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
