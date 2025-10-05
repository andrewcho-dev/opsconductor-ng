#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { chromium, Browser, Page, BrowserContext } from 'playwright';

// Browser state management
let browser: Browser | null = null;
let context: BrowserContext | null = null;
let page: Page | null = null;

// Initialize browser
async function initBrowser() {
  if (!browser) {
    browser = await chromium.launch({
      headless: true, // Headless mode for server environments
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  }
  if (!context) {
    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
  }
  if (!page) {
    page = await context.newPage();
  }
  return { browser, context, page };
}

// Clean up browser
async function closeBrowser() {
  if (page) await page.close();
  if (context) await context.close();
  if (browser) await browser.close();
  page = null;
  context = null;
  browser = null;
}

// Define available tools
const tools: Tool[] = [
  {
    name: 'browser_navigate',
    description: 'Navigate to a URL in the browser',
    inputSchema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'The URL to navigate to'
        }
      },
      required: ['url']
    }
  },
  {
    name: 'browser_click',
    description: 'Click an element on the page using a CSS selector',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector for the element to click'
        },
        timeout: {
          type: 'number',
          description: 'Timeout in milliseconds (default: 30000)',
          default: 30000
        }
      },
      required: ['selector']
    }
  },
  {
    name: 'browser_fill',
    description: 'Fill an input field with text',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector for the input field'
        },
        text: {
          type: 'string',
          description: 'Text to fill in the field'
        }
      },
      required: ['selector', 'text']
    }
  },
  {
    name: 'browser_get_text',
    description: 'Get text content from an element',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector for the element'
        }
      },
      required: ['selector']
    }
  },
  {
    name: 'browser_screenshot',
    description: 'Take a screenshot of the current page',
    inputSchema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Path to save the screenshot (optional)'
        },
        fullPage: {
          type: 'boolean',
          description: 'Capture full page (default: false)',
          default: false
        }
      }
    }
  },
  {
    name: 'browser_wait_for_selector',
    description: 'Wait for an element to appear on the page',
    inputSchema: {
      type: 'object',
      properties: {
        selector: {
          type: 'string',
          description: 'CSS selector to wait for'
        },
        timeout: {
          type: 'number',
          description: 'Timeout in milliseconds (default: 30000)',
          default: 30000
        }
      },
      required: ['selector']
    }
  },
  {
    name: 'browser_evaluate',
    description: 'Execute JavaScript in the browser context',
    inputSchema: {
      type: 'object',
      properties: {
        script: {
          type: 'string',
          description: 'JavaScript code to execute'
        }
      },
      required: ['script']
    }
  },
  {
    name: 'browser_get_url',
    description: 'Get the current page URL',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'browser_go_back',
    description: 'Navigate back in browser history',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'browser_reload',
    description: 'Reload the current page',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'browser_close',
    description: 'Close the browser',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  }
];

// Create MCP server
const server = new Server(
  {
    name: 'opsconductor-browser-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle tool listing
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // Initialize browser if needed (except for close command)
    if (name !== 'browser_close') {
      await initBrowser();
    }

    switch (name) {
      case 'browser_navigate': {
        const { url } = args as { url: string };
        await page!.goto(url, { waitUntil: 'networkidle' });
        return {
          content: [
            {
              type: 'text',
              text: `Navigated to ${url}`
            }
          ]
        };
      }

      case 'browser_click': {
        const { selector, timeout = 30000 } = args as { selector: string; timeout?: number };
        await page!.click(selector, { timeout });
        return {
          content: [
            {
              type: 'text',
              text: `Clicked element: ${selector}`
            }
          ]
        };
      }

      case 'browser_fill': {
        const { selector, text } = args as { selector: string; text: string };
        await page!.fill(selector, text);
        return {
          content: [
            {
              type: 'text',
              text: `Filled ${selector} with text`
            }
          ]
        };
      }

      case 'browser_get_text': {
        const { selector } = args as { selector: string };
        const text = await page!.textContent(selector);
        return {
          content: [
            {
              type: 'text',
              text: text || ''
            }
          ]
        };
      }

      case 'browser_screenshot': {
        const { path, fullPage = false } = args as { path?: string; fullPage?: boolean };
        const screenshot = await page!.screenshot({ 
          path, 
          fullPage,
          type: 'png'
        });
        return {
          content: [
            {
              type: 'text',
              text: path ? `Screenshot saved to ${path}` : 'Screenshot captured'
            }
          ]
        };
      }

      case 'browser_wait_for_selector': {
        const { selector, timeout = 30000 } = args as { selector: string; timeout?: number };
        await page!.waitForSelector(selector, { timeout });
        return {
          content: [
            {
              type: 'text',
              text: `Element found: ${selector}`
            }
          ]
        };
      }

      case 'browser_evaluate': {
        const { script } = args as { script: string };
        const result = await page!.evaluate(script);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      }

      case 'browser_get_url': {
        const url = page!.url();
        return {
          content: [
            {
              type: 'text',
              text: url
            }
          ]
        };
      }

      case 'browser_go_back': {
        await page!.goBack();
        return {
          content: [
            {
              type: 'text',
              text: 'Navigated back'
            }
          ]
        };
      }

      case 'browser_reload': {
        await page!.reload();
        return {
          content: [
            {
              type: 'text',
              text: 'Page reloaded'
            }
          ]
        };
      }

      case 'browser_close': {
        await closeBrowser();
        return {
          content: [
            {
              type: 'text',
              text: 'Browser closed'
            }
          ]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`
        }
      ],
      isError: true
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('OpsConductor Browser MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});