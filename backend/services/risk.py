import re

HIGH_RISK_PATTERNS = [
	r"\bsuicid(e|al)\b",
	r"\bkill(ing)? myself\b",
	r"\bend(ing)? my life\b",
	r"\bself[- ]?harm\b",
	r"\bi want to die\b",
	r"\bdon't want to live\b",
	r"\bno reason to live\b",
	r"\bcan'?t go on\b",
	r"\bjump(ing)? off\b",
	r"\bfrom a building\b",
	r"\bend it all\b",
	r"\bi should die\b",
	r"\bi want to disappear forever\b",
	r"\bno point living\b",
	r"\btak(e|ing) (my|other(s)?) life\b"
]

HIGH_RISK_KEYWORDS = {
	"hopeless",
	"worthless",
	"life is pointless",
}

MEDIUM_RISK_KEYWORDS = {
	"panic",
	"anxious",
	"anxiety",
	"stressed",
	"overwhelmed",
	"can\'t sleep",
}

LOW_SIGNAL_KEYWORDS = {
	"frustrated",
	"tired",
	"lonely",
	"empty",
	"numb",
}


def score_keywords(text: str) -> float:
	content = (text or "").lower()

	high_pattern_hits = sum(1 for pattern in HIGH_RISK_PATTERNS if re.search(pattern, content))
	high_keyword_hits = sum(1 for keyword in HIGH_RISK_KEYWORDS if keyword in content)
	medium_hits = sum(1 for keyword in MEDIUM_RISK_KEYWORDS if keyword in content)
	low_hits = sum(1 for keyword in LOW_SIGNAL_KEYWORDS if keyword in content)

	if high_pattern_hits > 0:
		return 1.0

	raw_score = high_keyword_hits * 0.65 + medium_hits * 0.35 + low_hits * 0.14
	return max(0.0, min(1.0, raw_score))


def assess_risk(text: str, sentiment: str = "neutral", emotion: str = "calm"):
	content = (text or "").lower()
	if any(re.search(pattern, content) for pattern in HIGH_RISK_PATTERNS):
		return "HIGH"
	if any(keyword in content for keyword in HIGH_RISK_KEYWORDS):
		return "HIGH"
	if any(keyword in content for keyword in MEDIUM_RISK_KEYWORDS):
		return "MEDIUM"
	if sentiment == "negative" and emotion in {"sadness", "anger"} and any(
		word in content for word in {"alone", "empty", "numb", "exhausted"}
	):
		return "MEDIUM"
	if sentiment == "negative" and emotion in {"stress", "anxiety", "sadness"}:
		return "MEDIUM"
	return "LOW"
