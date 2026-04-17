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

export async function analyzeDiary(email, text) {
	const { data } = await api.post('/ai/diary', { email, text })
	return data
}

export async function createPost(content) {
	const { data } = await api.post('/posts', { content })
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
