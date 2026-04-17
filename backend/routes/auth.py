from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from utils.otp import detect_role, generate_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])

otp_store = {}


class SendOtpRequest(BaseModel):
	email: EmailStr


class VerifyOtpRequest(BaseModel):
	email: EmailStr
	otp: str


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
	return {
		"success": True,
		"role": role,
		"email": email,
	}
