import json
import os
from difflib import SequenceMatcher

FAQ_FILE = "faqs.json"

DEFAULT_FAQS = [
    {"question": "When will I receive payment?", "answer": "Payment is released upon successful project completion and client approval. Upwork holds funds in escrow and releases them once the milestone is marked complete.", "keywords": ["payment", "pay", "money", "paid", "invoice", "escrow", "funds"]},
    {"question": "How do I apply for a job?", "answer": "To apply, submit a tailored proposal through Upwork highlighting your relevant experience. Include your portfolio and answer all questions in the job posting.", "keywords": ["apply", "application", "proposal", "job", "hire", "bid"]},
    {"question": "What are the working hours?", "answer": "We operate across multiple time zones. Core collaboration hours are flexible but we ask that you confirm your available hours during onboarding.", "keywords": ["hours", "time", "schedule", "availability", "timezone", "working", "online"]},
    {"question": "How do I submit my work?", "answer": "Please submit all deliverables via the Upwork platform using the file submission feature or by sharing a cloud link. Always include a brief summary of what was completed.", "keywords": ["submit", "submission", "deliver", "upload", "share", "send work", "output"]},
    {"question": "What tools do I need to use?", "answer": "We primarily use Python, Streamlit, Gmail API, and Google Drive for automation projects. AI tools such as ChatGPT and Claude are encouraged.", "keywords": ["tools", "software", "technology", "stack", "python", "streamlit", "use"]},
    {"question": "How do I communicate with the team?", "answer": "All communication happens through Upwork Messenger. For calls, we use Google Meet or Zoom. Please respond within 24 hours.", "keywords": ["communicate", "communication", "contact", "message", "call", "meeting", "reach"]},
    {"question": "What happens if I miss a deadline?", "answer": "Please notify us at least 24 hours in advance if you anticipate missing a deadline. We are flexible when informed promptly.", "keywords": ["deadline", "late", "miss", "delay", "extend", "extension", "overdue"]},
    {"question": "How do I verify my Upwork account?", "answer": "Go to your Upwork profile settings and complete the identity verification process. You will need a government-issued ID.", "keywords": ["verify", "verification", "account", "id", "identity", "upwork account"]},
    {"question": "Will there be more work after this project?", "answer": "Yes, this is the first of many automation projects. Strong performers will be offered continued collaboration across multiple pre-funded startups.", "keywords": ["more work", "long term", "future", "ongoing", "next project", "continue"]},
    {"question": "Do I need to record a video demo?", "answer": "Yes, for each deliverable please record a short Loom or Dropbox Capture video walkthrough showing your output. Share a public cloud link, not Google Drive.", "keywords": ["video", "loom", "demo", "record", "walkthrough", "screen", "show"]}
]

class FAQMatcher:
    def __init__(self, config):
        self.config = config
        self.faqs = self._load_faqs()

    def _load_faqs(self):
        if os.path.exists(FAQ_FILE):
            with open(FAQ_FILE, 'r') as f:
                return json.load(f)
        self._save_faqs(DEFAULT_FAQS)
        return DEFAULT_FAQS

    def _save_faqs(self, faqs):
        with open(FAQ_FILE, 'w') as f:
            json.dump(faqs, f, indent=2)

    def add_faq(self, question, answer, keywords=None):
        if not keywords:
            keywords = [w.lower() for w in question.split() if len(w) > 3]
        self.faqs.append({"question": question, "answer": answer, "keywords": keywords})
        self._save_faqs(self.faqs)

    def sync_from_drive(self, drive_handler):
        """
        Pull FAQs from Google Drive and merge with existing local FAQs.
        Drive FAQs take priority; duplicates (by question) are replaced.
        Returns (count_added, message).
        """
        drive_faqs, msg = drive_handler.fetch_faqs_from_drive()
        if not drive_faqs:
            return 0, msg

        # Build lookup of existing questions
        existing = {f['question'].lower(): i for i, f in enumerate(self.faqs)}
        added, updated = 0, 0

        for df in drive_faqs:
            key = df['question'].lower()
            if key in existing:
                self.faqs[existing[key]] = df  # update
                updated += 1
            else:
                self.faqs.append(df)
                added += 1

        self._save_faqs(self.faqs)
        summary = f"{msg} | Added: {added}, Updated: {updated}"
        return added + updated, summary

    def remove_drive_faqs(self):
        """Remove all FAQs that came from Google Drive (for re-sync)."""
        self.faqs = [f for f in self.faqs if f.get('source') != 'google_drive']
        self._save_faqs(self.faqs)

    def _keyword_score(self, text, faq):
        text_lower = text.lower()
        matches = sum(1 for kw in faq.get('keywords', []) if kw in text_lower)
        return matches / max(len(faq.get('keywords', [1])), 1)

    def _similarity_score(self, text, faq):
        combined = faq['question'] + " " + faq['answer']
        return SequenceMatcher(None, text.lower(), combined.lower()).ratio()

    def find_best_match(self, message_text):
        if not message_text or not self.faqs:
            return None
        threshold = self.config.get('confidence_threshold', 0.4)
        best_faq, best_score = None, 0.0
        for faq in self.faqs:
            score = (self._keyword_score(message_text, faq) * 0.7) + (self._similarity_score(message_text, faq) * 0.3)
            if score > best_score:
                best_score, best_faq = score, faq
        if best_score >= threshold and best_faq:
            return {**best_faq, 'score': best_score}
        for faq in self.faqs:
            if self._keyword_score(message_text, faq) > 0.2:
                return {**faq, 'score': 0.3}
        return None
