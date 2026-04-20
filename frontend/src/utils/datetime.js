const IST_TIME_ZONE = 'Asia/Kolkata'

function parseBackendTimestamp(value) {
	if (!value) {
		return null
	}

	const raw = String(value).trim()
	if (!raw) {
		return null
	}

	const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(raw)
	const normalized = hasTimezone ? raw : `${raw}Z`
	const date = new Date(normalized)
	if (Number.isNaN(date.getTime())) {
		return null
	}
	return date
}

function formatIstDateTime(value) {
	const date = parseBackendTimestamp(value)
	if (!date) {
		return ''
	}
	return new Intl.DateTimeFormat([], {
		timeZone: IST_TIME_ZONE,
		day: '2-digit',
		month: 'short',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
		hour12: false,
	}).format(date)
}

function formatIstTime(value) {
	const date = parseBackendTimestamp(value)
	if (!date) {
		return ''
	}
	return new Intl.DateTimeFormat([], {
		timeZone: IST_TIME_ZONE,
		hour: '2-digit',
		minute: '2-digit',
		hour12: false,
	}).format(date)
}

function formatIstDayDate(value) {
	const date = parseBackendTimestamp(value)
	if (!date) {
		return ''
	}
	return new Intl.DateTimeFormat([], {
		timeZone: IST_TIME_ZONE,
		weekday: 'short',
		day: '2-digit',
		month: 'short',
	}).format(date)
}

function getIstDayKey(value) {
	const date = parseBackendTimestamp(value)
	if (!date) {
		return ''
	}

	const parts = new Intl.DateTimeFormat('en-CA', {
		timeZone: IST_TIME_ZONE,
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
	}).formatToParts(date)
	const lookup = Object.fromEntries(parts.map((part) => [part.type, part.value]))
	return `${lookup.year}-${lookup.month}-${lookup.day}`
}

export { formatIstDateTime, formatIstDayDate, formatIstTime, getIstDayKey }
