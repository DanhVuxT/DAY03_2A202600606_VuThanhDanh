import os
import re
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        System prompt instructing the agent to follow ReAct format.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        
        # DÙNG STRING THƯỜNG, KHÔNG DÙNG f-string VÌ CÓ DẤU {}
        prompt = """You are a Weather Assistant AI Agent. You help users get weather information and provide advice.

TOOLS AVAILABLE:
""" + tool_descriptions + """

INSTRUCTIONS - You MUST follow this EXACT format:

Thought: [Your reasoning about what to do next]
Action: tool_name(param1="value1", param2="value2")

After you get the Observation (result), continue with another Thought/Action.

When you have enough information to answer, write:
Final Answer: [Your complete answer to the user]

EXAMPLES:

Example 1 - Get current weather:
User: "What's the weather in Hanoi?"
Thought: I need to get current weather for Hanoi
Action: get_current_weather(city="Hanoi")
Observation: {"temp": 25, "condition": "cloudy", "humidity": 70}
Thought: I have the weather data. Now I can answer.
Final Answer: Hanoi currently has cloudy conditions with a temperature of 25°C and humidity at 70%.

Example 2 - Need forecast:
User: "Should I bring an umbrella tomorrow in Da Nang?"
Thought: I need to check tomorrow's forecast for Da Nang
Action: get_weather_forecast(city="Da Nang", days=1)
Observation: {"date": "2026-06-02", "temp": 28, "condition": "rainy"}
Thought: It will be rainy tomorrow, so user needs an umbrella
Final Answer: Yes, bring an umbrella! Da Nang will have rainy conditions tomorrow with a temperature of 28°C.

IMPORTANT RULES:
1. Each step can ONLY call ONE tool
2. NEVER invent observations - only use what tools return
3. If a tool returns an error, mention it in your final answer
4. Always end with "Final Answer:" when you're done
5. Maximum """ + str(self.max_steps) + """ steps allowed

Now begin!
"""
        return prompt

    def run(self, user_input: str) -> str:
        """
        ReAct loop logic.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # Initialize conversation history
        messages = [{"role": "user", "content": user_input}]
        steps = 0
        previous_actions = []

        while steps < self.max_steps:
            steps += 1
            
            # Build prompt from history
            prompt = self._build_prompt_from_history(messages)
            
            # Generate LLM response
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            output = result.get("content", "")
            
            # Log the step
            logger.log_event("AGENT_STEP", {
                "step": steps,
                "output": output[:300],
                "latency_ms": result.get("latency_ms", 0)
            })
            
            # Check for Final Answer
            if "Final Answer:" in output:
                final_answer = self._extract_final_answer(output)
                logger.log_event("AGENT_END", {"steps": steps, "success": True})
                return final_answer
            
            # Parse Action from output
            action_info = self._parse_action(output)
            
            if action_info:
                tool_name, tool_args = action_info
                
                # Check for loop detection
                action_signature = f"{tool_name}({json.dumps(tool_args)})"
                if action_signature in previous_actions:
                    logger.log_event("LOOP_DETECTED", {"action": action_signature, "step": steps})
                    return f"I'm stuck in a loop calling {tool_name}. Please rephrase your request."
                previous_actions.append(action_signature)
                
                # Execute the tool
                observation = self._execute_tool(tool_name, tool_args)
                
                # Add to conversation history
                messages.append({"role": "assistant", "content": output})
                messages.append({"role": "observation", "content": f"Observation: {observation}"})
            else:
                # No valid action found
                logger.log_event("AGENT_ERROR", {"error": "No valid action found", "output": output[:200]})
                return "I couldn't determine what action to take. Please rephrase your request."
        
        # Max steps exceeded
        logger.log_event("AGENT_END", {"steps": self.max_steps, "success": False, "error": "max_steps exceeded"})
        return f"Unable to complete within {self.max_steps} steps. Please simplify your request."

    def _build_prompt_from_history(self, messages: List[Dict]) -> str:
        """Build prompt string from conversation history"""
        prompt_parts = []
        for msg in messages:
            if msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"Assistant: {msg['content']}")
            elif msg["role"] == "observation":
                prompt_parts.append(msg["content"])
            elif isinstance(msg.get("content"), str) and msg["content"].startswith("Observation:"):
                prompt_parts.append(msg["content"])
        return "\n\n".join(prompt_parts)

    def _parse_action(self, llm_output: str) -> Optional[tuple]:
        """
        Parse Action from LLM output.
        Expected format: Action: tool_name(param1="value1", param2=123)
        """
        lines = llm_output.strip().split('\n')
        action_line = None
        for line in lines:
            if line.strip().startswith("Action:"):
                action_line = line.strip()
                break
        
        if not action_line:
            return None
        
        action_part = action_line[7:].strip()
        match = re.match(r'(\w+)\((.*)\)', action_part)
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        args = {}
        if args_str:
            pairs = re.findall(r'(\w+)=["\']?([^"\',)]+)["\']?', args_str)
            for key, value in pairs:
                if value.isdigit():
                    args[key] = int(value)
                elif value.lower() == 'true':
                    args[key] = True
                elif value.lower() == 'false':
                    args[key] = False
                else:
                    args[key] = value.strip('"\'')
        
        return (tool_name, args)

    def _extract_final_answer(self, llm_output: str) -> str:
        """Extract text after 'Final Answer:'"""
        if "Final Answer:" in llm_output:
            parts = llm_output.split("Final Answer:", 1)
            return parts[1].strip()
        return llm_output

    def _execute_tool(self, tool_name: str, args: Dict) -> str:
        """Execute tool by name with given arguments."""
        tool_def = None
        for tool in self.tools:
            if tool['name'] == tool_name:
                tool_def = tool
                break
        
        if not tool_def:
            error_msg = f"Tool '{tool_name}' not found. Available tools: {[t['name'] for t in self.tools]}"
            logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": error_msg})
            return error_msg
        
        if 'function' in tool_def:
            try:
                result = tool_def['function'](**args)
                if isinstance(result, (dict, list)):
                    result_str = json.dumps(result, ensure_ascii=False)
                else:
                    result_str = str(result)
                logger.log_event("TOOL_CALL", {"tool": tool_name, "args": args, "result": result_str[:200]})
                return result_str
            except Exception as e:
                error_msg = f"Error executing {tool_name}: {str(e)}"
                logger.log_event("TOOL_ERROR", {"tool": tool_name, "args": args, "error": str(e)})
                return error_msg
        
        logger.log_event("TOOL_CALL", {"tool": tool_name, "args": args, "result": "mock_result"})
        return f"Mock result from {tool_name} with args {args}"