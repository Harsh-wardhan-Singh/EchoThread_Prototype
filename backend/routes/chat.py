from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from db import db
from routes.auth import resolve_session_email
from utils.otp import COUNSELOR_EMAIL, detect_role
from utils.time import now_ist_iso

router = APIRouter(prefix="/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
	content: str


class OpenChatByUuidRequest(BaseModel):
	student_uuid: str


def _normalize_risk_label(risk_value: str | None):
	value = (risk_value or "").strip().upper()
	if value in {"LOW", "MEDIUM", "HIGH"}:
		return value
	return None


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


def _serialize_messages(messages):
	return [
		{
			"id": message.get("id") or message.get("_id"),
			"chat_id": message.get("chat_id"),
			"sender_role": message.get("sender_role"),
			"content": message.get("content", ""),
			"timestamp": message.get("timestamp"),
		}
		for message in messages
	]


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


@router.get("/student")
def get_student_chat(x_session_token: str | None = Header(default=None)):
	student_email = resolve_session_email(x_session_token)
	if detect_role(student_email) != "student":
		raise HTTPException(status_code=403, detail="Student access required")

	chat = db.get_or_create_chat(student_email, COUNSELOR_EMAIL)
	if not chat:
		raise HTTPException(status_code=500, detail="Could not initialize chat")

	messages = db.get_messages_for_chat(chat.get("id"))
	return {
		"chat": {
			"id": chat.get("id") or chat.get("_id"),
			"student_id": chat.get("student_uuid"),
			"counselor_id": chat.get("counselor_uuid"),
			"created_at": chat.get("created_at"),
		},
		"messages": _serialize_messages(messages),
	}


@router.post("/student/messages")
def send_student_message(payload: SendMessageRequest, x_session_token: str | None = Header(default=None)):
	content = (payload.content or "").strip()
	if not content:
		raise HTTPException(status_code=400, detail="Message content cannot be empty")

	student_email = resolve_session_email(x_session_token)
	if detect_role(student_email) != "student":
		raise HTTPException(status_code=403, detail="Student access required")

	chat = db.get_or_create_chat(student_email, COUNSELOR_EMAIL)
	if not chat:
		raise HTTPException(status_code=500, detail="Could not initialize chat")

	message = {
		"id": f"m_{uuid4().hex[:10]}",
		"chat_id": chat.get("id") or chat.get("_id"),
		"sender_role": "student",
		"content": content,
		"timestamp": now_ist_iso(),
	}
	saved_message = db.add_message(message)
	return {"success": True, "message": saved_message}


@router.get("/counselor/chats")
def get_counselor_chats(x_session_token: str | None = Header(default=None)):
	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	chats = db.get_counselor_chats(counselor_email)
	risk_lookup = _build_student_risk_lookup(db.get_posts())
	items = []
	for chat in chats:
		chat_id = chat.get("id") or chat.get("_id")
		messages = db.get_messages_for_chat(chat_id)
		if not messages:
			continue
		last_seen = chat.get("counselor_last_seen_student_message_at")
		unseen_count = _count_unseen_student_messages(messages, last_seen)

		student_uuid = (chat.get("student_uuid") or "").strip() or None

		last_message = messages[-1] if messages else None
		items.append(
			{
				"chat_id": chat_id,
				"student_uuid": student_uuid,
				"risk_label": risk_lookup.get(student_uuid, "NO_INFORMATION"),
				"unseen_count": unseen_count,
				"has_unseen": unseen_count > 0,
				"created_at": chat.get("created_at"),
				"last_message": {
					"sender_role": last_message.get("sender_role"),
					"content": last_message.get("content"),
					"timestamp": last_message.get("timestamp"),
				}
				if last_message
				else None,
			}
		)

	items.sort(key=lambda chat: (chat.get("last_message") or {}).get("timestamp") or chat.get("created_at") or "", reverse=True)
	return {"chats": items}


@router.get("/counselor/messages/{chat_id}")
def get_counselor_messages(chat_id: str, x_session_token: str | None = Header(default=None)):
	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	chat = db.get_chat_by_id(chat_id)
	if not chat:
		raise HTTPException(status_code=404, detail="Chat not found")	
	counselor_uuid = db.get_or_create_user_uuid(counselor_email, "counselor")
	if (chat.get("counselor_uuid") or "") != counselor_uuid:
		raise HTTPException(status_code=403, detail="You can only access your own chats")

	student_uuid = (chat.get("student_uuid") or "").strip() or None
	risk_lookup = _build_student_risk_lookup(db.get_posts())

	messages = db.get_messages_for_chat(chat_id)
	last_student_timestamp = ""
	for message in messages:
		if message.get("sender_role") == "student":
			last_student_timestamp = message.get("timestamp") or last_student_timestamp
	if last_student_timestamp:
		db.mark_chat_seen_by_counselor(chat_id, last_student_timestamp)

	return {
		"chat": {
			"id": chat.get("id") or chat.get("_id"),
			"student_uuid": student_uuid,
			"risk_label": risk_lookup.get(student_uuid, "NO_INFORMATION"),
			"unseen_count": 0,
			"has_unseen": False,
			"counselor_id": chat.get("counselor_uuid"),
			"created_at": chat.get("created_at"),
		},
		"messages": _serialize_messages(messages),
	}


@router.post("/counselor/messages/{chat_id}")
def send_counselor_message(chat_id: str, payload: SendMessageRequest, x_session_token: str | None = Header(default=None)):
	content = (payload.content or "").strip()
	if not content:
		raise HTTPException(status_code=400, detail="Message content cannot be empty")

	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	chat = db.get_chat_by_id(chat_id)
	if not chat:
		raise HTTPException(status_code=404, detail="Chat not found")
	counselor_uuid = db.get_or_create_user_uuid(counselor_email, "counselor")
	if (chat.get("counselor_uuid") or "") != counselor_uuid:
		raise HTTPException(status_code=403, detail="You can only send to your own chats")

	message = {
		"id": f"m_{uuid4().hex[:10]}",
		"chat_id": chat.get("id") or chat.get("_id"),
		"sender_role": "counselor",
		"content": content,
		"timestamp": now_ist_iso(),
	}
	saved_message = db.add_message(message)
	return {"success": True, "message": saved_message}


@router.post("/counselor/open-chat-by-uuid")
def open_counselor_chat_by_uuid(payload: OpenChatByUuidRequest, x_session_token: str | None = Header(default=None)):
	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	student_uuid = (payload.student_uuid or "").strip()
	if not student_uuid:
		raise HTTPException(status_code=400, detail="student_uuid is required")

	student_email = db.get_email_by_user_uuid(student_uuid)
	if not student_email:
		raise HTTPException(status_code=404, detail="Student not found for this UUID")

	chat = db.get_or_create_chat(student_email, counselor_email)
	if not chat:
		raise HTTPException(status_code=500, detail="Could not initialize chat")

	risk_lookup = _build_student_risk_lookup(db.get_posts())
	return {
		"chat": {
			"chat_id": chat.get("id") or chat.get("_id"),
			"student_uuid": student_uuid,
			"risk_label": risk_lookup.get(student_uuid, "NO_INFORMATION"),
		}
	}
