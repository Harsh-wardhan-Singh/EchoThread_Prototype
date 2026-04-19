import axios from 'axios'
import { mockPosts, mockPulse } from '../data/mockData'

const api = axios.create({
	baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
	timeout: 5000,
})

export async function sendOtp(email) {
	await api.post('/auth/send-otp', { email })
	return { message: 'OTP sent' }
}

export async function verifyOtp(email, otp) {
	const { data } = await api.post('/auth/verify-otp', { email, otp })
	return data
}

export async function analyzeDiary(email, text, sessionToken) {
	const { data } = await api.post(
		'/ai/diary',
		{ email, text },
		{
			timeout: 30000,
			headers: { 'x-session-token': sessionToken },
		},
	)
	return data
}

export async function getDiaryWeek(email, sessionToken) {
	const { data } = await api.get('/ai/diary/week', {
		params: { email },
		headers: { 'x-session-token': sessionToken },
	})
	return data
}

export async function getDiaryHistory(email, sessionToken, weeks = 8) {
	const { data } = await api.get('/ai/diary/history', {
		params: { email, weeks },
		headers: { 'x-session-token': sessionToken },
	})
	return data
}

export async function createPost(content, sessionToken) {
	const { data } = await api.post('/posts', { content }, { headers: { 'x-session-token': sessionToken } })
	return data
}

export async function createPostComment(postId, content, sessionToken) {
	const { data } = await api.post(
		`/posts/${postId}/comments`,
		{ content },
		{ headers: { 'x-session-token': sessionToken } },
	)
	return data
}

export async function createPostReply(postId, commentId, content, sessionToken) {
	const { data } = await api.post(
		`/posts/${postId}/comments/${commentId}/replies`,
		{ content },
		{ headers: { 'x-session-token': sessionToken } },
	)
	return data
}

export async function getPosts() {
	try {
		const { data } = await api.get('/posts')
		return data
	} catch {
		return mockPosts
	}
}

export async function getFlaggedPosts() {
	try {
		const { data } = await api.get('/posts/flagged')
		return data
	} catch {
		return []
	}
}

export async function getPulse() {
	try {
		const { data } = await api.get('/pulse')
		return data
	} catch {
		return mockPulse
	}
}

export async function getStudentPulse(email, userUuid, sessionToken) {
	try {
		const { data } = await api.get('/pulse/student', {
			params: { email, user_uuid: userUuid },
			headers: { 'x-session-token': sessionToken },
		})
		return data
	} catch {
		return {
			mode: 'fake',
			email,
			user_uuid: userUuid,
			message: 'You’ve been a bit stressed this week. A small rest routine may help.',
			avg_stress_level: 'MEDIUM',
			avg_stress_score: 60,
			checkin_days: 4,
			stress_series: [
				{ day: 'Mon', score: 0.48 },
				{ day: 'Tue', score: 0.54 },
				{ day: 'Wed', score: 0.62 },
				{ day: 'Thu', score: 0.58 },
				{ day: 'Fri', score: 0.66 },
				{ day: 'Sat', score: 0.71 },
				{ day: 'Sun', score: 0.64 },
			],
			previous_week_history: [
				{ day: 'Mon', date: '2026-04-06', sentiment: 'negative', text: 'Felt stressed with deadlines.' },
				{ day: 'Tue', date: '2026-04-07', sentiment: 'neutral', text: 'Managed work, but was tired.' },
				{ day: 'Wed', date: '2026-04-08', sentiment: null, text: null },
				{ day: 'Thu', date: '2026-04-09', sentiment: 'positive', text: 'Had a calmer day after support from a friend.' },
				{ day: 'Fri', date: '2026-04-10', sentiment: null, text: null },
				{ day: 'Sat', date: '2026-04-11', sentiment: 'neutral', text: 'Weekend was mixed but manageable.' },
				{ day: 'Sun', date: '2026-04-12', sentiment: 'positive', text: 'Felt hopeful planning for the next week.' },
			],
		}
	}
}

export async function getCounselorPulse(sessionToken) {
	try {
		const { data } = await api.get('/pulse/counselor', {
			headers: { 'x-session-token': sessionToken },
		})
		return data
	} catch {
		return {
			mode: 'fake',
			total_students: 42,
			overall_stress_series: [
				{ day: 'Mon', score: 52 },
				{ day: 'Tue', score: 55 },
				{ day: 'Wed', score: 58 },
				{ day: 'Thu', score: 62 },
				{ day: 'Fri', score: 65 },
				{ day: 'Sat', score: 61 },
				{ day: 'Sun', score: 59 },
			],
			posts_series: [
				{ day: 'Mon', count: 7 },
				{ day: 'Tue', count: 8 },
				{ day: 'Wed', count: 10 },
				{ day: 'Thu', count: 9 },
				{ day: 'Fri', count: 12 },
				{ day: 'Sat', count: 11 },
				{ day: 'Sun', count: 9 },
			],
			sentiment_series: [
				{ day: 'Mon', positive: 57, negative: 43 },
				{ day: 'Tue', positive: 55, negative: 45 },
				{ day: 'Wed', positive: 52, negative: 48 },
				{ day: 'Thu', positive: 50, negative: 50 },
				{ day: 'Fri', positive: 47, negative: 53 },
				{ day: 'Sat', positive: 49, negative: 51 },
				{ day: 'Sun', positive: 51, negative: 49 },
			],
			risk_counts: { LOW: 28, MEDIUM: 11, HIGH: 3 },
			emotion_distribution: [
				{ emotion: 'calm', count: 12 },
				{ emotion: 'stress', count: 9 },
				{ emotion: 'anxiety', count: 8 },
				{ emotion: 'sadness', count: 6 },
				{ emotion: 'hopeful', count: 4 },
			],
			analytics_summary: [
				'Campus stress trend is moderate with a peak around mid-week.',
				'Negative sentiment rises on high-activity days; consider proactive outreach before deadlines.',
				'Most posts remain LOW risk, but MEDIUM/HIGH posts continue to require counselor attention.',
			],
		}
	}
}

export async function getStudentCounselorChat(sessionToken) {
	const { data } = await api.get('/chat/student', {
		headers: { 'x-session-token': sessionToken },
	})
	return data
}

export async function sendStudentCounselorMessage(content, sessionToken) {
	const { data } = await api.post(
		'/chat/student/messages',
		{ content },
		{ headers: { 'x-session-token': sessionToken } },
	)
	return data
}

export async function getCounselorChats(sessionToken) {
	const { data } = await api.get('/chat/counselor/chats', {
		headers: { 'x-session-token': sessionToken },
	})
	return data
}

export async function getCounselorChatMessages(chatId, sessionToken) {
	const { data } = await api.get(`/chat/counselor/messages/${chatId}`, {
		headers: { 'x-session-token': sessionToken },
	})
	return data
}

export async function sendCounselorChatMessage(chatId, content, sessionToken) {
	const { data } = await api.post(
		`/chat/counselor/messages/${chatId}`,
		{ content },
		{ headers: { 'x-session-token': sessionToken } },
	)
	return data
}
