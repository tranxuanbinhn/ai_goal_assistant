from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from src.core.models import Task
from src.core.logging.logger_config import setup_logger
from typing import List
from src.core.models.Task import ExecutableTask
import asyncio
from typing import Any, Dict, List
logger = setup_logger()
BASE_PATH = Path(__file__).resolve().parent.parent.parent
CREDENTAILS_FILE = BASE_PATH / "config" / "credentials.json"
TOKEN_FILE = BASE_PATH / "config" / "token.json"

SCOPES = ['https://www.googleapis.com/auth/tasks']
class GoogleTask():
    def __init__(self, service):
       self.service = service

    @classmethod
    async def creare (cls,credentials_file:str, token_file:str, scopes:list[str]):
        def _get_service_sync():
            creds = None
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
                    creds = flow.run_local_server(port=0)
        
                with open(token_file, 'w') as token_f:
                    token_f.write(creds.to_json())
            return build('tasks','v1', credentials=creds)
        service = await asyncio.to_thread(_get_service_sync)
        return cls(service)  

    async def create_task_list(self,title:str)->str:
        service = self.service

        tasklist_body = {
            "title":title
        }

        new_tasklist = await asyncio.to_thread(service.tasklists().insert(body = tasklist_body).execute)

        return new_tasklist.get('id')

    async def get_all_task_list(self):
        service = self.service
        results = await asyncio.to_thread(service.tasklists().list().execute)
        items = results.get('items',[])

        if not items:
            logger.info("Khong tim thay danh sach")
            return []
        return items

    async def create_google_task(self,title:str, notes:str = None, due_date:str = None, task_list_id:str = '@default'):
        service = self.service
        task_body = {
            'title':title
        }
        if notes:
            task_body['notes'] = notes

        if due_date:
                task_body['due'] = due_date

        created_task = await asyncio.to_thread(service.tasks().insert(
            tasklist = task_list_id,
            body = task_body
        ).execute)

        return created_task
    async def create_multiple_google_tasks(self, tasks: List[ExecutableTask], task_list_id:str = "@default")->List[Dict[str, Any]]:
        
        created_tasks = []
        errors = []
        def callback(request_id, response, exception):
            if exception is not None:
                errors.append({"request_id":request_id, "error":str(exception)})
            else:
                created_tasks.append(response)
        batch = self.service.new_batch_http_request(callback=callback)

        for idx, item in enumerate(tasks):
            task_body = {"title": item.title,
                         "due":item.google_task_due}
            if item.notes:
                task_body["notes"] = item.notes
            batch.add(
                self.service.tasks().insert(tasklist= task_list_id, body = task_body),
                request_id = str(idx)
            )
        await asyncio.to_thread( batch.execute)
        if errors:
            logger.error(f"Co {len(errors)} khi khoi tao")
        return created_tasks

    async def get_task_completion_stats(self, task_list_id :str = "@default", filter_this_week=True):
        params = {
            'tasklist':task_list_id,
            'showCompleted':True,
            'showHidden':True,
            'maxResults':100
        }
        if filter_this_week:
            now = datetime.now(timezone.utc)
            start_of_week = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
            params['dueMin'] = start_of_week.isoformat()
            params['dueMax'] = end_of_week.isoformat()
        completed_tasks = []
        incomplete_tasks = []
        page_token = None
        while True:
            if page_token:
                params['pageToken'] = page_token
            results = await asyncio.to_thread(self.service.tasks().list(**params).execute)
            items = results.get('items',[])
            for task in items:
                if task.get('status') == 'completed':
                    completed_tasks.append(task)
                else:
                    incomplete_tasks.append(task)
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        total = len(completed_tasks) + len(incomplete_tasks)
        percentage = (len(completed_tasks)/total * 100) if total > 0 else 0.0 
        return {
        'total': total,
        'completed_count': len(completed_tasks),
        'incomplete_count': len(incomplete_tasks),
        'completion_rate': round(percentage, 2),
        'completed_tasks': completed_tasks,
        'incomplete_tasks': incomplete_tasks
    }

if __name__ == "__main__":
    google_task = GoogleTask(CREDENTAILS_FILE, TOKEN_FILE)
    #rs1 = google_task.create_task_list("Hoc tap")
    #print(f"rs {rs1}")
    rs2 = google_task.get_all_task_list()
    print(rs2)
    print(rs2[0]['id'])
    #google_task.create_google_task("Hoc tap", task_list_id='aXV6Q0c1dEt2ZFQ2TmRHSw')
    #MTAzODI0MTg2MzkyMjcxMTExODI6MDow
    #xem percent hoan thanh
    rs3 = google_task.get_task_completion_stats(task_list_id='MTAzODI0MTg2MzkyMjcxMTExODI6MDow')
    print(f'rs3 {rs3}')