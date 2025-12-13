# Research Assistant Template for DBA Students

This repository is a **starter template** for building an automated research assistant to support DBA-level literature reviews. It is **not** a plug-and-play solution. You are expected to customize it so that it reflects **your own research topic, theories, methods, and sources**.

The template helps you:

* Search for new academic articles on a schedule
* Filter and tag them using your research vocabulary
* Generate short summaries and synthesis notes
* Save outputs to Zotero and optional cloud storage

The value comes from **how well you customize it**.

---

## Before You Start

You will need:

* A GitHub account
* Basic comfort editing Python files
* A Zotero account and API key
* API keys for any LLM or services you use
* Optional: Dropbox or Google Drive accounts

You should already have a **clear research focus**. This template will not define your topic for you.

---

## Files You Must Customize

### 1. `scholar_sync.py`

This is the most important file. It controls **what the system searches for** and **how articles are classified**.

You must edit the following sections:

**SEARCH_QUERIES**

* Replace the sample keywords with terms related to your research question
* Include synonyms and related phrases
* Be specific. Generic terms will return low-quality results

**RSS_FEEDS**

* Add or remove journal, publisher, or research feeds relevant to your field
* Do not rely on the default list unless it actually fits your topic

**VOCAB_ Lists**

These lists define how articles are tagged and grouped.

* Update theory names
* Update methods (qualitative, quantitative, mixed, etc.)
* Update sectors, populations, or institutional types
* Remove anything that does not apply to your research

If your vocab lists do not reflect your dissertation topic, the output will not be useful.

---

### 2. `synthesize.py`

This file controls **how summaries and synthesis notes are written**.

You should customize:

* Section headers used in the synthesis output
* Prompt text that guides how summaries are written
* Any logic that assumes a topic, theory set, or discipline

Think of this file as shaping the **voice and structure** of your weekly research notes.

---

### 3. `.github/workflows/*.yml`

This file controls **when and how the automation runs**.

You may want to change:

* The schedule (day or time it runs)
* Which scripts run (for example, Zotero only vs. Zotero + Dropbox)
* Environment variable names to match your secrets

You must also add your own secrets in GitHub:

* API keys
* Zotero credentials
* Cloud storage credentials if used

---

## Optional Connector Customization

### `dropbox_sync.py`

Only needed if you want Dropbox output.

Customize:

* Target folder paths
* Naming conventions
* OAuth setup using your own Dropbox app

Follow the comments in the file carefully.

---

### `drive_sync.py`

Only needed if you want Google Drive output.

Customize:

* Folder ID or destination path
* Service account setup
* Folder sharing permissions

Make sure the Drive folder is shared with the service account email.

---

### `dashboard.py`

Optional Streamlit dashboard.

Customize:

* Labels and category names
* Any charts that depend on vocab categories
* Topic-specific language shown in the UI

---

## Files You Usually Do Not Change

* `requirements.txt` unless you add new libraries
* Utility scripts unless you want different quality checks or metrics

---

## Important Notes for DBA Students

* This template reflects **one research workflow**, not all workflows
* You are responsible for ensuring methodological fit
* Automation does not replace reading. It supports it
* Poor customization will produce poor synthesis

If you fork this repo and tailor it well, you will end up with a living research system that supports your dissertation work week by week.

---

## DBA Student Customization Checklist

Before running the workflow, confirm that you have completed **all** of the following:

### Research Setup

* Defined a clear research topic and research question
* Identified key theories, methods, and constructs relevant to your study
* Listed the journals, publishers, or research outlets that matter most for your field

### Code Customization

* Updated `SEARCH_QUERIES` in `scholar_sync.py`
* Updated `RSS_FEEDS` to match your discipline
* Replaced all default `VOCAB_` lists with your own theory, method, and population terms
* Reviewed `synthesize.py` and adjusted section headings and prompts

### Automation and Access

* Forked the repository into your own GitHub account
* Added required API keys and tokens to GitHub Secrets
* Reviewed the GitHub Actions schedule and adjusted timing if needed

### Output and Review

