function PostCard({ post }) {
	const date = post?.created_at ? new Date(post.created_at).toLocaleString() : ''
	const comments = Array.isArray(post?.comments) ? post.comments : []
	const displayUserUuid = post?.user_uuid || 'unavailable'

	return (
		<article className="safe-card !rounded-md !p-5 space-y-4">
			<div className="flex items-center justify-between gap-3 mb-2">
				<p className="text-xs text-[#9887aa]">User UUID: {displayUserUuid}</p>
				<p className="text-xs text-[#9887aa]">{date}</p>
			</div>
			<p className="text-[#5f4d73] leading-relaxed text-[15px]">{post?.content}</p>

			{comments.length > 0 && (
				<div className="mt-4 pl-4 space-y-2 border-l border-white/70">
					{comments.map((comment, index) => (
						<p key={`${post?.id}-comment-${index}`} className="text-xs text-[#9b8dae] leading-relaxed">
							{comment}
						</p>
					))}
				</div>
			)}
		</article>
	)
}

export default PostCard
