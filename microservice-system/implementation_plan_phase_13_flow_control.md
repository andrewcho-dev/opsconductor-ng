# Phase 13: Job Flow Control & Logical Operations

**Status:** 📋 PLANNED  
**Estimated Timeline:** 4 Weeks  
**Stack:** Python FastAPI, Flow Control Engine, PostgreSQL, React TypeScript

---

## 🎯 **PHASE OVERVIEW**

Transform job execution from simple linear sequences into powerful, programmable workflows with 22+ flow control operations including conditionals (if/else, switch/case), loops (for, while, foreach), parallel branching, variable operations, and comprehensive error handling (try/catch). This will enable complex business logic within jobs.

---

## 🔀 **FLOW CONTROL OPERATIONS (22+ Operations)**

### **Conditional Logic**
- **flow.if**: If/else conditional execution
- **flow.switch**: Switch/case multi-branch logic
- **flow.condition**: Complex conditional expressions
- **flow.gate**: Conditional job continuation gates

### **Loop Constructs**
- **flow.for**: Traditional for loops with counters
- **flow.while**: While loops with conditions
- **flow.foreach**: Iterate over arrays/objects
- **flow.repeat**: Repeat operations N times
- **flow.until**: Loop until condition is met

### **Parallel Execution**
- **flow.parallel**: Execute steps in parallel
- **flow.race**: First-to-complete parallel execution
- **flow.batch**: Batch processing with concurrency limits
- **flow.fan-out**: Distribute work across multiple targets

### **Variable Operations**
- **var.set**: Set variable values
- **var.get**: Retrieve variable values
- **var.calculate**: Mathematical calculations
- **var.string**: String manipulation operations
- **var.array**: Array operations (push, pop, filter)
- **var.object**: Object manipulation

### **Error Handling**
- **flow.try**: Try/catch error handling
- **flow.retry**: Retry operations with backoff
- **flow.timeout**: Operation timeout handling
- **flow.fallback**: Fallback operations on failure

---

## 📋 **IMPLEMENTATION PHASES**

### **PHASE 13.1: Conditional Logic & Branching** (Week 1)

#### **Flow Control Engine Foundation**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class FlowControlType(Enum):
    IF = "flow.if"
    SWITCH = "flow.switch"
    FOR = "flow.for"
    WHILE = "flow.while"
    PARALLEL = "flow.parallel"
    TRY = "flow.try"

@dataclass
class FlowContext:
    variables: Dict[str, Any]
    job_run_id: str
    target_id: str
    current_step: int
    execution_stack: List[Dict[str, Any]]

