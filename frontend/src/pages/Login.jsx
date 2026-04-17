import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { sendOtp, verifyOtp } from '../services/api'

function Login({ onLogin }) {
	const [email, setEmail] = useState('')
	const [otp, setOtp] = useState('')
	const [info, setInfo] = useState('')
	const [error, setError] = useState('')
	const [loading, setLoading] = useState(false)
	const navigate = useNavigate()

	const handleSendOtp = async () => {
		setError('')
		setInfo('OTP sent')
		try {
			await sendOtp(email)
		} catch {
			setInfo('OTP sent')
		}
	}

	const handleVerify = async (event) => {
		event.preventDefault()
		setLoading(true)
		setError('')
		try {
			const result = await verifyOtp(email, otp)
			onLogin(result.role, result.email)
			if (result.role === 'counselor') {
				navigate('/counselor')
			} else {
				navigate('/diary')
			}
		} catch {
			setError('Invalid credentials or OTP.')
		} finally {
			setLoading(false)
		}
	}

	return (
		<main className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
			<section className="w-full max-w-md rounded-xl bg-white p-6 border border-slate-200 shadow-sm">
				<h1 className="text-2xl font-semibold text-slate-900">EchoThread Login</h1>
				<p className="text-sm text-slate-600 mt-1">Use institutional email and OTP.</p>

				<form className="mt-5 space-y-4" onSubmit={handleVerify}>
					<div>
						<label className="block text-sm text-slate-700 mb-1">Email</label>
						<input
							type="email"
							required
							value={email}
							onChange={(event) => setEmail(event.target.value)}
							className="w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						/>
					</div>

					<button
						type="button"
						onClick={handleSendOtp}
						className="w-full rounded bg-indigo-600 px-3 py-2 text-white font-medium hover:bg-indigo-700"
					>
						Send OTP
					</button>

					<div>
						<label className="block text-sm text-slate-700 mb-1">OTP</label>
						<input
							type="text"
							required
							value={otp}
							onChange={(event) => setOtp(event.target.value)}
							className="w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
						/>
					</div>

					<button
						type="submit"
						disabled={loading}
						className="w-full rounded bg-slate-900 px-3 py-2 text-white font-medium hover:bg-slate-950 disabled:opacity-60"
					>
						{loading ? 'Verifying...' : 'Login'}
					</button>
				</form>

				{info && <p className="mt-3 text-sm text-emerald-700">{info}</p>}
				{error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
			</section>
		</main>
	)
}

export default Login
