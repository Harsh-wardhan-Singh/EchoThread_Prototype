import os
from uuid import uuid4

from dotenv import load_dotenv

from data.fake_data import FAKE_DIARY, FAKE_POSTS
from utils.time import now_ist_iso
from utils.security import decrypt_text, email_hash, encrypt_text
from utils.otp import COUNSELOR_EMAIL, detect_role

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
			"emergency_access_logs": [],
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
			self._migrate_sensitive_fields()
		except Exception:
			self.client = None
			self.database = None

	def _ensure_indexes(self):
		if self.database is None:
			return
		try:
			for index in self.database.users.list_indexes():
				if index.get("key") == {"email": 1}:
					self.database.users.drop_index(index.get("name"))
		except Exception:
			pass
		try:
			for index in self.database.chats.list_indexes():
				if index.get("key") == {"student_id": 1, "counselor_id": 1}:
					self.database.chats.drop_index(index.get("name"))
		except Exception:
			pass
		try:
			self.database.users.create_index(
				"email_hash",
				name="email_hash_unique",
				unique=True,
				partialFilterExpression={"email_hash": {"$type": "string"}},
			)
		except Exception:
			pass
		try:
			self.database.chats.create_index(
				[("student_uuid", 1), ("counselor_uuid", 1)],
				name="student_uuid_counselor_uuid_unique",
				unique=True,
				partialFilterExpression={
					"student_uuid": {"$type": "string"},
					"counselor_uuid": {"$type": "string"},
				},
			)
		except Exception:
			pass
		try:
			self.database.messages.create_index([("chat_id", 1), ("timestamp", 1)])
		except Exception:
			pass
		try:
			self.database.diary_entries.create_index([("email_hash", 1), ("checkin_date", 1)])
		except Exception:
			pass
		try:
			self.database.emergency_access_logs.create_index("created_at")
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

	def _migrate_sensitive_fields(self):
		if self.database is None:
			return

		# Users: email -> email_hash + email_encrypted
		for user in self.database.users.find({"email": {"$exists": True}}):
			email_value = (user.get("email") or "").lower().strip()
			if not email_value:
				continue
			try:
				self.database.users.update_one(
					{"_id": user.get("_id")},
					{
						"$set": {
							"email_hash": email_hash(email_value),
							"email_encrypted": encrypt_text(email_value, aad="email"),
						},
						"$unset": {"email": ""},
					},
				)
			except Exception:
				continue

		# Diary: email/text -> email_hash/text_encrypted
		for entry in self.database.diary_entries.find({"$or": [{"email": {"$exists": True}}, {"text": {"$exists": True}}]}):
			updates = {"$set": {}, "$unset": {}}
			email_value = (entry.get("email") or "").lower().strip()
			if email_value:
				updates["$set"]["email_hash"] = email_hash(email_value)
				updates["$unset"]["email"] = ""
			text_value = entry.get("text")
			if text_value is not None:
				updates["$set"]["text_encrypted"] = encrypt_text(str(text_value), aad="diary")
				updates["$unset"]["text"] = ""
			if updates["$set"] or updates["$unset"]:
				self.database.diary_entries.update_one({"_id": entry.get("_id")}, updates)

		# Chats: student_id/counselor_id emails -> UUIDs
		for chat in self.database.chats.find({"$or": [{"student_id": {"$exists": True}}, {"counselor_id": {"$exists": True}}]}):
			student_uuid = chat.get("student_uuid")
			counselor_uuid = chat.get("counselor_uuid")
			if not student_uuid:
				student_email = (chat.get("student_id") or "").lower().strip()
				if student_email:
					student_uuid = self.get_or_create_user_uuid(student_email, detect_role(student_email) or "student")
			if not counselor_uuid:
				counselor_email = (chat.get("counselor_id") or "").lower().strip()
				if counselor_email:
					counselor_uuid = self.get_or_create_user_uuid(counselor_email, detect_role(counselor_email) or "counselor")
			updates = {
				"$set": {
					"student_uuid": student_uuid,
					"counselor_uuid": counselor_uuid,
				},
				"$unset": {
					"student_id": "",
					"counselor_id": "",
				},
			}
			try:
				self.database.chats.update_one({"_id": chat.get("_id")}, updates)
			except Exception:
				continue

		# Messages: content -> content_encrypted
		for message in self.database.messages.find({"content": {"$exists": True}}):
			content_value = message.get("content")
			if content_value is None:
				continue
			self.database.messages.update_one(
				{"_id": message.get("_id")},
				{
					"$set": {"content_encrypted": encrypt_text(str(content_value), aad="chat")},
					"$unset": {"content": ""},
				},
			)

		# Posts: drop plain email, keep UUID-based author identity
		for post in self.database.posts.find({"email": {"$exists": True}}):
			email_value = (post.get("email") or "").lower().strip()
			user_uuid = post.get("user_uuid")
			if not user_uuid and email_value:
				role = post.get("author_role") or detect_role(email_value) or "student"
				user_uuid = self.get_or_create_user_uuid(email_value, role)
			updates = {
				"$set": {
					"user_uuid": user_uuid,
					"email_hash": email_hash(email_value) if email_value else None,
				},
				"$unset": {"email": ""},
			}
			self.database.posts.update_one({"_id": post.get("_id")}, updates)

	def is_mongo_connected(self):
		return self.database is not None

	def add_post(self, post):
		post.setdefault("created_at", now_ist_iso())
		email_value = (post.get("email") or "").lower().strip()
		if email_value:
			post["email_hash"] = email_hash(email_value)
			post.pop("email", None)
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
		email_value = (entry.get("email") or "").lower().strip()
		if email_value:
			entry["email_hash"] = email_hash(email_value)
			entry.pop("email", None)
		if "text" in entry:
			entry["text_encrypted"] = encrypt_text(entry.get("text") or "", aad="diary")
			entry.pop("text", None)
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
		email_hash_value = email_hash(email)
		if self.database is not None:
			return self.database.diary_entries.count_documents({"email_hash": email_hash_value, "checkin_date": checkin_date}, limit=1) > 0
		return any(
			(entry.get("email_hash") == email_hash_value) and (entry.get("checkin_date") == checkin_date)
			for entry in self.memory["diary_entries"]
		)

	def get_diary_entries_for_email(self, email, start_checkin_date=None, end_checkin_date=None):
		email_hash_value = email_hash(email)
		if self.database is not None:
			query = {"email_hash": email_hash_value}
			if start_checkin_date or end_checkin_date:
				query["checkin_date"] = {}
				if start_checkin_date:
					query["checkin_date"]["$gte"] = start_checkin_date
				if end_checkin_date:
					query["checkin_date"]["$lte"] = end_checkin_date
			docs = list(self.database.diary_entries.find(query).sort("checkin_date", 1).sort("created_at", 1))
			items = [self._serialize(doc) for doc in docs]
			for item in items:
				item["text"] = decrypt_text(item.get("text_encrypted"), aad="diary")
			return items

		entries = [
			entry
			for entry in self.memory["diary_entries"]
			if entry.get("email_hash") == email_hash_value
		]
		if start_checkin_date:
			entries = [entry for entry in entries if (entry.get("checkin_date") or "") >= start_checkin_date]
		if end_checkin_date:
			entries = [entry for entry in entries if (entry.get("checkin_date") or "") <= end_checkin_date]
		entries.sort(key=lambda entry: (entry.get("checkin_date") or "", entry.get("created_at") or ""))
		decrypted = []
		for entry in entries:
			item = dict(entry)
			item["text"] = decrypt_text(item.get("text_encrypted"), aad="diary")
			decrypted.append(item)
		return decrypted

	def get_or_create_user_uuid(self, email, role=None):
		email_lower = (email or "").lower()
		if not email_lower:
			return None
		email_hash_value = email_hash(email_lower)

		if self.database is not None and ReturnDocument is not None:
			now = now_ist_iso()
			default_uuid = str(uuid4())
			doc = self.database.users.find_one_and_update(
				{"email_hash": email_hash_value},
				{
					"$setOnInsert": {
						"user_uuid": default_uuid,
						"created_at": now,
					},
					"$set": {
						"updated_at": now,
						"role": role,
						"email_hash": email_hash_value,
						"email_encrypted": encrypt_text(email_lower, aad="email"),
					},
				},
				upsert=True,
				return_document=ReturnDocument.AFTER,
			)
			if doc and doc.get("user_uuid"):
				return doc.get("user_uuid")

		user = self.memory["users"].get(email_hash_value)
		if user and user.get("user_uuid"):
			return user["user_uuid"]

		user_uuid = str(uuid4())
		self.memory["users"][email_hash_value] = {
			"email_hash": email_hash_value,
			"email_encrypted": encrypt_text(email_lower, aad="email"),
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
				return (decrypt_text(doc.get("email_encrypted"), aad="email") or "").lower() or None

		for user in self.memory["users"].values():
			if user.get("user_uuid") == uuid_value:
				return (decrypt_text(user.get("email_encrypted"), aad="email") or "").lower() or None

		return None

	def get_or_create_chat(self, student_id, counselor_id):
		student_email = (student_id or "").lower().strip()
		counselor_email = (counselor_id or "").lower().strip()
		if not student_email or not counselor_email:
			return None
		student_uuid = self.get_or_create_user_uuid(student_email, detect_role(student_email) or "student")
		counselor_uuid = self.get_or_create_user_uuid(counselor_email, detect_role(counselor_email) or "counselor")
		if not student_uuid or not counselor_uuid:
			return None

		if self.database is not None:
			doc = self.database.chats.find_one({"student_uuid": student_uuid, "counselor_uuid": counselor_uuid})
			if doc:
				return self._serialize(doc)

			chat = {
				"id": f"ch_{uuid4().hex[:10]}",
				"student_uuid": student_uuid,
				"counselor_uuid": counselor_uuid,
				"counselor_last_seen_student_message_at": None,
				"created_at": now_ist_iso(),
			}
			try:
				chat_doc = dict(chat)
				self.database.chats.insert_one(chat_doc)
				return self._serialize(chat_doc)
			except Exception:
				doc = self.database.chats.find_one({"student_uuid": student_uuid, "counselor_uuid": counselor_uuid})
				if doc:
					return self._serialize(doc)
				raise

		for chat in self.memory["chats"]:
			if chat.get("student_uuid") == student_uuid and chat.get("counselor_uuid") == counselor_uuid:
				return dict(chat)

		chat = {
			"id": f"ch_{uuid4().hex[:10]}",
			"student_uuid": student_uuid,
			"counselor_uuid": counselor_uuid,
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
		counselor_email = (counselor_id or "").lower().strip()
		if not counselor_email:
			return []
		counselor_uuid = self.get_or_create_user_uuid(counselor_email, detect_role(counselor_email) or "counselor")
		if self.database is not None:
			docs = list(self.database.chats.find({"counselor_uuid": counselor_uuid}).sort("created_at", -1))
			return [self._serialize(doc) for doc in docs]

		chats = [chat for chat in self.memory["chats"] if chat.get("counselor_uuid") == counselor_uuid]
		chats.sort(key=lambda chat: chat.get("created_at") or "", reverse=True)
		return [dict(chat) for chat in chats]

	def add_message(self, message):
		message.setdefault("id", f"m_{uuid4().hex[:10]}")
		message.setdefault("timestamp", now_ist_iso())
		if "content" in message:
			message["content_encrypted"] = encrypt_text(message.get("content") or "", aad="chat")
			message.pop("content", None)
		if self.database is not None:
			message_doc = dict(message)
			self.database.messages.insert_one(message_doc)
			result = self._serialize(message_doc)
			result["content"] = decrypt_text(result.get("content_encrypted"), aad="chat")
			return result
		self.memory["messages"].append(message)
		result = dict(message)
		result["content"] = decrypt_text(result.get("content_encrypted"), aad="chat")
		return result

	def get_messages_for_chat(self, chat_id):
		if self.database is not None:
			docs = list(self.database.messages.find({"chat_id": chat_id}).sort("timestamp", 1))
			items = [self._serialize(doc) for doc in docs]
			for item in items:
				item["content"] = decrypt_text(item.get("content_encrypted"), aad="chat")
			return items

		messages = [message for message in self.memory["messages"] if message.get("chat_id") == chat_id]
		messages.sort(key=lambda message: message.get("timestamp") or "")
		items = [dict(message) for message in messages]
		for item in items:
			item["content"] = decrypt_text(item.get("content_encrypted"), aad="chat")
		return items

	def add_emergency_access_log(self, actor_email, target_user_uuid, reason=None, outcome="success"):
		entry = {
			"id": f"eal_{uuid4().hex[:10]}",
			"created_at": now_ist_iso(),
			"actor_email_hash": email_hash((actor_email or "").lower().strip()),
			"target_user_uuid": (target_user_uuid or "").strip() or None,
			"reason_encrypted": encrypt_text((reason or "").strip(), aad="emergency_reason") if reason else None,
			"outcome": outcome,
		}
		if self.database is not None:
			self.database.emergency_access_logs.insert_one(dict(entry))
			return entry
		self.memory["emergency_access_logs"].append(entry)
		return dict(entry)


db = DatabaseManager()
