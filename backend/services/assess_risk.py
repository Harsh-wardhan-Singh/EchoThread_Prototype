from services.risk import score_keywords

WEIGHTS = {
	"sentiment": 0.3,
	"emotion": 0.25,
	"keywords": 0.45,
}

SENTIMENT_SCORES = {
	"positive": 0.05,
	"neutral": 0.35,
	"negative": 0.85,
}

EMOTION_SCORES = {
	"calm": 0.1,
	"stress": 0.55,
	"anxiety": 0.68,
	"sadness": 0.78,
	"anger": 0.62,
}

def score_sentiment(sentiment: str) -> float:
	key = (sentiment or "neutral").strip().lower()
	return SENTIMENT_SCORES.get(key, SENTIMENT_SCORES["neutral"])


def score_emotion(emotion: str) -> float:
	key = (emotion or "calm").strip().lower()
	return EMOTION_SCORES.get(key, 0.4)


def classify_risk(risk_score: float) -> str:
	if risk_score >= 0.7:
		return "HIGH"
	if risk_score >= 0.4:
		return "MEDIUM"
	return "LOW"


def assess_risk(text: str, sentiment: str = "neutral", emotion: str = "calm") -> dict:
	s_score = score_sentiment(sentiment)
	e_score = score_emotion(emotion)
	k_score = score_keywords(text)

	risk_score = (
		WEIGHTS["sentiment"] * s_score
		+ WEIGHTS["emotion"] * e_score
		+ WEIGHTS["keywords"] * k_score
	)
	risk_score = round(max(0.0, min(1.0, risk_score)), 4)
	risk = classify_risk(risk_score)

	return {
		"risk": risk,
		"risk_score": risk_score,
		"scores": {
			"sentiment": round(s_score, 4),
			"emotion": round(e_score, 4),
			"keywords": round(k_score, 4),
		},
		"weights": WEIGHTS,
	}
