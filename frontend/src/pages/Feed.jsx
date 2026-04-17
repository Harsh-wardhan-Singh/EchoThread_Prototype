import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar'
import PostCard from '../components/PostCard'
import { createPost, getPosts } from '../services/api'

function Feed({ role, onLogout }) {
	const [posts, setPosts] = useState([])
	const [content, setContent] = useState('')
	const [loading, setLoading] = useState(false)

	useEffect(() => {
		let mounted = true
		getPosts().then((data) => {
			if (mounted) {
				setPosts(data)
			}
		})
		return () => {
			mounted = false
		}
	}, [])

	const handleCreate = async (event) => {
		event.preventDefault()
		if (!content.trim()) {
			return
		}
		setLoading(true)
		try {
			await createPost(content.trim())
			setContent('')
			const data = await getPosts()
			setPosts(data)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="min-h-screen bg-slate-100">
			<Navbar role={role} onLogout={onLogout} />
			<main className="mx-auto max-w-4xl p-4 space-y-4">
				<section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
					<h1 className="text-xl font-semibold text-slate-900">Anonymous Feed</h1>
					<p className="text-sm text-slate-600 mt-1">Share thoughts anonymously with your campus.</p>
					<form className="mt-4" onSubmit={handleCreate}>
						<textarea
							rows={4}
							value={content}
							onChange={(event) => setContent(event.target.value)}
							placeholder="Write an anonymous post..."
							className="w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						/>
						<button
							type="submit"
							disabled={loading}
							className="mt-3 rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-60"
						>
							{loading ? 'Posting...' : 'Post'}
						</button>
					</form>
				</section>

				<section className="space-y-3">
					{posts.map((post) => (
						<PostCard key={post.id} post={post} />
					))}
				</section>
			</main>
		</div>
	)
}

export default Feed
