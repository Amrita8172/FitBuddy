import json
from typing import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User
from .schemas import FeedbackRequest, UserInput
from .services.ai_service import generate_nutrition_tip_with_flash, generate_workout_gemini, update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()

def _require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    import secrets
    if not (secrets.compare_digest(credentials.username, settings.admin_username) and secrets.compare_digest(credentials.password, settings.admin_password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials", headers={"WWW-Authenticate":"Basic"})

def _plan_dict(value: str) -> dict:
    try: return json.loads(value)
    except (TypeError, json.JSONDecodeError): return {"title":"Workout Plan","summary":value,"days":[],"safety":""}

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request":request})

@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(request: Request, username: Annotated[str, Form()], user_id: Annotated[str, Form()], age: Annotated[int, Form()], weight: Annotated[float, Form()], goal: Annotated[str, Form()], intensity: Annotated[str, Form()], db: Session = Depends(get_db)):
    data = UserInput(username=username,user_id=user_id,age=age,weight=weight,goal=goal,intensity=intensity)
    plan = generate_workout_gemini(data.model_dump())
    tip = generate_nutrition_tip_with_flash(data.goal)
    user = db.scalar(select(User).where(User.user_id == data.user_id))
    if user:
        for k,v in data.model_dump().items(): setattr(user,k,v)
        user.original_plan, user.updated_plan, user.last_feedback, user.nutrition_tip = json.dumps(plan), None, None, tip
    else:
        user = User(**data.model_dump(), original_plan=json.dumps(plan), nutrition_tip=tip)
        db.add(user)
    db.commit(); db.refresh(user)
    return templates.TemplateResponse(request=request,name="result.html",context={"request":request,"user":user,"plan":plan,"nutrition_tip":tip,"updated":False})

@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(request: Request, user_id: Annotated[str, Form()], feedback: Annotated[str, Form()], db: Session = Depends(get_db)):
    payload = FeedbackRequest(user_id=user_id, feedback=feedback)
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if not user: raise HTTPException(status_code=404, detail="User ID not found")
    current = _plan_dict(user.updated_plan or user.original_plan)
    revised = update_workout_plan(current, {"username":user.username,"age":user.age,"weight":user.weight,"goal":user.goal,"intensity":user.intensity}, payload.feedback)
    user.updated_plan, user.last_feedback = json.dumps(revised), payload.feedback
    db.commit(); db.refresh(user)
    return templates.TemplateResponse(request=request,name="result.html",context={"request":request,"user":user,"plan":revised,"nutrition_tip":user.nutrition_tip,"updated":True})

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, credentials: HTTPBasicCredentials = Depends(_require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse(request=request,name="admin.html",context={"request":request,"users":users})

@router.get("/api/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return {"user":{"id":user.user_id,"username":user.username,"age":user.age,"weight":user.weight,"goal":user.goal,"intensity":user.intensity},"original_plan":_plan_dict(user.original_plan),"updated_plan":_plan_dict(user.updated_plan) if user.updated_plan else None,"nutrition_tip":user.nutrition_tip,"last_feedback":user.last_feedback}

@router.post("/api/generate-workout")
def api_generate_workout(payload: UserInput, db: Session = Depends(get_db)):
    plan = generate_workout_gemini(payload.model_dump()); tip = generate_nutrition_tip_with_flash(payload.goal)
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if user:
        for k,v in payload.model_dump().items(): setattr(user,k,v)
        user.original_plan,user.updated_plan,user.last_feedback,user.nutrition_tip = json.dumps(plan),None,None,tip
    else:
        user = User(**payload.model_dump(),original_plan=json.dumps(plan),nutrition_tip=tip); db.add(user)
    db.commit()
    return {"user_id":payload.user_id,"plan":plan,"nutrition_tip":tip}

@router.post("/api/submit-feedback")
def api_submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == payload.user_id))
    if not user: raise HTTPException(status_code=404, detail="User not found")
    current = _plan_dict(user.updated_plan or user.original_plan)
    revised = update_workout_plan(current, {"username":user.username,"age":user.age,"weight":user.weight,"goal":user.goal,"intensity":user.intensity}, payload.feedback)
    user.updated_plan,user.last_feedback = json.dumps(revised),payload.feedback
    db.commit()
    return {"user_id":payload.user_id,"updated_plan":revised,"feedback":payload.feedback}

@router.delete("/api/users/{user_id}")
def delete_user(user_id: str, credentials: HTTPBasicCredentials = Depends(_require_admin), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user: raise HTTPException(status_code=404, detail="User not found")
    db.delete(user); db.commit()
    return {"message":"User deleted","user_id":user_id}
