import { useEffect, useState } from 'react'
import {
	CategoryScale,
	Chart as ChartJS,
	Legend,
	LineElement,
	LinearScale,
	PointElement,
	Title,
	Tooltip,
	BarElement,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import StudentLayout from '../components/StudentLayout'
import { getStudentPulse } from '../services/api'
import { Card, Section } from '../components/ui/Primitives'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend)

function Metric({ label, value }) {
	return (
		<Section className="!rounded-md p-4">
			<p className="text-xs text-[#9e8db0]">{label}</p>
			<p className="mt-1 text-xl font-semibold text-[#5f4d73]">{value}</p>
		</Section>
	)
}

function PulseDashboard({ role, email, userUuid, sessionToken, onLogout }) {
	const [pulse, setPulse] = useState(null)

	useEffect(() => {
		async function loadPulse() {
			const data = await getStudentPulse(email, userUuid, sessionToken)
			setPulse(data)
		}
		loadPulse()
	}, [email, userUuid, sessionToken])

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

	const labels = (pulse.stress_series || []).map((item) => item.day)
	const stressData = {
		labels,
		datasets: [
			{
				label: 'Stress score',
				data: (pulse.stress_series || []).map((item) => item.score),
				borderColor: '#d184c6',
				backgroundColor: 'rgba(209, 132, 198, 0.18)',
				tension: 0.35,
				pointRadius: 4,
			},
		],
	}

	const previousWeekLabels = (pulse.previous_week_history || []).map((item) => item.day)
	const previousWeekData = {
		labels: previousWeekLabels,
		datasets: [
			{
				label: 'Previous week sentiment',
				data: (pulse.previous_week_history || []).map((item) => (item.sentiment ? 1 : null)),
				backgroundColor: (pulse.previous_week_history || []).map((item) => {
					if (item.sentiment === 'positive') return '#4caf50'
					if (item.sentiment === 'negative') return '#e24b4b'
					if (item.sentiment === 'neutral') return '#9ea0a6'
					return 'rgba(0,0,0,0)'
				}),
				borderRadius: 8,
			},
		],
	}

	const commonOptions = {
		responsive: true,
		maintainAspectRatio: false,
		scales: {
			x: { grid: { display: false }, ticks: { color: '#8f7fa1' } },
			y: { beginAtZero: true, max: 1, ticks: { color: '#8f7fa1' }, grid: { color: 'rgba(210, 189, 231, 0.2)' } },
		},
		plugins: {
			legend: { labels: { color: '#7f6e91' } },
		},
	}

	const weeklyCheckins = pulse.checkin_days || (pulse.stress_series || []).filter((item) => item.score > 0).length
	const stressSeries = pulse.stress_series || []
	const checkinStressSeries = stressSeries.filter((item) => item.score > 0)
	const highestStressDay = checkinStressSeries.length
		? checkinStressSeries.reduce((highest, current) => (current.score > highest.score ? current : highest), checkinStressSeries[0]).day
		: '-'
	const lowestStressDay = checkinStressSeries.length
		? checkinStressSeries.reduce((lowest, current) => (current.score < lowest.score ? current : lowest), checkinStressSeries[0]).day
		: '-'

	return (
		<StudentLayout role={role} onLogout={onLogout}>
			<div className="space-y-4">
				<Card className="space-y-2">
					<h1 className="text-2xl font-semibold text-[#5f4d73]">Pulse reflection</h1>
					<p className="text-sm text-[#8e7d9f]">{pulse.message}</p>
				</Card>

				<section className="grid grid-cols-2 gap-3">
					<Metric label="Average Stress" value={pulse.avg_stress_level || 'LOW'} />
					<Metric label="Check-ins (7 days)" value={weeklyCheckins} />
					<Metric label="Highest Stress Day" value={highestStressDay} />
					<Metric label="Lowest Stress Day" value={lowestStressDay} />
				</section>

				<section className="space-y-4">
					<Section className="!rounded-md p-4 text-sm text-[#8e7d9f]">Stress levels over the last 7 days</Section>
					<Card className="!rounded-md !p-4 h-[260px]">
						<Line data={stressData} options={{ ...commonOptions, plugins: { ...commonOptions.plugins, legend: { display: false } } }} />
					</Card>

					<Section className="!rounded-md p-4 text-sm text-[#8e7d9f]">Previous week history sentiment</Section>
					<Card className="!rounded-md !p-4 h-[280px]">
						<Bar
							data={previousWeekData}
							options={{
								...commonOptions,
								plugins: {
									...commonOptions.plugins,
									legend: { display: false },
									tooltip: {
										callbacks: {
											label: (context) => {
												const entry = (pulse.previous_week_history || [])[context.dataIndex]
												if (!entry || !entry.sentiment) {
													return 'No check-in'
												}
												const text = entry.text || 'No text'
												return `${entry.sentiment}: ${text}`
											},
										},
									},
								},
								scales: {
									...commonOptions.scales,
									y: {
										...commonOptions.scales.y,
										max: 1,
										ticks: { display: false },
									},
								},
							}}
						/>
					</Card>
				</section>
			</div>
		</StudentLayout>
	)
}

export default PulseDashboard
