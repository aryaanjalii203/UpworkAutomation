import json
import os
import io
import csv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service_account.json'

class DriveHandler:
    def __init__(self, config):
        self.config = config
        self.folder_id = config.get('drive_folder_id', '')
        self.service = None
        self._connect()

    def _connect(self):
        """Authenticate with Google Drive using service account."""
        try:
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                print("[DriveHandler] service_account.json not found. Running in offline mode.")
                return
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            self.service = build('drive', 'v3', credentials=creds)
            print("[DriveHandler] Connected to Google Drive successfully.")
        except Exception as e:
            print(f"[DriveHandler] Connection failed: {e}")
            self.service = None

    def is_connected(self):
        return self.service is not None

    def list_files(self):
        """List all files in the configured Drive folder."""
        if not self.service or not self.folder_id:
            return []
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            result = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType)"
            ).execute()
            return result.get('files', [])
        except Exception as e:
            print(f"[DriveHandler] list_files error: {e}")
            return []

    def _download_file(self, file_id):
        """Download a file's content as text."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buffer.getvalue().decode('utf-8')
        except Exception as e:
            print(f"[DriveHandler] download error: {e}")
            return None

    def _export_google_sheet(self, file_id):
        """Export a Google Sheet as CSV text."""
        try:
            request = self.service.files().export_media(
                fileId=file_id, mimeType='text/csv')
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buffer.getvalue().decode('utf-8')
        except Exception as e:
            print(f"[DriveHandler] export error: {e}")
            return None

    def _parse_csv(self, content):
        """Parse CSV content into FAQ list. Expects Question,Answer columns."""
        faqs = []
        try:
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                # Support multiple column name formats
                question = (row.get('Question') or row.get('question') or
                           row.get('Q') or row.get('q') or '').strip()
                answer = (row.get('Answer') or row.get('answer') or
                         row.get('A') or row.get('a') or '').strip()
                if question and answer:
                    keywords = [w.lower() for w in question.split() if len(w) > 3]
                    faqs.append({
                        "question": question,
                        "answer": answer,
                        "keywords": keywords,
                        "source": "google_drive"
                    })
        except Exception as e:
            print(f"[DriveHandler] CSV parse error: {e}")
        return faqs

    def _parse_json(self, content):
        """Parse JSON content into FAQ list."""
        faqs = []
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    question = item.get('question', item.get('Question', '')).strip()
                    answer = item.get('answer', item.get('Answer', '')).strip()
                    if question and answer:
                        keywords = item.get('keywords',
                            [w.lower() for w in question.split() if len(w) > 3])
                        faqs.append({
                            "question": question,
                            "answer": answer,
                            "keywords": keywords,
                            "source": "google_drive"
                        })
        except Exception as e:
            print(f"[DriveHandler] JSON parse error: {e}")
        return faqs

    def fetch_faqs_from_drive(self):
        """
        Main method: scan Drive folder, parse all FAQ files, return merged list.
        Supports: .csv, .json, Google Sheets
        """
        if not self.is_connected():
            return [], "Not connected to Google Drive. Check service_account.json."

        if not self.folder_id or self.folder_id == 'DUMMY_FOLDER_ID':
            return [], "No valid Drive Folder ID configured."

        files = self.list_files()
        if not files:
            return [], "No files found in the Drive folder."

        all_faqs = []
        parsed_files = []

        for f in files:
            mime = f.get('mimeType', '')
            name = f.get('name', '')
            fid = f['id']

            content = None

            if mime == 'application/vnd.google-apps.spreadsheet':
                content = self._export_google_sheet(fid)
                if content:
                    all_faqs.extend(self._parse_csv(content))
                    parsed_files.append(name)

            elif name.endswith('.csv') or mime == 'text/csv':
                content = self._download_file(fid)
                if content:
                    all_faqs.extend(self._parse_csv(content))
                    parsed_files.append(name)

            elif name.endswith('.json') or mime == 'application/json':
                content = self._download_file(fid)
                if content:
                    all_faqs.extend(self._parse_json(content))
                    parsed_files.append(name)

        if not all_faqs:
            return [], f"Files found ({len(files)}) but no FAQs could be parsed. Ensure files have Question/Answer columns."

        msg = f"Synced {len(all_faqs)} FAQs from {len(parsed_files)} file(s): {', '.join(parsed_files)}"
        return all_faqs, msg
