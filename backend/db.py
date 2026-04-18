import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv

from data.fake_data import FAKE_DIARY, FAKE_POSTS

load_dotenv()

try:
	from pymongo import MongoClient, ReturnDocument
except Exception:
	MongoClient = None
	ReturnDocument = None


class DatabaseManager:
	def __init__(self):
		self.mongo_uri = os.getenv("MONGODB_URI", "") or os.getenv("MONGO_URI", "")
		self.client = None
		self.database = None
		self.memory = {
			"posts": [*FAKE_POSTS],
			"diary_entries": [*FAKE_DIARY],
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
		post.setdefault("created_at", datetime.utcnow().isoformat())
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

	def add_diary_entry(self, entry):
		entry.setdefault("created_at", datetime.utcnow().isoformat())
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
			now = datetime.utcnow().isoformat()
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
			"created_at": datetime.utcnow().isoformat(),
		}
		return user_uuid


db = DatabaseManager()
