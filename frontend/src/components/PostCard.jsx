import { useState } from 'react'
import { formatIstDateTime } from '../utils/datetime'

function VerifiedCounselorIcon() {
	return (
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-label="Verified counselor">
			<path d="M12 1.8L14.8 4.4L18.5 3.9L19.9 7.4L23.2 9.2L22.7 12.9L24 16.3L21 18.5L20 22.1L16.3 21.9L13.1 24L10.4 21.4L6.7 21.9L5.3 18.4L2 16.6L2.5 12.9L1.2 9.5L4.2 7.3L5.2 3.7L8.9 3.9L12 1.8Z" fill="#ccb8ff" />
			<path d="M8.4 12.4L10.8 14.7L15.7 9.8" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
		</svg>
	)
}

function CommentItem({ comment, postId, depth = 0, onAddReply }) {
	const [replyOpen, setReplyOpen] = useState(false)
	const [repliesOpen, setRepliesOpen] = useState(false)
	const [replyText, setReplyText] = useState('')
	const [replyLoading, setReplyLoading] = useState(false)

	const createdAt = formatIstDateTime(comment?.created_at)
	const author = comment?.user_uuid || 'unknown'
	const isCounselorComment = String(comment?.author_role || '').toLowerCase() === 'counselor'
	const replies = Array.isArray(comment?.replies) ? comment.replies : []
	const hasReplies = replies.length > 0
	const isNested = depth > 0
	const nestedIndent = Math.min(depth * 16, 64)

	const handleReplySubmit = async (event) => {
		event.preventDefault()
		if (!replyText.trim()) {
			return
		}
		setReplyLoading(true)
		try {
			await onAddReply(postId, comment.id, replyText.trim())
			setReplyText('')
			setReplyOpen(false)
		} finally {
			setReplyLoading(false)
		}
	}

	return (
		<div
			className={`space-y-3 ${isNested ? 'pl-4 border-l border-[#e3d7f0]' : ''}`}
			style={isNested ? { marginLeft: `${nestedIndent}px` } : undefined}
		>
			<div className="rounded-2xl border border-[#eadff6] bg-white/85 px-3 py-3 shadow-[0_4px_14px_rgba(216,198,235,0.18)]">
				<div className="flex items-center justify-between gap-2">
					{isCounselorComment ? (
						<div className="flex items-center gap-1.5">
							<p className="text-[11px] text-[#8e7d9f]">Counsellor</p>
							<VerifiedCounselorIcon />
						</div>
					) : (
						<p className="text-[11px] text-[#8e7d9f]">UUID: {author}</p>
					)}
					<p className="text-[11px] text-[#9b8dae]">{createdAt}</p>
				</div>
				<p className="text-sm text-[#5f4d73] mt-1 leading-relaxed">{comment?.content}</p>

				<div className="mt-2 flex items-center gap-3 flex-wrap">
					<button
						type="button"
						onClick={() => setReplyOpen((value) => !value)}
						className="text-xs text-[#8a79a0] hover:text-[#6f5e86]"
					>
						{replyOpen ? 'Cancel' : 'Reply'}
					</button>
					{hasReplies && (
						<button
							type="button"
							onClick={() => setRepliesOpen((value) => !value)}
							className="text-xs text-[#8a79a0] hover:text-[#6f5e86]"
						>
							{repliesOpen ? `Hide replies (${replies.length})` : `Show replies (${replies.length})`}
						</button>
					)}
				</div>

				{replyOpen && (
					<form className="mt-2 flex gap-2" onSubmit={handleReplySubmit}>
						<input
							type="text"
							value={replyText}
							onChange={(event) => setReplyText(event.target.value)}
							placeholder="Write a reply..."
							className="flex-1 rounded-xl border border-[#e7dbf4] bg-white px-3 py-2 text-sm text-[#5f4d73] outline-none"
						/>
						<button
							type="submit"
							disabled={replyLoading}
							className="rounded-xl bg-[#d8c7ef] px-3 py-2 text-xs text-[#5f4d73] disabled:opacity-60"
						>
							{replyLoading ? 'Posting...' : 'Reply'}
						</button>
					</form>
				)}
			</div>

			{hasReplies && repliesOpen && (
				<div className="space-y-3 pt-1">
					{replies.map((reply) => (
						<CommentItem key={reply.id} comment={reply} postId={postId} depth={depth + 1} onAddReply={onAddReply} />
					))}
				</div>
			)}
		</div>
	)
}

