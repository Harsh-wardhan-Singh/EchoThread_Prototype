import { useCallback, useEffect, useState } from 'react'
import PostCard from '../components/PostCard'
import StudentLayout from '../components/StudentLayout'
import { mockPosts } from '../data/mockData'
import { createPost, createPostComment, createPostReply, getPosts } from '../services/api'
import { Button, Card, Textarea } from '../components/ui/Primitives'

function Feed({ role, sessionToken, onLogout }) {
	const [posts, setPosts] = useState(mockPosts)
	const [content, setContent] = useState('')
	const [loading, setLoading] = useState(false)
	const [initialLoading, setInitialLoading] = useState(true)
	const [refreshing, setRefreshing] = useState(false)

	const loadPosts = useCallback(async (showRefreshState = false) => {
		if (showRefreshState) {
			setRefreshing(true)
		}
		try {
			const data = await getPosts()
			if (Array.isArray(data) && data.length > 0) {
				setPosts(data)
			} else {
				setPosts(mockPosts)
			}
		} catch {
			setPosts(mockPosts)
		} finally {
			setInitialLoading(false)
			if (showRefreshState) {
				setRefreshing(false)
			}
		}
	}, [])

	useEffect(() => {
		Promise.resolve().then(() => loadPosts())
		return undefined
	}, [loadPosts])

	const handleCreate = async (event) => {
		event.preventDefault()
		if (!content.trim()) {
			return
		}
		setLoading(true)
		try {
			await createPost(content.trim(), sessionToken)
			setContent('')
			await loadPosts(true)
		} finally {
			setLoading(false)
		}
	}

	const handleAddComment = async (postId, content) => {
		await createPostComment(postId, content, sessionToken)
		await loadPosts(true)
	}

	const handleAddReply = async (postId, commentId, content) => {
		await createPostReply(postId, commentId, content, sessionToken)
		await loadPosts(true)
	}

	const handleManualRefresh = async () => {
		await loadPosts(true)
	}

	return (
		<StudentLayout role={role} onLogout={onLogout}>
			<div className="space-y-4">
				<Card className="space-y-4">
					<div className="flex items-center justify-between gap-3 flex-wrap">
						<h1 className="text-2xl font-semibold text-[#5f4d73]">Community reflections</h1>
						<Button type="button" onClick={handleManualRefresh} disabled={refreshing} className="!h-10 !px-4 !text-xs !mb-0">
							{refreshing ? 'Refreshing...' : 'Refresh posts'}
						</Button>
					</div>
					<p className="text-sm text-[#8e7d9f]">A gentle stream of anonymous student thoughts.</p>
					<form className="mt-4" onSubmit={handleCreate}>
						<Textarea
							rows={4}
							value={content}
							onChange={(event) => setContent(event.target.value)}
							placeholder="Write an anonymous post..."
							className="min-h-[112px]"
						/>
						<Button type="submit" disabled={loading} className="mt-3">
							{loading ? 'Posting...' : 'Post'}
						</Button>
					</form>
				</Card>

				{initialLoading && (
					<Card>
						<p className="text-sm text-[#8e7d9f]">Posts are loading...</p>
					</Card>
				)}

				{!initialLoading && <p className="text-xs text-[#9b8dae] px-1">Posts refresh only when you click Refresh or submit.</p>}

				<section className="space-y-4">
					{posts.map((post) => (
						<div key={post.id} className="space-y-2">
							<PostCard post={post} onAddComment={handleAddComment} onAddReply={handleAddReply} />
							<div className="h-px bg-[#f3e6fa]" />
						</div>
					))}
				</section>
			</div>
		</StudentLayout>
	)
}

export default Feed
