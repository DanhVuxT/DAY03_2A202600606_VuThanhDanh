# Individual Report: Lab 3 - Chatbot vs ReAct Agent

**Student Name:** Vũ Thành Danh  
**Student ID:** 2A202600606  
**Date:** 06/01/2026

---

# I. Technical Contribution (15 Points)

## Modules Implemented

- `src/core/openrouter_provider.py` - OpenRouter API integration for accessing multiple LLM models.
- `src/core/gemini_provider.py` - Google Gemini API integration (migrated to new SDK).
- `src/agent/agent.py` - ReAct agent core logic with Thought-Action-Observation loop.
- `src/tools/weather_tools.py` - Mock weather tools for demonstration.
- `src/telemetry/logger.py` - Event logging system for debugging.

## Code Highlights

### OpenRouter Provider Implementation

```python
class OpenRouterProvider:
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model_name,
                "messages": messages
            }
        )

        return {
            "content": response.json()["choices"][0]["message"]["content"]
        }
```

### ReAct Action Parser

```python
def _parse_action(self, llm_output: str) -> Optional[tuple]:
    action_line = re.search(r'Action:\s*(\w+)\((.*?)\)', llm_output)

    if action_line:
        tool_name = action_line.group(1)
        args = self._parse_arguments(action_line.group(2))
        return (tool_name, args)

    return None
```

## Documentation

The agent follows a strict ReAct loop:

1. **Thought** – LLM reasons about what to do next.
2. **Action** – LLM selects a tool with parameters.
3. **Observation** – System executes the tool and returns the result.
4. The loop continues until a **Final Answer** is produced.

---

# II. Debugging Case Study (10 Points)

## Problem Description

Error encountered:

ImportError: cannot import name 'ReActAgent'
from partially initialized module 'src.agent.agent'
```

The agent was stuck in a circular import loop where `agent.py` was trying to import itself.

## Log Source

```python
# File: src/agent/agent.py (line 14)

from src.agent.agent import ReActAgent
```

This line caused the error.

## Diagnosis

### Root Cause

A circular import occurred because:

1. `main.py` imports `ReActAgent` from `src.agent.agent`.
2. Inside `agent.py`, there was another import statement attempting to import `ReActAgent` from the same module.
3. Python could not finish initializing the module before trying to import it again.

### Why This Happened

The import statement was accidentally left in the file after refactoring or copying code from another location.

## Solution

### Fix Applied

```python
# Before

from src.agent.agent import ReActAgent

# After

# No self-import required
```

### Lesson Learned

Always review import statements when refactoring. Python's circular import detection prevented an infinite recursion issue, but proper code review would have avoided the problem entirely.

---

# III. Personal Insights: Chatbot vs ReAct (10 Points)

## 1. Reasoning: How the Thought Block Helps

The Thought block transforms the LLM from a text generator into a reasoning engine.

| Aspect | Simple Chatbot | ReAct Agent with Thought |
|----------|----------|----------|
| Process | Question → Answer | Explicit reasoning before answering |
| Error Handling | May hallucinate | Uses tools to obtain data |
| Transparency | Hidden reasoning | Visible reasoning steps |
| Multi-step Tasks | Limited | Naturally decomposes tasks |

### Example

User: "Should I bring an umbrella tomorrow in Da Nang?"

Thought:
I need to check tomorrow's weather forecast.

Action:
get_weather_forecast(city="Da Nang", days=1)

Observation:
{"condition": "rainy", "rain_chance": 90}

Thought:
The forecast predicts rain.

Final Answer:
Yes, you should bring an umbrella.
```

Without the Thought step, the chatbot may guess. With ReAct, the reasoning process becomes explicit and grounded.

---

## 2. Reliability: When the Agent Performed Worse Than a Chatbot

### Case 1: Simple Factual Questions

**Chatbot**

"Hanoi's weather is 25°C."
```

Fast and direct.

**Agent**

Thought → Action → Observation → Answer
```

Adds unnecessary overhead.

### Case 2: Ambiguous Tool Parameters

Agents may struggle to parse complex parameters such as:

```python
city="Ho Chi Minh City"
```

while a chatbot can often interpret natural language more flexibly.

### Case 3: Infinite or Repeated Loops

An agent can become stuck in:

Thought → Action → Observation
       ↳ Thought → Action → Observation
```

repeating the same action.

A chatbot typically generates only one response and therefore cannot loop indefinitely.

### Conclusion

ReAct is not always better.

- Use **Chatbots** for straightforward Q&A.
- Use **ReAct Agents** when tool usage and multi-step reasoning are required.

---

## 3. Observation: How Environment Feedback Influences Decisions

Observation creates a feedback loop that grounds the model in real-world information.

### Without Observation

User: "Weather in Hanoi?"

LLM:
"It's sunny and 30°C."
```

Potential hallucination.

### With Observation

User: "Weather in Hanoi?"

Action:
get_current_weather(city="Hanoi")

Observation:
{"temp": 25, "condition": "cloudy"}

Final Answer:
"Hanoi is currently cloudy with a temperature of 25°C."
```

### Key Insights

- Observations act as external memory.
- Error observations help recovery.
- Structured JSON outputs are easier to process than free text.

---

# IV. Future Improvements (5 Points)

## Scalability

### Asynchronous Tool Calls

Use `asyncio` to execute independent tool calls concurrently.

### Tool Registry

Replace hardcoded tool lists with a plugin-based registry architecture.

### Distributed Tracing

Integrate OpenTelemetry for monitoring agent execution across services.

## Safety

### Supervisor LLM

```python
supervisor.check(
    action="delete_file",
    risk_level="HIGH",
    requires_approval=True
)
```

### Additional Safety Measures

- Rate limiting.
- Loop prevention.
- Budget tracking.
- Input validation and sanitization.

## Performance

### Tool Retrieval with Vector Databases

```python
relevant_tools = vector_db.similarity_search(
    user_query,
    k=5
)

prompt = f"""
Available tools:
{relevant_tools}

User:
{query}
"""
```

### Additional Optimizations

- Caching repeated tool calls.
- Lightweight models for simple reasoning tasks.
- Large models only for complex decisions.

## Production-Ready Enhancements

- Streaming responses.
- Agent state checkpointing.
- Human-in-the-loop approval systems.

---

# Summary

This lab demonstrated that ReAct agents excel at multi-step reasoning tasks requiring external tool usage, while traditional chatbots remain more efficient for straightforward question-answering scenarios.

The key takeaway is selecting the appropriate architecture for the problem:

- **Simple Q&A** → Direct Chatbot
- **Multi-step Reasoning + Tools** → ReAct Agent
- **Complex Planning** → Tree-of-Thoughts or Graph-ReAct

The debugging exercise highlighted the importance of systematic logging, dependency management, and awareness of circular imports. Future work should focus on hybrid systems capable of dynamically selecting the most appropriate reasoning strategy for a given task.