function PostCard({ post, onAddComment, onAddReply, onOpenStudentChat }) {
	const date = formatIstDateTime(post?.created_at)
	const comments = Array.isArray(post?.comments) ? post.comments : []
	const displayUserUuid = post?.user_uuid || 'unavailable'
	const isCounselorPost = post?.author_role === 'counselor'
	const canOpenChat = typeof onOpenStudentChat === 'function' && !isCounselorPost && !!post?.user_uuid
	const [commentsOpen, setCommentsOpen] = useState(false)
	const [commentText, setCommentText] = useState('')
	const [commentLoading, setCommentLoading] = useState(false)

	const handleCommentSubmit = async (event) => {
		event.preventDefault()
		if (!commentText.trim()) {
			return
		}
		setCommentLoading(true)
		try {
			await onAddComment(post.id, commentText.trim())
			setCommentText('')
		} finally {
			setCommentLoading(false)
		}
	}

	return (
		<article className="safe-card !rounded-md !p-5 space-y-4">
			<div className="flex items-center justify-between gap-3 mb-2">
				{isCounselorPost ? (
					<div className="flex items-center gap-1.5">
						<p className="text-xs text-[#9887aa]">Counsellor</p>
						<VerifiedCounselorIcon />
					</div>
				) : (
					<button
						type="button"
						onClick={() => {
							if (canOpenChat) {
								onOpenStudentChat(post.user_uuid)
							}
						}}
						disabled={!canOpenChat}
						className={`text-xs ${canOpenChat ? 'text-[#7d63a3] hover:text-[#5f4d73] underline underline-offset-2' : 'text-[#9887aa]'}`}
					>
						User UUID: {displayUserUuid}
					</button>
				)}
				<p className="text-xs text-[#9887aa]">{date}</p>
			</div>
			<p className="text-[#5f4d73] leading-relaxed text-[15px]">{post?.content}</p>

			<div className="pt-1">
				<button
					type="button"
					onClick={() => setCommentsOpen((value) => !value)}
					className="rounded-xl border border-[#e7dbf4] bg-white/80 px-3 py-2 text-xs text-[#6f5e86]"
				>
					{commentsOpen ? 'Hide comments' : `Open comments (${comments.length})`}
				</button>
			</div>

			{commentsOpen && (
				<div className="space-y-3 rounded-xl border border-[#eadff6] bg-[#fcf9ff] px-3 py-3">
					<form className="flex gap-2" onSubmit={handleCommentSubmit}>
						<input
							type="text"
							value={commentText}
							onChange={(event) => setCommentText(event.target.value)}
							placeholder="Write a comment..."
							className="flex-1 rounded-xl border border-[#e7dbf4] bg-white px-3 py-2 text-sm text-[#5f4d73] outline-none"
						/>
						<button
							type="submit"
							disabled={commentLoading}
							className="rounded-xl bg-[#d8c7ef] px-3 py-2 text-xs text-[#5f4d73] disabled:opacity-60"
						>
							{commentLoading ? 'Posting...' : 'Comment'}
						</button>
					</form>

					{comments.length > 0 ? (
						<div className="space-y-3">
							{comments.map((comment) => (
								<CommentItem
									key={comment.id}
									comment={comment}
									postId={post.id}
									onAddReply={onAddReply}
								/>
							))}
						</div>
					) : (
						<p className="text-xs text-[#9b8dae]">No comments yet. Be the first to comment.</p>
					)}
				</div>
			)}
		</article>
	)
}

export default PostCard
