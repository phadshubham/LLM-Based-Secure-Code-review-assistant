/**
 * Finding Details page – full finding with code snippet and AI review
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, ShieldCheck, Bot, Code2, AlertTriangle,
  Lightbulb, Wrench, FileCode, MapPin,
} from 'lucide-react'
import { getFinding } from '../services/api'
import SeverityBadge from '../components/SeverityBadge'
import ClassificationLabel, { VerifiedLabel, AIObservationLabel, AIPatchLabel } from '../components/ClassificationLabel'
import { LoadingPage } from '../components/LoadingStates'

function Section({ icon: Icon, title, iconColor = 'text-cyber-400', children }) {
  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
        <Icon size={14} className={iconColor} />
        {title}
      </h3>
      {children}
    </div>
  )
}

export default function FindingDetail() {
  const { findingId } = useParams()
  const navigate = useNavigate()
  const [finding, setFinding] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getFinding(findingId)
      .then(r => setFinding(r.data.finding))
      .finally(() => setLoading(false))
  }, [findingId])

  if (loading) return <LoadingPage message="Loading finding…" />
  if (!finding) return <div className="p-6 text-dark-400">Finding not found.</div>

  const ai = finding.ai_review

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-5 animate-fade-in">
      {/* Back */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-dark-400 hover:text-dark-200 text-sm transition-colors"
      >
        <ArrowLeft size={14} /> Back to Results
      </button>

      {/* Finding header */}
      <div className="glass-card p-5">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <SeverityBadge severity={finding.severity} />
              {finding.verified ? <VerifiedLabel /> : <AIObservationLabel />}
            </div>
            <h1 className="text-xl font-bold text-white">{finding.category}</h1>
            <p className="text-dark-400 text-sm mt-1">{finding.message}</p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div className="flex items-start gap-2">
            <FileCode size={14} className="text-dark-500 mt-0.5" />
            <div>
              <div className="text-xs text-dark-500">File</div>
              <div className="text-dark-200 font-mono text-xs break-all">
                {finding.file.split(/[\\/]/).slice(-2).join('/')}
              </div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <MapPin size={14} className="text-dark-500 mt-0.5" />
            <div>
              <div className="text-xs text-dark-500">Line</div>
              <div className="text-dark-200 font-mono">{finding.line ?? 'N/A'}</div>
            </div>
          </div>
          <div>
            <div className="text-xs text-dark-500">Scanner</div>
            <div className="text-dark-200 font-medium">{finding.tool}</div>
          </div>
          <div>
            <div className="text-xs text-dark-500">Rule ID</div>
            <div className="text-dark-300 font-mono text-xs">{finding.rule_id || 'N/A'}</div>
          </div>
        </div>
      </div>

      {/* Code snippet */}
      {finding.code_snippet && (
        <Section icon={FileCode} title="Relevant Source Code" iconColor="text-dark-400">
          <pre className="code-block text-xs leading-relaxed">
            {finding.code_snippet}
          </pre>
          <p className="text-xs text-dark-500 mt-2">
            Showing ±20 lines around line {finding.line}. Source code is read-only — never modified automatically.
          </p>
        </Section>
      )}

      {/* AI Explanation */}
      {ai ? (
        <>
          <Section icon={Bot} title="AI Explanation" iconColor="text-purple-400">
            <div className="text-sm text-dark-200 leading-relaxed">
              {ai.explanation || 'No explanation available.'}
            </div>
          </Section>

          <Section icon={AlertTriangle} title="Security Impact" iconColor="text-red-400">
            <div className="text-sm text-dark-200 leading-relaxed">
              {ai.impact || 'No impact assessment available.'}
            </div>
          </Section>

          <Section icon={Lightbulb} title="Recommended Fix" iconColor="text-amber-400">
            <div className="text-sm text-dark-200 leading-relaxed">
              {ai.recommendation || 'No recommendation available.'}
            </div>
          </Section>

          {ai.suggested_patch && ai.suggested_patch.trim() && (
            <div className="glass-card p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-dark-200 flex items-center gap-2">
                  <Code2 size={14} className="text-amber-400" />
                  Suggested Code Fix
                </h3>
                <AIPatchLabel />
              </div>
              <pre className="code-block text-xs leading-relaxed">
                {ai.suggested_patch}
              </pre>
              <div className="mt-3 flex items-start gap-2 p-3 bg-amber-950/20 border border-amber-800/30 rounded-lg">
                <AlertTriangle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-300/80">
                  <strong>AI-Generated Patch — Review before applying.</strong> This code suggestion was generated by a local AI model and has not been automatically applied to your project.
                  Always review, test, and understand any code changes before applying them.
                </p>
              </div>
            </div>
          )}

          {/* AI metadata */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-3 text-xs text-dark-500">
                <span>Model: <span className="text-dark-300">{ai.source || 'Qwen'}</span></span>
                <span>Confidence: <span className={`font-medium ${
                  ai.confidence === 'high' ? 'text-emerald-400' :
                  ai.confidence === 'medium' ? 'text-amber-400' :
                  'text-red-400'
                }`}>{ai.confidence || 'N/A'}</span></span>
              </div>
              <ClassificationLabel
                classification={ai.classification}
                verified={finding.verified}
              />
            </div>
          </div>
        </>
      ) : (
        <div className="glass-card p-8 text-center">
          <Bot size={32} className="mx-auto mb-3 text-dark-600" />
          <p className="text-dark-400 font-medium">AI Review Unavailable</p>
          <p className="text-dark-500 text-sm mt-1">
            AI explanation is not available for this finding.
            Please ensure Ollama is running with the configured Qwen model.
          </p>
        </div>
      )}
    </div>
  )
}
