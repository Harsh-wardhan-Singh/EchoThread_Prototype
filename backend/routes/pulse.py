import os
from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Header, HTTPException
from pydantic import EmailStr

from data.fake_data import FAKE_DIARY, FAKE_POSTS
from db import db
from routes.auth import resolve_session_email, verify_session
from utils.otp import detect_role

router = APIRouter(prefix="/pulse", tags=["pulse"])


def _to_datetime(value: str):
	try:
		return datetime.fromisoformat((value or "").replace("Z", ""))
	except Exception:
		return None


def _last_7_days():
	today = datetime.utcnow().date()
	return [today - timedelta(days=days_back) for days_back in range(6, -1, -1)]


def _day_key(day):
	return day.isoformat()


def _student_message(avg_stress):
	if avg_stress >= 70:
		return "You’ve been feeling quite stressed this week. Take gentle pauses and reach out if needed."
	if avg_stress >= 45:
		return "You’ve been a bit stressed this week. A small rest routine may help."
	return "Your week looks fairly balanced. Keep following what helps you feel grounded."


def _stress_level(avg_stress):
	if avg_stress >= 70:
		return "HIGH"
	if avg_stress >= 45:
		return "MEDIUM"
	return "LOW"


def _risk_to_stress(risk, risk_score):
	risk_value = (risk or "LOW").upper()
	if risk_score is not None:
		try:
			score_num = float(risk_score)
			if score_num <= 1:
				score_num *= 100
			return max(0, min(100, round(score_num)))
		except Exception:
			pass
	if risk_value == "HIGH":
		return 85
	if risk_value == "MEDIUM":
		return 55
	return 25


def _normalize_sentiment(sentiment):
	value = (sentiment or "neutral").lower()
	if value in {"positive", "negative", "neutral"}:
		return value
	return "neutral"


def _canonical_demo_email(email: str):
	value = (email or "").lower().strip()
	if value.endswith("@demo.hrc.ac.in"):
		return value.replace("@demo.hrc.ac.in", "@demo.hrc.du.ac.in")
	return value


def _emails_match(email_a: str, email_b: str):
	return _canonical_demo_email(email_a) == _canonical_demo_email(email_b)


def _build_previous_week_history(previous_week_entries):
	today = datetime.utcnow().date()
	current_week_start = today - timedelta(days=today.weekday())
	previous_week_start = current_week_start - timedelta(days=7)
	previous_week_days = [previous_week_start + timedelta(days=offset) for offset in range(7)]

	lookup = {}
	for entry in previous_week_entries:
		timestamp = _to_datetime(entry.get("created_at"))
		day_key = entry.get("checkin_date") or (timestamp.date().isoformat() if timestamp else None)
		if not day_key:
			continue
		lookup[day_key] = entry

	history = []
	for day in previous_week_days:
		day_key = day.isoformat()
		entry = lookup.get(day_key)
		sentiment = _normalize_sentiment(entry.get("sentiment") if entry else None)
		history.append(
			{
				"day": day.strftime("%a"),
				"date": day_key,
				"sentiment": sentiment if entry else None,
				"text": entry.get("text") if entry else None,
			}
		)

	return history


def _build_student_response(email, user_uuid, last_7_day_entries, previous_week_entries, mode):
	days = _last_7_days()
	day_lookup = {_day_key(day): {"day": day.strftime("%a"), "stress": [], "positive": 0, "negative": 0, "total": 0} for day in days}

	for entry in last_7_day_entries:
		timestamp = _to_datetime(entry.get("created_at"))
		day_key = entry.get("checkin_date") or (timestamp.date().isoformat() if timestamp else None)
		if day_key not in day_lookup:
			continue

		bucket = day_lookup[day_key]
		bucket["stress"].append(_risk_to_stress(entry.get("risk"), entry.get("risk_score")))
		sentiment = _normalize_sentiment(entry.get("sentiment"))
		if sentiment == "positive":
			bucket["positive"] += 1
		elif sentiment == "negative":
			bucket["negative"] += 1
		bucket["total"] += 1

	stress_series = []
	total_stress = 0
	checkin_days = 0
	for day in days:
		bucket = day_lookup[_day_key(day)]
		raw_stress_score = round(sum(bucket["stress"]) / len(bucket["stress"])) if bucket["stress"] else 0
		if bucket["total"] > 0:
			total_stress += raw_stress_score
			checkin_days += 1

		stress_series.append({"day": bucket["day"], "score": round(raw_stress_score / 100, 2)})

	avg_stress = round(total_stress / checkin_days, 1) if checkin_days else 0
	previous_week_history = _build_previous_week_history(previous_week_entries)
	return {
		"mode": mode,
		"email": email,
		"user_uuid": user_uuid,
		"message": _student_message(avg_stress),
		"avg_stress_level": _stress_level(avg_stress),
		"avg_stress_score": avg_stress,
		"checkin_days": checkin_days,
		"stress_series": stress_series,
		"previous_week_history": previous_week_history,
	}


