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
				backgroundColor: '#4f46e5',
			},
		],
	}

	const options = {
		responsive: true,
		plugins: {
			legend: { display: false },
			title: { display: true, text: '7-Day Campus Activity' },
		},
	}

	return (
		<div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
			<Bar options={options} data={data} />
		</div>
	)
}

export default PulseChart
