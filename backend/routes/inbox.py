from fastapi import APIRouter, Header, HTTPException

from db import db
from routes.auth import resolve_session_email
from utils.otp import COUNSELOR_EMAIL, detect_role

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _normalize_risk_label(risk_value: str | None):
	value = (risk_value or "").strip().upper()
	if value in {"LOW", "MEDIUM", "HIGH"}:
		return value
	return None


def _build_student_risk_lookup(posts):
	severity = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
	lookup = {}
	for post in posts:
		email = (post.get("email") or "").lower().strip()
		if not email:
			continue
		risk_label = _normalize_risk_label(post.get("risk"))
		if not risk_label:
			continue
		current = lookup.get(email)
		if current is None or severity[risk_label] > severity[current]:
			lookup[email] = risk_label
	return lookup


def _count_unseen_student_messages(messages, seen_timestamp):
	if not seen_timestamp:
		return len([message for message in messages if message.get("sender_role") == "student"])
	return len(
		[
			message
			for message in messages
			if message.get("sender_role") == "student" and (message.get("timestamp") or "") > seen_timestamp
		]
	)


@router.get("/counselor")
def get_counselor_inbox(x_session_token: str | None = Header(default=None)):
	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	posts = db.get_posts()
	risk_lookup = _build_student_risk_lookup(posts)
	items = []
	counselor_latest_message_by_student = {}

	chats = db.get_counselor_chats(counselor_email)
	for chat in chats:
		chat_id = chat.get("id") or chat.get("_id")
		if not chat_id:
			continue
		student_email = (chat.get("student_id") or "").lower().strip()
		if not student_email:
			continue
		messages = db.get_messages_for_chat(chat_id)
		latest_counselor_timestamp = ""
		for message in messages:
			if (message.get("sender_role") or "") != "counselor":
				continue
			timestamp = message.get("timestamp") or ""
			if timestamp > latest_counselor_timestamp:
				latest_counselor_timestamp = timestamp
		if latest_counselor_timestamp:
			counselor_latest_message_by_student[student_email] = latest_counselor_timestamp

	for post in posts:
		risk = _normalize_risk_label(post.get("risk"))
		if risk != "HIGH":
			continue
		post_id = post.get("id") or post.get("_id")
		if not post_id:
			continue
		student_email = (post.get("email") or "").lower().strip()
		student_uuid = db.get_or_create_user_uuid(student_email, "student") if student_email else None
		post_timestamp = post.get("created_at") or ""
		latest_counselor_timestamp = counselor_latest_message_by_student.get(student_email, "")
		if latest_counselor_timestamp and post_timestamp and latest_counselor_timestamp >= post_timestamp:
			continue
		items.append(
			{
				"id": f"post_{post_id}",
				"type": "high_risk_post",
				"kind_label": "Post",
				"post_id": post_id,
				"student_uuid": student_uuid,
				"risk_label": risk_lookup.get(student_email, "HIGH"),
				"timestamp": post_timestamp,
				"content": post.get("content") or "",
				"risk": "HIGH",
			}
		)

	for chat in chats:
		chat_id = chat.get("id") or chat.get("_id")
		if not chat_id:
			continue
		student_email = (chat.get("student_id") or "").lower().strip()
		student_uuid = db.get_or_create_user_uuid(student_email, "student") if student_email else None
		risk_label = risk_lookup.get(student_email, "NO_INFORMATION")

		messages = db.get_messages_for_chat(chat_id)
		last_seen = chat.get("counselor_last_seen_student_message_at")
		unseen_count = _count_unseen_student_messages(messages, last_seen)
		if unseen_count <= 0:
			continue

		latest_unseen_timestamp = ""
		for message in messages:
			if (message.get("sender_role") or "") != "student":
				continue
			timestamp = message.get("timestamp") or ""
			if (not last_seen or timestamp > last_seen) and timestamp > latest_unseen_timestamp:
				latest_unseen_timestamp = timestamp

		items.append(
			{
				"id": f"msg_{chat_id}_{latest_unseen_timestamp or unseen_count}",
				"type": "student_message",
				"kind_label": "Message",
				"chat_id": chat_id,
				"student_uuid": student_uuid,
				"risk_label": risk_label,
				"unseen_count": unseen_count,
				"timestamp": latest_unseen_timestamp,
				"content": "",
			}
		)

	items.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
	return {"items": items}
