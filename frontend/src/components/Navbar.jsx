import { Button } from './ui/Primitives'

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
		</nav>
	)
}

export default Navbar
