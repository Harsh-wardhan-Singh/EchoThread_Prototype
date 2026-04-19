import { useEffect, useMemo, useState } from 'react'
import Navbar from '../components/Navbar'
import { Button, Card, Input } from '../components/ui/Primitives'
import { getCounselorChatMessages, getCounselorChats, sendCounselorChatMessage } from '../services/api'

function CounselorChats({ role, sessionToken, onLogout }) {
	const [chats, setChats] = useState([])
	const [selectedChatId, setSelectedChatId] = useState(null)
	const [messages, setMessages] = useState([])
	const [input, setInput] = useState('')
	const [loadingChats, setLoadingChats] = useState(true)
	const [loadingMessages, setLoadingMessages] = useState(false)
	const [sending, setSending] = useState(false)
	const [error, setError] = useState('')

	const loadChats = async (preserveSelection = true) => {
		setLoadingChats(true)
		setError('')
		try {
			const data = await getCounselorChats(sessionToken)
			const chatItems = data.chats || []
			setChats(chatItems)
			if (chatItems.length === 0) {
				setSelectedChatId(null)
				setMessages([])
				return
			}
			if (!preserveSelection || !selectedChatId || !chatItems.some((item) => item.chat_id === selectedChatId)) {
				setSelectedChatId(chatItems[0].chat_id)
			}
		} catch {
			setError('Could not load counselor chats right now.')
		} finally {
			setLoadingChats(false)
		}
	}

	const loadMessages = async (chatId) => {
		if (!chatId) {
			setMessages([])
			return
		}
		setLoadingMessages(true)
		setError('')
		try {
			const data = await getCounselorChatMessages(chatId, sessionToken)
			setMessages(data.messages || [])
		} catch {
			setError('Could not load messages for this student.')
		} finally {
			setLoadingMessages(false)
		}
	}

	useEffect(() => {
		let isCancelled = false
		Promise.resolve()
			.then(async () => {
				if (isCancelled) {
					return
				}
				setLoadingChats(true)
				setError('')
				const data = await getCounselorChats(sessionToken)
				if (isCancelled) {
					return
				}
				const chatItems = data.chats || []
				setChats(chatItems)
				if (chatItems.length === 0) {
					setSelectedChatId(null)
					setMessages([])
					return
				}
				setSelectedChatId(chatItems[0].chat_id)
			})
			.catch(() => {
				if (!isCancelled) {
					setError('Could not load counselor chats right now.')
				}
			})
			.finally(() => {
				if (!isCancelled) {
					setLoadingChats(false)
				}
			})

		return () => {
			isCancelled = true
		}
	}, [sessionToken])

	useEffect(() => {
		if (!selectedChatId) {
			return
		}
		let isCancelled = false
		Promise.resolve()
			.then(async () => {
				if (isCancelled) {
					return
				}
				setLoadingMessages(true)
				setError('')
				const data = await getCounselorChatMessages(selectedChatId, sessionToken)
				if (!isCancelled) {
					setMessages(data.messages || [])
				}
			})
			.catch(() => {
				if (!isCancelled) {
					setError('Could not load messages for this student.')
				}
			})
			.finally(() => {
				if (!isCancelled) {
					setLoadingMessages(false)
				}
			})

		return () => {
			isCancelled = true
		}
	}, [selectedChatId, sessionToken])

	const sendMessage = async (event) => {
		event.preventDefault()
		const content = input.trim()
		if (!content || !selectedChatId) {
			return
		}
		setSending(true)
		setError('')
		try {
			await sendCounselorChatMessage(selectedChatId, content, sessionToken)
			setInput('')
			await loadMessages(selectedChatId)
			await loadChats(true)
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

	const selectedChat = chats.find((item) => item.chat_id === selectedChatId)

	const refreshAll = async () => {
		await loadChats(true)
		if (selectedChatId) {
			await loadMessages(selectedChatId)
		}
	}

	return (
		<div className="h-full min-h-0 flex flex-col safe-fade-slide overflow-hidden">
			<div className="z-20">
				<Navbar role={role} onLogout={onLogout} />
			</div>
			<main className="flex-1 min-h-0 p-4 overflow-hidden">
				<Card className="h-full min-h-0 !p-0 grid grid-cols-[300px_minmax(0,1fr)] overflow-hidden">
					<div className="border-r border-[#eadff6] flex flex-col min-h-0">
						<div className="px-4 py-3 border-b border-[#eadff6] flex items-center justify-between">
							<p className="text-base font-semibold text-[#5f4d73]">Chats</p>
							<Button type="button" onClick={refreshAll} className="!h-9 !px-3 !text-xs">Refresh</Button>
						</div>
						<div className="flex-1 min-h-0 overflow-y-auto bg-[#f8f2ff]">
							{loadingChats && <p className="px-4 py-3 text-sm text-[#8e7d9f]">Loading chats...</p>}
							{!loadingChats && chats.length === 0 && <p className="px-4 py-3 text-sm text-[#8e7d9f]">No student messages yet.</p>}
							{chats.map((chat) => (
								<button
									key={chat.chat_id}
									type="button"
									onClick={() => setSelectedChatId(chat.chat_id)}
									className={`w-full text-left px-4 py-3 border-b border-[#f0e6fb] transition-colors ${selectedChatId === chat.chat_id ? 'bg-white' : 'hover:bg-white/70'}`}
								>
									<p className="text-sm font-semibold text-[#5f4d73]">{chat.student_id}</p>
									<p className="text-xs text-[#8e7d9f] mt-1 truncate">{chat.last_message?.content || 'No messages yet'}</p>
								</button>
							))}
						</div>
					</div>

					<div className="flex flex-col min-h-0 overflow-hidden">
						<div className="px-4 py-3 border-b border-[#eadff6] flex items-center justify-between">
							<p className="text-base font-semibold text-[#5f4d73]">{selectedChat ? selectedChat.student_id : 'Select a student chat'}</p>
						</div>

						<div className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-4 py-3 space-y-3 bg-[#f8f2ff]">
							{!selectedChatId && <p className="text-sm text-[#8e7d9f]">Select a student from the left panel.</p>}
							{selectedChatId && loadingMessages && <p className="text-sm text-[#8e7d9f]">Loading messages...</p>}
							{selectedChatId && !loadingMessages && sortedMessages.length === 0 && <p className="text-sm text-[#8e7d9f]">No messages in this chat yet.</p>}
							{sortedMessages.map((message, index) => {
								const isCounselor = message.sender_role === 'counselor'
								const timeLabel = formatTime(message.timestamp)
								const messageDayKey = getDayKey(message.timestamp)
								const previousDayKey = index > 0 ? getDayKey(sortedMessages[index - 1]?.timestamp) : ''
								const showDateDivider = index === 0 || messageDayKey !== previousDayKey
								const dayDateLabel = formatDayDate(message.timestamp)
								return (
									<div key={message.id} className="chat-item">
										{showDateDivider && dayDateLabel && <div className="chat-date-divider">{dayDateLabel}</div>}
										<div className={`chat-row ${isCounselor ? 'chat-row-user' : 'chat-row-peer'}`}>
											<div className={`chat-bubble ${isCounselor ? 'chat-bubble-user' : 'chat-bubble-peer'}`}>
												<p className="leading-relaxed whitespace-pre-wrap break-words">
													{message.content}
												{timeLabel && (
														<span className={`chat-time ${isCounselor ? 'chat-time-user' : 'chat-time-peer'}`}>{timeLabel}</span>
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
								disabled={!selectedChatId}
							/>
							<Button type="submit" disabled={sending || !selectedChatId} className="!h-10 !px-4">
								{sending ? 'Sending...' : 'Send'}
							</Button>
						</form>
						{error && <p className="px-4 pb-3 text-sm text-[#a16788]">{error}</p>}
					</div>
				</Card>
			</main>
		</div>
	)
}

export default CounselorChats
