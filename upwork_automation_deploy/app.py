import streamlit as st
from datetime import datetime
from email_handler import EmailHandler
from faq_matcher import FAQMatcher
from workflow_engine import WorkflowEngine
from drive_handler import DriveHandler
from config import Config

st.set_page_config(page_title="Upwork Automation", page_icon="⚡", layout="wide")

# ─────────────────────────────────────────────────────────────
# GLOBAL STYLES
#  - FIX #2: hide the "Press Enter to apply" instruction text
#  - FIX #3/#6/#9: make all input text + labels clearly visible
#  - FIX #4/#7: sticky page header (title + search stay fixed)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
* { font-family: 'DM Sans', sans-serif; }

/* THEME-AWARE VISIBILITY FIX.
   Instead of hardcoding white text (which broke in light mode), we inherit
   Streamlit's own theme colors via its CSS variables. These automatically
   become dark text on light backgrounds, and light text on dark backgrounds,
   so everything stays readable in BOTH dark and light mode. */

/* All text, labels, titles inherit the active theme's text color */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stSlider label, .stRadio label, label, p, span, h1, h2, h3, h4,
.stMarkdown, .stExpander summary, .stExpander summary *,
section[data-testid="stSidebar"] *,
div[role="radiogroup"] label,
div[role="radiogroup"] label p,
div[role="radiogroup"] label div,
div[role="radiogroup"] label span {
    color: var(--text-color, inherit) !important;
    -webkit-text-fill-color: var(--text-color, inherit) !important;
    opacity: 1 !important;
}

/* Inputs follow the theme's secondary background + text color */
.stTextInput input, .stTextArea textarea, input, textarea {
    color: var(--text-color, inherit) !important;
    -webkit-text-fill-color: var(--text-color, inherit) !important;
    background-color: var(--secondary-background-color, transparent) !important;
}

/* Buttons keep the blue background with white text in BOTH modes
   (white reads fine on the blue fill regardless of theme) */
.stButton > button, .stButton > button *,
.stFormSubmitButton > button, .stFormSubmitButton > button * {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 500 !important; opacity: 1 !important;
}

/* Hide Streamlit's "Press Enter to apply" helper text */
div[data-testid="InputInstructions"] { display: none !important; }
.stTextInput div[data-baseweb="input"] + div { display: none !important; }

