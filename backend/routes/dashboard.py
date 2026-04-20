import os
from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Header, HTTPException

from data.fake_data import FAKE_DASHBOARD_POSTS
from db import db
from routes.auth import resolve_session_email
from utils.otp import detect_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


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


def _normalize_sentiment(sentiment):
	value = (sentiment or "neutral").lower()
	if value in {"positive", "negative", "neutral"}:
		return value
	return "neutral"


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


def _should_use_fake():
	return (os.getenv("DASHBOARD_USE_FAKE_DATA", "true") or "true").strip().lower() in {"1", "true", "yes", "on"}


def _build_dashboard_response(posts, total_students, mode):
	days = _last_7_days()
	day_lookup = {
		_day_key(day): {
			"day": day.strftime("%a"),
			"stress": [],
			"posts": 0,
			"negative_or_high_stress": 0,
			"sentiment_score_sum": 0,
			"sentiment_count": 0,
		}
		for day in days
	}

	risk_counter = Counter()
	emotion_counter = Counter()
	high_stress_emotions = {
		"stress",
		"anxiety",
		"sadness",
		"anger",
		"fear",
		"panic",
		"overwhelmed",
		"burnout",
		"lonely",
	}
	sentiment_score_map = {"positive": 1, "neutral": 0, "negative": -1}

	posts_in_window = []
	negative_or_high_stress_count = 0
	total_sentiment_score = 0
	total_sentiment_count = 0

	for post in posts:
		timestamp = _to_datetime(post.get("created_at"))
		if not timestamp:
			continue
		day_key = timestamp.date().isoformat()
		if day_key not in day_lookup:
			continue

		posts_in_window.append(post)
		bucket = day_lookup[day_key]
		bucket["posts"] += 1
		bucket["stress"].append(_risk_to_stress(post.get("risk"), post.get("risk_score")))

		sentiment = _normalize_sentiment(post.get("sentiment"))
		score = sentiment_score_map[sentiment]
		bucket["sentiment_score_sum"] += score
		bucket["sentiment_count"] += 1
		total_sentiment_score += score
		total_sentiment_count += 1

		risk_counter[(post.get("risk") or "LOW").upper()] += 1
		emotion = (post.get("emotion") or "calm").lower()
		emotion_counter[emotion] += 1

		if sentiment == "negative" or emotion in high_stress_emotions:
			negative_or_high_stress_count += 1
			bucket["negative_or_high_stress"] += 1

	overall_stress_series = []
	posts_series = []
	daily_stress_index_series = []
	for day in days:
		bucket = day_lookup[_day_key(day)]
		stress_score = round(sum(bucket["stress"]) / len(bucket["stress"])) if bucket["stress"] else 0
		overall_stress_series.append({"day": bucket["day"], "score": stress_score})
		posts_series.append({"day": bucket["day"], "count": bucket["posts"]})
		daily_stress_index = round((bucket["negative_or_high_stress"] / bucket["posts"]) * 100, 1) if bucket["posts"] else 0
		daily_stress_index_series.append({"day": bucket["day"], "score": daily_stress_index, "posts": bucket["posts"]})

	total_posts = len(posts_in_window)
	stress_index = round((negative_or_high_stress_count / total_posts) * 100, 1) if total_posts else 0
	avg_sentiment_score = round(total_sentiment_score / total_sentiment_count, 2) if total_sentiment_count else 0
	avg_stress = round(sum(item["score"] for item in overall_stress_series) / len(overall_stress_series), 1) if overall_stress_series else 0
	peak_daily_stress_index = max(daily_stress_index_series, key=lambda item: item["score"], default=None)

	emotion_distribution = [{"emotion": emotion, "count": count} for emotion, count in emotion_counter.most_common(8)]

	analytics_summary = [
		f"{total_posts} feed posts were observed in the last 7 days.",
		f"Stress index is {stress_index}% (posts that are negative or show high-stress emotions).",
		f"Average sentiment score is {avg_sentiment_score} on a -1 to +1 scale.",
		f"Average stress score is {avg_stress} out of 100 from post-level risk signals.",
	]
	if peak_daily_stress_index and peak_daily_stress_index["posts"] > 0 and peak_daily_stress_index["score"] >= 80:
		analytics_summary.append(
			f"A stress-index spike was detected on {peak_daily_stress_index['day']} at {peak_daily_stress_index['score']}% of posts."
		)

	return {
		"mode": mode,
		"total_students": total_students,
		"total_posts": total_posts,
		"stress_index": stress_index,
		"avg_sentiment_score": avg_sentiment_score,
		"overall_stress_series": overall_stress_series,
		"posts_series": posts_series,
		"risk_counts": {
			"LOW": risk_counter.get("LOW", 0),
			"MEDIUM": risk_counter.get("MEDIUM", 0),
			"HIGH": risk_counter.get("HIGH", 0),
		},
		"emotion_distribution": emotion_distribution,
		"analytics_summary": analytics_summary,
	}


@router.get("/counselor")
def get_counselor_dashboard(x_session_token: str | None = Header(default=None)):
	email = resolve_session_email(x_session_token)
	if detect_role(email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	if _should_use_fake():
		total_students = len({(item.get("email") or "").lower() for item in FAKE_DASHBOARD_POSTS if item.get("email")})
		return _build_dashboard_response(FAKE_DASHBOARD_POSTS, total_students, mode="fake")

	posts = db.get_posts()
	total_students = db.count_users_by_role("student")
	return _build_dashboard_response(posts, total_students, mode="database")
