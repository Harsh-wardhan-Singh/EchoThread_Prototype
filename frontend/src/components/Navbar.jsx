import { Link, useLocation } from 'react-router-dom'

function NavLink({ to, children }) {
	const location = useLocation()
	const active = location.pathname === to
	return (
		<Link
			to={to}
			className={`px-3 py-2 rounded text-sm font-medium ${
				active ? 'bg-indigo-600 text-white' : 'text-slate-700 hover:bg-slate-200'
			}`}
		>
			{children}
		</Link>
	)
}

function Navbar({ role, onLogout }) {
	return (
		<nav className="border-b border-slate-200 bg-white">
			<div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
				<div className="flex items-center gap-3">
					<span className="text-lg font-semibold text-slate-800">EchoThread</span>
					<span className="text-xs uppercase px-2 py-1 rounded bg-slate-100 text-slate-600">{role}</span>
				</div>
				<div className="flex items-center gap-2">
					{role === 'student' && (
						<>
							<NavLink to="/diary">Diary</NavLink>
							<NavLink to="/feed">Feed</NavLink>
							<NavLink to="/pulse">Pulse</NavLink>
						</>
					)}
					{role === 'counselor' && <NavLink to="/counselor">Counselor</NavLink>}
					<button
						type="button"
						onClick={onLogout}
						className="ml-2 px-3 py-2 rounded text-sm font-medium bg-slate-800 text-white hover:bg-slate-900"
					>
						Logout
					</button>
				</div>
			</div>
		</nav>
	)
}

export default Navbar
