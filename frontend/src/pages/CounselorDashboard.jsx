import { useEffect, useState } from 'react'
import {
	ArcElement,
	BarElement,
	CategoryScale,
	Chart as ChartJS,
	Legend,
	LineElement,
	LinearScale,
	PointElement,
	Title,
	Tooltip,
} from 'chart.js'
import { Bar, Line, Pie } from 'react-chartjs-2'
import Navbar from '../components/Navbar'
import { getCounselorPulse } from '../services/api'
import { Card, Section } from '../components/ui/Primitives'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend)

function Metric({ label, value }) {
	return (
		<Section className="!rounded-md p-4">
			<p className="text-xs text-[#9e8db0]">{label}</p>
			<p className="mt-1 text-xl font-semibold text-[#5f4d73]">{value}</p>
		</Section>
	)
}

function CounselorDashboard({ role, sessionToken, onLogout }) {
	const [pulse, setPulse] = useState(null)

	useEffect(() => {
		async function loadPulse() {
			const data = await getCounselorPulse(sessionToken)
			setPulse(data)
		}
		loadPulse()
	}, [sessionToken])

	if (!pulse) {
		return (
			<div className="h-full min-h-0 flex flex-col safe-fade-slide overflow-hidden">
				<div className="z-20">
					<Navbar role={role} onLogout={onLogout} />
				</div>
				<main className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-4">
					<Card className="text-sm text-[#8e7d9f]">Loading counselor pulse analytics...</Card>
				</main>
			</div>
		)
	}

	const labels = (pulse.overall_stress_series || []).map((item) => item.day)
	const chartOptions = {
		responsive: true,
		maintainAspectRatio: false,
		scales: {
			x: { grid: { display: false }, ticks: { color: '#8f7fa1' } },
			y: { beginAtZero: true, ticks: { color: '#8f7fa1' }, grid: { color: 'rgba(210, 189, 231, 0.2)' } },
		},
		plugins: { legend: { labels: { color: '#7f6e91' } } },
	}

	const overallStressData = {
		labels,
		datasets: [
			{
				label: 'Campus stress score',
				data: (pulse.overall_stress_series || []).map((item) => item.score),
				borderColor: '#9b70d6',
				backgroundColor: 'rgba(155, 112, 214, 0.14)',
				tension: 0.35,
				pointRadius: 4,
			},
		],
	}

	const postsData = {
		labels,
		datasets: [
			{
				label: 'Posts',
				data: (pulse.posts_series || []).map((item) => item.count),
				backgroundColor: '#f3b5d3',
				borderRadius: 8,
			},
		],
	}

	const sentimentData = {
		labels,
		datasets: [
			{
				label: 'Positive sentiment',
				data: (pulse.sentiment_series || []).map((item) => item.positive),
				borderColor: '#4caf50',
				backgroundColor: 'rgba(76, 175, 80, 0.15)',
				tension: 0.35,
				pointRadius: 4,
			},
			{
				label: 'Negative sentiment',
				data: (pulse.sentiment_series || []).map((item) => item.negative),
				borderColor: '#e24b4b',
				backgroundColor: 'rgba(226, 75, 75, 0.15)',
				tension: 0.35,
				pointRadius: 4,
			},
		],
	}

	const emotionData = {
		labels: (pulse.emotion_distribution || []).map((item) => item.emotion),
		datasets: [
			{
				data: (pulse.emotion_distribution || []).map((item) => item.count),
				backgroundColor: ['#f6aac8', '#ccb8ff', '#9b70d6', '#86c7ff', '#ffd28e', '#9adab5', '#f7a7a7', '#c3b8aa'],
			},
		],
	}

	const totalPosts = (pulse.posts_series || []).reduce((sum, item) => sum + item.count, 0)
	const avgCampusStress = (pulse.overall_stress_series || []).length
		? Math.round((pulse.overall_stress_series || []).reduce((sum, item) => sum + (item.score || 0), 0) / pulse.overall_stress_series.length)
		: 0

	return (
		<div className="h-full min-h-0 flex flex-col safe-fade-slide overflow-hidden">
			<div className="z-20">
				<Navbar role={role} onLogout={onLogout} />
			</div>
			<main className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-4 space-y-4">
				<Card className="space-y-2">
					<h1 className="text-2xl font-semibold text-[#5f4d73]">Campus pulse analytics</h1>
					<p className="text-sm text-[#8e7d9f]">7-day counselor report built only from community feed posts.</p>
				</Card>

				<section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
					<Metric label="Current Students" value={pulse.total_students} />
					<Metric label="7-Day Posts" value={totalPosts} />
					<Metric label="High Risk Posts" value={pulse.risk_counts?.HIGH ?? 0} />
					<Metric label="Avg Campus Stress" value={`${avgCampusStress}%`} />
				</section>

				<section className="grid grid-cols-1 xl:grid-cols-2 gap-4">
					<Card className="space-y-2 !rounded-md">
						<p className="text-sm text-[#8e7d9f]">Overall campus stress (last 7 days)</p>
						<div className="h-[280px]">
							<Line data={overallStressData} options={chartOptions} />
						</div>
					</Card>

					<Card className="space-y-2 !rounded-md">
						<p className="text-sm text-[#8e7d9f]">Number of posts (last 7 days)</p>
						<div className="h-[280px]">
							<Bar data={postsData} options={{ ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: false } } }} />
						</div>
					</Card>

					<Card className="space-y-2 !rounded-md">
						<p className="text-sm text-[#8e7d9f]">Campus positive vs negative sentiment</p>
						<div className="h-[280px]">
							<Line data={sentimentData} options={chartOptions} />
						</div>
					</Card>

					<Card className="space-y-2 !rounded-md">
						<p className="text-sm text-[#8e7d9f]">Emotion distribution</p>
						<div className="h-[280px]">
							<Pie data={emotionData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#7f6e91' } } } }} />
						</div>
					</Card>
				</section>

				<section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
					<Card className="space-y-2 !rounded-md">
						<p className="text-sm font-semibold text-[#5f4d73]">Risk distribution (posts)</p>
						<div className="grid grid-cols-3 gap-2">
							<Section className="!rounded-md p-3 text-center">
								<p className="text-xs text-[#9e8db0]">LOW</p>
								<p className="text-lg font-semibold text-[#5f4d73]">{pulse.risk_counts?.LOW ?? 0}</p>
							</Section>
							<Section className="!rounded-md p-3 text-center">
								<p className="text-xs text-[#9e8db0]">MEDIUM</p>
								<p className="text-lg font-semibold text-[#5f4d73]">{pulse.risk_counts?.MEDIUM ?? 0}</p>
							</Section>
							<Section className="!rounded-md p-3 text-center">
								<p className="text-xs text-[#9e8db0]">HIGH</p>
								<p className="text-lg font-semibold text-[#5f4d73]">{pulse.risk_counts?.HIGH ?? 0}</p>
							</Section>
						</div>
					</Card>

					<Card className="space-y-2 !rounded-md">
						<p className="text-sm font-semibold text-[#5f4d73]">7-day analytical report</p>
						<ul className="space-y-2 text-sm text-[#7f6e91]">
							{(pulse.analytics_summary || []).map((line, index) => (
								<li key={`insight-${index}`} className="rounded-md bg-white/70 px-3 py-2">{line}</li>
							))}
						</ul>
					</Card>
				</section>
			</main>
		</div>
	)
}

export default CounselorDashboard
