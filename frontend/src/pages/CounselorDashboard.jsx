import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import { getFlaggedPosts } from '../services/api'
import { Card, Section, Textarea } from '../components/ui/Primitives'

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
		<div className="space-y-4 safe-fade-slide">
			<Navbar role={role} onLogout={onLogout} />
			<main className="space-y-4">
				<Card className="space-y-2">
					<h1 className="text-2xl font-semibold text-[#5f4d73]">Care dashboard</h1>
					<p className="text-sm text-[#8e7d9f]">Posts that may need compassionate follow-up.</p>
				</Card>

				<section className="space-y-4">
					{posts.map((post) => (
						<Card key={post.id} className="space-y-4">
							<div className="flex flex-wrap items-center gap-2">
								<span className="safe-chip">
									{post.risk === 'HIGH' ? 'High Risk' : 'Medium Risk'}
								</span>
								<span className="safe-chip">Needs Attention</span>
							</div>

							<p className="text-[#5f4d73] leading-relaxed">{post.content}</p>
							<p className="text-xs text-[#9382a6] capitalize">
								{post.sentiment} • {post.emotion}
							</p>

							<Section className="p-3 sm:p-4">
								<p className="text-xs text-[#9585a9] mb-2">Counselor Response Draft</p>
								<Textarea
									rows={2}
									placeholder="Write a short, supportive response..."
									className="min-h-[92px]"
								/>
							</Section>
						</Card>
					))}

					{posts.length === 0 && (
						<Card className="text-sm text-[#8e7d9f]">
							No flagged posts found.
						</Card>
					)}
				</section>
			</main>
		</div>
	)
}

export default CounselorDashboard
