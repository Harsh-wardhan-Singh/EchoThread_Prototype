import { useState } from 'react'

function MoodTracker({ result }) {
	const [showDetails, setShowDetails] = useState(false)

	if (!result) {
		return null
	}

	const readableSummary = {
		stress: 'You seem a bit stressed today. A short pause and a small reset might help.',
		anxiety: 'You may be feeling anxious right now. Try taking a few slow breaths and grounding yourself.',
		sadness: 'Your reflection feels heavy today. Reaching out to someone you trust could help.',
		calm: 'You seem emotionally steady today. Keep nurturing what is helping you feel balanced.',
		anger: 'There may be some frustration in your note. A brief walk or break could ease the intensity.',
	}

	let summary = readableSummary[result.emotion] || 'Thanks for sharing your thoughts. Keep checking in with yourself kindly.'

	if (result.risk === 'HIGH') {
		summary =
			'Your note suggests you may be in deep pain right now. You deserve immediate support from a trusted person or local emergency/crisis service.'
	}

	return (
		<div className="safe-section mt-5 space-y-2">
			<h3 className="font-semibold text-[#5d4f6f]">A gentle reflection</h3>
			<p className="text-sm text-[#7f6e91] leading-relaxed">{summary}</p>

			<button
				type="button"
				onClick={() => setShowDetails((current) => !current)}
				className="mt-2 inline-flex items-center rounded-full px-3 py-1.5 text-xs font-medium text-[#7a6a8f] bg-white/75 hover:bg-white/90 transition-all duration-300"
			>
				{showDetails ? 'Hide details' : 'More'}
			</button>

			{showDetails && (
				<div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
					<div>
						<p className="text-[#9a8aac]">Sentiment</p>
						<p className="font-medium text-[#5d4f6f] capitalize">{result.sentiment}</p>
					</div>
					<div>
						<p className="text-[#9a8aac]">Emotion</p>
						<p className="font-medium text-[#5d4f6f] capitalize">{result.emotion}</p>
					</div>
					<div>
						<p className="text-[#9a8aac]">Risk</p>
						<p className="font-medium text-[#5d4f6f]">{result.risk}</p>
					</div>
					<div>
						<p className="text-[#9a8aac]">Risk Score</p>
						<p className="font-medium text-[#5d4f6f]">{typeof result.risk_score === 'number' ? result.risk_score.toFixed(2) : '—'}</p>
					</div>
				</div>
			)}
		</div>
	)
}

export default MoodTracker
