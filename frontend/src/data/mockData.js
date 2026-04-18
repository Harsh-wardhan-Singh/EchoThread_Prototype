export const mockPosts = [
	{
		id: 'm1',
		user_uuid: 'a5d2f4d9-9c8e-4df2-8bf1-5f319f2d7a11',
		content: 'I feel nervous about internals but trying to stay focused.',
		created_at: new Date(Date.now() - 3600 * 1000 * 8).toISOString(),
	},
	{
		id: 'm2',
		user_uuid: '1c0f93e0-6020-4ff2-9a61-a9b8a05b7dd3',
		content: 'Small wins today. Finished one assignment and feel calm.',
		created_at: new Date(Date.now() - 3600 * 1000 * 20).toISOString(),
	},
]

export const mockPulse = {
	total_posts: 8,
	total_diary_entries: 6,
	sentiment_distribution: {
		positive: 4,
		neutral: 3,
		negative: 7,
	},
	risk_distribution: {
		LOW: 6,
		MEDIUM: 4,
		HIGH: 1,
	},
	top_emotions: [
		{ emotion: 'stress', count: 4 },
		{ emotion: 'anxiety', count: 3 },
		{ emotion: 'calm', count: 2 },
	],
	seven_day_activity: [
		{ date: 'Mon', count: 1 },
		{ date: 'Tue', count: 2 },
		{ date: 'Wed', count: 3 },
		{ date: 'Thu', count: 2 },
		{ date: 'Fri', count: 1 },
		{ date: 'Sat', count: 4 },
		{ date: 'Sun', count: 1 },
	],
}
