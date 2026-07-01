# Upwork Automation Dashboard v3.1

Built for the onboarding automation project.

## What it does
- Reads incoming Upwork email notifications from Gmail
- Matches email content to a FAQ knowledge base
- Auto-replies via Gmail
- Syncs FAQs directly from Google Drive (CSV, JSON, or Google Sheets)
- Visual Streamlit dashboard to manage everything

## Bug Fixes in v3.1 (all QA items addressed)
1. Counter no longer multiplies on repeated "Run Workflow Now" clicks (stays at 5)
2. "Press Enter to apply" helper text hidden from search box (tooltip/alignment)
3. Search list auto-refreshes when keyword is cleared (no Enter key needed)
4. FAQ Manager title + search box now stay fixed (sticky) while list scrolls
5. "Add FAQ" adds exactly one entry per submit; form clears after submit
6. Inbox emails load only after clicking "Fetch Emails" (empty on load)
7. Settings title stays fixed; all textbox content fully visible
8. No conflicting "processed / not processed" message on a single click

## How to run
1. pip install -r requirements.txt
2. streamlit run app.py
3. Open http://localhost:8501

## Google Drive Setup
1. Google Cloud Console -> new project -> enable Google Drive API
2. Create a Service Account, download the JSON key
3. Rename it service_account.json, place in project root
4. Share the FAQ Drive folder with the service account email
5. Paste the Drive Folder ID in Settings -> Google Drive Settings
6. Drive Sync page -> Sync FAQs from Drive

## Switching to Production
1. Set "dummy_mode": false in config.json
2. Add GMAIL_APP_PASSWORD as an environment variable
3. Place service_account.json in project root
4. Update Gmail address and Drive Folder ID in Settings

## Project Structure
- app.py - Streamlit dashboard
- drive_handler.py - Google Drive auth, file reading, FAQ parsing
- email_handler.py - Gmail read/send logic
- faq_matcher.py - FAQ matching engine + Drive sync
- workflow_engine.py - Connects all components
- config.py - Configuration manager
- requirements.txt - Dependencies
- faqs.json - FAQ knowledge base
