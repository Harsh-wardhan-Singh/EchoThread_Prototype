from datetime import datetime, timedelta, timezone


IST = timezone(timedelta(hours=5, minutes=30))


def now_ist_iso():
	return datetime.now(IST).isoformat()
