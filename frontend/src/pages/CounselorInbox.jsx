import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CounselorLayout from '../components/CounselorLayout'
import { getCounselorInbox, openCounselorChatByUuid } from '../services/api'
import { Button, Card } from '../components/ui/Primitives'
import { formatIstDateTime } from '../utils/datetime'

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

function RiskBadge({ label }) {
	const riskLabel = RISK_LABEL_TEXT[label] ? label : 'NO_INFORMATION'
	return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${RISK_BADGE_STYLES[riskLabel]}`}>{RISK_LABEL_TEXT[riskLabel]}</span>
}

function CounselorInbox({ role, sessionToken, onLogout }) {
	const navigate = useNavigate()
	const [items, setItems] = useState([])
	const [loading, setLoading] = useState(true)
	const [refreshing, setRefreshing] = useState(false)
	const [error, setError] = useState('')

	const loadInbox = useCallback(async (showRefresh = false) => {
		if (showRefresh) {
			setRefreshing(true)
		} else {
			setLoading(true)
		}
		setError('')
		try {
			let data
			try {
				data = await getCounselorInbox(sessionToken)
			} catch {
				data = await getCounselorInbox(sessionToken)
			}
			setItems(data.items || [])
		} catch {
			setError('Could not refresh inbox right now. Showing last loaded data.')
		} finally {
			setLoading(false)
			if (showRefresh) {
				setRefreshing(false)
			}
		}
	}, [sessionToken])

	useEffect(() => {
		Promise.resolve().then(() => loadInbox())
		return undefined
	}, [loadInbox])

	const formatTime = (timestamp) => {
		return formatIstDateTime(timestamp)
	}

	const inboxItems = useMemo(() => items, [items])

	const openItem = async (item) => {
		setError('')
		if (item.type === 'high_risk_post') {
			if (item.post_id) {
				navigate(`/counselor/feed?postId=${encodeURIComponent(item.post_id)}`)
			} else {
				navigate('/counselor/feed')
			}
			return
		}
		if (item.type === 'student_message') {
			if (item.chat_id) {
				navigate(`/counselor/chats?chatId=${encodeURIComponent(item.chat_id)}`)
				return
			}
			if (item.student_uuid) {
				try {
					const result = await openCounselorChatByUuid(item.student_uuid, sessionToken)
					const chatId = result?.chat?.chat_id
					if (chatId) {
						navigate(`/counselor/chats?chatId=${encodeURIComponent(chatId)}`)
						return
					}
				} catch {
					setError('Could not open this chat right now.')
					return
				}
			}
			setError('Could not open this chat right now.')
		}
	}

	const openChatWithUuid = async (event, studentUuid) => {
		event.stopPropagation()
		if (!studentUuid) {
			return
		}
		setError('')
		try {
			const result = await openCounselorChatByUuid(studentUuid, sessionToken)
			const chatId = result?.chat?.chat_id
			if (chatId) {
				navigate(`/counselor/chats?chatId=${encodeURIComponent(chatId)}`)
				return
			}
			setError('Could not open this chat right now.')
		} catch {
			setError('Could not open this chat right now.')
		}
	}

	return (
		<CounselorLayout role={role} onLogout={onLogout}>
			<Card className="space-y-4">
				<div className="flex items-center justify-between gap-3 flex-wrap">
					<h1 className="text-2xl font-semibold text-[#5f4d73]">Inbox</h1>
					<Button type="button" onClick={() => loadInbox(true)} disabled={refreshing} className="!h-10 !px-4 !text-xs !mb-0">
						{refreshing ? 'Refreshing...' : 'Refresh inbox'}
					</Button>
				</div>
				<p className="text-sm text-[#8e7d9f]">New high-risk posts and student message alerts.</p>
			</Card>

			{loading && items.length === 0 && (
				<Card>
					<p className="text-sm text-[#8e7d9f]">Loading inbox...</p>
				</Card>
			)}

			{error && (
				<Card>
					<p className="text-sm text-[#a16788]">{error}</p>
				</Card>
			)}

			{!loading && (
				<section className="counselor-chat-selector-panel overflow-hidden border border-[#eadcf8]">
					{inboxItems.length === 0 ? (
						<Card>
							<p className="text-sm text-[#8e7d9f]">No inbox alerts yet.</p>
						</Card>
					) : (
						inboxItems.map((item) => {
							const isPost = item.type === 'high_risk_post'
							return (
								<button
									key={item.id}
									type="button"
									onClick={() => {
										void openItem(item)
									}}
									className={`counselor-chat-selector w-full text-left px-4 py-3 ${!isPost ? 'is-unseen' : ''}`}
								>
									<p className={`text-[11px] font-semibold uppercase tracking-wide ${isPost ? 'text-[#a23434]' : 'text-[#6d5b87]'}`}>
										{item.kind_label || (isPost ? 'Post' : 'Message')}
									</p>
									<div className="flex items-center justify-between gap-3">
										<p className={`text-sm font-semibold ${isPost ? 'text-[#a23434]' : 'text-[#5f4d73]'} truncate`}>
											{isPost ? 'HIGH-RISK POST ALERT' : ''}
											{item.student_uuid ? (
												<span
													onClick={(event) => openChatWithUuid(event, item.student_uuid)}
													className="text-[#7d63a3] hover:text-[#5f4d73] underline underline-offset-2"
												>
													{item.student_uuid}
												</span>
											) : (
												'Unknown UUID'
											)}
											{!isPost ? ' has messaged you' : ''}
										</p>
										<div className="flex items-center gap-2 shrink-0">
											{item.risk_label && <RiskBadge label={item.risk_label} />}
											{!isPost && item.unseen_count > 0 && <span className="counselor-chat-unseen-count">{item.unseen_count}</span>}
											<p className="text-xs text-[#8e7d9f]">{formatTime(item.timestamp)}</p>
										</div>
									</div>
									<p className={`mt-1 text-sm truncate ${isPost ? 'text-[#7f4d4d]' : 'text-[#7f6e91]'}`}>
										{isPost ? item.content || 'Open to review the flagged post.' : 'Open chat to view unread messages.'}
									</p>
								</button>
							)
						})
					)}
				</section>
			)}
		</CounselorLayout>
	)
}

export default CounselorInbox
