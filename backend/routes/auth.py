import base64
import hashlib
import hmac
import os
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from uuid import uuid4

from db import db
from utils.otp import detect_role, generate_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])

otp_store = {}
session_store = {}
SESSION_SECRET = (os.getenv("SESSION_SECRET") or "echothread-dev-session-secret").encode("utf-8")
SESSION_TTL_SECONDS = 60 * 60 * 24 * 14


class SendOtpRequest(BaseModel):
	email: EmailStr


class VerifyOtpRequest(BaseModel):
	email: EmailStr
	otp: str


def _encode_payload(payload: str):
	return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").rstrip("=")


def _decode_payload(payload_b64: str):
	padding = "=" * (-len(payload_b64) % 4)
	decoded = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8"))
	return decoded.decode("utf-8")


def _sign_payload(payload: str):
	return hmac.new(SESSION_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _create_session_token(email: str):
	issued_at = int(time.time())
	payload = f"{email}|{issued_at}"
	return f"{_encode_payload(payload)}.{_sign_payload(payload)}"


def _extract_email_from_signed_token(session_token: str):
	if "." not in session_token:
		return None
	payload_b64, signature = session_token.split(".", 1)
	try:
		payload = _decode_payload(payload_b64)
	except Exception:
		return None

	if not hmac.compare_digest(_sign_payload(payload), signature):
		return None

	parts = payload.split("|", 1)
	if len(parts) != 2:
		return None

	token_email = (parts[0] or "").lower()
	try:
		issued_at = int(parts[1])
	except Exception:
		return None

	if issued_at + SESSION_TTL_SECONDS < int(time.time()):
		return None

	return token_email


@router.post("/send-otp")
def send_otp(payload: SendOtpRequest):
	role = detect_role(payload.email)
	if role is None:
		raise HTTPException(status_code=400, detail="Only HRC student/counselor emails are allowed.")

	otp_store[payload.email.lower()] = generate_otp()
	return {"message": "OTP sent"}


@router.post("/verify-otp")
def verify_user_otp(payload: VerifyOtpRequest):
	email = payload.email.lower()
	role = detect_role(email)
	if role is None:
		raise HTTPException(status_code=400, detail="Invalid institutional account.")

	actual_otp = otp_store.get(email)
	if not verify_otp(email, payload.otp, actual_otp):
		raise HTTPException(status_code=401, detail="Invalid OTP")

	otp_store.pop(email, None)
	user_uuid = db.get_or_create_user_uuid(email, role)
	session_token = _create_session_token(email)
	session_store[session_token] = email
	return {
		"success": True,
		"role": role,
		"email": email,
		"user_uuid": user_uuid,
		"session_token": session_token,
	}


def verify_session(email: str, session_token: str | None):
	if not session_token:
		raise HTTPException(status_code=401, detail="Missing session token")

	email_lower = (email or "").lower()
	stored_email = session_store.get(session_token)
	if stored_email is not None:
		if stored_email == email_lower:
			return
		raise HTTPException(status_code=403, detail="You can only access your own diary data")

	signed_email = _extract_email_from_signed_token(session_token)
	if signed_email is None:
		raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
	if signed_email != email_lower:
		raise HTTPException(status_code=403, detail="You can only access your own diary data")


def resolve_session_email(session_token: str | None):
	if not session_token:
		raise HTTPException(status_code=401, detail="Missing session token")

	stored_email = session_store.get(session_token)
	if stored_email is not None:
		return stored_email

	signed_email = _extract_email_from_signed_token(session_token)
	if signed_email is None:
		raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
	return signed_email
