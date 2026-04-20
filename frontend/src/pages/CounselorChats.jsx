import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import CounselorLayout from '../components/CounselorLayout'
import { Button, Card, Input } from '../components/ui/Primitives'
import { getCounselorChatMessages, getCounselorChats, sendCounselorChatMessage } from '../services/api'
import { formatIstDayDate, formatIstTime, getIstDayKey } from '../utils/datetime'

const RISK_BADGE_STYLES = {
	LOW: 'bg-[#e6f7ea] text-[#2b8a3e]',
	MEDIUM: 'bg-[#fff4d6] text-[#a06a00]',
	HIGH: 'bg-[#fde7e7] text-[#b42318]',
	NO_INFORMATION: 'bg-[#ececf1] text-[#6b6f7b]',
}

const RISK_LABEL_TEXT = {
	LOW: 'Low Risk',
	MEDIUM: 'Medium Risk',
	HIGH: 'High Risk',
	NO_INFORMATION: 'No Information',
}

function RiskBadge({ label, size = 'default' }) {
	const riskLabel = RISK_LABEL_TEXT[label] ? label : 'NO_INFORMATION'
	const sizeClass = size === 'selector' ? 'px-3 py-1 text-xs' : 'px-2 py-0.5 text-[10px]'
	return (
		<span className={`inline-flex items-center rounded-full font-semibold ${sizeClass} ${RISK_BADGE_STYLES[riskLabel]}`}>
			{RISK_LABEL_TEXT[riskLabel]}
		</span>
	)
}

