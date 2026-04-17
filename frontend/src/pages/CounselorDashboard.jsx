import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import { getFlaggedPosts } from '../services/api'

function CounselorDashboard({ role, onLogout }) {
	const [posts, setPosts] = useState([])

	useEffect(() => {
		async function loadFlagged() {
			const data = await getFlaggedPosts()
			setPosts(data)
		}
		loadFlagged()
	}, [])

	return (
		<div className="min-h-screen bg-slate-100">
			<Navbar role={role} onLogout={onLogout} />
			<main className="mx-auto max-w-6xl p-4">
				<h1 className="text-2xl font-semibold text-slate-900">Counselor Dashboard</h1>
				<p className="text-sm text-slate-600 mt-1">Flagged posts requiring attention.</p>

				<section className="mt-4 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
					<table className="min-w-full text-sm">
						<thead className="bg-slate-50 text-slate-600">
							<tr>
								<th className="px-4 py-3 text-left">Post</th>
								<th className="px-4 py-3 text-left">Risk</th>
								<th className="px-4 py-3 text-left">Sentiment</th>
								<th className="px-4 py-3 text-left">Emotion</th>
							</tr>
						</thead>
						<tbody>
							{posts.map((post) => (
								<tr key={post.id} className="border-t border-slate-100">
									<td className="px-4 py-3 text-slate-800">{post.content}</td>
									<td className="px-4 py-3 font-medium text-slate-800">{post.risk}</td>
									<td className="px-4 py-3 capitalize text-slate-700">{post.sentiment}</td>
									<td className="px-4 py-3 capitalize text-slate-700">{post.emotion}</td>
								</tr>
							))}
							{posts.length === 0 && (
								<tr>
									<td className="px-4 py-4 text-slate-500" colSpan={4}>
										No flagged posts found.
									</td>
								</tr>
							)}
						</tbody>
					</table>
				</section>
			</main>
		</div>
	)
}

export default CounselorDashboard
