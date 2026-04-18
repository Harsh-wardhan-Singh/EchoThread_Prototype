from datetime import datetime, timedelta

now = datetime.utcnow()
today = now.date()
current_week_start = today - timedelta(days=today.weekday())
previous_week_start = current_week_start - timedelta(days=7)

STUDENT_ONE_EMAIL = "student1@sample.hrc.du.ac.in"
STUDENT_TWO_EMAIL = "student2@sample.hrc.du.ac.in"

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
		"email": STUDENT_ONE_EMAIL,
		"text": "I am stressed about attendance and deadlines.",
		"created_at": (now - timedelta(days=2)).isoformat(),
		"checkin_date": (now - timedelta(days=2)).date().isoformat(),
		"sentiment": "negative",
		"emotion": "stress",
		"risk": "MEDIUM",
		"risk_score": 0.46,
	},
	{
		"id": "d2",
		"email": STUDENT_TWO_EMAIL,
		"text": "Feeling better today after talking with friends.",
		"created_at": (now - timedelta(hours=18)).isoformat(),
		"checkin_date": (now - timedelta(hours=18)).date().isoformat(),
		"sentiment": "positive",
		"emotion": "calm",
		"risk": "LOW",
		"risk_score": 0.16,
	},
	{
		"id": "d_prev_1",
		"email": STUDENT_ONE_EMAIL,
		"text": "I had an okay Monday and felt calmer by night.",
		"created_at": datetime.combine(previous_week_start + timedelta(days=0), datetime.min.time()).replace(hour=19, minute=25).isoformat(),
		"checkin_date": (previous_week_start + timedelta(days=0)).isoformat(),
		"sentiment": "positive",
		"emotion": "calm",
		"risk": "LOW",
		"risk_score": 0.18,
	},
	{
		"id": "d_prev_2",
		"email": STUDENT_ONE_EMAIL,
		"text": "Tuesday felt heavy with assignments but manageable.",
		"created_at": datetime.combine(previous_week_start + timedelta(days=1), datetime.min.time()).replace(hour=20, minute=10).isoformat(),
		"checkin_date": (previous_week_start + timedelta(days=1)).isoformat(),
		"sentiment": "neutral",
		"emotion": "stress",
		"risk": "LOW",
		"risk_score": 0.28,
	},
	{
		"id": "d_prev_4",
		"email": STUDENT_ONE_EMAIL,
		"text": "Thursday I felt anxious before class, then better later.",
		"created_at": datetime.combine(previous_week_start + timedelta(days=3), datetime.min.time()).replace(hour=18, minute=55).isoformat(),
		"checkin_date": (previous_week_start + timedelta(days=3)).isoformat(),
		"sentiment": "negative",
		"emotion": "anxiety",
		"risk": "MEDIUM",
		"risk_score": 0.49,
	},
	{
		"id": "d_prev_5",
		"email": STUDENT_ONE_EMAIL,
		"text": "Friday felt balanced and I got through most tasks.",
		"created_at": datetime.combine(previous_week_start + timedelta(days=4), datetime.min.time()).replace(hour=19, minute=40).isoformat(),
		"checkin_date": (previous_week_start + timedelta(days=4)).isoformat(),
		"sentiment": "neutral",
		"emotion": "calm",
		"risk": "LOW",
		"risk_score": 0.24,
	},
	{
		"id": "d_prev_7",
		"email": STUDENT_ONE_EMAIL,
		"text": "Sunday was reflective; I felt sad at first, then settled.",
		"created_at": datetime.combine(previous_week_start + timedelta(days=6), datetime.min.time()).replace(hour=21, minute=5).isoformat(),
		"checkin_date": (previous_week_start + timedelta(days=6)).isoformat(),
		"sentiment": "negative",
		"emotion": "sadness",
		"risk": "LOW",
		"risk_score": 0.33,
	},
]