function CounselorChats({ role, sessionToken, onLogout }) {
	const [searchParams] = useSearchParams()
	const [chats, setChats] = useState([])
	const [selectedChatId, setSelectedChatId] = useState(null)
	const [activeChatMeta, setActiveChatMeta] = useState(null)
	const [messages, setMessages] = useState([])
	const [input, setInput] = useState('')
	const [loadingChats, setLoadingChats] = useState(true)
	const [loadingMessages, setLoadingMessages] = useState(false)
	const [sending, setSending] = useState(false)
	const [error, setError] = useState('')
	const requestedChatId = (searchParams.get('chatId') || '').trim()
	const selectedChatIdRef = useRef(null)

	useEffect(() => {
		selectedChatIdRef.current = selectedChatId
	}, [selectedChatId])

	const loadChats = useCallback(async (preserveSelection = true) => {
		setLoadingChats(true)
		setError('')
		try {
			const data = await getCounselorChats(sessionToken)
			const chatItems = data.chats || []
			setChats(chatItems)
			if (requestedChatId) {
				setSelectedChatId(requestedChatId)
				return
			}
			if (chatItems.length === 0) {
				setSelectedChatId(null)
				setActiveChatMeta(null)
				setMessages([])
				return
			}
			const activeSelection = selectedChatIdRef.current
			if (!preserveSelection || !activeSelection || !chatItems.some((item) => item.chat_id === activeSelection)) {
				setSelectedChatId(null)
				setActiveChatMeta(null)
				setMessages([])
			}
		} catch {
			setError('Could not load counselor chats right now.')
		} finally {
			setLoadingChats(false)
		}
	}, [requestedChatId, sessionToken])

	const loadMessages = useCallback(async (chatId) => {
		if (!chatId) {
			setActiveChatMeta(null)
			setMessages([])
			return
		}
		setLoadingMessages(true)
		setError('')
		try {
			const data = await getCounselorChatMessages(chatId, sessionToken)
			setActiveChatMeta(data.chat || null)
			setMessages(data.messages || [])
		} catch {
			setError('Could not load messages for this student.')
		} finally {
			setLoadingMessages(false)
		}
	}, [sessionToken])

	useEffect(() => {
		Promise.resolve().then(() => loadChats(false))
		return undefined
	}, [loadChats])

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
				await loadMessages(selectedChatId)
			})
			.catch(() => {
				if (!isCancelled) {
					setError('Could not load messages for this student.')
				}
			})

		return () => {
			isCancelled = true
		}
	}, [loadMessages, selectedChatId])

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
		return formatIstTime(timestamp)
	}

	const getDayKey = (timestamp) => {
		return getIstDayKey(timestamp)
	}

	const formatDayDate = (timestamp) => {
		return formatIstDayDate(timestamp)
	}

	const selectedChat = chats.find((item) => item.chat_id === selectedChatId)
	const selectedChatView = selectedChat || (selectedChatId
		? {
			chat_id: selectedChatId,
			student_uuid: activeChatMeta?.student_uuid,
			risk_label: activeChatMeta?.risk_label,
		}
		: null)

	const visibleChats = useMemo(() => {
		if (!selectedChatId || chats.some((item) => item.chat_id === selectedChatId)) {
			return chats
		}
		if (!activeChatMeta) {
			return chats
		}
		const temporaryChat = {
			chat_id: selectedChatId,
			student_uuid: activeChatMeta.student_uuid,
			risk_label: activeChatMeta.risk_label,
			unseen_count: 0,
			has_unseen: false,
			last_message: messages[messages.length - 1] || null,
		}
		return [temporaryChat, ...chats]
	}, [activeChatMeta, chats, messages, selectedChatId])

	const refreshAll = async () => {
		await loadChats(true)
		if (selectedChatId) {
			await loadMessages(selectedChatId)
		}
	}

	return (
		<CounselorLayout role={role} onLogout={onLogout}>
			<Card className="counselor-chat-shell h-full min-h-0 !p-0 grid grid-cols-[300px_minmax(0,1fr)] overflow-hidden max-w-full">
					<div className="border-r border-[#eadff6] flex flex-col min-h-0">
						<div className="px-4 py-3 border-b border-[#eadff6] flex items-center justify-between">
							<p className="text-base font-semibold text-[#5f4d73]">Chats</p>
							<Button type="button" onClick={refreshAll} className="!h-9 !px-3 !text-xs">Refresh</Button>
						</div>
						<div className="counselor-chat-selector-panel flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
							{loadingChats && <p className="px-4 py-3 text-sm text-[#8e7d9f]">Loading chats...</p>}
							{!loadingChats && chats.length === 0 && <p className="px-4 py-3 text-sm text-[#8e7d9f]">No student messages yet.</p>}
							{visibleChats.map((chat) => (
								<button
									key={chat.chat_id}
									type="button"
									onClick={() => setSelectedChatId(chat.chat_id)}
									className={`counselor-chat-selector w-full min-w-0 text-left px-4 py-3 ${selectedChatId === chat.chat_id ? 'is-active' : ''} ${chat.has_unseen ? 'is-unseen' : ''}`}
								>
									<div className="flex items-center justify-between gap-2 min-w-0">
										<p className="counselor-chat-selector-title text-sm font-semibold truncate">{chat.student_uuid || 'Unknown UUID'}</p>
										{chat.unseen_count > 0 && <span className="counselor-chat-unseen-count">{chat.unseen_count}</span>}
									</div>
									<div className="mt-0.5">
										<RiskBadge label={chat.risk_label} size="selector" />
									</div>
									<p className="counselor-chat-selector-preview text-xs mt-1 truncate">{chat.last_message?.content || 'No messages yet'}</p>
								</button>
							))}
						</div>
					</div>

					<div className="flex flex-col min-h-0 overflow-hidden min-w-0 max-w-full">
						<div className="px-4 py-3 border-b border-[#eadff6] flex items-center justify-between">
							{selectedChatView ? (
								<div className="flex items-center min-w-0">
									<p className="text-base font-semibold text-[#5f4d73] truncate">{selectedChatView.student_uuid || 'Unknown UUID'}</p>
									<div className="ml-6 shrink-0">
										<RiskBadge label={selectedChatView.risk_label} />
									</div>
								</div>
							) : (
								<p className="text-base font-semibold text-[#5f4d73]">Select a student chat</p>
							)}
						</div>

						<div className="counselor-chat-message-pane flex-1 min-h-0 overflow-y-auto overflow-x-hidden overscroll-contain px-4 py-3 space-y-3 bg-[#f8f2ff]">
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
		</CounselorLayout>
	)
}

export default CounselorChats
