import { useEffect, useMemo, useState } from 'react'
import StudentLayout from '../components/StudentLayout'
import { Button, Card, Input } from '../components/ui/Primitives'
import { getStudentCounselorChat, sendStudentCounselorMessage } from '../services/api'

function OpenChat({ role, sessionToken, onLogout }) {
	const [messages, setMessages] = useState([])
	const [input, setInput] = useState('')
	const [loading, setLoading] = useState(true)
	const [sending, setSending] = useState(false)
	const [error, setError] = useState('')

	const loadChat = async () => {
		if (!sessionToken) {
			return
		}
		setLoading(true)
		setError('')
		try {
			const data = await getStudentCounselorChat(sessionToken)
			setMessages(data.messages || [])
		} catch {
			setError('Could not load counselor chat right now.')
		} finally {
			setLoading(false)
		}
	}

	useEffect(() => {
		if (!sessionToken) {
			return
		}
		let isCancelled = false
		Promise.resolve()
			.then(async () => {
				if (isCancelled) {
					return
				}
				setLoading(true)
				setError('')
				const data = await getStudentCounselorChat(sessionToken)
				if (!isCancelled) {
					setMessages(data.messages || [])
				}
			})
			.catch(() => {
				if (!isCancelled) {
					setError('Could not load counselor chat right now.')
				}
			})
			.finally(() => {
				if (!isCancelled) {
					setLoading(false)
				}
			})

		return () => {
			isCancelled = true
		}
	}, [sessionToken])

	const sendMessage = async (event) => {
		event.preventDefault()
		const content = input.trim()
		if (!content) {
			return
		}

		setSending(true)
		setError('')
		try {
			await sendStudentCounselorMessage(content, sessionToken)
			setInput('')
			await loadChat()
		} catch {
			setError('Could not send message. Please try again.')
		} finally {
			setSending(false)
		}
	}

	const sortedMessages = useMemo(() => {
		return [...messages].sort((a, b) => (a.timestamp || '').localeCompare(b.timestamp || ''))
	}, [messages])

	const formatTime = (timestamp) => {
		if (!timestamp) {
			return ''
		}
		try {
			return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
		} catch {
			return ''
		}
	}

	const getDayKey = (timestamp) => {
		if (!timestamp) {
			return ''
		}
		try {
			const date = new Date(timestamp)
			return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
		} catch {
			return ''
		}
	}

	const formatDayDate = (timestamp) => {
		if (!timestamp) {
			return ''
		}
		try {
			return new Date(timestamp).toLocaleDateString([], { weekday: 'short', day: '2-digit', month: 'short' })
		} catch {
			return ''
		}
	}

	return (
		<StudentLayout role={role} onLogout={onLogout}>
			<Card className="h-full !p-0 flex flex-col overflow-hidden">
				<div className="px-4 py-3 border-b border-[#eadff6] flex items-center justify-between">
					<div className="flex items-center gap-2">
						<p className="text-base font-semibold text-[#5f4d73]">counselor@hrc.du.ac.in</p>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-label="Verified counselor">
							<path d="M12 1.8L14.8 4.4L18.5 3.9L19.9 7.4L23.2 9.2L22.7 12.9L24 16.3L21 18.5L20 22.1L16.3 21.9L13.1 24L10.4 21.4L6.7 21.9L5.3 18.4L2 16.6L2.5 12.9L1.2 9.5L4.2 7.3L5.2 3.7L8.9 3.9L12 1.8Z" fill="#ccb8ff" />
							<path d="M8.4 12.4L10.8 14.7L15.7 9.8" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
						</svg>
					</div>
					<Button type="button" onClick={loadChat} className="!h-9 !px-3 !text-xs">Refresh</Button>
				</div>

				<div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-4 py-3 space-y-3 bg-[#f8f2ff]">
					{loading && <p className="text-sm text-[#8e7d9f]">Loading chat...</p>}
					{!loading && sortedMessages.length === 0 && <p className="text-sm text-[#8e7d9f]">Start your conversation with the counselor.</p>}
					{sortedMessages.map((message, index) => {
						const isStudent = message.sender_role === 'student'
						const timeLabel = formatTime(message.timestamp)
						const messageDayKey = getDayKey(message.timestamp)
						const previousDayKey = index > 0 ? getDayKey(sortedMessages[index - 1]?.timestamp) : ''
						const showDateDivider = index === 0 || messageDayKey !== previousDayKey
						const dayDateLabel = formatDayDate(message.timestamp)
						return (
							<div key={message.id} className="chat-item">
								{showDateDivider && dayDateLabel && <div className="chat-date-divider">{dayDateLabel}</div>}
								<div className={`chat-row ${isStudent ? 'chat-row-user' : 'chat-row-peer'}`}>
									<div className={`chat-bubble ${isStudent ? 'chat-bubble-user' : 'chat-bubble-peer'}`}>
										<p className="leading-relaxed whitespace-pre-wrap break-words">
											{message.content}
										{timeLabel && (
												<span className={`chat-time ${isStudent ? 'chat-time-user' : 'chat-time-peer'}`}>{timeLabel}</span>
										)}
										</p>
									</div>
								</div>
								</div>
						)
					})}
				</div>

				<form onSubmit={sendMessage} className="px-4 py-3 border-t border-[#eadff6] flex items-center gap-2">
					<Input
						type="text"
						placeholder="Type your message"
						value={input}
						onChange={(event) => setInput(event.target.value)}
						className="!h-10 flex-1"
					/>
					<Button type="submit" disabled={sending} className="!h-10 !px-4">
						{sending ? 'Sending...' : 'Send'}
					</Button>
				</form>
				{error && <p className="px-4 pb-3 text-sm text-[#a16788]">{error}</p>}
			</Card>
		</StudentLayout>
	)
}

export default OpenChat