/* Cards: use theme variables so they adapt to light/dark automatically */
.metric-card, .msg-card, .faq-card {
    background: var(--secondary-background-color, #1a1f2e) !important;
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 10px;
}
/* All text inside cards inherits the theme text color for guaranteed contrast */
.msg-card, .msg-card *, .faq-card, .faq-card * {
    color: var(--text-color, inherit) !important;
}
.metric-card { padding:20px; text-align:center; }
.metric-value { font-size:36px; font-weight:600; color:#4f9cf9 !important; font-family:'DM Mono',monospace; }
.metric-label { font-size:11px; color:#9aa0ad !important; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }
.msg-card { padding:16px 20px; margin-bottom:12px; }
.faq-card { padding:14px 18px; margin-bottom:8px; }
/* keep the sender email in accent blue, readable on both themes */
.msg-card .sender { color:#3b82f6 !important; font-size:13px; }
.msg-card .matched { color:#9aa0ad !important; font-size:12px; }

/* sticky header inherits the page background so it works in both themes */
.sticky-head {
    position: sticky; top: 0; z-index: 999;
    background: var(--background-color, inherit);
    padding: 8px 0 10px 0;
    border-bottom: 1px solid rgba(128,128,128,0.25);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# RESOURCE INIT  (handlers only — NO mutable run-state cached)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def init():
    c = Config()
    f = FAQMatcher(c)
    e = EmailHandler(c)
    w = WorkflowEngine(c, e, f)
    d = DriveHandler(c)
    return c, f, e, w, d

config, faq_matcher, email_handler, workflow_engine, drive_handler = init()

# ── Session state (the single source of truth for counts) ──
if 'logs' not in st.session_state: st.session_state.logs = []
if 'processed' not in st.session_state: st.session_state.processed = []   # FIX #1/#8
if 'emails' not in st.session_state: st.session_state.emails = []          # FIX #6
if 'last_run_msg' not in st.session_state: st.session_state.last_run_msg = ""

def log(msg, level="info"):
    st.session_state.logs.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "message": msg, "level": level})

# ── Callbacks ──
def run_workflow_callback():
    """FIX #1 & #8: REPLACE results each run so totals never accumulate.
    Runs inside a callback so state is set BEFORE the script reruns,
    which also fixes the conflicting-message bug (#8/Ambiguous)."""
    results = workflow_engine.run()
    st.session_state.processed = results          # replace, never append
    for r in results:
        log(f"Processed email from {r['from']} — {r['status']}", "success")
    st.session_state.last_run_msg = f"Processed {len(results)} email(s)" if results else "No new emails found"

def fetch_emails_callback():
    """FIX #6: emails populate only when this runs."""
    st.session_state.emails = email_handler.fetch_upwork_emails(10)
    log(f"Fetched {len(st.session_state.emails)} emails")

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ Upwork Automation")
    st.markdown("---")
    page = st.radio("Nav", ["Dashboard","Inbox","FAQ Manager","Drive Sync","Settings","Logs"], label_visibility="collapsed")
    st.markdown("---")
    gmail_ok = email_handler.test_connection()
    faq_ok = len(faq_matcher.faqs) > 0
    drive_ok = drive_handler.is_connected()
    st.markdown(f"{'🟢' if gmail_ok else '🔴'} Gmail &nbsp;&nbsp; {'🟢' if faq_ok else '🔴'} FAQs &nbsp;&nbsp; {'🟢' if drive_ok else '🔴'} Drive", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Upwork Automation v3.1")

# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────
if page == "Dashboard":
    st.markdown("## ⚡ Automation Dashboard")
    st.caption("Upwork onboarding & communication automation")
    st.markdown("---")

    # Counts read directly from the single source of truth
    total = len(st.session_state.processed)
    sent = len([m for m in st.session_state.processed if m['status']=='sent'])
    pending = len([m for m in st.session_state.processed if m['status']=='pending'])
    failed = len([m for m in st.session_state.processed if m['status']=='failed'])

    c1,c2,c3,c4 = st.columns(4)
    for col,val,label in zip([c1,c2,c3,c4],[total,sent,pending,failed],["Total Processed","Replies Sent","Pending","Failed"]):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3,2])

    with col2:
        st.markdown("**Workflow Control**")
        # FIX #1/#8: on_click callback sets state BEFORE rerun → no double-click,
        # no conflicting message, no multiplying count.
        st.button("▶ Run Workflow Now", use_container_width=True, on_click=run_workflow_callback)
        if st.session_state.last_run_msg:
            if st.session_state.last_run_msg.startswith("Processed"):
                st.success(st.session_state.last_run_msg)
            else:
                st.info(st.session_state.last_run_msg)

        st.markdown("<br>**How It Works**", unsafe_allow_html=True)
        for n,s in [("1","Gmail checked for Upwork emails"),("2","Email content extracted"),("3","FAQ knowledge base searched"),("4","Auto-reply sent via Gmail")]:
            st.markdown(f"""<div style="display:flex;gap:10px;align-items:center;background:var(--secondary-background-color,#1a1f2e);border:1px solid rgba(128,128,128,0.25);border-radius:8px;padding:10px 14px;margin-bottom:6px">
                <div style="width:24px;height:24px;border-radius:50%;background:#1d4ed8;color:white;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;flex-shrink:0">{n}</div>
                <div style="font-size:13px;color:#9ca3af">{s}</div></div>""", unsafe_allow_html=True)

    with col1:
        st.markdown("**Recent Activity**")
        # FIX #8: panel updates in the SAME render as the count
        if st.session_state.processed:
            for msg in st.session_state.processed[-5:][::-1]:
                color = "#34d399" if msg['status']=='sent' else "#fbbf24"
                st.markdown(f"""
                <div class="msg-card">
                    <div style="display:flex;justify-content:space-between">
                        <span class="sender">{msg['from']}</span>
                        <span style="color:{color} !important;font-size:11px;font-weight:600">{msg['status'].upper()}</span>
                    </div>
                    <div style="font-size:14px;margin:4px 0;color:#e8eaf0 !important;font-weight:500">{msg['subject']}</div>
                    <div style="color:#b8c0d0 !important;font-size:12px;margin-top:4px">Matched: {msg.get('matched_faq','N/A')}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No messages processed yet. Click 'Run Workflow Now'.")

# ─────────────────────────────────────────────────────────────
# INBOX
# ─────────────────────────────────────────────────────────────
elif page == "Inbox":
    st.markdown("## 📥 Email Inbox")
    st.caption("Click 'Fetch Emails' to load Upwork notifications.")
    col1,col2 = st.columns([4,1])
    with col2:
        # FIX #6: emails appear only after this is clicked
        st.button("📧 Fetch Emails", use_container_width=True, on_click=fetch_emails_callback)

    if not st.session_state.emails:
        st.info("No emails loaded yet. Click 'Fetch Emails' above to load them.")
    else:
        for em in st.session_state.emails:
            with st.expander(f"📧 {em['subject']}"):
                st.markdown(f"<div style='color:var(--text-color,inherit)'><b>From:</b> {em['from']} &nbsp;|&nbsp; <b>Time:</b> {em['time']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:var(--text-color,inherit);margin-top:6px'><b>Message:</b> {em['body']}</div>", unsafe_allow_html=True)
                matched = faq_matcher.find_best_match(em['body'])
                if matched:
                    st.success(f"FAQ Match: {matched['question']}")
                    st.info(f"Reply: {matched['answer']}")
                    if st.button("Send This Reply", key=f"r_{em['id']}"):
                        email_handler.send_reply(em, matched['answer'])
                        st.success("Reply sent!")
                        log(f"Reply sent to {em['from']}", "success")
                else:
                    st.warning("No FAQ match found")

# ─────────────────────────────────────────────────────────────
# FAQ MANAGER
# ─────────────────────────────────────────────────────────────
elif page == "FAQ Manager":
    tab1, tab2 = st.tabs(["View FAQs", "Add / Test"])

    with tab1:
        # FIX #3 (definitive): Streamlit's text_input only reruns on Enter or
        # focus-loss, so it can never filter live as you delete characters.
        # To meet the requirement ("show the full list without pressing Enter")
        # we render the search box + FAQ list as a self-contained HTML/JS
        # component. JavaScript filters on every keystroke — including deletes —
        # entirely in the browser, with zero Enter key needed.
        import json as _json
        import html as _html
        import streamlit.components.v1 as _components

        faq_payload = []
        for f in faq_matcher.faqs:
            faq_payload.append({
                "q": f["question"],
                "a": f["answer"],
                "src": "🌐" if f.get("source") == "google_drive" else "💾",
            })
        drive_count = len([f for f in faq_matcher.faqs if f.get('source') == 'google_drive'])
        local_count = len(faq_matcher.faqs) - drive_count
        data_js = _json.dumps(faq_payload)

        component_html = """
<style>
  /* The component runs in an isolated iframe, so it uses prefers-color-scheme
     to follow the user's light/dark preference, matching the rest of the app. */
  :root {
    --bg: #ffffff; --fg: #1a1a1a; --card: #f4f6fb;
    --muted: #6b7280; --border: #d6dbe6; --accent: #1d4ed8;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1117; --fg: #e8eaf0; --card: #1a1f2e;
      --muted: #8b93a7; --border: #2a3044; --accent: #4f9cf9;
    }
  }
  body { margin:0; }
</style>
<div style="font-family:'DM Sans',sans-serif;color:var(--fg);">
  <div style="position:sticky;top:0;background:var(--bg);z-index:5;padding-bottom:8px;">
    <h3 style="color:var(--fg);margin:0 0 10px 0;">📚 FAQ Knowledge Base</h3>
    <label style="color:var(--fg);font-size:13px;">Search FAQs</label>
    <input id="faqSearch" type="text" placeholder="Type to filter..."
      style="width:100%;box-sizing:border-box;margin-top:6px;padding:12px 14px;
             border-radius:8px;border:1px solid var(--border);background:var(--card);
             color:var(--fg);font-size:14px;outline:none;" />
    <div id="faqCount" style="color:var(--muted);font-size:12px;margin-top:8px;"></div>
  </div>
  <div id="faqList" style="margin-top:8px;"></div>
</div>
<script>
  const FAQS = __DATA__;
  const DRIVE = __DRIVE__;
  const LOCAL = __LOCAL__;
  const box = document.getElementById('faqSearch');
  const list = document.getElementById('faqList');
  const count = document.getElementById('faqCount');

  function esc(s){
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
  function render(items){
    list.innerHTML = items.map(f => `
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;
                  padding:14px 18px;margin-bottom:8px;">
        <div style="display:flex;justify-content:space-between;">
          <div style="color:var(--accent);font-size:13px;font-weight:600;">Q: ${esc(f.q)}</div>
          <div style="font-size:11px;color:var(--muted);">${f.src}</div>
        </div>
        <div style="color:var(--fg);font-size:13px;margin-top:6px;">A: ${esc(f.a)}</div>
      </div>`).join('');
    count.textContent = items.length + ' FAQs shown  •  🌐 ' + DRIVE +
                        ' from Drive  •  💾 ' + LOCAL + ' local';
  }
  function filter(){
    const t = box.value.trim().toLowerCase();
    if(!t){ render(FAQS); return; }
    render(FAQS.filter(f =>
      f.q.toLowerCase().includes(t) || f.a.toLowerCase().includes(t)));
  }
  // 'input' fires on EVERY change: typing AND deleting — no Enter needed.
  box.addEventListener('input', filter);
  render(FAQS);  // show full list on load
</script>
"""
        component_html = (component_html
            .replace("__DATA__", data_js)
            .replace("__DRIVE__", str(drive_count))
            .replace("__LOCAL__", str(local_count)))
        # height scales with number of FAQs
        _components.html(component_html, height=min(700, 180 + len(faq_payload) * 95), scrolling=True)

    with tab2:
        st.markdown("**Add New FAQ**")
        # FIX #5: a form with clear_on_submit. One submit = one FAQ, fields clear,
        # and re-clicking does nothing because the inputs are now empty (guarded).
        if 'faq_msg' not in st.session_state: st.session_state.faq_msg = None  # (text, type)

        with st.form("add_faq_form", clear_on_submit=True):
            q = st.text_input("Question")
            a = st.text_area("Answer", height=80)
            submitted = st.form_submit_button("Add FAQ")
        if submitted:
            if q.strip() and a.strip():
                faq_matcher.add_faq(q.strip(), a.strip())
                st.session_state.faq_msg = ("FAQ added successfully!", "success")
                log(f"FAQ added: {q.strip()}", "success")
            else:
                st.session_state.faq_msg = ("Please fill in both question and answer.", "warning")

        # FIX (dismissable message): show feedback with a visible ✕ close button
        if st.session_state.faq_msg:
            text, kind = st.session_state.faq_msg
            mc1, mc2 = st.columns([10, 1])
            with mc1:
                (st.success if kind == "success" else st.warning)(text)
            with mc2:
                if st.button("✕", key="dismiss_faq_msg"):
                    st.session_state.faq_msg = None
                    st.rerun()

        st.markdown("---")
        st.markdown("**Test Matching**")
        test = st.text_area("Paste a message to test", height=80, key="faq_test")
        if st.button("Test"):
            m = faq_matcher.find_best_match(test)
            if m:
                st.success(f"Match: {m['question']}")
                st.info(f"Reply: {m['answer']}")
                st.metric("Confidence", f"{m['score']:.0%}")
            else:
                st.warning("No match found")

# ─────────────────────────────────────────────────────────────
# DRIVE SYNC
# ─────────────────────────────────────────────────────────────
elif page == "Drive Sync":
    st.markdown("## 🌐 Google Drive FAQ Sync")
    st.caption("Pull FAQ data directly from your Google Drive folder")
    st.markdown("---")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("**Connection Status**")
        if drive_handler.is_connected():
            st.success("✅ Connected to Google Drive")
            st.markdown(f"**Folder ID:** `{config.get('drive_folder_id', '')}`")
            st.markdown("---"); st.markdown("**Files in Drive Folder**")
            files = drive_handler.list_files()
            if files:
                for f in files:
                    icon = "📊" if "sheet" in f.get('mimeType','') else "📄"
                    st.markdown(f"{icon} `{f['name']}`")
            else:
                st.warning("No files found in the configured folder.")
        else:
            st.error("❌ Not connected to Google Drive")
            st.markdown("""
**To connect:**
1. Create a Service Account in Google Cloud Console
2. Enable the Google Drive API
3. Download the JSON key and rename it `service_account.json`
4. Place it in the project root folder
5. Share your Drive folder with the service account email
6. Restart the app
            """)
    with col2:
        st.markdown("**Sync Controls**")
        drive_count = len([f for f in faq_matcher.faqs if f.get('source') == 'google_drive'])
        st.metric("FAQs from Drive", drive_count)
        st.metric("Total FAQs", len(faq_matcher.faqs))
        st.markdown("---")
        if st.button("🔄 Sync FAQs from Drive", use_container_width=True, disabled=not drive_handler.is_connected()):
            with st.spinner("Syncing..."):
                count, msg = faq_matcher.sync_from_drive(drive_handler)
                (st.success if count > 0 else st.warning)(msg)
                log(f"Drive sync: {msg}", "success" if count else "warning")
            st.rerun()
        if st.button("🗑 Remove Drive FAQs", use_container_width=True):
            faq_matcher.remove_drive_faqs()
            st.success("Drive FAQs removed. Local FAQs kept.")
            log("Drive FAQs cleared", "info")
            st.rerun()
        st.markdown("---")
        st.markdown("**Supported Formats**")
        st.markdown("- 📊 Google Sheets\n- 📄 CSV files\n- 📋 JSON files")

# ─────────────────────────────────────────────────────────────
# SETTINGS  (FIX #9 + settings UI: title stays, text visible)
# ─────────────────────────────────────────────────────────────
elif page == "Settings":
    st.markdown('<div class="sticky-head"><h2>⚙️ Settings</h2></div>', unsafe_allow_html=True)
    st.info("Currently running in Dummy Mode. Replace credentials below when real access details are shared.")

    with st.expander("Gmail Settings", expanded=True):
        gmail = st.text_input("Gmail Address", value=config.get('gmail_user',''))
        st.caption("Set GMAIL_APP_PASSWORD as an environment variable for production use.")
        if st.button("Test Gmail"):
            st.warning("Add real credentials first to test connection")
    with st.expander("Google Drive Settings", expanded=True):
        folder = st.text_input("Google Drive Folder ID", value=config.get('drive_folder_id',''))
        st.caption("Get this from the URL of the shared Drive folder.")
        st.caption("Also place service_account.json in the project root to enable Drive connection.")
    with st.expander("Workflow Settings", expanded=True):
        auto = st.toggle("Auto Reply", value=config.get('auto_reply', True))
        conf = st.slider("Match Confidence Threshold", 0.0, 1.0, config.get('confidence_threshold', 0.5), 0.05)
        default_r = st.text_area("Default Reply (no match)", value=config.get('default_reply',''), height=80)

    if st.button("💾 Save All Settings"):
        config.update({'gmail_user': gmail, 'drive_folder_id': folder, 'auto_reply': auto, 'confidence_threshold': conf, 'default_reply': default_r})
        st.success("Settings saved!")
        log("Settings updated")

# ─────────────────────────────────────────────────────────────
# LOGS
# ─────────────────────────────────────────────────────────────
elif page == "Logs":
    st.markdown("## 📋 System Logs")
    col1,col2 = st.columns([4,1])
    with col2:
        if st.button("Clear"):
            st.session_state.logs = []
            st.rerun()
    if st.session_state.logs:
        for l in st.session_state.logs:
            color = {"success":"#34d399","warning":"#fbbf24","info":"#93c5fd"}.get(l["level"], "#93c5fd")
            st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:12px;padding:6px 12px;border-radius:6px;margin-bottom:4px;background:#111827;border-left:3px solid {color};color:{color}">[{l["time"]}] {l["message"]}</div>', unsafe_allow_html=True)
    else:
        st.info("No logs yet.")
