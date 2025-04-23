import os
import json
import asyncio
import pickle
from datetime import datetime
import aiofiles
from functools import lru_cache
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.config.project_config import project_settings


# SCOPES = ['https://www.googleapis.com/auth/drive.file']
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

CREDENTIALS_FILE = project_settings.GOOGLE_CREDENTIAL_JSON_PATH
TOKEN_PICKLE = project_settings.GOOGLE_TOKEN_PICKLE_PATH
GOOGLE_CREDENTIAL_JSON = project_settings.GOOGLE_CREDENTIAL_JSON


class GoogleDriveService:
    def __init__(self):
        self.creds = self._get_user_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)
        self.drive_service = self.service

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_user_credentials():
        creds = None
        credentials_json_str = GOOGLE_CREDENTIAL_JSON
        
        if credentials_json_str:
            credentials_info = json.loads(credentials_json_str)
        else:
            raise ValueError("Did not find GOOGLE_CREDENTIAL_JSON.")
        
        if os.path.exists(TOKEN_PICKLE):
            with open(TOKEN_PICKLE, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_PICKLE, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    # @staticmethod
    # @lru_cache(maxsize=1)
    # def _get_user_credentials():
    #     creds = None
    #     if os.path.exists(TOKEN_PICKLE):
    #         with open(TOKEN_PICKLE, 'rb') as token:
    #             creds = pickle.load(token)

    #     if not creds or not creds.valid:
    #         if creds and creds.expired and creds.refresh_token:
    #             creds.refresh(Request())
    #         else:
    #             flow = InstalledAppFlow.from_client_secrets_file(
    #                 CREDENTIALS_FILE, SCOPES)
    #             creds = flow.run_local_server(port=0)

    #         # Save token
    #         with open(TOKEN_PICKLE, 'wb') as token:
    #             pickle.dump(creds, token)

    #     return creds

    async def upload_text_file(self, content: str, filename: str = "prompt", delete_after_upload: bool = False) -> str:
        # Save file localy
        ltr_fix = "\u200E"
        content = ltr_fix + content.replace("\n", "\n" + ltr_fix)
        filename = f"{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt" 
        file_path = os.path.join(project_settings.PROMPT_DIR, filename)
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)

        file_metadata = {
            'name': filename,
            'mimeType': 'text/plain'
        }
        media = MediaFileUpload(file_path, mimetype='text/plain')
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        # Make file accessible by link
        self.service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'},
        ).execute()

        if delete_after_upload:
            await asyncio.sleep(1)
            os.remove(file_path)

        file_id = file.get('id')
        public_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        return public_url
