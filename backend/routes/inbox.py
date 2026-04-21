import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from fastapi import APIRouter, Header, HTTPException

from data.fake_data import FAKE_DASHBOARD_POSTS
from db import db
from routes.auth import resolve_session_email
from utils.otp import COUNSELOR_EMAIL, detect_role

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _normalize_risk_label(risk_value: str | None):
	value = str(risk_value or "").strip().upper()
	if value in {"LOW", "MEDIUM", "HIGH"}:
		return value
	return None


def _use_fake_feed():
	env_file = Path(__file__).resolve().parents[1] / ".env"
	value = dotenv_values(env_file).get("FEED_USE_FAKE_DATA")
	if value is None:
		value = os.getenv("FEED_USE_FAKE_DATA", "false")
	return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_timestamp(timestamp):
	if isinstance(timestamp, datetime):
		return timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=timezone.utc)
	value = str(timestamp or "").strip()
	if not value:
		return None
	try:
		parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
		return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
	except Exception:
		return None


def _is_after(left_timestamp: str | None, right_timestamp: str | None):
	left = _parse_timestamp(left_timestamp)
	right = _parse_timestamp(right_timestamp)
	if left and right:
		return left > right
	if left and not right:
		return True
	if not left:
		return False
	return str(left_timestamp or "") > str(right_timestamp or "")


def _sort_timestamp_key(timestamp: str | None):
	parsed = _parse_timestamp(timestamp)
	if parsed is not None:
		try:
			return parsed.timestamp()
		except Exception:
			return float("-inf")
	return float("-inf")


def _risk_priority(risk_label: str | None):
	value = _normalize_risk_label(risk_label)
	if value == "HIGH":
		return 0
	if value == "MEDIUM":
		return 1
	if value == "LOW":
		return 2
	if value == "NO_INFORMATION":
		return 3
	return 3


def _inbox_sort_key(item):
	risk_rank = _risk_priority(item.get("risk_label"))
	timestamp_rank = _sort_timestamp_key(item.get("timestamp"))
	if timestamp_rank == float("-inf"):
		return (risk_rank, float("inf"))
	return (risk_rank, -timestamp_rank)


def _build_student_risk_lookup(posts):
	severity = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
	lookup = {}
	for post in posts:
		student_uuid = (post.get("user_uuid") or "").strip()
		if not student_uuid:
			continue
		risk_label = _normalize_risk_label(post.get("risk"))
		if not risk_label:
			continue
		current = lookup.get(student_uuid)
		if current is None or severity[risk_label] > severity[current]:
			lookup[student_uuid] = risk_label
	return lookup


def _count_unseen_student_messages(messages, seen_timestamp):
	if not seen_timestamp:
		return len([message for message in messages if message.get("sender_role") == "student"])
	return len(
		[
			message
			for message in messages
			if message.get("sender_role") == "student" and _is_after(message.get("timestamp"), seen_timestamp)
		]
	)


@router.get("/counselor")
def get_counselor_inbox(x_session_token: str | None = Header(default=None)):
	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	posts = [*FAKE_DASHBOARD_POSTS] if _use_fake_feed() else db.get_posts()
	risk_lookup = _build_student_risk_lookup(posts)
	items = []
	counselor_latest_message_by_student = {}
	chat_states = []

	chats = db.get_counselor_chats(counselor_email)
	for chat in chats:
		chat_id = chat.get("id") or chat.get("_id")
		if not chat_id:
			continue
		student_uuid = (chat.get("student_uuid") or "").strip()
		if not student_uuid:
			continue
		messages = db.get_messages_for_chat(chat_id)
		chat_states.append(
			{
				"chat_id": chat_id,
				"student_uuid": student_uuid,
				"last_seen": chat.get("counselor_last_seen_student_message_at"),
				"messages": messages,
			}
		)
		latest_counselor_timestamp = ""
		for message in messages:
			if (message.get("sender_role") or "") != "counselor":
				continue
			timestamp = message.get("timestamp") or ""
			if _is_after(timestamp, latest_counselor_timestamp):
				latest_counselor_timestamp = timestamp
		if latest_counselor_timestamp:
			counselor_latest_message_by_student[student_uuid] = latest_counselor_timestamp

	for post in posts:
		risk = _normalize_risk_label(post.get("risk"))
		if risk != "HIGH":
			continue
		post_id = post.get("id") or post.get("_id")
		if not post_id:
			continue
		student_uuid = (post.get("user_uuid") or "").strip() or None
		post_timestamp = post.get("created_at") or ""
		latest_counselor_timestamp = counselor_latest_message_by_student.get(student_uuid, "")
		if latest_counselor_timestamp and post_timestamp and not _is_after(post_timestamp, latest_counselor_timestamp):
			continue
		items.append(
			{
				"id": f"post_{str(post_id)}",
				"type": "high_risk_post",
				"kind_label": "Post",
				"post_id": str(post_id),
				"student_uuid": student_uuid,
				"risk_label": risk_lookup.get(student_uuid, "HIGH"),
				"timestamp": post_timestamp,
				"content": str(post.get("content") or ""),
				"risk": "HIGH",
			}
		)

	for chat_state in chat_states:
		chat_id = chat_state["chat_id"]
		student_uuid = chat_state["student_uuid"]
		risk_label = risk_lookup.get(student_uuid, "NO_INFORMATION")

		messages = chat_state["messages"]
		last_seen = chat_state["last_seen"]
		unseen_count = _count_unseen_student_messages(messages, last_seen)
		if unseen_count <= 0:
			continue

		latest_unseen_timestamp = ""
		for message in messages:
			if (message.get("sender_role") or "") != "student":
				continue
			timestamp = message.get("timestamp") or ""
			if (not last_seen or _is_after(timestamp, last_seen)) and _is_after(timestamp, latest_unseen_timestamp):
				latest_unseen_timestamp = timestamp

		items.append(
			{
				"id": f"msg_{chat_id}_{latest_unseen_timestamp or unseen_count}",
				"type": "student_message",
				"kind_label": "Message",
				"chat_id": str(chat_id),
				"student_uuid": student_uuid,
				"risk_label": risk_label,
				"unseen_count": unseen_count,
				"timestamp": latest_unseen_timestamp,
				"content": "",
			}
		)

	items.sort(key=_inbox_sort_key)
	return {"items": items}
