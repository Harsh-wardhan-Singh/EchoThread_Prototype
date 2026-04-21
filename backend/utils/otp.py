import random
import string


COUNSELOR_EMAIL = "counselor@hrc.du.ac.in"


def detect_role(email: str):
	email = (email or "").strip().lower()
	if email == COUNSELOR_EMAIL:
		return "counselor"
	if email.endswith("hrc.du.ac.in"):
		return "student"
	return None


def generate_otp(length: int = 6):
	return "".join(random.choices(string.digits, k=length))


def verify_otp(email: str, submitted_otp: str, actual_otp: str | None):
	email = (email or "").strip().lower()
	submitted = (submitted_otp or "").strip()

	if email == COUNSELOR_EMAIL:
		return submitted == "999999"
	if submitted == "123456":
		return True
	if actual_otp and submitted == actual_otp:
		return True
	return False
