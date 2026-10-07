/**
 * Classification label: VERIFIED FINDING / AI OBSERVATION / AI-GENERATED PATCH
 */
import { ShieldCheck, Bot, Code2 } from 'lucide-react'

export function VerifiedLabel() {
  return (
    <span className="label-verified">
      <ShieldCheck size={12} />
      VERIFIED FINDING
    </span>
  )
}

export function AIObservationLabel() {
  return (
    <span className="label-ai-obs">
      <Bot size={12} />
      AI OBSERVATION
    </span>
  )
}

export function AIPatchLabel() {
  return (
    <span className="label-ai-patch">
      <Code2 size={12} />
      AI-GENERATED PATCH
    </span>
  )
}

export default function ClassificationLabel({ classification, verified }) {
  if (verified === false) return <AIObservationLabel />
  if (classification === 'AI_OBSERVATION') return <AIObservationLabel />
  if (classification === 'AI_PATCH') return <AIPatchLabel />
  return <VerifiedLabel />
}