class FlowControlStep(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def execute(self, context: FlowContext) -> FlowResult:
        pass

class ConditionalStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        condition = self.config['condition']
        true_steps = self.config.get('true_steps', [])
        false_steps = self.config.get('false_steps', [])
        
        # Evaluate condition
        condition_result = self.evaluate_condition(condition, context.variables)
        
        # Execute appropriate branch
        if condition_result:
            return await self.execute_steps(true_steps, context)
        else:
            return await self.execute_steps(false_steps, context)
    
    def evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Evaluate conditional expression"""
        # Simple expression evaluator (can be enhanced with proper parser)
        # Supports: ==, !=, <, >, <=, >=, and, or, not
        
        # Replace variables in condition
        for var_name, var_value in variables.items():
            condition = condition.replace(f"${{{var_name}}}", str(var_value))
        
        # Evaluate expression safely
        try:
            return eval(condition)  # In production, use a safe expression evaluator
        except:
            return False
```

#### **Switch/Case Implementation**
```python
class SwitchStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        switch_value = self.evaluate_expression(self.config['value'], context.variables)
        cases = self.config['cases']
        default_steps = self.config.get('default', [])
        
        # Find matching case
        for case in cases:
            if case['value'] == switch_value:
                return await self.execute_steps(case['steps'], context)
        
        # Execute default case if no match
        if default_steps:
            return await self.execute_steps(default_steps, context)
        
        return FlowResult(status='completed', message='No matching case found')
```

#### **Job Definition with Flow Control**
```json
{
  "name": "Conditional Deployment Job",
  "description": "Deploy application based on environment",
  "parameters": {
    "environment": {"type": "string", "enum": ["dev", "staging", "prod"]},
    "force_deploy": {"type": "boolean", "default": false}
  },
  "steps": [
    {
      "name": "Check Environment",
      "type": "flow.if",
      "config": {
        "condition": "${environment} == 'prod' and not ${force_deploy}",
        "true_steps": [
          {
            "name": "Production Safety Check",
            "type": "powershell.exec",
            "config": {
              "command": "Write-Host 'Production deployment requires force_deploy=true'"
            }
          },
          {
            "name": "Exit Job",
            "type": "flow.exit",
            "config": {"status": "cancelled", "message": "Production deployment cancelled"}
          }
        ],
        "false_steps": [
          {
            "name": "Proceed with Deployment",
            "type": "flow.switch",
            "config": {
              "value": "${environment}",
              "cases": [
                {
                  "value": "dev",
                  "steps": [
                    {"name": "Deploy to Dev", "type": "powershell.exec", "config": {"command": "Deploy-App -Environment Dev"}}
                  ]
                },
                {
                  "value": "staging",
                  "steps": [
                    {"name": "Deploy to Staging", "type": "powershell.exec", "config": {"command": "Deploy-App -Environment Staging"}}
                  ]
                },
                {
                  "value": "prod",
                  "steps": [
                    {"name": "Deploy to Production", "type": "powershell.exec", "config": {"command": "Deploy-App -Environment Production"}}
                  ]
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

---

### **PHASE 13.2: Loop Constructs** (Week 2)

#### **For Loop Implementation**
```python
class ForLoopStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        start = int(self.evaluate_expression(self.config['start'], context.variables))
        end = int(self.evaluate_expression(self.config['end'], context.variables))
        step = int(self.config.get('step', 1))
        loop_var = self.config['variable']
        loop_steps = self.config['steps']
        
        results = []
        
        for i in range(start, end + 1, step):
            # Set loop variable
            context.variables[loop_var] = i
            
            # Execute loop body
            loop_result = await self.execute_steps(loop_steps, context)
            results.append(loop_result)
            
            # Check for break conditions
            if loop_result.status == 'break':
                break
            elif loop_result.status == 'continue':
                continue
            elif loop_result.status == 'failed' and not self.config.get('continue_on_error', False):
                return FlowResult(status='failed', message=f'Loop failed at iteration {i}')
        
        return FlowResult(status='completed', message=f'Loop completed {len(results)} iterations')

class WhileLoopStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        condition = self.config['condition']
        loop_steps = self.config['steps']
        max_iterations = self.config.get('max_iterations', 1000)
        
        iteration = 0
        results = []
        
        while self.evaluate_condition(condition, context.variables) and iteration < max_iterations:
            iteration += 1
            context.variables['_iteration'] = iteration
            
            # Execute loop body
            loop_result = await self.execute_steps(loop_steps, context)
            results.append(loop_result)
            
            # Check for break conditions
            if loop_result.status == 'break':
                break
            elif loop_result.status == 'continue':
                continue
            elif loop_result.status == 'failed' and not self.config.get('continue_on_error', False):
                return FlowResult(status='failed', message=f'While loop failed at iteration {iteration}')
        
        return FlowResult(status='completed', message=f'While loop completed {iteration} iterations')

class ForEachStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        array_expr = self.config['array']
        item_var = self.config['item_variable']
        index_var = self.config.get('index_variable', '_index')
        loop_steps = self.config['steps']
        
        # Evaluate array expression
        array = self.evaluate_expression(array_expr, context.variables)
        if not isinstance(array, list):
            return FlowResult(status='failed', message='ForEach requires an array')
        
        results = []
        
        for index, item in enumerate(array):
            # Set loop variables
            context.variables[item_var] = item
            context.variables[index_var] = index
            
            # Execute loop body
            loop_result = await self.execute_steps(loop_steps, context)
            results.append(loop_result)
            
            # Check for break conditions
            if loop_result.status == 'break':
                break
            elif loop_result.status == 'continue':
                continue
            elif loop_result.status == 'failed' and not self.config.get('continue_on_error', False):
                return FlowResult(status='failed', message=f'ForEach failed at index {index}')
        
        return FlowResult(status='completed', message=f'ForEach completed {len(results)} iterations')
```

#### **Loop Job Example**
```json
{
  "name": "Multi-Server Deployment",
  "steps": [
    {
      "name": "Deploy to All Servers",
      "type": "flow.foreach",
      "config": {
        "array": "${servers}",
        "item_variable": "server",
        "index_variable": "server_index",
        "continue_on_error": true,
        "steps": [
          {
            "name": "Deploy to Server",
            "type": "powershell.exec",
            "config": {
              "command": "Deploy-Application -Server ${server.hostname} -Version ${version}"
            }
          },
          {
            "name": "Verify Deployment",
            "type": "flow.retry",
            "config": {
              "max_attempts": 3,
              "delay": 30,
              "steps": [
                {
                  "name": "Check Service",
                  "type": "powershell.exec",
                  "config": {
                    "command": "Test-ServiceHealth -Server ${server.hostname}"
                  }
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

---

### **PHASE 13.3: Variable Operations & Flow Control** (Week 3)

#### **Variable Operations**
```python
class VariableOperations:
    @staticmethod
    def set_variable(context: FlowContext, name: str, value: Any) -> FlowResult:
        """Set a variable value"""
        context.variables[name] = value
        return FlowResult(status='completed', message=f'Variable {name} set to {value}')
    
    @staticmethod
    def calculate(context: FlowContext, expression: str, result_var: str) -> FlowResult:
        """Perform mathematical calculation"""
        try:
            # Replace variables in expression
            for var_name, var_value in context.variables.items():
                if isinstance(var_value, (int, float)):
                    expression = expression.replace(f"${{{var_name}}}", str(var_value))
            
            # Evaluate mathematical expression
            result = eval(expression)  # Use safe math evaluator in production
            context.variables[result_var] = result
            
            return FlowResult(status='completed', message=f'Calculation result: {result}')
        except Exception as e:
            return FlowResult(status='failed', message=f'Calculation error: {str(e)}')
    
    @staticmethod
    def string_operation(context: FlowContext, operation: str, **kwargs) -> FlowResult:
        """Perform string operations"""
        if operation == 'concat':
            strings = kwargs.get('strings', [])
            result = ''.join(str(s) for s in strings)
            context.variables[kwargs['result_var']] = result
            
        elif operation == 'replace':
            text = kwargs['text']
            old = kwargs['old']
            new = kwargs['new']
            result = text.replace(old, new)
            context.variables[kwargs['result_var']] = result
            
        elif operation == 'split':
            text = kwargs['text']
            delimiter = kwargs['delimiter']
            result = text.split(delimiter)
            context.variables[kwargs['result_var']] = result
        
        return FlowResult(status='completed', message=f'String operation {operation} completed')

class VariableStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        operation = self.config['operation']
        
        if operation == 'set':
            return VariableOperations.set_variable(
                context, 
                self.config['name'], 
                self.evaluate_expression(self.config['value'], context.variables)
            )
        elif operation == 'calculate':
            return VariableOperations.calculate(
                context,
                self.config['expression'],
                self.config['result_variable']
            )
        elif operation in ['concat', 'replace', 'split']:
            return VariableOperations.string_operation(context, operation, **self.config)
        
        return FlowResult(status='failed', message=f'Unknown variable operation: {operation}')
```

#### **Parallel Execution**
```python
import asyncio

class ParallelStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        parallel_steps = self.config['steps']
        max_concurrency = self.config.get('max_concurrency', len(parallel_steps))
        fail_fast = self.config.get('fail_fast', False)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_step_with_semaphore(step_config):
            async with semaphore:
                return await self.execute_single_step(step_config, context)
        
        # Execute steps in parallel
        tasks = [execute_step_with_semaphore(step) for step in parallel_steps]
        
        if fail_fast:
            # Stop on first failure
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                results.append(result)
                if result.status == 'failed':
                    # Cancel remaining tasks
                    for remaining_task in tasks:
                        if not remaining_task.done():
                            remaining_task.cancel()
                    break
        else:
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = sum(1 for r in results if r.status == 'completed')
        failed = sum(1 for r in results if r.status == 'failed')
        
        if failed == 0:
            return FlowResult(status='completed', message=f'All {successful} parallel steps completed')
        elif successful > 0:
            return FlowResult(status='partial', message=f'{successful} succeeded, {failed} failed')
        else:
            return FlowResult(status='failed', message=f'All {failed} parallel steps failed')
```

---

### **PHASE 13.4: Error Handling & Advanced Logic** (Week 4)

#### **Try/Catch Error Handling**
```python
class TryStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        try_steps = self.config['try_steps']
        catch_steps = self.config.get('catch_steps', [])
        finally_steps = self.config.get('finally_steps', [])
        
        try:
            # Execute try block
            try_result = await self.execute_steps(try_steps, context)
            
            if try_result.status == 'failed':
                # Execute catch block
                if catch_steps:
                    context.variables['_error'] = try_result.error_message
                    catch_result = await self.execute_steps(catch_steps, context)
                    
                    # If catch succeeds, consider the whole try/catch successful
                    if catch_result.status == 'completed':
                        try_result = catch_result
            
            return try_result
            
        finally:
            # Always execute finally block
            if finally_steps:
                await self.execute_steps(finally_steps, context)

class RetryStep(FlowControlStep):
    async def execute(self, context: FlowContext) -> FlowResult:
        steps = self.config['steps']
        max_attempts = self.config.get('max_attempts', 3)
        delay = self.config.get('delay', 1)
        backoff_multiplier = self.config.get('backoff_multiplier', 2)
        
        last_result = None
        current_delay = delay
        
        for attempt in range(1, max_attempts + 1):
            context.variables['_attempt'] = attempt
            
            result = await self.execute_steps(steps, context)
            
            if result.status == 'completed':
                return result
            
            last_result = result
            
            # Wait before retry (except on last attempt)
            if attempt < max_attempts:
                await asyncio.sleep(current_delay)
                current_delay *= backoff_multiplier
        
        return FlowResult(
            status='failed',
            message=f'All {max_attempts} retry attempts failed. Last error: {last_result.error_message}'
        )
```

#### **Advanced Flow Control Job Example**
```json
{
  "name": "Complex Deployment Workflow",
  "parameters": {
    "servers": {"type": "array", "default": ["web1", "web2", "web3"]},
    "version": {"type": "string", "required": true},
    "rollback_on_failure": {"type": "boolean", "default": true}
  },
  "steps": [
    {
      "name": "Initialize Variables",
      "type": "var.set",
      "config": {
        "variables": {
          "deployment_start_time": "${system.timestamp}",
          "successful_deployments": 0,
          "failed_deployments": 0
        }
      }
    },
    {
      "name": "Deploy to Servers",
      "type": "flow.try",
      "config": {
        "try_steps": [
          {
            "name": "Parallel Deployment",
            "type": "flow.parallel",
            "config": {
              "max_concurrency": 2,
              "fail_fast": false,
              "steps": [
                {
                  "name": "Deploy to Each Server",
                  "type": "flow.foreach",
                  "config": {
                    "array": "${servers}",
                    "item_variable": "server",
                    "steps": [
                      {
                        "name": "Deploy with Retry",
                        "type": "flow.retry",
                        "config": {
                          "max_attempts": 3,
                          "delay": 30,
                          "steps": [
                            {
                              "name": "Deploy Application",
                              "type": "powershell.exec",
                              "config": {
                                "command": "Deploy-App -Server ${server} -Version ${version}"
                              }
                            },
                            {
                              "name": "Verify Deployment",
                              "type": "powershell.exec",
                              "config": {
                                "command": "Test-Deployment -Server ${server}"
                              }
                            }
                          ]
                        }
                      },
                      {
                        "name": "Increment Success Counter",
                        "type": "var.calculate",
                        "config": {
                          "expression": "${successful_deployments} + 1",
                          "result_variable": "successful_deployments"
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
        ],
        "catch_steps": [
          {
            "name": "Handle Deployment Failure",
            "type": "flow.if",
            "config": {
              "condition": "${rollback_on_failure}",
              "true_steps": [
                {
                  "name": "Rollback Deployments",
                  "type": "flow.foreach",
                  "config": {
                    "array": "${servers}",
                    "item_variable": "server",
                    "steps": [
                      {
                        "name": "Rollback Server",
                        "type": "powershell.exec",
                        "config": {
                          "command": "Rollback-App -Server ${server}"
                        }
                      }
                    ]
                  }
                }
              ],
              "false_steps": [
                {
                  "name": "Log Failure",
                  "type": "notify.email",
                  "config": {
                    "recipients": ["admin@company.com"],
                    "subject": "Deployment Failed - No Rollback",
                    "body": "Deployment failed but rollback was disabled. Manual intervention required."
                  }
                }
              ]
            }
          }
        ],
        "finally_steps": [
          {
            "name": "Send Deployment Report",
            "type": "notify.email",
            "config": {
              "recipients": ["team@company.com"],
              "subject": "Deployment Report - ${version}",
              "body": "Deployment completed.\nSuccessful: ${successful_deployments}\nFailed: ${failed_deployments}\nDuration: ${system.timestamp - deployment_start_time}ms"
            }
          }
        ]
      }
    }
  ]
}
```

---

## 🎨 **NODE-RED STYLE VISUAL FLOW DESIGNER**

**Inspired by Node-RED's intuitive drag-and-drop interface, OpsConductor's flow control system will feature a canvas-based visual designer where users connect nodes with wires to create complex workflows.**

### **Visual Canvas Layout**
```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Palette          │              Canvas Area                  │
│                      │                                           │
│  🔀 Flow Control     │    [Start] ──→ [Check File] ──┐          │
│  ├ If/Else          │                                │          │
│  ├ Switch/Case      │                                ▼          │
│  ├ For Loop         │                          [File Exists?]   │
│  └ While Loop       │                               │ │         │
│                      │                          True │ │ False  │
│  📁 File Ops         │                               ▼ ▼         │
│  ├ Copy File        │                        [Copy File] [Create] │
│  ├ Move File        │                               │ │         │
│  └ Delete File      │                               ▼ ▼         │
│                      │                            [Join] ──→ [End] │
│  💻 System          │                                           │
│  ├ PowerShell       │                                           │
│  ├ Shell Cmd        │                                           │
│  └ Service          │                                           │
└─────────────────────────────────────────────────────────────────┘
```

### **Node Types & Visual Design**

**Conditional Nodes (Diamond Shape):**
```
     ┌─────────┐
    ╱           ╲
   ╱ File Exists? ╲     ← Diamond for decisions
  ╱               ╲
 ●                 ○ True
  ╲               ╱
   ╲             ╱
    ╲___________╱
          │
          ○ False
```

**Loop Nodes (Rounded Rectangle):**
```
┌─────────────────┐
│ 🔄 For Loop     │
│                 │
│ i = 1 to 5      │  ← Shows loop parameters
│                 │
● ─────────────── ○ ──┐  ← Loop output
└─────────────────┘   │
          │           │
          ○ Loop Body │  ← Connection to loop content
          │           │
          └───────────┘  ← Loop back connection
```

**Parallel Nodes (Multiple Outputs):**
```
┌─────────────────┐
│ ⚡ Parallel     │
│                 │
│ 3 Branches      │
│                 │
● ─────────────── ○ Branch 1
                  ○ Branch 2
                  ○ Branch 3
└─────────────────┘
```

---

## 🔧 **API ENDPOINTS**

### **Flow Control Execution**
```
POST   /api/v1/jobs/:id/execute-flow    # Execute job with flow control
GET    /api/v1/jobs/:id/flow-status     # Get flow execution status
POST   /api/v1/jobs/:id/flow-control    # Control flow execution (pause/resume/stop)
```

### **Flow Validation**
```
POST   /api/v1/jobs/validate-flow       # Validate flow control logic
POST   /api/v1/jobs/simulate-flow       # Simulate flow execution
```

### **Variable Management**
```
GET    /api/v1/runs/:id/variables       # Get job run variables
POST   /api/v1/runs/:id/variables       # Set job run variables
```

---

## 🎯 **EXPECTED BENEFITS**

### **Operational Benefits**
- **Programmable Workflows**: Transform simple job sequences into powerful, adaptive programs
- **Dynamic Execution**: Jobs adapt to runtime conditions, data, and environmental factors
- **Error Resilience**: Comprehensive error handling, recovery, and retry mechanisms
- **Complex Logic**: Support for sophisticated business logic within automation workflows

### **Developer Experience**
- **Visual Programming**: Node-RED style visual flow designer for intuitive workflow creation
- **Rich Control Structures**: Full programming language constructs (loops, conditionals, variables)
- **Debugging Support**: Step-by-step execution tracking and variable inspection
- **Template System**: Reusable flow patterns and logic templates

### **Enterprise Features**
- **Scalable Execution**: Parallel processing and concurrency control
- **Robust Error Handling**: Multi-level error handling and recovery strategies
- **Variable Management**: Comprehensive variable operations and data manipulation
- **Flow Control**: Advanced flow control with branching, looping, and conditional logic

---

This phase will transform OpsConductor from a simple automation tool into a powerful workflow programming platform, enabling users to create sophisticated, adaptive automation workflows that can handle complex business logic and dynamic execution scenarios.