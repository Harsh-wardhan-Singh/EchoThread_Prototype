import { useEffect, useState } from 'react'
import PulseChart from '../components/PulseChart'
import StudentLayout from '../components/StudentLayout'
import { getPulse } from '../services/api'
import { Card, Section } from '../components/ui/Primitives'

function Metric({ label, value }) {
	return (
		<Section className="!rounded-md p-4">
			<p className="text-xs text-[#9e8db0]">{label}</p>
			<p className="mt-1 text-xl font-semibold text-[#5f4d73]">{value}</p>
		</Section>
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
		return (
			<StudentLayout role={role} onLogout={onLogout}>
				<div className="space-y-4">
					<Card>
						<p className="text-sm text-[#8e7d9f]">Loading your pulse reflections...</p>
					</Card>
				</div>
			</StudentLayout>
		)
	}

	return (
		<StudentLayout role={role} onLogout={onLogout}>
			<div className="space-y-4">
				<Card className="space-y-2">
					<h1 className="text-2xl font-semibold text-[#5f4d73]">Pulse reflection</h1>
					<p className="text-sm text-[#8e7d9f]">A soft weekly snapshot of your emotional rhythm.</p>
				</Card>

				<section className="grid grid-cols-2 gap-3">
					<Metric label="Total Posts" value={pulse.total_posts} />
					<Metric label="Diary Entries" value={pulse.total_diary_entries} />
					<Metric label="Low Mood" value={pulse.sentiment_distribution.negative} />
					<Metric label="High Risk" value={pulse.risk_distribution.HIGH} />
				</section>

				<section className="space-y-3">
					<Section className="!rounded-md p-4 text-sm text-[#8e7d9f]">Weekly activity trend</Section>
					<PulseChart activity={pulse.seven_day_activity} />
				</section>
			</div>
		</StudentLayout>
	)
}

export default PulseDashboard
