🤖 The Automated Research Assistant (DBA Edition)

"Stop searching. Start synthesizing."

This is an open-source workflow designed for Doctoral candidates and Research Leaders. It automates the discovery, analysis, and synthesis of academic literature, turning a manual slog into a streamlined intelligence operation.

🏗️ The Ecosystem

This system integrates multiple tools into a single pipeline:

The Engine (GitHub Actions): Runs every Monday at 3 AM. Scans 30+ sources, filters noise, and manages data.

The Brain (Google Gemini): Reads papers, drafts summaries, and writes strategic briefs.

The Archive (Zotero): Stores citations, PDFs, and AI-generated notes.

The Validator (Scite & Elicit): Checks credibility and extracts deep data.

The Dashboard (Streamlit): Visualizes trends, gaps, and networks.

🚀 Setup Guide (One-Time)

To run this yourself, you need to fork this repository and add your own API keys.

Step 1: Fork & Config

Fork this repository to your own GitHub account.

Edit scholar_sync.py to customize:

SEARCH_QUERIES: Replace with your research topics (e.g., "IT Governance").

RSS_FEEDS: Add industry sources (e.g., HBR, Brookings, EDUCAUSE).

VOCAB_ Lists: Define the theories and methods relevant to your field.

Step 2: Get Your Keys (Free Tiers)

Zotero: Get User ID and a new Key (Write Access) from Zotero Settings.

Google Gemini: Get a free API Key from Google AI Studio.

Dropbox: Create an App in the Dropbox Console.

Critical: Enable files.content.write permissions before generating the token.

Generate a refresh_token using the OAuth flow (see dropbox_sync.py comments for help).

Google Drive (Optional): Create a Service Account in Google Cloud, download the JSON key, and share a folder with the robot's email.

Step 3: Add Secrets to GitHub

Go to Settings -> Secrets and variables -> Actions and add:
ZOTERO_USER_ID, ZOTERO_API_KEY, GEMINI_API_KEY, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN (plus GDRIVE_ secrets if using Drive).

📅 The Weekly Workflow (User Manual)

1. Monday Morning Triage (15 Minutes)

Goal: Filter the robot's findings.

Open Zotero. Click the #_NEW_ARRIVAL tag.

Scan: Review titles and AI-generated tags (🔥 Trending, ⭐ Proven).

Validate with Scite:

Use the Scite Zotero Plugin.

Look at the "Scite" column next to the paper.

Green: Supported. Blue: Contrasted (Read these carefully!).

Retracted: Delete immediately.

Decide:

Delete irrelevant papers.

Keep good papers (remove the #_NEW_ARRIVAL tag).

Expand the item to read the "10-Point AI Summary" note for a quick overview.

2. Synthesis Review (10 Minutes)

Goal: Get the "Big Picture" of the week.

Open Dropbox/Google Drive. Find the folder [Date] - Research Batch.

Read the Reports:

EXECUTIVE_BRIEF.md: A strategic memo for leadership (Trends, Risks, Opportunities).

WEEKLY_SYNTHESIS.md: A narrative academic summary connecting this week's papers.

CONNECT_THE_DOTS.md: A cumulative analysis linking new papers to your older library.

PRACTITIONER_TOOLKIT.md: Actionable frameworks and KPIs extracted from the research.

3. Deep Work (Mid-Week)

Goal: Extract specific data for your dissertation.

Select the top 2-3 papers for deep reading.

Use Elicit (The Deep Dive):

If the AI summary is too high-level, upload the PDF to Elicit.com.

Ask specific questions: "What was the sample size?", "How do they define 'Digital Equity'?", "What are the exact limitations?"

Copy these details into your Zotero notes.

4. Visualization Dashboard (Monthly Review)

Goal: Spot trends and identify research gaps.

Launch Streamlit:

Open Terminal/CMD in your project folder.

Run: streamlit run dashboard.py

Explore:

Trend Forecast: Are your topics growing or shrinking?

Knowledge Graph: Visualize connections between papers and theories.

Heatmap: Identify "Cold Zones" (years/topics with no coverage) to target your next search.

5. Writing (Friday)

Goal: Produce output.

Open Word.

Cite: Use Zotero to insert citations.

Annotate: Since the robot saved the "Annotated Bib" paragraph to the Extra field, use a custom CSL style to automatically generate your Annotated Bibliography without typing.

Maintained by Darice. MIT License.
