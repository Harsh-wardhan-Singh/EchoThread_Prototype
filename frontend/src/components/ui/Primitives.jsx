function merge(...parts) {
	return parts.filter(Boolean).join(' ')
}

export function AppContainer({ children, className = '', shellClassName = '' }) {
	return (
		<div className={merge('safe-app-shell', shellClassName)}>
			<div className={merge('safe-app-container safe-fade-slide', className)}>{children}</div>
		</div>
	)
}

export function Card({ children, className = '' }) {
	return <section className={merge('safe-card', className)}>{children}</section>
}

export function Section({ children, className = '' }) {
	return <section className={merge('safe-section', className)}>{children}</section>
}

export function Button({ children, className = '', ...props }) {
	return (
		<button className={merge('safe-button', className)} {...props}>
			{children}
		</button>
	)
}

export function Input({ icon, className = '', ...props }) {
	return (
		<div className="safe-input-shell">
			{icon && <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#b69ac8]">{icon}</span>}
			<input className={merge('safe-input', icon ? 'pl-11' : '', className)} {...props} />
		</div>
	)
}

export function Textarea({ className = '', ...props }) {
	return <textarea className={merge('safe-textarea', className)} {...props} />
}
