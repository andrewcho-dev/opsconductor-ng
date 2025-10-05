# E2E Test: AI Chat Functionality

## Test Objective
Verify that the AI Chat interface works and can send/receive messages.

## Prerequisites
- User is logged in
- AI Pipeline service is running

## Test Steps

### 1. Navigate to AI Chat
```
Tool: browser_click
Args: { "selector": "a[href='/ai-chat']" }
Expected: Navigation to AI chat page
```

### 2. Wait for Chat Interface
```
Tool: browser_wait_for_selector
Args: { "selector": "textarea, input[type='text']", "timeout": 5000 }
Expected: Chat input field appears
```

### 3. Verify Chat History Area
```
Tool: browser_wait_for_selector
Args: { "selector": ".chat-messages, .message-container" }
Expected: Message display area exists
```

### 4. Send Test Message
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Hello, can you help me?" 
}
Expected: Message typed in input
```

### 5. Click Send Button
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
Expected: Message sent
```

### 6. Wait for User Message to Appear
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".user-message, .message.user",
  "timeout": 5000 
}
Expected: User message appears in chat
```

### 7. Wait for AI Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message, .message.assistant",
  "timeout": 30000 
}
Expected: AI response appears
```

### 8. Get AI Response Text
```
Tool: browser_get_text
Args: { "selector": ".ai-message:last-child, .message.assistant:last-child" }
Expected: Returns AI response text
```

### 9. Verify Response is Not Empty
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelector('.ai-message:last-child, .message.assistant:last-child')?.textContent?.length > 0" 
}
Expected: Returns true
```

### 10. Test Follow-up Message
```
Tool: browser_fill
Args: { 
  "selector": "textarea, input[type='text']", 
  "text": "Show me all Linux servers" 
}
```

### 11. Send Follow-up
```
Tool: browser_click
Args: { "selector": "button[aria-label='Send'], button:has-text('Send')" }
Expected: Second message sent
```

### 12. Wait for Second Response
```
Tool: browser_wait_for_selector
Args: { 
  "selector": ".ai-message:nth-last-child(1), .message.assistant:nth-last-child(1)",
  "timeout": 30000 
}
Expected: Second AI response appears
```

### 13. Count Total Messages
```
Tool: browser_evaluate
Args: { 
  "script": "document.querySelectorAll('.message, .user-message, .ai-message').length" 
}
Expected: Returns 4 (2 user + 2 AI)
```

### 14. Take Screenshot
```
Tool: browser_screenshot
Args: { 
  "path": "/home/opsconductor/opsconductor-ng/tests/e2e/screenshots/ai-chat.png",
  "fullPage": true
}
Expected: Screenshot saved
```

## Success Criteria
- ✅ Chat interface loads
- ✅ Messages can be sent
- ✅ AI responds to messages
- ✅ Chat history displays correctly
- ✅ Multiple messages work

## Failure Scenarios
- ❌ Chat doesn't load (check frontend routing)
- ❌ Send button doesn't work (check event handlers)
- ❌ No AI response (check AI pipeline service)
- ❌ Response timeout (check LLM service)
- ❌ Messages don't appear (check WebSocket/polling)

## Performance Checks
- Response time < 30 seconds
- UI remains responsive during processing
- No console errors