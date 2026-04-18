from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Header
from pydantic import BaseModel

from db import db
from routes.auth import resolve_session_email
from services.assess_risk import assess_risk
from services.sentiment import analyze_text

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreateRequest(BaseModel):
	content: str


@router.post("")
def create_post(payload: PostCreateRequest, x_session_token: str | None = Header(default=None)):
	email = resolve_session_email(x_session_token)
	user_uuid = db.get_or_create_user_uuid(email, "student")
	analysis = analyze_text(payload.content)
	risk_data = assess_risk(payload.content, analysis["sentiment"], analysis["emotion"])
	post = {
		"id": f"p_{uuid4().hex[:10]}",
		"email": email,
		"user_uuid": user_uuid,
		"content": payload.content,
		"created_at": datetime.utcnow().isoformat(),
		"sentiment": analysis["sentiment"],
		"emotion": analysis["emotion"],
		"risk": risk_data["risk"],
		"risk_score": risk_data["risk_score"],
		"risk_scores": risk_data["scores"],
	}
	db.add_post(post)
	return {
		"id": post["id"],
		"user_uuid": post["user_uuid"],
		"content": post["content"],
		"created_at": post["created_at"],
		"risk": post["risk"],
		"risk_score": post["risk_score"],
	}


@router.get("")
def get_posts():
	posts = db.get_posts()
	posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

	def resolve_user_uuid(post):
		uuid_value = post.get("user_uuid")
		if uuid_value:
			return uuid_value
		email = (post.get("email") or "").lower()
		if email:
			return db.get_or_create_user_uuid(email, "student")
		return None

	return [
		{
			"id": p.get("id") or p.get("_id"),
			"user_uuid": resolve_user_uuid(p),
			"content": p.get("content", ""),
			"created_at": p.get("created_at"),
		}
		for p in posts
	]


@router.get("/flagged")
def get_flagged_posts():
	posts = db.get_posts()
	flagged = [
		p
		for p in posts
		if p.get("risk") in {"MEDIUM", "HIGH"}
	]
	flagged.sort(key=lambda x: x.get("created_at", ""), reverse=True)
	return [
		{
			"id": p.get("id") or p.get("_id"),
			"content": p.get("content", ""),
			"created_at": p.get("created_at"),
			"risk": p.get("risk", "LOW"),
			"risk_score": p.get("risk_score", 0.0),
			"sentiment": p.get("sentiment", "neutral"),
			"emotion": p.get("emotion", "calm"),
		}
		for p in flagged
	]
