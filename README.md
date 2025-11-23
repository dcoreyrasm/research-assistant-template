# research-assistant-template
Google scholar to zotero sync

🤖 The Automated Research Assistant
​Stop searching. Start synthesizing.
​This is an open-source workflow that automates the literature review process. It connects Semantic Scholar to Zotero using GitHub Actions to deliver a curated list of high-impact research papers to your library every Monday morning.
​🌟 Features
​Automated Search: Runs weekly at 3:00 AM EST while you sleep.
​Quality Filters: Uses a "Sliding Scale" algorithm:
​2025 Papers: Accepted immediately (Breaking News).
​2024 Papers: Must have 15+ citations.
​Older Papers: Must have 50+ citations.
​Smart Tagging: Visualizes impact directly in Zotero:
​🔥 Trending (New)
​⭐ Proven (Recent)
​🏆 High Impact
​Duplicate Protection: Checks your library to ensure zero duplicates.
​Dashboard: Generates a status report in your repository.
​🚀 Setup Guide (No Coding Required)
​Step 1: Get Your Zotero Keys
​Log in to Zotero API Settings.
​Get your User ID: Look for Your UserID for use in API calls is 1234567. Save this number.
​Create a Key: Click "Create new private key".
​Check "Allow write access".
​Save the key string (e.g., H8d9a8s7d9...).
​Step 2: Clone this Workflow
​Fork this repository (or copy the files to a new repo).
​Customize Topics: Open scholar_sync.py and edit the SEARCH_QUERIES list (lines 18-25) to match your research interests.
​Step 3: Add Secrets
​Go to your GitHub Repo Settings -> Secrets and variables -> Actions.
​Add two new secrets:
​ZOTERO_USER_ID: Your number from Step 1.
​ZOTERO_API_KEY: Your key string from Step 1.
​Step 4: Turn it On
​Go to the Actions tab.
​Select Weekly Zotero Sync.
​Click Run workflow.
​🧠 Workflow Usage
​Monday Morning: Open Zotero.
​Filter: Click the _NEW_ARRIVAL tag.
​Triage: Review the papers. If you keep one, delete the _NEW_ARRIVAL tag. If you dislike it, delete the item.
​Created by Darice as a tool for academic research efficiency.