* Confirmed Zotero is receiving new items correctly
* Verified summaries and tags make sense for your research
* Read the outputs. Do not assume they are correct
* Refined vocab and prompts based on what you see

### Ongoing Use

* Revisit vocab lists as your dissertation focus evolves
* Adjust queries as your research question sharpens
* Treat this as a living system, not a one-time setup

---

## The Automated Research Assistant (DBA Edition)

“Stop searching. Start synthesizing.”

This is an open-source workflow designed for doctoral candidates and research leaders. It automates discovery, screening, and synthesis of academic literature to reduce manual overhead and support sustained scholarly work.

---

## The Ecosystem

This system integrates several tools into a single pipeline:

* **The Engine (GitHub Actions)**
  Runs every Monday at 3:00 AM. Scans sources, filters results, and manages execution.

* **The Brain (Google Gemini)**
  Reads papers, drafts summaries, and produces structured research notes.

* **The Archive (Zotero)**
  Stores citations, PDFs, and AI-generated notes.

* **The Validator (Scite and Elicit)**
  Checks citation context and extracts methodological details.

* **The Dashboard (Streamlit)**
  Visualizes trends, gaps, and relationships across the literature.

---

## Setup Guide (One-Time)

### Step 1. Fork and Configure

Fork this repository into your own GitHub account.

Edit `scholar_sync.py` to customize:

* `SEARCH_QUERIES` with your research topics
* `RSS_FEEDS` with journals or industry sources
* `VOCAB_` lists with your theories and methods

---

### Step 2. Get Your Keys (Free Tiers Available)

* **Zotero**
  Get your User ID and create a new API key with write access.

* **Google Gemini**
  Get an API key from Google AI Studio.

* **Dropbox (Optional)**
  Create an app in the Dropbox console.
  Enable `files.content.write` permissions before generating the token.
  Generate a `refresh_token` using the OAuth flow described in `dropbox_sync.py`.

* **Google Drive (Optional)**
  Create a Service Account in Google Cloud.
  Download the JSON key file.
  Share your target Drive folder with the service account email.

---

### Step 3. Add Secrets to GitHub

Go to **Settings → Secrets and variables → Actions** and add:

* `ZOTERO_USER_ID`
* `ZOTERO_API_KEY`
* `GEMINI_API_KEY`
* `DROPBOX_APP_KEY`
* `DROPBOX_APP_SECRET`
* `DROPBOX_REFRESH_TOKEN`
* Any required `GDRIVE_` secrets if using Drive

---

## The Weekly Workflow (User Manual)

### 1. Monday Morning Triage (15 minutes)

Goal: Filter incoming research.

* Open Zotero and click the `#_NEW_ARRIVAL` tag
* Review titles and AI-generated tags
* Use the Scite Zotero plugin to review citation context
* Delete irrelevant or retracted items
* Keep relevant papers and remove the `#_NEW_ARRIVAL` tag
* Read the “10-Point AI Summary” note for a quick overview

---

### 2. Synthesis Review (10 minutes)

Goal: See the big picture.

Open your Dropbox or Google Drive folder for the weekly batch and review:

* `EXECUTIVE_BRIEF.md`
* `WEEKLY_SYNTHESIS.md`
* `CONNECT_THE_DOTS.md`
* `PRACTITIONER_TOOLKIT.md`

---

### 3. Deep Work (Mid-Week)

Goal: Extract dissertation-level detail.

* Select the top 2–3 papers
* Upload PDFs to Elicit if needed
* Ask targeted questions about methods, samples, definitions, and limitations
* Copy verified details into Zotero notes

---

### 4. Visualization Dashboard (Monthly Review)

Goal: Spot trends and gaps.

From your project folder, run:

```
streamlit run dashboard.py
```

Explore trends, topic coverage, and under-researched areas.

---

### 5. Writing (Friday)

Goal: Produce draft material.

* Write in Word
* Insert citations using Zotero
* Use Zotero notes and custom CSL styles to generate annotated bibliography entries

---

Maintained by Darice Corey
MIT License
