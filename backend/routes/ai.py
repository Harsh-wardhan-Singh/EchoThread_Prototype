import os
from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from data.fake_data import FAKE_DIARY
from db import db
from routes.auth import verify_session
from services.assess_risk import assess_risk
from services.risk import resolve_high_risk_support_message
from services.sentiment import analyze_text

router = APIRouter(prefix="/ai", tags=["ai"])

DEMO_STUDENT_ONE_EMAIL = "student1@demo.hrc.du.ac.in"
DEMO_STUDENT_TWO_EMAIL = "student2@demo.hrc.du.ac.in"


class AnalyzeRequest(BaseModel):
	text: str


class DiaryRequest(BaseModel):
	email: EmailStr
	text: str


def _flag_enabled(name: str, default: bool = False):
	value = os.getenv(name, "true" if default else "false")
	return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _canonical_demo_email(email: str):
	value = (email or "").lower().strip()
	if value.endswith("@demo.hrc.ac.in"):
		return value.replace("@demo.hrc.ac.in", "@demo.hrc.du.ac.in")
	return value


def _emails_match(email_a: str, email_b: str):
	return _canonical_demo_email(email_a) == _canonical_demo_email(email_b)


def _get_diary_entries(email: str, start_checkin_date=None, end_checkin_date=None):
	if _flag_enabled("DIARY_USE_FAKE_DATA", default=True):
		entries = [
			entry
			for entry in FAKE_DIARY
			if _emails_match(entry.get("email", ""), email)
		]
		if start_checkin_date:
			entries = [entry for entry in entries if (entry.get("checkin_date") or "") >= start_checkin_date]
		if end_checkin_date:
			entries = [entry for entry in entries if (entry.get("checkin_date") or "") <= end_checkin_date]
		entries.sort(key=lambda entry: (entry.get("checkin_date") or "", entry.get("created_at") or ""))
		return entries

	return db.get_diary_entries_for_email(email, start_checkin_date, end_checkin_date)


def _has_diary_entry_for_day(email: str, checkin_date: str):
	if _flag_enabled("DIARY_USE_FAKE_DATA", default=True):
		entries = _get_diary_entries(email, checkin_date, checkin_date)
		return any((entry.get("checkin_date") or "") == checkin_date for entry in entries)
	return db.has_diary_entry_for_day(email, checkin_date)


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
	support_message = resolve_high_risk_support_message(payload.text, risk_data.get("risk"))
	return {
		**analysis,
		**risk_data,
		"support_message": support_message,
	}


@router.post("/diary")
def create_diary_entry(payload: DiaryRequest, x_session_token: str | None = Header(default=None)):
	email = payload.email.lower()
	verify_session(email, x_session_token)
	today = datetime.utcnow().date().isoformat()
	if _has_diary_entry_for_day(email, today):
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
	support_message = resolve_high_risk_support_message(payload.text, risk_data.get("risk"))
	entry = {
		"id": f"d_{uuid4().hex[:10]}",
		"email": _canonical_demo_email(email) if _flag_enabled("DIARY_USE_FAKE_DATA", default=True) else email,
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
		if _flag_enabled("DIARY_USE_FAKE_DATA", default=True):
			FAKE_DIARY.append(entry)
		else:
			db.add_diary_entry(entry)
	except Exception:
		saved = False
	return {
		"saved": saved,
		"checkin_date": today,
		**analysis,
		**risk_data,
		"support_message": support_message,
	}


@router.get("/diary/week")
def get_diary_week(email: EmailStr, x_session_token: str | None = Header(default=None)):
	email_lower = email.lower()
	verify_session(email_lower, x_session_token)

	today = datetime.utcnow().date()
	start_day = today - timedelta(days=6)
	start_str = start_day.isoformat()
	end_str = today.isoformat()

	entries = _get_diary_entries(email_lower, start_str, end_str)
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

	entries = _get_diary_entries(email_lower)
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
	if _flag_enabled("DIARY_USE_FAKE_DATA", default=True) and (
		_emails_match(email_lower, DEMO_STUDENT_ONE_EMAIL) or _emails_match(email_lower, DEMO_STUDENT_TWO_EMAIL)
	):
		previous_week_start = (current_week_start - timedelta(days=7)).isoformat()
		ordered_weeks = [week for week in ordered_weeks if week.get("week_start") == previous_week_start]

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
