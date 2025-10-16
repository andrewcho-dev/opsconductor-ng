/**
 * Selector Search Component
 * UI for searching tools using the selector API
 */

import React, { useState, useEffect } from 'react';
import { HttpError } from '../lib/http';
import {
  searchTools,
  recordAuditTrail,
  generateTraceId,
  getCurrentUserId,
} from '../services/selector';
import {
  SelectorSearchRequest,
  SelectorSearchResponse,
  SelectorTool,
} from '../types/selector';
import './SelectorSearch.css';

const AVAILABLE_PLATFORMS = [
  'windows',
  'linux',
  'macos',
  'network',
  'cloud',
];

const SelectorSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [k, setK] = useState(3);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);
  const [results, setResults] = useState<SelectorSearchResponse | null>(null);

  // Countdown timer for retry
  useEffect(() => {
    if (retryAfter !== null && retryAfter > 0) {
      const timer = setTimeout(() => {
        setRetryAfter(retryAfter - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (retryAfter === 0) {
      setRetryAfter(null);
    }
  }, [retryAfter]);

  const handlePlatformToggle = (platform: string) => {
    setSelectedPlatforms(prev => {
      if (prev.includes(platform)) {
        return prev.filter(p => p !== platform);
      } else {
        // Limit to 5 platforms
        if (prev.length >= 5) {
          setError('Maximum 5 platforms allowed');
          return prev;
        }
        return [...prev, platform];
      }
    });
  };

  const handleSearch = async () => {
    // Validation
    if (!query.trim()) {
      setError('Query is required');
      return;
    }

    if (query.length > 200) {
      setError('Query must be 200 characters or less');
      return;
    }

    if (k < 1 || k > 10) {
      setError('K must be between 1 and 10');
      return;
    }

    setLoading(true);
    setError(null);
    setRetryAfter(null);
    setResults(null);

    const startTime = Date.now();
    const traceId = generateTraceId();

    try {
      const request: SelectorSearchRequest = {
        query: query.trim(),
        k,
        platforms: selectedPlatforms.length > 0 ? selectedPlatforms : undefined,
      };

      console.log(`[Selector] Starting search: query="${request.query}", k=${request.k}, platforms=${request.platforms?.join(',') || 'none'}`);
      
      const response = await searchTools(request);
      const duration = Date.now() - startTime;
      
      // Runtime guard: ensure response has required fields
      if (!response || typeof response !== 'object') {
        throw new Error('Invalid response from server');
      }
      
      const safeResponse: SelectorSearchResponse = {
        query: response.query || request.query,
        platforms: response.platforms || request.platforms || [],
        k: response.k || request.k || k,
        results: Array.isArray(response.results) ? response.results : [],
        from_cache: response.from_cache === true,
        duration_ms: typeof response.duration_ms === 'number' ? response.duration_ms : duration,
      };
      
      console.log(`[Selector] Search completed in ${duration}ms: ${safeResponse.results.length} results, from_cache=${safeResponse.from_cache}`);
      
      setResults(safeResponse);

      // Record audit trail (fire-and-forget)
      recordAuditTrail({
        trace_id: traceId,
        user_id: getCurrentUserId(),
        input: query.trim(),
        output: `Found ${safeResponse.results.length} tools`,
        tools: [
          {
            name: 'selector',
            latency_ms: duration,
            ok: true,
          },
        ],
        duration_ms: duration,
        created_at: new Date().toISOString(),
      });
    } catch (err) {
      const duration = Date.now() - startTime;
      console.error(`[Selector] Search failed after ${duration}ms:`, err);
      
      if (err instanceof Error && 'status' in err) {
        const httpError = err as HttpError;

        if (httpError.status === 503 && httpError.retryAfter) {
          setRetryAfter(httpError.retryAfter);
          setError(
            httpError.data?.hint ||
              'Service temporarily unavailable. Please try again.'
          );
        } else if (httpError.status === 400) {
          setError(
            httpError.data?.message ||
              'Invalid request. Please check your input.'
          );
        } else {
          setError(httpError.message || 'An error occurred');
        }
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleSearch();
    }
  };

  return (
    <div className="selector-search">
      <div className="selector-search-header">
        <h2>Tool Selector</h2>
        <p className="selector-search-description">
          Search for tools by describing what you want to do
        </p>
      </div>

      <div className="selector-search-form">
        {/* Query Input */}
        <div className="form-group">
          <label htmlFor="query">Query</label>
          <input
            id="query"
            type="text"
            className="form-control"
            placeholder="e.g., scan windows network interfaces"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            maxLength={200}
            disabled={loading}
          />
          <small className="form-text">
            {query.length}/200 characters
          </small>
        </div>

        {/* K Input */}
        <div className="form-group">
          <label htmlFor="k">Number of Results (k)</label>
          <input
            id="k"
            type="number"
            className="form-control"
            min={1}
            max={10}
            value={k}
            onChange={e => setK(parseInt(e.target.value, 10))}
            disabled={loading}
          />
          <small className="form-text">Between 1 and 10</small>
        </div>

        {/* Platform Selection */}
        <div className="form-group">
          <label>Platforms (optional, max 5)</label>
          <div className="platform-selector">
            {AVAILABLE_PLATFORMS.map(platform => (
              <button
                key={platform}
                type="button"
                className={`platform-button ${
                  selectedPlatforms.includes(platform) ? 'selected' : ''
                }`}
                onClick={() => handlePlatformToggle(platform)}
                disabled={loading}
              >
                {platform}
              </button>
            ))}
          </div>
        </div>

        {/* Search Button */}
        <button
          className="btn btn-primary"
          onClick={handleSearch}
          disabled={loading || (retryAfter !== null && retryAfter > 0)}
        >
          {loading ? 'Searching...' : retryAfter !== null && retryAfter > 0 ? `Retry in ${retryAfter}s` : 'Search'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
          {retryAfter !== null && retryAfter > 0 && (
            <div className="retry-countdown">
              Retry available in {retryAfter} seconds
            </div>
          )}
        </div>
      )}

      {/* Results Display */}
      {results && (
        <div className="selector-results">
          <div className="results-header">
            <h3>Results</h3>
            <div className="results-meta">
              <span className="badge badge-info">
                {Array.isArray(results.results) ? results.results.length : 0} tools found
              </span>
              {results.from_cache && (
                <span className="badge badge-warning">From Cache</span>
              )}
              <span className="badge badge-secondary">
                {typeof results.duration_ms === 'number' ? results.duration_ms.toFixed(1) : '0.0'}ms
              </span>
            </div>
          </div>

          {!Array.isArray(results.results) || results.results.length === 0 ? (
            <div className="empty-state">
              <p>No tools found matching your query.</p>
              <p>Try adjusting your search terms or removing platform filters.</p>
            </div>
          ) : (
            <div className="results-list">
              {results.results.map((tool, index) => (
                <ToolCard key={`${tool?.name || 'unknown'}-${index}`} tool={tool} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface ToolCardProps {
  tool: SelectorTool;
}

const ToolCard: React.FC<ToolCardProps> = ({ tool }) => {
  // Runtime guards for missing fields
  if (!tool || typeof tool !== 'object') {
    return (
      <div className="tool-card">
        <div className="tool-name">Unknown Tool</div>
        <div className="tool-description">Tool data unavailable</div>
      </div>
    );
  }

  const name = typeof tool.name === 'string' ? tool.name : 'Unknown Tool';
  const description = typeof tool.short_desc === 'string' ? tool.short_desc : 'No description available';

  return (
    <div className="tool-card">
      <div className="tool-name">{name}</div>
      <div className="tool-description">{description}</div>
    </div>
  );
};

export default SelectorSearch;