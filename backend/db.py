import os
from uuid import uuid4

from dotenv import load_dotenv

from data.fake_data import FAKE_DIARY, FAKE_POSTS
from utils.time import now_ist_iso

load_dotenv()

try:
	from pymongo import MongoClient, ReturnDocument
except Exception:
	MongoClient = None
	ReturnDocument = None

try:
	from bson import ObjectId
except Exception:
	ObjectId = None


class DatabaseManager:
	def __init__(self):
		self.mongo_uri = os.getenv("MONGODB_URI", "") or os.getenv("MONGO_URI", "")
		self.client = None
		self.database = None
		self.memory = {
			"posts": [*FAKE_POSTS],
			"diary_entries": [*FAKE_DIARY],
			"chats": [],
			"messages": [],
			"users": {},
		}
		self._connect_mongo()

	def _connect_mongo(self):
		if not self.mongo_uri or MongoClient is None:
			return
		try:
			self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1500)
			self.client.admin.command("ping")
			self.database = self.client.get_database("echothread")
			self._ensure_indexes()
			self._seed_if_empty()
		except Exception:
			self.client = None
			self.database = None

	def _ensure_indexes(self):
		if self.database is None:
			return
		try:
			self.database.users.create_index("email", unique=True)
		except Exception:
			pass
		try:
			self.database.chats.create_index([("student_id", 1), ("counselor_id", 1)], unique=True)
		except Exception:
			pass
		try:
			self.database.messages.create_index([("chat_id", 1), ("timestamp", 1)])
		except Exception:
			pass

	def _seed_if_empty(self):
		if self.database is None:
			return

		if self.database.posts.count_documents({}) == 0:
			self.database.posts.insert_many(FAKE_POSTS)
		if self.database.diary_entries.count_documents({}) == 0:
			self.database.diary_entries.insert_many(FAKE_DIARY)

	def _serialize(self, doc):
		if not doc:
			return doc
		data = dict(doc)
		if "_id" in data:
			data["_id"] = str(data["_id"])
		return data

	def is_mongo_connected(self):
		return self.database is not None

	def add_post(self, post):
		post.setdefault("created_at", now_ist_iso())
		if self.database is not None:
			self.database.posts.insert_one(post)
			return post
		self.memory["posts"].append(post)
		return post

	def get_posts(self):
		if self.database is not None:
			docs = list(self.database.posts.find({}))
			return [self._serialize(doc) for doc in docs]
		return [*self.memory["posts"]]

	def _build_post_filter(self, post_id):
		query = {"id": post_id}
		if ObjectId is not None:
			try:
				query = {"$or": [{"id": post_id}, {"_id": ObjectId(post_id)}]}
			except Exception:
				query = {"id": post_id}
		return query

	def get_post_by_id(self, post_id):
		if self.database is not None:
			doc = self.database.posts.find_one(self._build_post_filter(post_id))
			return self._serialize(doc)

		for post in self.memory["posts"]:
			if post.get("id") == post_id or str(post.get("_id")) == str(post_id):
				return dict(post)
		return None

	def save_post_comments(self, post_id, comments):
		if self.database is not None:
			self.database.posts.update_one(
				self._build_post_filter(post_id),
				{"$set": {"comments": comments}},
			)
			return

		for index, post in enumerate(self.memory["posts"]):
			if post.get("id") == post_id or str(post.get("_id")) == str(post_id):
				updated = dict(post)
				updated["comments"] = comments
				self.memory["posts"][index] = updated
				return

	def add_diary_entry(self, entry):
		entry.setdefault("created_at", now_ist_iso())
		if self.database is not None:
			self.database.diary_entries.insert_one(entry)
			return entry
		self.memory["diary_entries"].append(entry)
		return entry

	def get_diary_entries(self):
		if self.database is not None:
			docs = list(self.database.diary_entries.find({}))
			return [self._serialize(doc) for doc in docs]
		return [*self.memory["diary_entries"]]

	def has_diary_entry_for_day(self, email, checkin_date):
		email_lower = (email or "").lower()
		if self.database is not None:
			return self.database.diary_entries.count_documents({"email": email_lower, "checkin_date": checkin_date}, limit=1) > 0
		return any(
			(entry.get("email", "").lower() == email_lower) and (entry.get("checkin_date") == checkin_date)
			for entry in self.memory["diary_entries"]
		)

	def get_diary_entries_for_email(self, email, start_checkin_date=None, end_checkin_date=None):
		email_lower = (email or "").lower()
		if self.database is not None:
			query = {"email": email_lower}
			if start_checkin_date or end_checkin_date:
				query["checkin_date"] = {}
				if start_checkin_date:
					query["checkin_date"]["$gte"] = start_checkin_date
				if end_checkin_date:
					query["checkin_date"]["$lte"] = end_checkin_date
			docs = list(self.database.diary_entries.find(query).sort("checkin_date", 1).sort("created_at", 1))
			return [self._serialize(doc) for doc in docs]

		entries = [
			entry
			for entry in self.memory["diary_entries"]
			if entry.get("email", "").lower() == email_lower
		]
		if start_checkin_date:
			entries = [entry for entry in entries if (entry.get("checkin_date") or "") >= start_checkin_date]
		if end_checkin_date:
			entries = [entry for entry in entries if (entry.get("checkin_date") or "") <= end_checkin_date]
		entries.sort(key=lambda entry: (entry.get("checkin_date") or "", entry.get("created_at") or ""))
		return entries

	def get_or_create_user_uuid(self, email, role=None):
		email_lower = (email or "").lower()
		if not email_lower:
			return None

		if self.database is not None and ReturnDocument is not None:
			now = now_ist_iso()
			default_uuid = str(uuid4())
			doc = self.database.users.find_one_and_update(
				{"email": email_lower},
				{
					"$setOnInsert": {
						"user_uuid": default_uuid,
						"created_at": now,
					},
					"$set": {
						"updated_at": now,
						"role": role,
					},
				},
				upsert=True,
				return_document=ReturnDocument.AFTER,
			)
			if doc and doc.get("user_uuid"):
				return doc.get("user_uuid")

		user = self.memory["users"].get(email_lower)
		if user and user.get("user_uuid"):
			return user["user_uuid"]

		user_uuid = str(uuid4())
		self.memory["users"][email_lower] = {
			"email": email_lower,
			"user_uuid": user_uuid,
			"role": role,
			"created_at": now_ist_iso(),
		}
		return user_uuid

	def count_users_by_role(self, role):
		if self.database is not None:
			return self.database.users.count_documents({"role": role})
		return sum(1 for user in self.memory["users"].values() if user.get("role") == role)

	def get_email_by_user_uuid(self, user_uuid):
		uuid_value = (user_uuid or "").strip()
		if not uuid_value:
			return None

		if self.database is not None:
			doc = self.database.users.find_one({"user_uuid": uuid_value})
			if doc:
				return (doc.get("email") or "").lower() or None

		for email, user in self.memory["users"].items():
			if user.get("user_uuid") == uuid_value:
				return (email or "").lower() or None

		return None

	def get_or_create_chat(self, student_id, counselor_id):
		student_value = (student_id or "").lower()
		counselor_value = (counselor_id or "").lower()
		if not student_value or not counselor_value:
			return None

		if self.database is not None:
			doc = self.database.chats.find_one({"student_id": student_value, "counselor_id": counselor_value})
			if doc:
				return self._serialize(doc)

			chat = {
				"id": f"ch_{uuid4().hex[:10]}",
				"student_id": student_value,
				"counselor_id": counselor_value,
				"counselor_last_seen_student_message_at": None,
				"created_at": now_ist_iso(),
			}
			try:
				chat_doc = dict(chat)
				self.database.chats.insert_one(chat_doc)
				return self._serialize(chat_doc)
			except Exception:
				doc = self.database.chats.find_one({"student_id": student_value, "counselor_id": counselor_value})
				if doc:
					return self._serialize(doc)
				raise

		for chat in self.memory["chats"]:
			if chat.get("student_id") == student_value and chat.get("counselor_id") == counselor_value:
				return dict(chat)

		chat = {
			"id": f"ch_{uuid4().hex[:10]}",
			"student_id": student_value,
			"counselor_id": counselor_value,
			"counselor_last_seen_student_message_at": None,
			"created_at": now_ist_iso(),
		}
		self.memory["chats"].append(chat)
		return chat

	def mark_chat_seen_by_counselor(self, chat_id, seen_timestamp):
		if not chat_id or not seen_timestamp:
			return

		if self.database is not None:
			self.database.chats.update_one(
				{"id": chat_id},
				{"$set": {"counselor_last_seen_student_message_at": seen_timestamp}},
			)
			return

		for index, chat in enumerate(self.memory["chats"]):
			if chat.get("id") == chat_id:
				updated = dict(chat)
				updated["counselor_last_seen_student_message_at"] = seen_timestamp
				self.memory["chats"][index] = updated
				return

	def get_chat_by_id(self, chat_id):
		if self.database is not None:
			doc = self.database.chats.find_one({"id": chat_id})
			return self._serialize(doc)

		for chat in self.memory["chats"]:
			if chat.get("id") == chat_id:
				return dict(chat)
		return None

	def get_counselor_chats(self, counselor_id):
		counselor_value = (counselor_id or "").lower()
		if self.database is not None:
			docs = list(self.database.chats.find({"counselor_id": counselor_value}).sort("created_at", -1))
			return [self._serialize(doc) for doc in docs]

		chats = [chat for chat in self.memory["chats"] if chat.get("counselor_id") == counselor_value]
		chats.sort(key=lambda chat: chat.get("created_at") or "", reverse=True)
		return [dict(chat) for chat in chats]

	def add_message(self, message):
		message.setdefault("id", f"m_{uuid4().hex[:10]}")
		message.setdefault("timestamp", now_ist_iso())
		if self.database is not None:
			message_doc = dict(message)
			self.database.messages.insert_one(message_doc)
			return self._serialize(message_doc)
		self.memory["messages"].append(message)
		return dict(message)

	def get_messages_for_chat(self, chat_id):
		if self.database is not None:
			docs = list(self.database.messages.find({"chat_id": chat_id}).sort("timestamp", 1))
			return [self._serialize(doc) for doc in docs]

		messages = [message for message in self.memory["messages"] if message.get("chat_id") == chat_id]
		messages.sort(key=lambda message: message.get("timestamp") or "")
		return [dict(message) for message in messages]


db = DatabaseManager()
