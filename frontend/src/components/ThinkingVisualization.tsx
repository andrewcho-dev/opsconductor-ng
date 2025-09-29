/**
 * Real-time AI thinking visualization component
 * Implements the BIGBRAIN.md live Ollama reasoning stream
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Zap, 
  Target, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Activity,
  Lightbulb,
  Search,
  Settings,
  Eye,
  Wifi,
  WifiOff
} from 'lucide-react';
import { ThinkingWebSocketClient, ThinkingStep, ProgressUpdate } from '../services/thinkingWebSocket';

interface ThinkingVisualizationProps {
  sessionId: string;
  isActive: boolean;
  onConnectionChange?: (connected: boolean) => void;
}

const ThinkingVisualization: React.FC<ThinkingVisualizationProps> = ({
  sessionId,
  isActive,
  onConnectionChange
}) => {
  const [wsClient, setWsClient] = useState<ThinkingWebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [progressUpdates, setProgressUpdates] = useState<ProgressUpdate[]>([]);
  const [currentThinking, setCurrentThinking] = useState<ThinkingStep | null>(null);
  const [currentProgress, setCurrentProgress] = useState<ProgressUpdate | null>(null);
  const thinkingEndRef = useRef<HTMLDivElement>(null);

  // Initialize WebSocket client
  useEffect(() => {
    if (!sessionId || !isActive) return;

    const client = new ThinkingWebSocketClient(sessionId);
    setWsClient(client);

    // Set up event handlers
    const unsubscribeConnection = client.onConnection((connected) => {
      setIsConnected(connected);
      onConnectionChange?.(connected);
    });

    const unsubscribeThinking = client.onThinking((step) => {
      setThinkingSteps(prev => [...prev, step]);
      setCurrentThinking(step);
      
      // Auto-scroll to latest thinking
      setTimeout(() => {
        thinkingEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    });

    const unsubscribeProgress = client.onProgress((update) => {
      setProgressUpdates(prev => [...prev, update]);
      setCurrentProgress(update);
    });

    // Connect to WebSocket
    client.connect().catch(error => {
      console.error('Failed to connect to thinking WebSocket:', error);
    });

    return () => {
      unsubscribeConnection();
      unsubscribeThinking();
      unsubscribeProgress();
      client.disconnect();
    };
  }, [sessionId, isActive, onConnectionChange]);

  // Clear thinking when session changes
  useEffect(() => {
    setThinkingSteps([]);
    setProgressUpdates([]);
    setCurrentThinking(null);
    setCurrentProgress(null);
  }, [sessionId]);

  const getThinkingIcon = (type: string) => {
    switch (type) {
      case 'analysis': return <Search className="thinking-icon" />;
      case 'decision': return <Target className="thinking-icon" />;
      case 'planning': return <Settings className="thinking-icon" />;
      case 'evaluation': return <TrendingUp className="thinking-icon" />;
      case 'execution': return <Zap className="thinking-icon" />;
      case 'reflection': return <Lightbulb className="thinking-icon" />;
      default: return <Brain className="thinking-icon" />;
    }
  };

  const getThinkingTypeColor = (type: string) => {
    switch (type) {
      case 'analysis': return '#3b82f6'; // blue
      case 'decision': return '#ef4444'; // red
      case 'planning': return '#8b5cf6'; // purple
      case 'evaluation': return '#f59e0b'; // amber
      case 'execution': return '#10b981'; // emerald
      case 'reflection': return '#6366f1'; // indigo
      default: return '#6b7280'; // gray
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'; // green
    if (confidence >= 0.6) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const timeString = date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    const milliseconds = Math.floor(date.getMilliseconds() / 100);
    return `${timeString}.${milliseconds}`;
  };

  if (!isActive) {
    return null;
  }

  return (
    <div className="thinking-visualization">
      <style>
        {`
          .thinking-visualization {
            background: var(--neutral-50);
            border: 1px solid var(--neutral-200);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            max-height: 400px;
            overflow-y: auto;
          }

          .thinking-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--neutral-200);
          }

          .thinking-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: var(--neutral-800);
          }

          .connection-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
          }

          .connection-status.connected {
            background: var(--success-green-light);
            color: var(--success-green);
          }

          .connection-status.disconnected {
            background: var(--danger-red-light);
            color: var(--danger-red);
          }

          .thinking-stream {
            display: flex;
            flex-direction: column;
            gap: 12px;
          }

          .thinking-step {
            background: white;
            border: 1px solid var(--neutral-200);
            border-radius: 6px;
            padding: 12px;
            position: relative;
            animation: slideIn 0.3s ease-out;
          }

          .thinking-step.current {
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 2px var(--primary-blue-light);
          }

          @keyframes slideIn {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          .thinking-step-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
          }

          .thinking-type {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            font-size: 13px;
            text-transform: capitalize;
          }

          .thinking-icon {
            width: 14px;
            height: 14px;
          }

          .thinking-meta {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 11px;
            color: var(--neutral-600);
          }

          .confidence-badge {
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 500;
            color: white;
            font-size: 10px;
          }

          .thinking-content {
            font-size: 13px;
            line-height: 1.4;
            color: var(--neutral-700);
            margin-bottom: 8px;
          }

          .reasoning-chain {
            background: var(--neutral-50);
            border-radius: 4px;
            padding: 8px;
            margin-top: 8px;
          }

          .reasoning-chain-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--neutral-600);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          .reasoning-steps {
            list-style: none;
            padding: 0;
            margin: 0;
          }

          .reasoning-step {
            font-size: 12px;
            color: var(--neutral-700);
            padding: 2px 0;
            position: relative;
            padding-left: 12px;
          }

          .reasoning-step::before {
            content: '→';
            position: absolute;
            left: 0;
            color: var(--neutral-400);
            font-weight: bold;
          }

          .alternatives-section {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--neutral-200);
          }

          .alternatives-title {
            font-size: 11px;
            font-weight: 600;
            color: var(--neutral-600);
            margin-bottom: 4px;
          }

          .alternatives-list {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
          }

          .alternative-tag {
            background: var(--neutral-100);
            color: var(--neutral-700);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
          }

          .progress-section {
            background: var(--primary-blue-light);
            border: 1px solid var(--primary-blue);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
          }

          .progress-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
          }

          .progress-title {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 600;
            color: var(--primary-blue);
            font-size: 13px;
          }

          .progress-bar {
            background: var(--neutral-200);
            border-radius: 4px;
            height: 6px;
            overflow: hidden;
            margin-top: 8px;
          }

          .progress-fill {
            background: var(--primary-blue);
            height: 100%;
            transition: width 0.3s ease;
          }

          .empty-state {
            text-align: center;
            color: var(--neutral-500);
            font-size: 13px;
            padding: 20px;
          }

          .empty-state-icon {
            width: 32px;
            height: 32px;
            margin: 0 auto 8px;
            opacity: 0.5;
          }
        `}
      </style>

      <div className="thinking-header">
        <div className="thinking-title">
          <Brain size={16} />
          AI Thinking Stream
        </div>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
          {isConnected ? 'Live' : 'Disconnected'}
        </div>
      </div>

      {currentProgress && (
        <div className="progress-section">
          <div className="progress-header">
            <div className="progress-title">
              <Activity size={14} />
              {currentProgress.operation}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--primary-blue)' }}>
              {formatTimestamp(currentProgress.timestamp)}
            </div>
          </div>
          {currentProgress.current_step && (
            <div style={{ fontSize: '12px', color: 'var(--neutral-700)' }}>
              {currentProgress.current_step}
            </div>
          )}
          {currentProgress.progress_percentage !== undefined && (
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${currentProgress.progress_percentage}%` }}
              />
            </div>
          )}
        </div>
      )}

      <div className="thinking-stream">
        {thinkingSteps.length === 0 ? (
          <div className="empty-state">
            <Brain className="empty-state-icon" />
            <div>Waiting for AI thinking...</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>
              Real-time reasoning will appear here when the AI processes your request
            </div>
          </div>
        ) : (
          thinkingSteps.map((step, index) => (
            <div 
              key={step.id} 
              className={`thinking-step ${step === currentThinking ? 'current' : ''}`}
            >
              <div className="thinking-step-header">
                <div 
                  className="thinking-type"
                  style={{ color: getThinkingTypeColor(step.thinking_type) }}
                >
                  {getThinkingIcon(step.thinking_type)}
                  {step.thinking_type}
                </div>
                <div className="thinking-meta">
                  <div 
                    className="confidence-badge"
                    style={{ backgroundColor: getConfidenceColor(step.confidence_level) }}
                  >
                    {Math.round(step.confidence_level * 100)}%
                  </div>
                  <div>{formatTimestamp(step.timestamp)}</div>
                  {step.metadata?.step_number && step.metadata?.total_steps && (
                    <div>
                      Step {step.metadata.step_number}/{step.metadata.total_steps}
                    </div>
                  )}
                </div>
              </div>

              <div className="thinking-content">
                {step.thinking_content}
              </div>

              {step.reasoning_chain && step.reasoning_chain.length > 0 && (
                <div className="reasoning-chain">
                  <div className="reasoning-chain-title">Reasoning Chain</div>
                  <ul className="reasoning-steps">
                    {step.reasoning_chain.map((reason, idx) => (
                      <li key={idx} className="reasoning-step">
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {step.alternatives_considered && step.alternatives_considered.length > 0 && (
                <div className="alternatives-section">
                  <div className="alternatives-title">Alternatives Considered</div>
                  <div className="alternatives-list">
                    {step.alternatives_considered.map((alt, idx) => (
                      <span key={idx} className="alternative-tag">
                        {alt}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {step.decision_factors && step.decision_factors.length > 0 && (
                <div className="alternatives-section">
                  <div className="alternatives-title">Decision Factors</div>
                  <div className="alternatives-list">
                    {step.decision_factors.map((factor, idx) => (
                      <span key={idx} className="alternative-tag">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={thinkingEndRef} />
      </div>
    </div>
  );
};

export default ThinkingVisualization;