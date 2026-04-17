import os
from datetime import datetime

from dotenv import load_dotenv

from data.fake_data import FAKE_DIARY, FAKE_POSTS

load_dotenv()

try:
	from pymongo import MongoClient
except Exception:
	MongoClient = None


class DatabaseManager:
	def __init__(self):
		self.mongo_uri = os.getenv("MONGODB_URI", "") or os.getenv("MONGO_URI", "")
		self.client = None
		self.database = None
		self.memory = {
			"posts": [*FAKE_POSTS],
			"diary_entries": [*FAKE_DIARY],
		}
		self._connect_mongo()

	def _connect_mongo(self):
		if not self.mongo_uri or MongoClient is None:
			return
		try:
			self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1500)
			self.client.admin.command("ping")
			self.database = self.client.get_database("echothread")
			self._seed_if_empty()
		except Exception:
			self.client = None
			self.database = None

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


db = DatabaseManager()
