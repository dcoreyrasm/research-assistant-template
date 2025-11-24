# research-assistant-template
Google scholar to zotero sync


🤖 Automated Research Assistant

Stop searching. Start synthesizing.

This open-source workflow automates the literature review process.
It connects Semantic Scholar to Zotero using GitHub Actions and delivers a curated list of high-impact research papers to your library every Monday morning.


---

🌟 Features

Automated Search

Runs weekly at 3:00 AM EST while you sleep.

Quality Filters

Uses a simple sliding scale:

2025 papers: Accepted immediately (breaking news).

2024 papers: Must have 15+ citations.

Older papers: Must have 50+ citations.


Smart Tagging

Adds impact markers directly in Zotero:

🔥 Trending (New)

⭐ Proven (Recent)

🏆 High Impact


Duplicate Protection

Checks your Zotero library before adding anything new.

Dashboard

Generates a weekly status report inside your GitHub repository.


---

🚀 Setup Guide

No coding required.

Step 1: Get Your Zotero Keys

1. Log in to your Zotero API Settings.


2. Find your User ID (look for “Your UserID for use in API calls is …”).


3. Create a new private key.


4. Check Allow write access.


5. Save your key string (example: H8d9a8s7d9...).



Step 2: Clone the Workflow

Fork this repository, or copy the workflow files to a new repo.

Open scholar_sync.py.

Edit the SEARCH_QUERIES list to match your research topics.


Step 3: Add Secrets

Go to:
Repo Settings → Secrets and variables → Actions
Add:

ZOTERO_USER_ID

ZOTERO_API_KEY


Step 4: Turn it On

1. Go to the Actions tab.


2. Select Weekly Zotero Sync.


3. Click Run workflow.




---

🧠 Workflow Usage

Monday Routine

Open Zotero.

Filter using the _NEW_ARRIVAL tag.

Triage each paper:

If you keep it: remove the tag.

If it’s irrelevant: delete it.




---

Created by Darice as a workflow to support efficient academic research.
