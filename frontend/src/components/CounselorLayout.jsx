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

function DashboardIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M4.5 5.5H10.5V11.5H4.5V5.5ZM13.5 5.5H19.5V9.5H13.5V5.5ZM13.5 12.5H19.5V18.5H13.5V12.5ZM4.5 14.5H10.5V18.5H4.5V14.5Z" stroke="currentColor" strokeWidth="1.6" />
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

function ChatIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M6.5 7.5H17.5A2 2 0 0 1 19.5 9.5V15A2 2 0 0 1 17.5 17H11L7.5 19V17H6.5A2 2 0 0 1 4.5 15V9.5A2 2 0 0 1 6.5 7.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
		</svg>
	)
}

function InboxIcon() {
	return (
		<svg width="50" height="50" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M4.5 6.5H19.5V17.5H4.5V6.5Z" stroke="currentColor" strokeWidth="1.6" />
			<path d="M4.5 13.5H8.5L10 15H14L15.5 13.5H19.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
		</svg>
	)
}

function CounselorLayout({ role, onLogout, children }) {
	return (
		<div className="h-full min-h-0 flex flex-col safe-fade-slide overflow-hidden">
			<div className="z-20">
				<Navbar role={role} onLogout={onLogout} />
			</div>
			<div className="flex-1 min-h-0 p-4 grid grid-cols-[290px_minmax(0,1fr)] gap-4 items-stretch overflow-hidden">
				<aside className="safe-section !p-3 h-full flex flex-col gap-2 overflow-hidden">
					<SideLink to="/counselor" icon={<DashboardIcon />}>Dashboard</SideLink>
					<SideLink to="/counselor/feed" icon={<FeedIcon />}>Feed</SideLink>
					<SideLink to="/counselor/chats" icon={<ChatIcon />}>Chats</SideLink>
					<SideLink to="/counselor/inbox" icon={<InboxIcon />}>Inbox</SideLink>
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

export default CounselorLayout
