from datetime import datetime


class WorkflowEngine:
    def __init__(self, config, email_handler, faq_matcher):
        self.config = config
        self.email_handler = email_handler
        self.faq_matcher = faq_matcher

    def run(self):
        """
        Main workflow:
        1. Fetch unread Upwork emails
        2. Match each to a FAQ
        3. Send auto-reply
        4. Return results
        """
        emails = self.email_handler.fetch_upwork_emails(limit=10)
        results = []

        for em in emails:
            matched = self.faq_matcher.find_best_match(em['body'])
            reply_text = matched['answer'] if matched else self.config.get('default_reply')

            if self.config.get('auto_reply', True):
                success = self.email_handler.send_reply(em, reply_text)
                status = 'sent' if success else 'failed'
            else:
                status = 'pending'

            results.append({
                'id': em['id'],
                'from': em['from'],
                'subject': em['subject'],
                'matched_faq': matched['question'] if matched else 'No match',
                'reply': reply_text,
                'status': status,
                'time': datetime.now().strftime("%H:%M:%S")
            })

        return results
