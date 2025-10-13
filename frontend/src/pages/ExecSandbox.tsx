/**
 * Exec Sandbox Page
 * Testing UI for /ai/execute endpoint (PR #4 walking skeleton)
 */
import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Loader, Play } from 'lucide-react';
import PageContainer from '../components/PageContainer';
import PageHeader from '../components/PageHeader';
import { execRun, ExecResponse } from '../services/exec';

const ExecSandbox: React.FC = () => {
  const [input, setInput] = useState<string>('');
  const [tool, setTool] = useState<string>('echo');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ExecResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) {
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await execRun(input, tool);
      setResult(response);
    } catch (error) {
      console.error('Exec failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInput('');
    setResult(null);
  };

  return (
    <PageContainer>
      <PageHeader
        title="Exec Sandbox"
        subtitle="Test AI execution endpoint (walking skeleton)"
      />

      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <form onSubmit={handleSubmit}>
                {/* Tool Selection */}
                <div className="mb-3">
                  <label htmlFor="tool" className="form-label">
                    Tool
                  </label>
                  <select
                    id="tool"
                    className="form-select"
                    value={tool}
                    onChange={(e) => setTool(e.target.value)}
                    disabled={loading}
                  >
                    <option value="echo">echo</option>
                  </select>
                  <div className="form-text">
                    Currently only "echo" tool is available for testing
                  </div>
                </div>

                {/* Input Text */}
                <div className="mb-3">
                  <label htmlFor="input" className="form-label">
                    Input
                  </label>
                  <textarea
                    id="input"
                    className="form-control"
                    rows={4}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder='Enter input text (e.g., "ping" or "Hello OpsConductor!")'
                    disabled={loading}
                    required
                  />
                  <div className="form-text">
                    Try "ping" to get "pong" response
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="d-flex gap-2">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading || !input.trim()}
                  >
                    {loading ? (
                      <>
                        <Loader className="me-2" size={16} />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Play className="me-2" size={16} />
                        Execute
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleClear}
                    disabled={loading}
                  >
                    Clear
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Results Panel */}
      {result && (
        <div className="row mt-4">
          <div className="col-12">
            <div className="card">
              <div className="card-header d-flex align-items-center">
                {result.success ? (
                  <>
                    <CheckCircle className="text-success me-2" size={20} />
                    <span className="fw-bold">Success</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="text-danger me-2" size={20} />
                    <span className="fw-bold">Error</span>
                  </>
                )}
              </div>
              <div className="card-body">
                {/* Success Output */}
                {result.success && result.output && (
                  <div className="mb-3">
                    <label className="form-label fw-bold">Output</label>
                    <pre className="bg-light p-3 rounded border">
                      {result.output}
                    </pre>
                  </div>
                )}

                {/* Error Details */}
                {!result.success && result.error && (
                  <div className="mb-3">
                    <label className="form-label fw-bold text-danger">
                      Error
                    </label>
                    <div className="alert alert-danger mb-0">
                      <div className="mb-2">
                        <strong>Code:</strong> {result.error.code}
                      </div>
                      <div>
                        <strong>Message:</strong> {result.error.message}
                      </div>
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div className="row g-3">
                  <div className="col-md-4">
                    <label className="form-label fw-bold">Trace ID</label>
                    <div className="text-muted small font-monospace">
                      {result.trace_id}
                    </div>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fw-bold">Duration</label>
                    <div className="text-muted">
                      {result.duration_ms.toFixed(2)} ms
                    </div>
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fw-bold">Tool</label>
                    <div className="text-muted">{result.tool}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Info Panel */}
      <div className="row mt-4">
        <div className="col-12">
          <div className="card border-info">
            <div className="card-body">
              <h6 className="card-title">
                <AlertCircle className="me-2" size={16} />
                About Exec Sandbox
              </h6>
              <p className="card-text mb-2">
                This sandbox tests the end-to-end execution path through the
                automation-service proxy to the ai-pipeline service.
              </p>
              <ul className="mb-0">
                <li>
                  <strong>Walking Skeleton:</strong> Minimal implementation to
                  verify the full execution path
                </li>
                <li>
                  <strong>Echo Tool:</strong> Simple tool that echoes input
                  ("ping" → "pong")
                </li>
                <li>
                  <strong>Telemetry:</strong> Check browser console for
                  detailed logs
                </li>
                <li>
                  <strong>Metrics:</strong> View Prometheus metrics at{' '}
                  <code>http://localhost:8010/metrics</code>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export default ExecSandbox;