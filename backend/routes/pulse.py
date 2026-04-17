from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter

from db import db

router = APIRouter(prefix="/pulse", tags=["pulse"])


def _to_datetime(value: str):
	try:
		return datetime.fromisoformat(value)
	except Exception:
		return None


@router.get("")
def get_pulse():
	posts = db.get_posts()
	diaries = db.get_diary_entries()
	combined = [*posts, *diaries]

	sentiment_counter = Counter(item.get("sentiment", "neutral") for item in combined)
	risk_counter = Counter(item.get("risk", "LOW") for item in combined)
	emotion_counter = Counter(item.get("emotion", "calm") for item in combined)

	today = datetime.utcnow().date()
	trend = []
	for days_back in range(6, -1, -1):
		current_day = today - timedelta(days=days_back)
		count = 0
		for item in combined:
			parsed = _to_datetime(item.get("created_at", ""))
			if parsed and parsed.date() == current_day:
				count += 1
		trend.append({"date": current_day.isoformat(), "count": count})

	return {
		"total_posts": len(posts),
		"total_diary_entries": len(diaries),
		"sentiment_distribution": {
			"positive": sentiment_counter.get("positive", 0),
			"neutral": sentiment_counter.get("neutral", 0),
			"negative": sentiment_counter.get("negative", 0),
		},
		"risk_distribution": {
			"LOW": risk_counter.get("LOW", 0),
			"MEDIUM": risk_counter.get("MEDIUM", 0),
			"HIGH": risk_counter.get("HIGH", 0),
		},
		"top_emotions": [
			{"emotion": emotion, "count": count}
			for emotion, count in emotion_counter.most_common(5)
		],
		"seven_day_activity": trend,
	}
