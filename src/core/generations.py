from google.genai import types
from google import genai
from dotenv import load_dotenv
from src.core.models.RoadMap import RoadmapOverview
import os

load_dotenv()
API_KEY =os.getenv("GEMINI_API_KEY")
class Generation():
    def __init__(self, api_key:str | None):
        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RoadmapOverview
        )
    def generateRoadmap(self, promt:str)->RoadmapOverview:
        chat = self.client.chats.create(
            model="gemini-3.5-flash",
            config=self.config,
        )
        response = chat.send_message(promt)
        return RoadmapOverview.model_validate_json(response.text)

if __name__=="__main__":
    gen = Generation(api_key=API_KEY)
    promt = "Hãy tạo một lộ trình tổng quan (Roadmap Overview) học lập trình Backend với Python cho người mới bắt đầu từ con số 0 trong vòng 6 tháng"
    rs = gen.generateRoadmap(promt=promt)
    print(rs)