def _build_counselor_response(posts, total_students, mode):
	days = _last_7_days()
	day_lookup = {
		_day_key(day): {
			"day": day.strftime("%a"),
			"stress": [],
			"posts": 0,
			"positive": 0,
			"negative": 0,
			"total_sentiment": 0,
		}
		for day in days
	}

	risk_counter = Counter()
	emotion_counter = Counter()

	for post in posts:
		timestamp = _to_datetime(post.get("created_at"))
		if not timestamp:
			continue
		day_key = timestamp.date().isoformat()
		if day_key not in day_lookup:
			continue

		bucket = day_lookup[day_key]
		bucket["posts"] += 1
		bucket["stress"].append(_risk_to_stress(post.get("risk"), post.get("risk_score")))

		sentiment = _normalize_sentiment(post.get("sentiment"))
		if sentiment == "positive":
			bucket["positive"] += 1
		elif sentiment == "negative":
			bucket["negative"] += 1
		bucket["total_sentiment"] += 1

		risk_counter[(post.get("risk") or "LOW").upper()] += 1
		emotion_counter[(post.get("emotion") or "calm").lower()] += 1

	overall_stress_series = []
	posts_series = []
	sentiment_series = []
	for day in days:
		bucket = day_lookup[_day_key(day)]
		stress_score = round(sum(bucket["stress"]) / len(bucket["stress"])) if bucket["stress"] else 0
		if bucket["total_sentiment"] > 0:
			positive_score = round((bucket["positive"] / bucket["total_sentiment"]) * 100)
			negative_score = round((bucket["negative"] / bucket["total_sentiment"]) * 100)
		else:
			positive_score = 0
			negative_score = 0

		overall_stress_series.append({"day": bucket["day"], "score": stress_score})
		posts_series.append({"day": bucket["day"], "count": bucket["posts"]})
		sentiment_series.append({"day": bucket["day"], "positive": positive_score, "negative": negative_score})

	emotion_distribution = [{"emotion": emotion, "count": count} for emotion, count in emotion_counter.most_common(8)]
	total_posts = len(posts)
	high_risk = risk_counter.get("HIGH", 0)
	medium_risk = risk_counter.get("MEDIUM", 0)
	avg_stress = round(sum(item["score"] for item in overall_stress_series) / len(overall_stress_series), 1) if overall_stress_series else 0

	analytics_summary = [
		f"{total_posts} campus posts were observed in the last 7 days.",
		f"Average campus stress score is {avg_stress} out of 100 based on feed risk patterns.",
		f"{high_risk} HIGH-risk and {medium_risk} MEDIUM-risk posts may need prioritized counselor outreach.",
	]

	return {
		"mode": mode,
		"total_students": total_students,
		"overall_stress_series": overall_stress_series,
		"posts_series": posts_series,
		"sentiment_series": sentiment_series,
		"risk_counts": {
			"LOW": risk_counter.get("LOW", 0),
			"MEDIUM": risk_counter.get("MEDIUM", 0),
			"HIGH": risk_counter.get("HIGH", 0),
		},
		"emotion_distribution": emotion_distribution,
		"analytics_summary": analytics_summary,
	}


def _should_use_fake():
	return (os.getenv("PULSE_USE_FAKE_DATA", "true") or "true").strip().lower() in {"1", "true", "yes", "on"}


@router.get("/student")
def get_student_pulse(email: EmailStr, user_uuid: str, x_session_token: str | None = Header(default=None)):
	email_lower = email.lower()
	verify_session(email_lower, x_session_token)

	expected_uuid = db.get_or_create_user_uuid(email_lower, "student")
	if expected_uuid != user_uuid:
		raise HTTPException(status_code=403, detail="Pulse data can only be accessed by the owning student")

	if _should_use_fake():
		entries = [entry for entry in FAKE_DIARY if _emails_match(entry.get("email", ""), email_lower)]
		last_7_days = _last_7_days()
		start_day = _day_key(last_7_days[0])
		end_day = _day_key(last_7_days[-1])
		last_7_day_entries = [entry for entry in entries if start_day <= (entry.get("checkin_date") or "") <= end_day]

		today = datetime.utcnow().date()
		current_week_start = today - timedelta(days=today.weekday())
		previous_week_start = current_week_start - timedelta(days=7)
		previous_week_end = previous_week_start + timedelta(days=6)
		previous_week_entries = [
			entry
			for entry in entries
			if previous_week_start.isoformat() <= (entry.get("checkin_date") or "") <= previous_week_end.isoformat()
		]
		return _build_student_response(email_lower, user_uuid, last_7_day_entries, previous_week_entries, mode="fake")

	days = _last_7_days()
	start_day = _day_key(days[0])
	end_day = _day_key(days[-1])
	last_7_day_entries = db.get_diary_entries_for_email(email_lower, start_day, end_day)

	today = datetime.utcnow().date()
	current_week_start = today - timedelta(days=today.weekday())
	previous_week_start = current_week_start - timedelta(days=7)
	previous_week_end = previous_week_start + timedelta(days=6)
	previous_week_entries = db.get_diary_entries_for_email(
		email_lower,
		previous_week_start.isoformat(),
		previous_week_end.isoformat(),
	)
	return _build_student_response(email_lower, user_uuid, last_7_day_entries, previous_week_entries, mode="database")


@router.get("/counselor")
def get_counselor_pulse(x_session_token: str | None = Header(default=None)):
	email = resolve_session_email(x_session_token)
	if detect_role(email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	if _should_use_fake():
		total_students = len({(item.get("email") or "").lower() for item in FAKE_DIARY if item.get("email")})
		return _build_counselor_response(FAKE_POSTS, total_students, mode="fake")

	posts = db.get_posts()
	total_students = db.count_users_by_role("student")
	return _build_counselor_response(posts, total_students, mode="database")


@router.get("")
def get_legacy_pulse(email: EmailStr, user_uuid: str, x_session_token: str | None = Header(default=None)):
	return get_student_pulse(email=email, user_uuid=user_uuid, x_session_token=x_session_token)
