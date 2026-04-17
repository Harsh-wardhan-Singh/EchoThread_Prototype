from datetime import datetime, timedelta

now = datetime.utcnow()

FAKE_POSTS = [
	{
		"id": "p1",
		"content": "Exams are close and I feel anxious most nights.",
		"created_at": (now - timedelta(days=1)).isoformat(),
		"sentiment": "negative",
		"emotion": "anxiety",
		"risk": "MEDIUM",
	},
	{
		"id": "p2",
		"content": "I had a calm day after finishing my assignment.",
		"created_at": (now - timedelta(hours=8)).isoformat(),
		"sentiment": "positive",
		"emotion": "calm",
		"risk": "LOW",
	},
]

FAKE_DIARY = [
	{
		"id": "d1",
		"email": "student1@sample.hrc.ac.in",
		"text": "I am stressed about attendance and deadlines.",
		"created_at": (now - timedelta(days=2)).isoformat(),
		"sentiment": "negative",
		"emotion": "stress",
		"risk": "MEDIUM",
	},
	{
		"id": "d2",
		"email": "student2@sample.hrc.ac.in",
		"text": "Feeling better today after talking with friends.",
		"created_at": (now - timedelta(hours=18)).isoformat(),
		"sentiment": "positive",
		"emotion": "calm",
		"risk": "LOW",
	},
]
