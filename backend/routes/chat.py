from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from db import db
from routes.auth import resolve_session_email
from utils.otp import COUNSELOR_EMAIL, detect_role

router = APIRouter(prefix="/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
	content: str


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
			"student_id": chat.get("student_id"),
			"counselor_id": chat.get("counselor_id"),
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
		"timestamp": datetime.utcnow().isoformat(),
	}
	saved_message = db.add_message(message)
	return {"success": True, "message": saved_message}


@router.get("/counselor/chats")
def get_counselor_chats(x_session_token: str | None = Header(default=None)):
	counselor_email = resolve_session_email(x_session_token)
	if counselor_email != COUNSELOR_EMAIL or detect_role(counselor_email) != "counselor":
		raise HTTPException(status_code=403, detail="Counselor access required")

	chats = db.get_counselor_chats(counselor_email)
	items = []
	for chat in chats:
		chat_id = chat.get("id") or chat.get("_id")
		messages = db.get_messages_for_chat(chat_id)
		student_messages = [message for message in messages if message.get("sender_role") == "student"]
		if not student_messages:
			continue

		last_message = messages[-1] if messages else None
		items.append(
			{
				"chat_id": chat_id,
				"student_id": chat.get("student_id"),
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
	if (chat.get("counselor_id") or "").lower() != counselor_email:
		raise HTTPException(status_code=403, detail="You can only access your own chats")

	messages = db.get_messages_for_chat(chat_id)
	return {
		"chat": {
			"id": chat.get("id") or chat.get("_id"),
			"student_id": chat.get("student_id"),
			"counselor_id": chat.get("counselor_id"),
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
	if (chat.get("counselor_id") or "").lower() != counselor_email:
		raise HTTPException(status_code=403, detail="You can only send to your own chats")

	message = {
		"id": f"m_{uuid4().hex[:10]}",
		"chat_id": chat.get("id") or chat.get("_id"),
		"sender_role": "counselor",
		"content": content,
		"timestamp": datetime.utcnow().isoformat(),
	}
	saved_message = db.add_message(message)
	return {"success": True, "message": saved_message}
