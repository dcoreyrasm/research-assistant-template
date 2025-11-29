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

Edit scholar_sync.py:

Look for the SEARCH_QUERIES list (lines 60+).

Replace my topics (IT Governance, AI Literacy) with your research interests.

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

Permissions: Go to the Permissions tab and check files.content.write and files.content.read. Submit.

Generate Refresh Token:

Paste this URL in your browser (swap YOUR_APP_KEY with your actual key):
https://www.dropbox.com/oauth2/authorize?client_id=YOUR_APP_KEY&token_access_type=offline&response_type=code

Copy the "Access Code".

Exchange it for a token using Terminal/CMD:
curl https://api.dropbox.com/oauth2/token -d code=YOUR_ACCESS_CODE -d grant_type=authorization_code -d client_id=YOUR_APP_KEY -d client_secret=YOUR_APP_SECRET

Copy the "refresh_token" string from the result.

Step 3: Add Secrets to GitHub

Go to your GitHub Repo Settings -> Secrets and variables -> Actions and add these 6 secrets:

Secret Name

Value

ZOTERO_USER_ID

Your numeric Zotero ID

ZOTERO_API_KEY

Your Zotero Key String

GEMINI_API_KEY

Your Google AI Key

DROPBOX_APP_KEY

Your Dropbox App Key

DROPBOX_APP_SECRET

Your Dropbox App Secret

DROPBOX_REFRESH_TOKEN

Your Dropbox Refresh Token

Step 4: Turn it On

Go to the Actions tab.

Select Weekly Zotero Sync.

Click Run workflow.

📂 What you get

In Zotero: New papers appear tagged as #_NEW_ARRIVAL. Expand the item to see the AI-generated "10-Point Summary" note.

In Dropbox: A new folder is created weekly containing markdown files of your synthesis and summaries.

In GitHub: A literature_matrix.csv is updated weekly with all your data for Excel analysis.

Maintained by Darice. MIT License.
