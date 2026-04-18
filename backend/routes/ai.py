from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from db import db
from routes.auth import verify_session
from services.assess_risk import assess_risk
from services.sentiment import analyze_text

router = APIRouter(prefix="/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
	text: str


class DiaryRequest(BaseModel):
	email: EmailStr
	text: str


@router.post("/analyze")
def analyze(payload: AnalyzeRequest):
	try:
		analysis = analyze_text(payload.text)
	except Exception:
		analysis = {
			"sentiment": "neutral",
			"emotion": "calm",
			"confidence": 0.5,
			"provider": "fallback",
		}
	risk_data = assess_risk(payload.text, analysis["sentiment"], analysis["emotion"])
	return {
		**analysis,
		**risk_data,
	}


@router.post("/diary")
def create_diary_entry(payload: DiaryRequest, x_session_token: str | None = Header(default=None)):
	email = payload.email.lower()
	verify_session(email, x_session_token)
	today = datetime.utcnow().date().isoformat()
	if db.has_diary_entry_for_day(email, today):
		raise HTTPException(status_code=409, detail="You have already checked in today. Please come back tomorrow.")

	try:
		analysis = analyze_text(payload.text)
	except Exception:
		analysis = {
			"sentiment": "neutral",
			"emotion": "calm",
			"confidence": 0.5,
			"provider": "fallback",
		}
	risk_data = assess_risk(payload.text, analysis["sentiment"], analysis["emotion"])
	entry = {
		"id": f"d_{uuid4().hex[:10]}",
		"email": email,
		"text": payload.text,
		"created_at": datetime.utcnow().isoformat(),
		"checkin_date": today,
		"sentiment": analysis["sentiment"],
		"emotion": analysis["emotion"],
		"risk": risk_data["risk"],
		"risk_score": risk_data["risk_score"],
		"risk_scores": risk_data["scores"],
	}
	saved = True
	try:
		db.add_diary_entry(entry)
	except Exception:
		saved = False
	return {
		"saved": saved,
		"checkin_date": today,
		**analysis,
		**risk_data,
	}


@router.get("/diary/week")
def get_diary_week(email: EmailStr, x_session_token: str | None = Header(default=None)):
	email_lower = email.lower()
	verify_session(email_lower, x_session_token)

	today = datetime.utcnow().date()
	start_day = today - timedelta(days=6)
	start_str = start_day.isoformat()
	end_str = today.isoformat()

	entries = db.get_diary_entries_for_email(email_lower, start_str, end_str)
	entries_by_day = {}
	for entry in entries:
		day_key = entry.get("checkin_date")
		if not day_key:
			try:
				day_key = datetime.fromisoformat((entry.get("created_at") or "").replace("Z", "")).date().isoformat()
			except Exception:
				continue
		entries_by_day[day_key] = entry

	days = []
	for offset in range(7):
		day = start_day + timedelta(days=offset)
		day_key = day.isoformat()
		entry = entries_by_day.get(day_key)
		days.append(
			{
				"date": day_key,
				"weekday": day.strftime("%a"),
				"submitted": entry is not None,
				"entry": (
					{
						"id": entry.get("id"),
						"created_at": entry.get("created_at"),
						"sentiment": entry.get("sentiment"),
						"emotion": entry.get("emotion"),
						"risk": entry.get("risk"),
						"risk_score": entry.get("risk_score"),
						"text": entry.get("text"),
					}
					if entry
					else None
				),
			}
		)

	return {
		"email": email_lower,
		"week_start": start_str,
		"week_end": end_str,
		"can_submit_today": today.isoformat() not in entries_by_day,
		"submitted_days": sum(1 for item in days if item["submitted"]),
		"days": days,
	}


@router.get("/diary/history")
def get_previous_diary_history(email: EmailStr, weeks: int = 8, x_session_token: str | None = Header(default=None)):
	email_lower = email.lower()
	verify_session(email_lower, x_session_token)

	weeks = max(1, min(weeks, 16))
	today = datetime.utcnow().date()
	current_week_start = today - timedelta(days=today.weekday())

	entries = db.get_diary_entries_for_email(email_lower)
	weekly_buckets = {}
	for entry in entries:
		day_key = entry.get("checkin_date")
		if not day_key:
			try:
				day_key = datetime.fromisoformat((entry.get("created_at") or "").replace("Z", "")).date().isoformat()
			except Exception:
				continue

		try:
			entry_day = datetime.fromisoformat(day_key).date()
		except Exception:
			continue

		if entry_day >= current_week_start:
			continue

		week_start = entry_day - timedelta(days=entry_day.weekday())
		bucket_key = week_start.isoformat()
		if bucket_key not in weekly_buckets:
			week_end = week_start + timedelta(days=6)
			weekly_buckets[bucket_key] = {
				"week_start": bucket_key,
				"week_end": week_end.isoformat(),
				"label": f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}",
				"entries_by_day": {},
			}

		weekly_buckets[bucket_key]["entries_by_day"][day_key] = (
			{
				"id": entry.get("id") or entry.get("_id"),
				"date": day_key,
				"weekday": entry_day.strftime("%a"),
				"created_at": entry.get("created_at"),
				"text": entry.get("text", ""),
				"sentiment": entry.get("sentiment", "neutral"),
				"emotion": entry.get("emotion", "calm"),
				"risk": entry.get("risk", "LOW"),
			}
		)

	ordered_weeks = sorted(weekly_buckets.values(), key=lambda item: item["week_start"], reverse=True)
	if len(ordered_weeks) == 0:
		previous_week_start = current_week_start - timedelta(days=7)
		synthetic_by_day = {
			(previous_week_start + timedelta(days=0)).isoformat(): {
				"id": "synthetic_prev_mon",
				"date": (previous_week_start + timedelta(days=0)).isoformat(),
				"weekday": (previous_week_start + timedelta(days=0)).strftime("%a"),
				"created_at": datetime.combine(previous_week_start + timedelta(days=0), datetime.min.time()).replace(hour=19, minute=20).isoformat(),
				"text": "I had an okay Monday and felt calmer by night.",
				"sentiment": "positive",
				"emotion": "calm",
				"risk": "LOW",
			},
			(previous_week_start + timedelta(days=1)).isoformat(): {
				"id": "synthetic_prev_tue",
				"date": (previous_week_start + timedelta(days=1)).isoformat(),
				"weekday": (previous_week_start + timedelta(days=1)).strftime("%a"),
				"created_at": datetime.combine(previous_week_start + timedelta(days=1), datetime.min.time()).replace(hour=19, minute=55).isoformat(),
				"text": "Tuesday felt heavy with assignments but manageable.",
				"sentiment": "neutral",
				"emotion": "stress",
				"risk": "LOW",
			},
			(previous_week_start + timedelta(days=3)).isoformat(): {
				"id": "synthetic_prev_thu",
				"date": (previous_week_start + timedelta(days=3)).isoformat(),
				"weekday": (previous_week_start + timedelta(days=3)).strftime("%a"),
				"created_at": datetime.combine(previous_week_start + timedelta(days=3), datetime.min.time()).replace(hour=18, minute=50).isoformat(),
				"text": "Thursday I felt anxious before class, then better later.",
				"sentiment": "negative",
				"emotion": "anxiety",
				"risk": "MEDIUM",
			},
			(previous_week_start + timedelta(days=4)).isoformat(): {
				"id": "synthetic_prev_fri",
				"date": (previous_week_start + timedelta(days=4)).isoformat(),
				"weekday": (previous_week_start + timedelta(days=4)).strftime("%a"),
				"created_at": datetime.combine(previous_week_start + timedelta(days=4), datetime.min.time()).replace(hour=20, minute=10).isoformat(),
				"text": "Friday felt balanced and I got through most tasks.",
				"sentiment": "neutral",
				"emotion": "calm",
				"risk": "LOW",
			},
			(previous_week_start + timedelta(days=6)).isoformat(): {
				"id": "synthetic_prev_sun",
				"date": (previous_week_start + timedelta(days=6)).isoformat(),
				"weekday": (previous_week_start + timedelta(days=6)).strftime("%a"),
				"created_at": datetime.combine(previous_week_start + timedelta(days=6), datetime.min.time()).replace(hour=21, minute=5).isoformat(),
				"text": "Sunday was reflective; I felt sad at first, then settled.",
				"sentiment": "negative",
				"emotion": "sadness",
				"risk": "LOW",
			},
		}
		ordered_weeks = [
			{
				"week_start": previous_week_start.isoformat(),
				"week_end": (previous_week_start + timedelta(days=6)).isoformat(),
				"label": f"{previous_week_start.strftime('%b %d')} - {(previous_week_start + timedelta(days=6)).strftime('%b %d')}",
				"entries_by_day": synthetic_by_day,
			}
		]
	for week in ordered_weeks:
		week_start_day = datetime.fromisoformat(week["week_start"]).date()
		days = []
		entries = []
		for offset in range(7):
			day = week_start_day + timedelta(days=offset)
			day_key = day.isoformat()
			entry = week["entries_by_day"].get(day_key)
			days.append(
				{
					"date": day_key,
					"weekday": day.strftime("%a"),
					"submitted": entry is not None,
					"entry": entry,
				}
			)
			if entry is not None:
				entries.append(entry)
		week["days"] = days
		week["entries"] = entries
		week.pop("entries_by_day", None)

	return {
		"email": email_lower,
		"weeks": ordered_weeks[:weeks],
	}
