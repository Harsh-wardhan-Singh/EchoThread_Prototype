import os
from pathlib import Path
from uuid import uuid4

from dotenv import dotenv_values
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from data.fake_data import FAKE_DASHBOARD_POSTS
from db import db
from routes.auth import resolve_session_email
from services.assess_risk import assess_risk
from services.sentiment import analyze_text
from utils.otp import COUNSELOR_EMAIL, detect_role
from utils.time import now_ist_iso

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreateRequest(BaseModel):
	content: str


class CommentCreateRequest(BaseModel):
	content: str


def _use_fake_feed():
	env_file = Path(__file__).resolve().parents[1] / ".env"
	value = dotenv_values(env_file).get("FEED_USE_FAKE_DATA")
	if value is None:
		value = os.getenv("FEED_USE_FAKE_DATA", "false")
	return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_comment_node(comment, fallback_id=None, counselor_uuid=None):
	if isinstance(comment, str):
		return {
			"id": fallback_id or f"legacy_{uuid4().hex[:10]}",
			"author_role": "student",
			"user_uuid": None,
			"content": comment,
			"created_at": None,
			"replies": [],
		}

	if not isinstance(comment, dict):
		return {
			"id": fallback_id or f"legacy_{uuid4().hex[:10]}",
			"author_role": "student",
			"user_uuid": None,
			"content": "",
			"created_at": None,
			"replies": [],
		}

	replies = comment.get("replies") if isinstance(comment.get("replies"), list) else []
	user_uuid = comment.get("user_uuid")
	author_role = (comment.get("author_role") or "").strip().lower()
	if author_role not in {"student", "counselor"}:
		resolved_email = db.get_email_by_user_uuid(user_uuid) if user_uuid else None
		resolved_role = detect_role(resolved_email) if resolved_email else None
		if resolved_role in {"student", "counselor"}:
			author_role = resolved_role
		else:
			author_role = "counselor" if counselor_uuid and user_uuid and user_uuid == counselor_uuid else "student"
	return {
		"id": comment.get("id") or fallback_id or f"c_{uuid4().hex[:10]}",
		"author_role": author_role,
		"user_uuid": user_uuid,
		"content": comment.get("content", ""),
		"created_at": comment.get("created_at"),
		"replies": [_normalize_comment_node(reply, counselor_uuid=counselor_uuid) for reply in replies],
	}


def _normalize_comments(comments, counselor_uuid=None):
	if not isinstance(comments, list):
		return []
	return [
		_normalize_comment_node(comment, fallback_id=f"legacy_{index}", counselor_uuid=counselor_uuid)
		for index, comment in enumerate(comments)
	]


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
	author_role = detect_role(email) or "student"
	user_uuid = db.get_or_create_user_uuid(email, author_role)
	analysis = analyze_text(payload.content)
	risk_data = assess_risk(payload.content, analysis["sentiment"], analysis["emotion"])
	post = {
		"id": f"p_{uuid4().hex[:10]}",
		"author_role": author_role,
		"user_uuid": user_uuid,
		"content": payload.content,
		"created_at": now_ist_iso(),
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
		"author_role": post["author_role"],
		"user_uuid": post["user_uuid"],
		"content": post["content"],
		"created_at": post["created_at"],
		"risk": post["risk"],
		"risk_score": post["risk_score"],
	}


@router.get("")
def get_posts():
	posts = [*FAKE_DASHBOARD_POSTS] if _use_fake_feed() else db.get_posts()
	posts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
	counselor_uuid = db.get_or_create_user_uuid(COUNSELOR_EMAIL, "counselor")

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
			"author_role": p.get("author_role") or detect_role((p.get("email") or "").lower()) or "student",
			"user_uuid": resolve_user_uuid(p),
			"content": p.get("content", ""),
			"created_at": p.get("created_at"),
			"comments": _normalize_comments(p.get("comments", []), counselor_uuid=counselor_uuid),
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
	author_role = detect_role(email) or "student"
	user_uuid = db.get_or_create_user_uuid(email, author_role)
	post = db.get_post_by_id(post_id)
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")

	counselor_uuid = db.get_or_create_user_uuid(COUNSELOR_EMAIL, "counselor")
	comments = _normalize_comments(post.get("comments", []), counselor_uuid=counselor_uuid)
	comment = {
		"id": f"c_{uuid4().hex[:10]}",
		"author_role": author_role,
		"user_uuid": user_uuid,
		"content": payload.content.strip(),
		"created_at": now_ist_iso(),
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
	author_role = detect_role(email) or "student"
	user_uuid = db.get_or_create_user_uuid(email, author_role)
	post = db.get_post_by_id(post_id)
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")

	counselor_uuid = db.get_or_create_user_uuid(COUNSELOR_EMAIL, "counselor")
	comments = _normalize_comments(post.get("comments", []), counselor_uuid=counselor_uuid)
	reply = {
		"id": f"r_{uuid4().hex[:10]}",
		"author_role": author_role,
		"user_uuid": user_uuid,
		"content": payload.content.strip(),
		"created_at": now_ist_iso(),
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
	posts = [*FAKE_DASHBOARD_POSTS] if _use_fake_feed() else db.get_posts()
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
