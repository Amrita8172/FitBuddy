import os
os.environ["GOOGLE_API_KEY"] = ""
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
init_db()
client = TestClient(app)

def test_health():
    r=client.get("/health")
    assert r.status_code==200 and r.json()["status"]=="ok"

def test_home():
    r=client.get("/")
    assert r.status_code==200 and "Build your plan" in r.text

def test_generate_and_feedback():
    r=client.post("/api/generate-workout", json={"username":"Test User","user_id":"TEST001","age":22,"weight":65,"goal":"muscle gain","intensity":"medium"})
    assert r.status_code==200 and len(r.json()["plan"]["days"])==7
    r=client.post("/api/submit-feedback", json={"user_id":"TEST001","feedback":"Add one extra rest day."})
    assert r.status_code==200 and len(r.json()["updated_plan"]["days"])==7
