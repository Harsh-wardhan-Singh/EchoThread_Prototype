from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from db import db
from services.risk import assess_risk
from services.sentiment import analyze_text

router = APIRouter(prefix="/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
	text: str


class DiaryRequest(BaseModel):
	email: EmailStr
	text: str


@router.post("/analyze")
def analyze(payload: AnalyzeRequest):
	analysis = analyze_text(payload.text)
	risk = assess_risk(payload.text, analysis["sentiment"], analysis["emotion"])
	return {
		**analysis,
		"risk": risk,
	}


@router.post("/diary")
def create_diary_entry(payload: DiaryRequest):
	analysis = analyze_text(payload.text)
	risk = assess_risk(payload.text, analysis["sentiment"], analysis["emotion"])
	entry = {
		"id": f"d_{uuid4().hex[:10]}",
		"email": payload.email,
		"text": payload.text,
		"created_at": datetime.utcnow().isoformat(),
		"sentiment": analysis["sentiment"],
		"emotion": analysis["emotion"],
		"risk": risk,
	}
	db.add_diary_entry(entry)
	return {
		"saved": True,
		**analysis,
		"risk": risk,
	}
