import StudentLayout from '../components/StudentLayout'
import { Card } from '../components/ui/Primitives'

function OpenChat({ role, onLogout }) {
	return (
		<StudentLayout role={role} onLogout={onLogout}>
			<Card className="space-y-2">
				<h1 className="text-2xl font-semibold text-[#5f4d73]">Open chat</h1>
				<p className="text-sm text-[#8e7d9f]">Coming soon. We will configure this next.</p>
			</Card>
		</StudentLayout>
	)
}

export default OpenChat
