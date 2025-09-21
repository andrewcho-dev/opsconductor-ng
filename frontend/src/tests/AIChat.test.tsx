/**
 * Progressive AI Chat Component Tests
 * Starting simple and building to complex multi-tier scenarios
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AIChat from '../components/AIChat';
import { aiApi } from '../services/api';

// Mock the API
jest.mock('../services/api', () => ({
  aiApi: {
    chat: jest.fn()
  }
}));

const mockedAiApi = aiApi as jest.Mocked<typeof aiApi>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Wrapper component with router
const AITestWrapper: React.FC<{children: React.ReactNode}> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('AIChat Component - Progressive Testing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('[]');
  });

  // LEVEL 1: Basic Component Rendering and Interaction Tests
  
  describe('Level 1: Basic Component Tests', () => {
    test('renders AI chat interface', () => {
      render(<AIChat />, { wrapper: AITestWrapper });
      
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByText(/send/i)).toBeInTheDocument();
    });

    test('allows user to type a message', () => {
      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'What is DNS?' } });
      
      expect(input).toHaveValue('What is DNS?');
    });

    test('clears input after sending message', async () => {
      mockedAiApi.chat.mockResolvedValue({
        response: 'DNS stands for Domain Name System...',
        intent: 'information',
        confidence: 0.95,
        execution_started: false
      });

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'What is DNS?' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });

    test('displays loading state while waiting for response', async () => {
      mockedAiApi.chat.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          response: 'Test response',
          intent: 'information',
          confidence: 0.95,
          execution_started: false
        }), 100))
      );

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);
      
      expect(screen.getByRole('textbox')).toBeDisabled();
      
      await waitFor(() => {
        expect(screen.getByRole('textbox')).not.toBeDisabled();
      });
    });

    test('handles empty message submission', () => {
      render(<AIChat />, { wrapper: AITestWrapper });
      
      const sendButton = screen.getByText(/send/i);
      fireEvent.click(sendButton);
      
      expect(mockedAiApi.chat).not.toHaveBeenCalled();
    });
  });

  // LEVEL 2: Basic IT Knowledge Question Tests
  
  describe('Level 2: Basic IT Knowledge Questions', () => {
    const basicITQuestions = [
      'What is TCP/IP?',
      'Explain what DNS does',
      'What is the difference between HTTP and HTTPS?',
      'What is a firewall?',
      'How does SSH work?'
    ];

    test.each(basicITQuestions)('handles basic IT question: %s', async (question) => {
      mockedAiApi.chat.mockResolvedValue({
        response: `Answer about ${question}`,
        intent: 'information',
        confidence: 0.9,
        execution_started: false
      });

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: question } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(mockedAiApi.chat).toHaveBeenCalledWith({
          message: question,
          user_id: 1,
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText(`Answer about ${question}`)).toBeInTheDocument();
      });
    });

    test('maintains conversation context for follow-up questions', async () => {
      const initialResponse = {
        response: 'DNS stands for Domain Name System...',
        intent: 'information',
        confidence: 0.95,
        conversation_id: 'conv_123',
        execution_started: false
      };
      
      const followUpResponse = {
        response: 'DNS servers translate domain names to IP addresses...',
        intent: 'information',
        confidence: 0.92,
        conversation_id: 'conv_123',
        execution_started: false
      };

      mockedAiApi.chat
        .mockResolvedValueOnce(initialResponse)
        .mockResolvedValueOnce(followUpResponse);

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      // First question
      fireEvent.change(input, { target: { value: 'What is DNS?' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText(/DNS stands for Domain Name System/)).toBeInTheDocument();
      });
      
      // Follow-up question
      fireEvent.change(input, { target: { value: 'How does it work?' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(mockedAiApi.chat).toHaveBeenCalledWith({
          message: 'How does it work?',
          user_id: 1,
          conversation_id: 'conv_123'
        });
      });
    });
  });

  // LEVEL 3: Complex Multi-Component Questions
  
  describe('Level 3: Complex Multi-Component Scenarios', () => {
    const complexQuestions = [
      'How would you troubleshoot a slow network connection that affects multiple users in different VLANs?',
      'Design a network architecture for a company with 500 employees across 3 locations',
      'Explain how to implement high availability for a web application with database backend'
    ];

    test.each(complexQuestions)('handles complex scenario: %s', async (question) => {
      const complexResponse = {
        response: `Complex multi-step solution for: ${question}...`,
        intent: 'solution_design',
        confidence: 0.85,
        execution_started: false,
        intent_classification: {
          intent_type: 'complex_troubleshooting',
          confidence: 0.85,
          method: 'pattern_matching',
          alternatives: [],
          entities: [],
          context_analysis: {
            confidence_score: 0.85,
            risk_level: 'medium',
            requirements_count: 3,
            recommendations: ['step1', 'step2', 'step3']
          },
          reasoning: 'Complex multi-component question detected',
          metadata: {
            engine: 'ai_brain',
            success: true
          }
        }
      };

      mockedAiApi.chat.mockResolvedValue(complexResponse);

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: question } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(mockedAiApi.chat).toHaveBeenCalledWith({
          message: question,
          user_id: 1,
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText(new RegExp(question.slice(0, 20), 'i'))).toBeInTheDocument();
      });
    });

    test('displays debug information when debug mode is enabled', async () => {
      const debugResponse = {
        response: 'Test response with debug info',
        intent: 'information',
        confidence: 0.9,
        execution_started: false,
        intent_classification: {
          intent_type: 'information_request',
          confidence: 0.9,
          method: 'ml_classifier',
          alternatives: [],
          entities: [],
          context_analysis: {
            confidence_score: 0.9,
            risk_level: 'low',
            requirements_count: 1,
            recommendations: []
          },
          reasoning: 'Simple information request',
          metadata: {
            engine: 'ai_brain',
            success: true
          }
        },
        _routing: {
          service: 'ai_brain',
          service_type: 'general',
          response_time: 150,
          cached: false
        }
      };

      // Mock localStorage to return debug mode enabled
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'opsconductor_ai_debug_mode') return 'true';
        return '[]';
      });

      mockedAiApi.chat.mockResolvedValue(debugResponse);

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Test debug question' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText(/ai_brain/i)).toBeInTheDocument();
      });
    });
  });

  // LEVEL 4: Error Handling and Edge Cases
  
  describe('Level 4: Error Handling and Resilience', () => {
    test('handles API errors gracefully', async () => {
      mockedAiApi.chat.mockRejectedValue(new Error('Network error'));

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText(/error.*network error/i)).toBeInTheDocument();
      });
    });

    test('handles timeout scenarios', async () => {
      mockedAiApi.chat.mockRejectedValue(new Error('timeout'));

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Long running question' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText(/timeout/i)).toBeInTheDocument();
      });
    });

    test('handles malformed API responses', async () => {
      mockedAiApi.chat.mockResolvedValue({} as any);

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);
      
      // Should not crash and should handle gracefully
      await waitFor(() => {
        expect(screen.getByRole('textbox')).not.toBeDisabled();
      });
    });

    test('persists chat history to localStorage', async () => {
      mockedAiApi.chat.mockResolvedValue({
        response: 'Test response',
        intent: 'information',
        confidence: 0.9,
        execution_started: false
      });

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Test question' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'opsconductor_ai_chat_history',
          expect.stringContaining('Test question')
        );
      });
    });
  });

  // LEVEL 5: Advanced Integration and Performance
  
  describe('Level 5: Advanced Integration Scenarios', () => {
    test('handles automation job creation responses', async () => {
      const automationResponse = {
        response: 'Created automation job for your request',
        intent: 'automation',
        confidence: 0.95,
        job_id: 'job_123',
        automation_job_id: 456,
        execution_started: true,
        execution_started: true,
        workflow: {
          name: 'Network Diagnostics',
          steps: ['check_connectivity', 'analyze_logs', 'generate_report']
        }
      };

      mockedAiApi.chat.mockResolvedValue(automationResponse);

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { 
        target: { value: 'Create a job to check network connectivity for all servers' }
      });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText(/automation job #456 has been started/i)).toBeInTheDocument();
      });
    });

    test('handles multiple rapid-fire questions', async () => {
      const questions = [
        'What is DNS?',
        'What is DHCP?',
        'What is a firewall?'
      ];

      // Mock responses for each question
      questions.forEach((_, index) => {
        mockedAiApi.chat.mockResolvedValueOnce({
          response: `Response ${index + 1}`,
          intent: 'information',
          confidence: 0.9,
          execution_started: false
        });
      });

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      // Send multiple questions rapidly
      for (let i = 0; i < questions.length; i++) {
        fireEvent.change(input, { target: { value: questions[i] } });
        fireEvent.click(sendButton);
      }
      
      // All questions should be sent
      await waitFor(() => {
        expect(mockedAiApi.chat).toHaveBeenCalledTimes(questions.length);
      });
      
      // All responses should appear
      await waitFor(() => {
        questions.forEach((_, index) => {
          expect(screen.getByText(`Response ${index + 1}`)).toBeInTheDocument();
        });
      });
    });

    test('handles very long responses gracefully', async () => {
      const longResponse = 'A'.repeat(10000); // 10KB response
      
      mockedAiApi.chat.mockResolvedValue({
        response: longResponse,
        intent: 'information',
        confidence: 0.9,
        execution_started: false
      });

      render(<AIChat />, { wrapper: AITestWrapper });
      
      const input = screen.getByRole('textbox');
      const sendButton = screen.getByText(/send/i);
      
      fireEvent.change(input, { target: { value: 'Complex question requiring detailed response' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        // Should render without performance issues
        expect(screen.getByText(longResponse.substring(0, 100))).toBeInTheDocument();
      });
    });
  });
});