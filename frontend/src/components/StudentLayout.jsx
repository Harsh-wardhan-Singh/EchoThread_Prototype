import { Link, useLocation } from 'react-router-dom'
import Navbar from './Navbar'

function SideLink({ to, icon, children }) {
	const location = useLocation()
	const active = location.pathname === to

	return (
		<Link
			to={to}
			className={`w-full text-left px-4 py-4 min-h-14 rounded-md text-xl font-medium no-underline hover:no-underline focus:no-underline active:no-underline transition-all duration-300 flex items-center gap-3 ${
				active
					? 'bg-gradient-to-r from-[#f6aac8] to-[#ccb8ff] text-white shadow-[0_10px_24px_rgba(244,180,217,0.28)]'
					: 'text-[#8f7fa1] hover:bg-white/70'
			}`}
		>
			<span className="inline-flex items-center justify-center w-6 h-6">{icon}</span>
			{children}
		</Link>
	)
}

function DiaryIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M7 4.5H17A2.5 2.5 0 0 1 19.5 7V19.5H7A2.5 2.5 0 0 1 4.5 17V7A2.5 2.5 0 0 1 7 4.5Z" stroke="currentColor" strokeWidth="1.6" />
			<path d="M9 9H15M9 12.5H15M9 16H13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
		</svg>
	)
}

function FeedIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M5 7.5H19M5 12H19M5 16.5H14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
		</svg>
	)
}

function PulseIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M3.5 13H7.5L10.2 7.5L13.6 16.5L16.3 11H20.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
		</svg>
	)
}

function ChatIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M6.5 7.5H17.5A2 2 0 0 1 19.5 9.5V15A2 2 0 0 1 17.5 17H11L7.5 19V17H6.5A2 2 0 0 1 4.5 15V9.5A2 2 0 0 1 6.5 7.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
		</svg>
	)
}

function StudentLayout({ role, onLogout, children }) {
	return (
		<div className="h-full min-h-0 flex flex-col safe-fade-slide overflow-hidden">
			<div className="z-20">
				<Navbar role={role} onLogout={onLogout} />
			</div>
			<div className="flex-1 min-h-0 p-4 grid grid-cols-[290px_minmax(0,1fr)] gap-4 items-stretch overflow-hidden">
				<aside className="safe-section !p-3 h-full flex flex-col gap-2 overflow-hidden">
					<SideLink to="/diary" icon={<DiaryIcon />}>Diary</SideLink>
					<SideLink to="/feed" icon={<FeedIcon />}>Feed</SideLink>
					<SideLink to="/pulse" icon={<PulseIcon />}>Pulse</SideLink>
					<SideLink to="/chat" icon={<ChatIcon />}>Counselor chat</SideLink>
				</aside>
				<main className="min-h-0 h-full overflow-hidden pr-2">
					<div className="safe-section h-full !p-4 overflow-y-auto overflow-x-hidden">
						{children}
					</div>
				</main>
			</div>
		</div>
	)
}

export default StudentLayout
