import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import PulseChart from '../components/PulseChart'
import { getPulse } from '../services/api'

function Metric({ label, value }) {
	return (
		<div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
			<p className="text-sm text-slate-500">{label}</p>
			<p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
		</div>
	)
}

function PulseDashboard({ role, onLogout }) {
	const [pulse, setPulse] = useState(null)

	useEffect(() => {
		async function loadPulse() {
			const data = await getPulse()
			setPulse(data)
		}
		loadPulse()
	}, [])

	if (!pulse) {
		return null
	}

	return (
		<div className="min-h-screen bg-slate-100">
			<Navbar role={role} onLogout={onLogout} />
			<main className="mx-auto max-w-6xl p-4 space-y-4">
				<h1 className="text-2xl font-semibold text-slate-900">Campus Pulse Dashboard</h1>

				<section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
					<Metric label="Total Posts" value={pulse.total_posts} />
					<Metric label="Diary Entries" value={pulse.total_diary_entries} />
					<Metric label="Negative Sentiment" value={pulse.sentiment_distribution.negative} />
					<Metric label="High Risk" value={pulse.risk_distribution.HIGH} />
				</section>

				<PulseChart activity={pulse.seven_day_activity} />
			</main>
		</div>
	)
}

export default PulseDashboard
