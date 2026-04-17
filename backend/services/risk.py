HIGH_RISK_KEYWORDS = {
	"suicide",
	"kill myself",
	"self harm",
	"end my life",
	"hopeless",
}

MEDIUM_RISK_KEYWORDS = {
	"panic",
	"anxious",
	"anxiety",
	"stressed",
	"overwhelmed",
	"can\'t sleep",
}


def assess_risk(text: str, sentiment: str = "neutral", emotion: str = "calm"):
	content = (text or "").lower()
	if any(keyword in content for keyword in HIGH_RISK_KEYWORDS):
		return "HIGH"
	if any(keyword in content for keyword in MEDIUM_RISK_KEYWORDS):
		return "MEDIUM"
	if sentiment == "negative" and emotion in {"stress", "anxiety", "sadness"}:
		return "MEDIUM"
	return "LOW"
