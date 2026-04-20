from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import db
from routes.ai import router as ai_router
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.dashboard import router as dashboard_router
from routes.inbox import router as inbox_router
from routes.post import router as post_router
from routes.pulse import router as pulse_router

app = FastAPI(title="EchoThread API", version="0.1.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(inbox_router)
app.include_router(post_router)
app.include_router(pulse_router)


@app.get("/")
def root():
	return {
		"name": "EchoThread API",
		"status": "ok",
		"mongo_connected": db.is_mongo_connected(),
	}
