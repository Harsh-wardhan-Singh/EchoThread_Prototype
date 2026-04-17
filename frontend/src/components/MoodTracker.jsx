function MoodTracker({ result }) {
	if (!result) {
		return null
	}

	return (
		<div className="rounded-lg border border-slate-200 bg-slate-50 p-4 mt-4">
			<h3 className="font-semibold text-slate-800">Latest Analysis</h3>
			<div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
				<div>
					<p className="text-slate-500">Sentiment</p>
					<p className="font-medium text-slate-800 capitalize">{result.sentiment}</p>
				</div>
				<div>
					<p className="text-slate-500">Emotion</p>
					<p className="font-medium text-slate-800 capitalize">{result.emotion}</p>
				</div>
				<div>
					<p className="text-slate-500">Risk</p>
					<p className="font-medium text-slate-800">{result.risk}</p>
				</div>
			</div>
		</div>
	)
}

export default MoodTracker
