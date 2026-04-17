import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

try:
	from huggingface_hub import InferenceClient
except Exception:
	InferenceClient = None


EMOTION_KEYWORDS = {
	"stress": ["stress", "deadline", "pressure", "overwhelmed"],
	"anxiety": ["anxious", "panic", "worried", "fear"],
	"calm": ["calm", "peaceful", "relaxed", "better"],
	"sadness": ["sad", "lonely", "down", "empty"],
	"anger": ["angry", "frustrated", "irritated", "rage"],
}

POSITIVE_WORDS = {"good", "better", "great", "happy", "calm", "hopeful"}
NEGATIVE_WORDS = {"bad", "stressed", "anxious", "sad", "panic", "hopeless"}


def _fallback_analysis(text: str):
	content = (text or "").lower()
	pos_hits = sum(1 for word in POSITIVE_WORDS if word in content)
	neg_hits = sum(1 for word in NEGATIVE_WORDS if word in content)

	if neg_hits > pos_hits:
		sentiment = "negative"
	elif pos_hits > neg_hits:
		sentiment = "positive"
	else:
		sentiment = "neutral"

	emotion = "calm"
	for candidate, words in EMOTION_KEYWORDS.items():
		if any(word in content for word in words):
			emotion = candidate
			break

	return {
		"sentiment": sentiment,
		"emotion": emotion,
		"confidence": 0.65,
		"provider": "fallback",
	}


def _extract_json(raw_text: str):
	if not raw_text:
		return None
	try:
		return json.loads(raw_text)
	except Exception:
		match = re.search(r"\{.*\}", raw_text, re.DOTALL)
		if not match:
			return None
		try:
			return json.loads(match.group(0))
		except Exception:
			return None


def _normalize_result(payload):
	if not payload:
		return None

	sentiment = str(payload.get("sentiment", "neutral")).lower()
	if sentiment not in {"positive", "neutral", "negative"}:
		sentiment = "neutral"

	emotion = str(payload.get("emotion", "calm")).lower()
	try:
		confidence = float(payload.get("confidence", 0.75))
	except Exception:
		confidence = 0.75

	return {
		"sentiment": sentiment,
		"emotion": emotion,
		"confidence": max(0.0, min(1.0, confidence)),
		"provider": "llama",
	}


def _analyze_with_chat_completion(client, model: str, text: str):
	response = client.chat_completion(
		model=model,
		messages=[
			{
				"role": "system",
				"content": (
					"Classify the student's text and return strict JSON only with keys: "
					"sentiment, emotion, confidence. sentiment must be one of "
					"positive, neutral, negative."
				),
			},
			{"role": "user", "content": text},
		],
		max_tokens=120,
		temperature=0.2,
	)

	content = ""
	if response and getattr(response, "choices", None):
		choice = response.choices[0]
		if getattr(choice, "message", None):
			content = (choice.message.content or "").strip()

	payload = _extract_json(content)
	return _normalize_result(payload)


def _analyze_with_text_generation(client, model: str, text: str):
	prompt = (
		"You are a sentiment classifier for mental wellness journaling. "
		"Return strict JSON with keys: sentiment, emotion, confidence. "
		"sentiment must be one of positive/neutral/negative. "
		"emotion should be a short label like stress/anxiety/calm/sadness/anger. "
		f"Text: {text}"
	)
	response = client.text_generation(
		model=model,
		prompt=prompt,
		max_new_tokens=120,
		temperature=0.2,
	)
	payload = _extract_json(response)
	return _normalize_result(payload)


def _map_emotion_label(label: str):
	value = (label or "").strip().lower()
	if value in {"nervousness", "fear", "anxiety"}:
		return "anxiety"
	if value in {"sadness", "grief", "disappointment"}:
		return "sadness"
	if value in {"anger", "annoyance", "frustration"}:
		return "anger"
	if value in {"neutral", "calm", "contentment"}:
		return "calm"
	if value in {"stress", "overwhelmed", "tension"}:
		return "stress"
	return value or "calm"


def _analyze_with_hf_classifiers(client, text: str):
	sentiment_scores = client.text_classification(
		text,
		model="cardiffnlp/twitter-roberta-base-sentiment-latest",
	)
	emotion_scores = client.text_classification(
		text,
		model="SamLowe/roberta-base-go_emotions",
	)

	if not sentiment_scores or not emotion_scores:
		return None

	best_sentiment = sentiment_scores[0]
	best_emotion = emotion_scores[0]

	return {
		"sentiment": str(best_sentiment.label).lower(),
		"emotion": _map_emotion_label(str(best_emotion.label)),
		"confidence": max(0.0, min(1.0, float(best_sentiment.score))),
		"provider": "hf-classifier",
	}


def analyze_text(text: str):
	token = os.getenv("HF_TOKEN", "") or os.getenv("HF_API_KEY", "")
	model = os.getenv("HF_MODEL", "").strip()
	if InferenceClient is None or not token:
		return _fallback_analysis(text)

	try:
		client = InferenceClient(token=token)
	except Exception:
		return _fallback_analysis(text)

	if model:
		try:
			result = _analyze_with_chat_completion(client, model, text)
			if result:
				return result
		except Exception:
			pass

		try:
			result = _analyze_with_text_generation(client, model, text)
			if result:
				return result
		except Exception:
			pass

	try:
		result = _analyze_with_hf_classifiers(client, text)
		if result:
			return result
	except Exception:
		pass

	return _fallback_analysis(text)
