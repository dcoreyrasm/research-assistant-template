🤖 The Automated Research Assistant (DBA Edition)

"Stop searching. Start synthesizing."

This is an open-source workflow designed for Doctoral candidates and Research Leaders. It automates the discovery, analysis, and synthesis of academic literature.

Every Monday morning, this system:

Scans 30+ sources (Semantic Scholar, EDUCAUSE, Brookings, HBR) for your research topics.

Filters noise using a "Sliding Scale" algorithm (accepting only high-impact or breaking news papers).

Reads & Summarizes every paper using Google Gemini 1.5 Pro, creating a "10-Point Summary" in your Zotero notes.

Synthesizes the weekly batch into a narrative literature review draft (WEEKLY_SYNTHESIS.md) and a strategic memo (EXECUTIVE_BRIEF.md).

Delivers everything to your Zotero library and a synchronized Dropbox folder.

🚀 Setup Guide (No Coding Required)

To run this yourself, you need to fork this repository and add your own API keys.

Step 1: Fork & Config

Fork this repository to your own GitHub account.

Edit scholar_sync.py to customize the brain of the analyst:

Research Topics: Look for SEARCH_QUERIES = [...] (approx. line 75). Replace my topics (e.g., "IT Governance") with your specific research interests.

Industry Feeds: Look for RSS_FEEDS = [...] (approx. line 90). Add or remove URLs for the blogs, think tanks (like Brookings or Pew), or journals you want to monitor.

Controlled Vocabulary: Look for the lists starting with VOCAB_ (e.g., VOCAB_THEORY, VOCAB_METHOD). These lists guide the AI on how to tag your papers. Update them with the theories and methods relevant to your field.

Step 2: Get Your Keys

You need 4 sets of keys. All are free tiers.

1. Zotero (The Library)

Go to Zotero API Settings.

Copy your User ID (listed at the top).

Create a new Key with Write Access. Copy the key string.

2. Google Gemini (The Brain)

Go to Google AI Studio.

Create a free API Key.

3. Dropbox (The Delivery)

Go to Dropbox App Console.

Create an App (Scoped Access -> App Folder).

Permissions (CRITICAL): Go to the Permissions tab before you generate any tokens. Check files.content.write and files.content.read. Click Submit at the bottom.

Generate Refresh Token:

Paste this URL in your browser (swap YOUR_APP_KEY with your actual key):
https://www.dropbox.com/oauth2/authorize?client_id=YOUR_APP_KEY&token_access_type=offline&response_type=code

Copy the "Access Code".

Exchange it for a token using Terminal/CMD (do this quickly, the code expires in 5 mins):
curl https://api.dropbox.com/oauth2/token -d code=YOUR_ACCESS_CODE -d grant_type=authorization_code -d client_id=YOUR_APP_KEY -d client_secret=YOUR_APP_SECRET

Copy the "refresh_token" string from the JSON result (do not include quotes).

Step 3: Add Secrets to GitHub

Go to your GitHub Repo Settings -> Secrets and variables -> Actions and add these 6 secrets:

| Secret Name | Value |
| ZOTERO_USER_ID | Your numeric Zotero ID |
| ZOTERO_API_KEY | Your Zotero Key String |
| GEMINI_API_KEY | Your Google AI Key |
| DROPBOX_APP_KEY | Your Dropbox App Key |
| DROPBOX_APP_SECRET | Your Dropbox App Secret |
| DROPBOX_REFRESH_TOKEN | Your Dropbox Refresh Token |

Step 4: Turn it On

Go to the Actions tab.

Select Weekly Zotero Sync.

Click Run workflow.

📂 What you get

In Zotero: New papers appear tagged as #_NEW_ARRIVAL. Expand the item to see the AI-generated "10-Point Summary" note.

In Dropbox: A new folder is created weekly (e.g., /2025-11-28 - Research Batch/) containing:

WEEKLY_SYNTHESIS.md: A narrative academic comparison of the week's papers.

EXECUTIVE_BRIEF.md: A 1-page strategic memo for leadership.

DEEP_DIVE_[Topic].md: A cumulative analysis of your #1 most researched topic.

Individual Summaries: Markdown files for every single paper found.

In GitHub: A literature_matrix.csv is updated weekly with all your data for Excel analysis.

Maintained by Darice. MIT License.
