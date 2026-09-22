from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

from src.core.logging.logger_config import setup_logger

logger = setup_logger()
BASE_PATH = Path(__file__).resolve().parent.parent.parent
CREDENTAILS_FILE = BASE_PATH / "config" / "credentials.json"
TOKEN_FILE = BASE_PATH / "config" / "token.json"

SCOPES = ['https://www.googleapis.com/auth/tasks']
class GoogleTask():
    def __init__(self, credentials_file:str, token_file:str):
        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
    
            with open(token_file, 'w') as token_f:
                token_f.write(creds.to_json())
        self.service = build('tasks','v1', credentials=creds)
        
    

    def create_task_list(self,title:str)->str:
        service = self.service

        tasklist_body = {
            "title":title
        }

        new_tasklist = service.tasklists().insert(body = tasklist_body).execute()

        return new_tasklist.get('id')

    def get_all_task_list(self):
        service = self.service
        results = service.tasklists().list().execute()
        items = results.get('items',[])

        if not items:
            logger.info("Khong tim thay danh sach")
            return []
        return items

    def create_google_task(self,title:str, notes:str = None, due_date:str = None, task_list_id:str = '@default'):
        service = self.service
        task_body = {
            'title':title
        }
        if notes:
            task_body['notes'] = notes

        if due_date:
                task_body['due'] = due_date

        created_task = service.tasks().insert(
            tasklist = task_list_id,
            body = task_body
        ).execute()

        return created_task

if __name__ == "__main__":
    google_task = GoogleTask(CREDENTAILS_FILE, TOKEN_FILE)
    #rs1 = google_task.create_task_list("Hoc tap")
    #print(f"rs {rs1}")
    rs2 = google_task.get_all_task_list()
    print(rs2)
    print(rs2[0]['id'])
    #google_task.create_google_task("Hoc tap", task_list_id='aXV6Q0c1dEt2ZFQ2TmRHSw')
    