import json, os, imaplib, smtplib, email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

DUMMY_EMAILS = [
    {"id": "dummy_001", "from": "freelancer1@example.com", "subject": "Upwork Notification: New Message from Alex Turner", "body": "Hi, I just accepted your contract offer. When will I receive payment for the first milestone?", "time": "09:15 AM", "is_upwork": True},
    {"id": "dummy_002", "from": "contractor2@example.com", "subject": "Upwork Notification: New Message from Sarah Chen", "body": "Hello, I wanted to ask about the working hours and what timezone you operate in?", "time": "10:32 AM", "is_upwork": True},
    {"id": "dummy_003", "from": "dev3@example.com", "subject": "Upwork Notification: New Message from Raj Patel", "body": "I have completed the task. How do I submit my work and what tools should I use to share the files?", "time": "11:48 AM", "is_upwork": True},
    {"id": "dummy_004", "from": "designer4@example.com", "subject": "Upwork Notification: New Message from Maria Lopez", "body": "Quick question, do I need to record a video demo of my output or just send the files?", "time": "01:05 PM", "is_upwork": True},
    {"id": "dummy_005", "from": "writer5@example.com", "subject": "Upwork Notification: New Message from James Wu", "body": "Will there be more projects after this one? I am interested in long term collaboration.", "time": "02:20 PM", "is_upwork": True}
]

class EmailHandler:
    def __init__(self, config):
        self.config = config
        self.dummy_mode = config.is_dummy_mode()
        self._sent_log = []

    def test_connection(self):
        if self.dummy_mode:
            return False
        return os.path.exists('token.pickle') or os.path.exists('credentials.json')

    def get_dummy_emails(self):
        return DUMMY_EMAILS

    def fetch_upwork_emails(self, limit=10):
        if self.dummy_mode:
            return DUMMY_EMAILS[:limit]
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.config.get('gmail_user'), os.environ.get('GMAIL_APP_PASSWORD', ''))
            mail.select('inbox')
            _, search_data = mail.search(None, 'FROM "upwork.com" UNSEEN')
            email_ids = search_data[0].split()[-limit:]
            emails = []
            for eid in email_ids:
                _, data = mail.fetch(eid, '(RFC822)')
                msg = email_lib.message_from_bytes(data[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                emails.append({"id": eid.decode(), "from": msg['from'], "subject": msg['subject'], "body": body[:500], "time": datetime.now().strftime("%I:%M %p"), "is_upwork": True})
            mail.logout()
            return emails
        except:
            return []

    def send_reply(self, original_email: dict, reply_text: str) -> bool:
        if self.dummy_mode:
            self._sent_log.append({"to": original_email['from'], "subject": f"Re: {original_email['subject']}", "body": reply_text, "time": datetime.now().strftime("%H:%M:%S"), "status": "simulated"})
            return True
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.get('gmail_user')
            msg['To'] = original_email['from']
            msg['Subject'] = f"Re: {original_email['subject']}"
            msg.attach(MIMEText(reply_text, 'plain'))
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.config.get('gmail_user'), os.environ.get('GMAIL_APP_PASSWORD', ''))
                server.send_message(msg)
            return True
        except:
            return False

    def get_sent_log(self):
        return self._sent_log
