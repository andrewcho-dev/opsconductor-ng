import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { Copy, Download, Check } from 'lucide-react';

interface MessageContentProps {
  content: string;
  isUser: boolean;
  formatToggle?: {
    currentFormat: 'text' | 'json';
    onToggle: () => void;
  };
}

const MessageContent: React.FC<MessageContentProps> = ({ content, isUser, formatToggle }) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyToClipboard = async (code: string) => {
    try {
      console.log('Copying to clipboard:', code.substring(0, 100) + '...'); // Debug log
      
      // Try modern Clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(code);
        setCopiedCode(code);
        setTimeout(() => setCopiedCode(null), 2000);
        console.log('Copy successful (Clipboard API)!'); // Debug log
      } else {
        // Fallback to older method
        const textArea = document.createElement('textarea');
        textArea.value = code;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
          setCopiedCode(code);
          setTimeout(() => setCopiedCode(null), 2000);
          console.log('Copy successful (execCommand fallback)!'); // Debug log
        } else {
          throw new Error('execCommand copy failed');
        }
      }
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy to clipboard. Please select and copy manually.');
    }
  };

  const downloadCode = (code: string, language: string) => {
    const extensions: { [key: string]: string } = {
      javascript: 'js',
      typescript: 'ts',
      python: 'py',
      bash: 'sh',
      shell: 'sh',
      json: 'json',
      yaml: 'yml',
      html: 'html',
      css: 'css',
      sql: 'sql',
      jsx: 'jsx',
      tsx: 'tsx',
      csv: 'csv',
    };

    const ext = extensions[language?.toLowerCase()] || 'txt';
    const mimeType = language?.toLowerCase() === 'csv' ? 'text/csv' : 'text/plain';
    const blob = new Blob([code], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = language?.toLowerCase() === 'csv' ? `export_${Date.now()}.csv` : `code.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="message-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const codeString = String(children).replace(/\n$/, '');

            if (!inline && language) {
              // Block code with syntax highlighting
              return (
                <div style={{ position: 'relative', marginTop: '12px', marginBottom: '12px' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: '#2d2d2d',
                      borderTopLeftRadius: '8px',
                      borderTopRightRadius: '8px',
                      borderBottom: '1px solid #444',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      {!formatToggle && (
                        <span
                          style={{
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            color: '#888',
                            textTransform: 'uppercase',
                          }}
                        >
                          {language}
                        </span>
                      )}
                      {formatToggle && (
                        <div style={{
                          display: 'inline-flex',
                          borderRadius: '4px',
                          backgroundColor: '#1a1a1a',
                          padding: '2px'
                        }}>
                          {(['text', 'json'] as const).map((format) => {
                            const isActive = formatToggle.currentFormat === format;
                            return (
                              <button
                                key={format}
                                onClick={formatToggle.onToggle}
                                style={{
                                  padding: '3px 8px',
                                  fontSize: '11px',
                                  fontWeight: '500',
                                  border: 'none',
                                  borderRadius: '3px',
                                  backgroundColor: isActive ? '#3d3d3d' : 'transparent',
                                  color: isActive ? '#fff' : '#888',
                                  cursor: 'pointer',
                                  transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => {
                                  if (!isActive) {
                                    e.currentTarget.style.backgroundColor = '#2d2d2d';
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  if (!isActive) {
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                  }
                                }}
                              >
                                {format.toUpperCase()}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => copyToClipboard(codeString)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: copiedCode === codeString ? '#10b981' : '#888',
                          cursor: 'pointer',
                          padding: '4px 8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '12px',
                          transition: 'color 0.2s',
                          borderRadius: '4px',
                        }}
                        onMouseEnter={(e) => {
                          if (copiedCode !== codeString) {
                            e.currentTarget.style.backgroundColor = '#3d3d3d';
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                        title="Copy to clipboard"
                      >
                        {copiedCode === codeString ? (
                          <>
                            <Check size={14} />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={14} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => downloadCode(codeString, language)}
                        style={{
                          background: language?.toLowerCase() === 'csv' ? '#10b981' : 'none',
                          border: language?.toLowerCase() === 'csv' ? '1px solid #10b981' : 'none',
                          color: language?.toLowerCase() === 'csv' ? '#fff' : '#888',
                          cursor: 'pointer',
                          padding: '4px 8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '12px',
                          transition: 'all 0.2s',
                          borderRadius: '4px',
                          fontWeight: language?.toLowerCase() === 'csv' ? 600 : 400,
                        }}
                        onMouseEnter={(e) => {
                          if (language?.toLowerCase() === 'csv') {
                            e.currentTarget.style.backgroundColor = '#059669';
                          } else {
                            e.currentTarget.style.backgroundColor = '#3d3d3d';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (language?.toLowerCase() === 'csv') {
                            e.currentTarget.style.backgroundColor = '#10b981';
                          } else {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }
                        }}
                        title={language?.toLowerCase() === 'csv' ? 'Download CSV file' : 'Download code'}
                      >
                        <Download size={14} />
                        <span>{language?.toLowerCase() === 'csv' ? 'Download CSV' : 'Download'}</span>
                      </button>
                    </div>
                  </div>
                  <SyntaxHighlighter
                    style={vscDarkPlus as any}
                    language={language}
                    PreTag="div"
                    customStyle={{
                      margin: 0,
                      borderTopLeftRadius: 0,
                      borderTopRightRadius: 0,
                      borderBottomLeftRadius: '8px',
                      borderBottomRightRadius: '8px',
                      fontSize: '14px',
                    }}
                    {...props}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                </div>
              );
            } else {
              // Inline code
              return (
                <code
                  style={{
                    backgroundColor: isUser ? 'rgba(255, 255, 255, 0.2)' : '#e5e7eb',
                    color: isUser ? '#fff' : '#1f2937',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
                    fontSize: '0.9em',
                  }}
                  {...props}
                >
                  {children}
                </code>
              );
            }
          },
          p({ children }) {
            return <p style={{ margin: '0 0 8px 0', lineHeight: '1.6' }}>{children}</p>;
          },
          ul({ children }) {
            return <ul style={{ margin: '0 0 8px 0', paddingLeft: '20px' }}>{children}</ul>;
          },
          ol({ children }) {
            return <ol style={{ margin: '0 0 8px 0', paddingLeft: '20px' }}>{children}</ol>;
          },
          li({ children }) {
            return <li style={{ marginBottom: '4px' }}>{children}</li>;
          },
          strong({ children }) {
            return <strong style={{ fontWeight: 600 }}>{children}</strong>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MessageContent;