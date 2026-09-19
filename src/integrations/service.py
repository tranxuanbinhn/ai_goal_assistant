from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

from core.logging.logger_config import setup_logger

logger = setup_logger()
BASE_PATH = Path(__file__).resolve().parent.parent.parent
CREDENTAILS_FILE = BASE_PATH / "config" / "credentials.json"
TOKEN_FILE = BASE_PATH / "config" / "token.json"

SCOPES = ['https://www.googleapis.com/auth/tasks']
class GoogleTask():
    def __init__(self, credentials_file:str, token_file:str):
        ()
def get_service_task():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTAILS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token_file:
            token_file.write(creds.to_json())
    service = build('tasks','v1', credentials=creds)
    return service

def create_task_list(title:str)->str:
    service = get_service_task()

    tasklist_body = {
        "title":title
    }

    new_tasklist = service.tasklists().insert(body = tasklist_body).execute()

    return new_tasklist.get('id')

def get_all_task_list():
    service = get_service_task()
    results = service.tasklists().list().execute()
    items = results.get('items',[])

    if not items:
        logger.info("Khong tim thay danh sach")
        return []
    return items

def create_google_task(title:str, notes:str = None, due_date:str = None):
    service = get_service_task()
    task_body = {
        'title':title
    }
    if notes:
        task_body['notes'] = notes

    if due_date:
            task_body['due'] = due_date

    created_task = service.tasks().insert(
        tasklist = '@default',
        body = task_body
    ).execute()

    return created_task
    