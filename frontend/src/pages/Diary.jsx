import { useEffect, useMemo, useState } from 'react'
import MoodTracker from '../components/MoodTracker'
import StudentLayout from '../components/StudentLayout'
import { analyzeDiary, createPost, getDiaryWeek, sendStudentCounselorMessage } from '../services/api'
import { Button, Card, Section, Textarea } from '../components/ui/Primitives'

function Diary({ role, email, sessionToken, onLogout }) {
	const [text, setText] = useState('')
	const [result, setResult] = useState(null)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState('')
	const [weekData, setWeekData] = useState(null)
	const [weekLoading, setWeekLoading] = useState(false)
	const [suggestionOpen, setSuggestionOpen] = useState(false)
	const [suggestionText, setSuggestionText] = useState('')
	const [actionLoading, setActionLoading] = useState(false)
	const [actionFeedback, setActionFeedback] = useState('')

	const refreshWeek = async () => {
		if (!email || !sessionToken) {
			return
		}
		setWeekLoading(true)
		try {
			const data = await getDiaryWeek(email, sessionToken)
			setWeekData(data)
		} catch (requestError) {
			if (requestError?.response?.status === 401 || requestError?.response?.status === 403) {
				setError('Your session expired. Please log in again.')
			} else {
				setError('Could not load your weekly check-in history right now.')
			}
		} finally {
			setWeekLoading(false)
		}
	}

	useEffect(() => {
		if (!email || !sessionToken) {
			return
		}

		let isCancelled = false
		Promise.resolve()
			.then(async () => {
				if (isCancelled) {
					return
				}
				setWeekLoading(true)
				const data = await getDiaryWeek(email, sessionToken)
				if (!isCancelled) {
					setWeekData(data)
				}
			})
			.catch((requestError) => {
				if (!isCancelled) {
					if (requestError?.response?.status === 401 || requestError?.response?.status === 403) {
						setError('Your session expired. Please log in again.')
					} else {
						setError('Could not load your weekly check-in history right now.')
					}
				}
			})
			.finally(() => {
				if (!isCancelled) {
					setWeekLoading(false)
				}
			})

		return () => {
			isCancelled = true
		}
	}, [email, sessionToken])

	const canSubmitToday = useMemo(() => {
		if (!weekData) {
			return true
		}
		return Boolean(weekData.can_submit_today)
	}, [weekData])

	const supportMessage = result?.support_message || ''

	const handleAnalyze = async (event) => {
		event.preventDefault()
		if (!canSubmitToday) {
			setError('You already checked in today. You can submit again tomorrow.')
			return
		}
		if (!text.trim()) {
			return
		}
		setLoading(true)
		setError('')
		try {
			const submittedText = text.trim()
			const data = await analyzeDiary(email, submittedText, sessionToken)
			setResult(data)
			setText('')
			setSuggestionText(submittedText)
			setSuggestionOpen(true)
			setActionFeedback('')
			await refreshWeek()
		} catch (requestError) {
			if (requestError?.response?.status === 409) {
				setError('You already checked in today. You can submit again tomorrow.')
			} else if (requestError?.response?.status === 401 || requestError?.response?.status === 403) {
				setError('Your session expired. Please log in again.')
			} else {
				setError('Could not process your entry right now. Please try once more.')
			}
		} finally {
			setLoading(false)
		}
	}

	const handleSendToCounselor = async () => {
		if (!suggestionText.trim()) {
			return
		}
		setActionLoading(true)
		setActionFeedback('')
		try {
			await sendStudentCounselorMessage(`[From: Diary] ${suggestionText.trim()}`, sessionToken)
			setActionFeedback('Sent to counselor chat.')
		} catch {
			setActionFeedback('Could not send to counselor right now.')
		} finally {
			setActionLoading(false)
		}
	}

	const handleTurnIntoPost = async () => {
		if (!suggestionText.trim()) {
			return
		}
		setActionLoading(true)
		setActionFeedback('')
		try {
			await createPost(suggestionText.trim(), sessionToken)
			setActionFeedback('Posted to feed.')
		} catch {
			setActionFeedback('Could not create post right now.')
		} finally {
			setActionLoading(false)
		}
	}

	return (
		<StudentLayout role={role} onLogout={onLogout}>
			<div className="space-y-4">
				<Card className="space-y-2.5">
					<div className="flex items-center justify-between gap-3 flex-wrap">
						<h2 className="text-lg font-semibold text-[#5f4d73]">Weekly check-in tracker</h2>
						<p className="text-xs text-[#8e7d9f]">
							{weekData ? `${weekData.submitted_days}/7 days submitted` : 'Loading...'}
						</p>
					</div>
					<div className="relative pt-1 pb-0.5">
						<div className="absolute left-[7%] right-[7%] top-[17px] h-[2px] bg-[#ddd2eb]" />
						<div className="grid grid-cols-7 gap-1.5 relative z-10">
						{(weekData?.days || []).map((day) => (
							<div key={day.date} className="flex flex-col items-center gap-2">
								<div
									className={`w-7 h-7 rounded-full border flex items-center justify-center shadow-sm ${
										day.submitted
											? 'bg-[#efe8ff] border-[#ccb8ff]'
											: 'bg-white/80 border-[#dfd4ea]'
									}`}
								>
									{day.submitted ? <span className="text-xs leading-none">🌸</span> : <span className="w-1.5 h-1.5 rounded-full bg-[#c7b7d9]" />}
								</div>
								<div className="text-center">
									<p className="text-xs font-semibold text-[#74638a] leading-none">{day.weekday}</p>
									<p className="text-[10px] text-[#9a8aac] mt-0.5">{day.date.slice(5)}</p>
								</div>
							</div>
						))}
						</div>
					</div>
					{weekLoading && <p className="text-sm text-[#8e7d9f]">Refreshing your week...</p>}
				</Card>

				<Card className="space-y-4">
					<h1 className="text-2xl font-semibold text-[#5f4d73]">Your private journal</h1>
					<p className="text-sm text-[#8e7d9f]">Write freely. This is your personal safe space, visible only to you.</p>

					<form className="space-y-3" onSubmit={handleAnalyze}>
						<Textarea
							rows={8}
							value={text}
							onChange={(event) => setText(event.target.value)}
							placeholder="How are you feeling today?"
							className="min-h-[190px]"
							disabled={!canSubmitToday || loading}
						/>
						<Button type="submit" disabled={loading || !canSubmitToday}>
							{loading ? 'Saving...' : 'Save your thoughts'}
						</Button>
						{!canSubmitToday && <p className="text-sm text-[#7f6e91]">You already checked in today. Come back tomorrow.</p>}
						{error && <p className="text-sm text-[#a16788]">{error}</p>}
					</form>

					<MoodTracker result={result} />

					{suggestionOpen && Boolean(suggestionText) && (
						<Section className="!rounded-md p-4 space-y-3">
							<div className="flex items-start justify-between gap-3">
								<div>
									<p className="text-sm font-semibold text-[#5f4d73]">Would you like to share this?</p>
									<p className="text-xs text-[#8e7d9f] mt-1">You can send your check-in text to the counselor or turn it into a post.</p>
								</div>
								<button
									type="button"
									onClick={() => setSuggestionOpen(false)}
									className="text-[#9a8aac] hover:text-[#6f5f83] leading-none text-lg"
									aria-label="Close suggestion"
								>
									×
								</button>
							</div>

							{supportMessage && (
								<div className="rounded-xl border border-[#f4c7d9] bg-[#fff3f8] px-3 py-2">
									<p className="text-sm text-[#8d4d6d] leading-relaxed">{supportMessage}</p>
								</div>
							)}

							<div className="flex flex-wrap gap-2">
								<Button type="button" onClick={handleSendToCounselor} disabled={actionLoading} className="!h-10 !mb-0">
									Send this to counselor
								</Button>
								<Button type="button" onClick={handleTurnIntoPost} disabled={actionLoading} className="!h-10 !mb-0">
									Turn this into a post
								</Button>
							</div>

							{actionFeedback && <p className="text-sm text-[#7f6e91]">{actionFeedback}</p>}
						</Section>
					)}
				</Card>
			</div>
		</StudentLayout>
	)
}

export default Diary
