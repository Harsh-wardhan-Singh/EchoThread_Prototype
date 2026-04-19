import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from data.fake_data import FAKE_POSTS
from db import db
from routes.auth import resolve_session_email
from services.assess_risk import assess_risk
from services.sentiment import analyze_text

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreateRequest(BaseModel):
	content: str


class CommentCreateRequest(BaseModel):
	content: str


def _use_fake_feed():
	value = os.getenv("FEED_USE_FAKE_DATA", "false")
	return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_comment_node(comment, fallback_id=None):
	if isinstance(comment, str):
		return {
			"id": fallback_id or f"legacy_{uuid4().hex[:10]}",
			"user_uuid": None,
			"content": comment,
			"created_at": None,
			"replies": [],
		}

	if not isinstance(comment, dict):
		return {
			"id": fallback_id or f"legacy_{uuid4().hex[:10]}",
			"user_uuid": None,
			"content": "",
			"created_at": None,
			"replies": [],
		}

	replies = comment.get("replies") if isinstance(comment.get("replies"), list) else []
	return {
		"id": comment.get("id") or fallback_id or f"c_{uuid4().hex[:10]}",
		"user_uuid": comment.get("user_uuid"),
		"content": comment.get("content", ""),
		"created_at": comment.get("created_at"),
		"replies": [_normalize_comment_node(reply) for reply in replies],
	}


def _normalize_comments(comments):
	if not isinstance(comments, list):
		return []
	return [_normalize_comment_node(comment, fallback_id=f"legacy_{index}") for index, comment in enumerate(comments)]


def _append_reply(nodes, parent_id, reply):
	for node in nodes:
		if node.get("id") == parent_id:
			node.setdefault("replies", []).append(reply)
			return True
		if _append_reply(node.get("replies", []), parent_id, reply):
			return True
	return False


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
		"comments": [],
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
	posts = [*FAKE_POSTS] if _use_fake_feed() else db.get_posts()
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
			"comments": _normalize_comments(p.get("comments", [])),
		}
		for p in posts
	]


@router.post("/{post_id}/comments")
def add_comment(post_id: str, payload: CommentCreateRequest, x_session_token: str | None = Header(default=None)):
	if _use_fake_feed():
		raise HTTPException(status_code=409, detail="Feed comments are disabled while fake feed mode is enabled")

	if not payload.content.strip():
		raise HTTPException(status_code=400, detail="Comment cannot be empty")

	email = resolve_session_email(x_session_token)
	user_uuid = db.get_or_create_user_uuid(email, "student")
	post = db.get_post_by_id(post_id)
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")

	comments = _normalize_comments(post.get("comments", []))
	comment = {
		"id": f"c_{uuid4().hex[:10]}",
		"user_uuid": user_uuid,
		"content": payload.content.strip(),
		"created_at": datetime.utcnow().isoformat(),
		"replies": [],
	}
	comments.append(comment)
	db.save_post_comments(post_id, comments)
	return {
		"success": True,
		"comment": comment,
	}


@router.post("/{post_id}/comments/{comment_id}/replies")
def add_reply(post_id: str, comment_id: str, payload: CommentCreateRequest, x_session_token: str | None = Header(default=None)):
	if _use_fake_feed():
		raise HTTPException(status_code=409, detail="Feed replies are disabled while fake feed mode is enabled")

	if not payload.content.strip():
		raise HTTPException(status_code=400, detail="Reply cannot be empty")

	email = resolve_session_email(x_session_token)
	user_uuid = db.get_or_create_user_uuid(email, "student")
	post = db.get_post_by_id(post_id)
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")

	comments = _normalize_comments(post.get("comments", []))
	reply = {
		"id": f"r_{uuid4().hex[:10]}",
		"user_uuid": user_uuid,
		"content": payload.content.strip(),
		"created_at": datetime.utcnow().isoformat(),
		"replies": [],
	}

	if not _append_reply(comments, comment_id, reply):
		raise HTTPException(status_code=404, detail="Parent comment not found")

	db.save_post_comments(post_id, comments)
	return {
		"success": True,
		"reply": reply,
	}


@router.get("/flagged")
def get_flagged_posts():
	posts = [*FAKE_POSTS] if _use_fake_feed() else db.get_posts()
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
