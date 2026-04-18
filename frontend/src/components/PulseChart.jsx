import {
	CategoryScale,
	Chart as ChartJS,
	Legend,
	LinearScale,
	BarElement,
	Title,
	Tooltip,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

function PulseChart({ activity = [] }) {
	const labels = activity.map((item) => item.date)
	const values = activity.map((item) => item.count)

	const data = {
		labels,
		datasets: [
			{
				label: 'Activity',
				data: values,
				backgroundColor: '#f3b5d3',
				borderRadius: 0,
			},
		],
	}

	const options = {
		responsive: true,
		plugins: {
			legend: { display: false },
			title: { display: true, text: '7-Day Campus Activity' },
		},
		scales: {
			x: {
				grid: { display: false },
				ticks: { color: '#9b8caf' },
			},
			y: {
				grid: { color: 'rgba(210, 189, 231, 0.2)' },
				ticks: { color: '#9b8caf' },
			},
		},
	}

	return (
		<div className="safe-card !rounded-md !p-4 sm:!p-5">
			<Bar options={options} data={data} />
		</div>
	)
}

export default PulseChart
