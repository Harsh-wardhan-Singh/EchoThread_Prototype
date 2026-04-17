function PostCard({ post }) {
	const date = post?.created_at ? new Date(post.created_at).toLocaleString() : ''

	return (
		<article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
			<p className="text-slate-800 leading-relaxed">{post?.content}</p>
			<p className="mt-3 text-xs text-slate-500">{date}</p>
		</article>
	)
}

export default PostCard
