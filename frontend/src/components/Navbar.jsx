import { Link, useLocation } from 'react-router-dom'
import { Button } from './ui/Primitives'

function NavLink({ to, children }) {
	const location = useLocation()
	const active = location.pathname === to
	return (
		<Link
			to={to}
			className={`flex-1 text-center px-3 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
				active
					? 'bg-gradient-to-r from-[#f6aac8] to-[#ccb8ff] text-white shadow-[0_10px_24px_rgba(244,180,217,0.3)]'
					: 'text-[#8f7fa1] hover:bg-white/70 hover:scale-[1.02]'
			}`}
		>
			{children}
		</Link>
	)
}

function Navbar({ role, onLogout }) {
	return (
		<nav className="w-full">
			<div className="safe-section !rounded-none !rounded-t-[var(--radius-app)] !p-3 sm:!p-4 flex items-center justify-between">
				<div className="flex items-center gap-4">
					<div className="flex items-end gap-2 text-[#5d4f6f] leading-none">
						<span className="text-3xl sm:text-3xl" aria-hidden="true">🌸</span>
						<span className="text-[3rem] sm:text-[5.5rem] md:text-[6.5rem] font-serif font-black tracking-tight">EchoThread</span>
					</div>
					<span className="safe-chip uppercase">
						{role}
					</span>
				</div>
				<Button type="button" onClick={onLogout} className="!h-9 !px-4 !text-xs">
					Logout
				</Button>
			</div>

			{role === 'counselor' && (
				<div className="mt-3 px-4 pb-4">
					<div className="safe-section !p-2">
						<div className="flex gap-2">
							<NavLink to="/counselor">Dashboard</NavLink>
							<NavLink to="/counselor/chats">Chats</NavLink>
						</div>
					</div>
				</div>
			)}
		</nav>
	)
}

export default Navbar
