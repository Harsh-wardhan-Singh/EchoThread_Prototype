from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from db import db
from services.risk import assess_risk
from services.sentiment import analyze_text

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreateRequest(BaseModel):
	content: str


@router.post("")
def create_post(payload: PostCreateRequest):
	analysis = analyze_text(payload.content)
	risk = assess_risk(payload.content, analysis["sentiment"], analysis["emotion"])
	post = {
		"id": f"p_{uuid4().hex[:10]}",
		"content": payload.content,
		"created_at": datetime.utcnow().isoformat(),
		"sentiment": analysis["sentiment"],
		"emotion": analysis["emotion"],
		"risk": risk,
	}
	db.add_post(post)
	return {
		"id": post["id"],
		"content": post["content"],
		"created_at": post["created_at"],
	}


@router.get("")
def get_posts():
	posts = db.get_posts()
	posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
	return [
		{
			"id": p.get("id") or p.get("_id"),
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
			"sentiment": p.get("sentiment", "neutral"),
			"emotion": p.get("emotion", "calm"),
		}
		for p in flagged
	]
