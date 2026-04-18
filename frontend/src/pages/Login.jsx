import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { sendOtp, verifyOtp } from '../services/api'
import { Button, Card, Input, Section } from '../components/ui/Primitives'

function MailIcon() {
	return (
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path d="M4 7.5L12 13.5L20 7.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
			<rect x="3.5" y="5.5" width="17" height="13" rx="3" stroke="currentColor" strokeWidth="1.5" />
		</svg>
	)
}

function ShieldIcon() {
	return (
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
			<path
				d="M12 3.8L18.2 6.2V11.6C18.2 15.2 15.9 18.4 12 20.2C8.1 18.4 5.8 15.2 5.8 11.6V6.2L12 3.8Z"
				stroke="currentColor"
				strokeWidth="1.5"
				strokeLinejoin="round"
			/>
			<path d="M9.7 11.8L11.3 13.3L14.5 10.1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
		</svg>
	)
}

function Login({ onLogin }) {
	const [email, setEmail] = useState('')
	const [otp, setOtp] = useState('')
	const [otpRequested, setOtpRequested] = useState(false)
	const [info, setInfo] = useState('')
	const [error, setError] = useState('')
	const [loading, setLoading] = useState(false)
	const navigate = useNavigate()

	const handleSendOtp = async () => {
		setError('')
		setInfo('OTP sent')
		setOtpRequested(true)
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
			onLogin(result.role, result.email, result.session_token, result.user_uuid)
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
		<main className="w-full">
			<Card className="space-y-6 sm:space-y-7 !p-6 sm:!p-8 overflow-hidden">
				<div className="text-center space-y-2">
					<div className="mx-auto h-14 w-14 rounded-2xl bg-gradient-to-br from-[#ffd7e8] to-[#eee2ff] shadow-[0_10px_28px_rgba(241,190,218,0.35)]" />
					<h1 className="text-[28px] font-semibold tracking-tight text-[#5d4f6f]">EchoThread</h1>
					<p className="text-sm text-[#8f7fa1]">A gentle, anonymous space to check in with yourself.</p>
				</div>

				<form className="space-y-2" onSubmit={handleVerify}>
					<div className="w-full">
						<Input
							type="email"
							required
							value={email}
							onChange={(event) => setEmail(event.target.value)}
							placeholder="College email"
							icon={<MailIcon />}
						/>
					</div>

					<Button type="button" onClick={handleSendOtp} className="w-full">
						Send OTP
					</Button>

					<div
						className={`overflow-hidden transition-all duration-500 ${
							otpRequested
								? 'max-h-40 opacity-100 translate-y-0 overflow-visible'
								: 'max-h-0 opacity-0 -translate-y-1 overflow-hidden'
						}`}
					>
						<div className="w-full pt-0.5">
							<Input
								type="text"
								required={otpRequested}
								value={otp}
								onChange={(event) => setOtp(event.target.value)}
								placeholder="Enter OTP"
								icon={<ShieldIcon />}
							/>
						</div>
					</div>

					<Button type="submit" disabled={loading} className="w-full">
						{loading ? 'Verifying...' : 'Login'}
					</Button>

					{info && <Section className="text-sm text-[#7f6e91] py-3">{info}</Section>}
					{error && <Section className="text-sm text-[#a16788] py-3">Invalid OTP. Please try again.</Section>}
				</form>
			</Card>
		</main>
	)
}

export default Login
