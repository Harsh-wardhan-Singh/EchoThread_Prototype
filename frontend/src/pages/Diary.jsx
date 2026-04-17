import { useState } from 'react'
import Navbar from '../components/Navbar'
import MoodTracker from '../components/MoodTracker'
import { analyzeDiary } from '../services/api'

function Diary({ role, email, onLogout }) {
	const [text, setText] = useState('')
	const [result, setResult] = useState(null)
	const [loading, setLoading] = useState(false)

	const handleAnalyze = async (event) => {
		event.preventDefault()
		if (!text.trim()) {
			return
		}
		setLoading(true)
		try {
			const data = await analyzeDiary(email, text.trim())
			setResult(data)
			setText('')
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="min-h-screen bg-slate-100">
			<Navbar role={role} onLogout={onLogout} />
			<main className="mx-auto max-w-4xl p-4">
				<section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
					<h1 className="text-xl font-semibold text-slate-900">Private Diary</h1>
					<p className="text-sm text-slate-600 mt-1">Write your thoughts and get AI emotion analysis.</p>

					<form className="mt-4" onSubmit={handleAnalyze}>
						<textarea
							rows={5}
							value={text}
							onChange={(event) => setText(event.target.value)}
							placeholder="How are you feeling today?"
							className="w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						/>
						<button
							type="submit"
							disabled={loading}
							className="mt-3 rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-60"
						>
							{loading ? 'Analyzing...' : 'Analyze & Save'}
						</button>
					</form>

					<MoodTracker result={result} />
				</section>
			</main>
		</div>
	)
}

export default Diary
