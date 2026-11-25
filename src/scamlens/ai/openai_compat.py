"""Universal OpenAI-Compatible Client for Groq, Ollama, vLLM, OpenAI, and Gemini.

Provides a unified tool calling interface:
- Groq: https://api.groq.com/openai/v1
- Ollama: http://localhost:11434/v1
- vLLM: http://localhost:8000/v1
- Gemini (OpenAI endpoint): https://generativelanguage.googleapis.com/v1beta/openai
- OpenAI: https://api.openai.com/v1
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scamlens.ai.base import BaseLLMClient
from scamlens.ai.tools import SCAMLENS_TOOLS, ToolDispatcher
from scamlens.core.config import get_settings
from scamlens.core.exceptions import ModelInferenceError

DEFAULT_PRESET_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1",
    "openai": "https://api.openai.com/v1",
    "ollama": "http://localhost:11434/v1",
    "vllm": "http://localhost:8000/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "custom": "",
}


class OpenAICompatibleClient(BaseLLMClient):
    """Universal client supporting the standard OpenAI Chat Completions & Tool Calling API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        vision_model: Optional[str] = None,
        provider: str = "groq",
        ca_cert: Optional[str] = None,
    ):
        settings = get_settings()
        self.provider = provider.lower()

        # Base URL resolution
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif self.provider == "custom":
            self.base_url = (settings.custom_ai_base_url or os.getenv("CUSTOM_AI_BASE_URL", "")).rstrip("/")
        elif self.provider == "vllm" and settings.vllm_base_url:
            self.base_url = settings.vllm_base_url.rstrip("/")
        else:
            default_url = DEFAULT_PRESET_ENDPOINTS.get(self.provider, DEFAULT_PRESET_ENDPOINTS["groq"])
            self.base_url = default_url.rstrip("/")

        # API key resolution
        if api_key is not None:
            self.api_key = api_key
        elif self.provider == "custom":
            self.api_key = settings.custom_ai_api_key or os.getenv("CUSTOM_AI_API_KEY", "")
        elif self.provider == "vllm" and settings.vllm_api_key:
            self.api_key = settings.vllm_api_key
        elif self.provider == "groq":
            self.api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
        elif self.provider == "gemini":
            self.api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        elif self.provider == "openai":
            self.api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
        elif self.provider in ("ollama", "vllm"):
            self.api_key = os.getenv("OPENAI_API_KEY", "local-token")
        else:
            self.api_key = os.getenv("AI_API_KEY", "")

        # Model resolution
        if model:
            self.model = model
        elif self.provider == "custom":
            self.model = settings.custom_ai_model or os.getenv("CUSTOM_AI_MODEL") or "Qwen/Qwen3-8B"
        elif self.provider == "vllm" and settings.vllm_model:
            self.model = settings.vllm_model
        elif self.provider == "groq":
            self.model = settings.groq_model or "llama-3.3-70b-versatile"
        elif self.provider == "gemini":
            self.model = settings.gemini_model or "gemini-1.5-flash"
        elif self.provider == "openai":
            self.model = settings.openai_model or "gpt-4o-mini"
        elif self.provider == "ollama":
            self.model = "llama3.1:latest"
        elif self.provider == "vllm":
            self.model = "default"
        else:
            self.model = "llama-3.3-70b-versatile"

        # Vision model resolution
        if vision_model:
            self.vision_model = vision_model
        elif self.provider == "custom":
            self.vision_model = settings.custom_ai_vision_model or os.getenv("CUSTOM_AI_VISION_MODEL") or self.model
        elif self.provider == "groq":
            self.vision_model = settings.groq_vision_model or "llama-3.2-11b-vision-preview"
        elif self.provider == "gemini":
            self.vision_model = "gemini-1.5-flash"
        elif self.provider == "openai":
            self.vision_model = "gpt-4o-mini"
        else:
            self.vision_model = "llama-3.2-11b-vision-preview"

        # CA Cert resolution (for custom SSL certificates)
        if ca_cert:
            self.ca_cert = ca_cert
        elif self.provider == "custom":
            self.ca_cert = settings.custom_ai_ca_cert or os.getenv("CUSTOM_AI_CA_CERT")
        elif self.provider == "vllm":
            self.ca_cert = settings.vllm_ca_cert or settings.custom_ai_ca_cert or os.getenv("VLLM_CA_CERT") or os.getenv("CUSTOM_AI_CA_CERT")
        else:
            self.ca_cert = os.getenv("CUSTOM_AI_CA_CERT") or os.getenv("SSL_CERT_FILE")

    def _call_chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform POST request to /chat/completions endpoint."""
        endpoint = f"{self.base_url}/chat/completions"

        # Safe offline mock fallback when testing or developing without key
        if not self.api_key and self.provider not in ("ollama", "vllm", "custom"):
            return {
                "choices": [{
                    "message": {
                        "content": (
                            f"[Simulated {self.provider.upper()} Output] Model: {self.model}. "
                            f"Configure {self.provider.upper()}_API_KEY for live inference."
                        ),
                        "tool_calls": None,
                    }
                }]
            }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ScamLens-AI/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        # SSL context for custom CA certificate or self-signed/private endpoints
        urlopen_kwargs: Dict[str, Any] = {"timeout": 60}
        settings = get_settings()
        ca_cert_path = (
            self.ca_cert
            or getattr(settings, "custom_ai_ca_cert", None)
            or os.getenv("CUSTOM_AI_CA_CERT")
            or os.getenv("SSL_CERT_FILE")
        )
        if ca_cert_path:
            p = Path(ca_cert_path)
            if not p.is_absolute():
                _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
                p = (_PROJECT_ROOT / p).resolve()
            if p.is_file():
                import ssl

                urlopen_kwargs["context"] = ssl.create_default_context(cafile=str(p))
        elif endpoint.startswith("https://") and (
            getattr(settings, "custom_ai_insecure_skip_verify", False)
            or os.getenv("CUSTOM_AI_INSECURE_SKIP_VERIFY", "").lower() in ("1", "true", "yes")
        ):
            import ssl

            urlopen_kwargs["context"] = ssl._create_unverified_context()

        try:
            with urllib.request.urlopen(req, **urlopen_kwargs) as resp:
                resp_bytes = resp.read()
                return json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise ModelInferenceError(
                f"{self.provider.upper()} API HTTP error {exc.code} at {endpoint}: {err_body}"
            ) from exc
        except Exception as exc:
            raise ModelInferenceError(
                f"Failed to communicate with {self.provider.upper()} API at {endpoint}: {exc}"
            ) from exc

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.2,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Standard OpenAI chat completion call with tool definitions."""
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        return self._call_chat_completions(payload)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Simple text generation using the OpenAI format."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.chat_completion(messages=messages, temperature=temperature)
        choices = response.get("choices", [])
        if not choices:
            raise ModelInferenceError("Empty response choices received.")
        return choices[0].get("message", {}).get("content", "")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Structured JSON generation using response_format={'type': 'json_object'}."""
        sys_p = system_prompt or "You are an AI scam investigator. Output must be valid JSON."
        if "json" not in sys_p.lower():
            sys_p += " Output must be valid JSON."

        messages = [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        if not self.api_key and self.provider not in ("ollama", "vllm"):
            return {
                "assessment": "SIMULATED_MOCK",
                "provider": self.provider,
                "model": self.model,
            }

        response = self._call_chat_completions(payload)
        content = response["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ModelInferenceError(f"Failed to parse JSON response: {content}") from exc

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Multimodal image/screenshot analysis via OpenAI standard image_url format."""
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "image/png"

        with open(path, "rb") as f:
            encoded_bytes = base64.b64encode(f.read()).decode("utf-8")

        data_url = f"data:{mime_type};base64,{encoded_bytes}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
        messages.append({"role": "user", "content": user_content})

        response = self.chat_completion(
            messages=messages,
            model=self.vision_model,
            temperature=0.2,
        )
        return response["choices"][0]["message"]["content"]

    def _run_single_tool_call(
        self,
        tc: Dict[str, Any],
        turn: int,
        tool_dispatcher: ToolDispatcher,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Any]]:
        """Execute one OpenAI tool_call dict and return history record, ToolMessage, and evidence."""
        tc_id = tc.get("id", f"call_{turn}")
        fn = tc.get("function", {})
        fn_name = fn.get("name", "")
        args_str = fn.get("arguments", "{}")
        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except Exception:
            args = {}
        if not isinstance(args, dict):
            args = {}

        t0 = time.perf_counter()
        if hasattr(tool_dispatcher, "execute_tool_with_evidence"):
            tool_result, evidence = tool_dispatcher.execute_tool_with_evidence(fn_name, args)
        else:
            tool_result = tool_dispatcher.execute_tool(fn_name, args)
            evidence = []
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        history_entry = {
            "id": tc_id,
            "tool": fn_name,
            "arguments": args,
            "result": tool_result,
            "execution_time_ms": elapsed_ms,
        }
        tool_message = {
            "role": "tool",
            "tool_call_id": tc_id,
            "content": json.dumps(tool_result),
        }
        return history_entry, tool_message, evidence

    def run_agent_loop(
        self,
        initial_prompt: str,
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        dispatcher: Optional[ToolDispatcher] = None,
        max_turns: int = 5,
        parallel_tools: bool = True,
        on_event: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute an agentic tool calling loop in OpenAI format.

        Compatible with Groq, OpenAI, Ollama, vLLM, and Gemini.
        1. Model receives messages and available tools.
        2. If model generates tool_calls, dispatcher executes them (concurrently when parallel_tools=True).
        3. Tool results are appended with role: 'tool' and sent back to model.
        4. Loop repeats until model generates final text answer or max_turns is reached
           (on the final allowed turn after tools ran, tools are omitted to force synthesis).
        """
        tools_to_use = tools or SCAMLENS_TOOLS
        tool_dispatcher = dispatcher or ToolDispatcher()

        def _emit(stage: str, message: str, **extra: Any) -> None:
            if callable(on_event):
                try:
                    on_event({"stage": stage, "message": message, **extra})
                except Exception:
                    pass

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_prompt},
        ]
        executed_tool_calls: List[Dict[str, Any]] = []
        collected_evidence: List[Any] = []

        for turn in range(max_turns):
            # Force final text synthesis on the last turn if tools already executed
            is_forced_synthesis = (turn == max_turns - 1) and bool(executed_tool_calls)
            _emit(
                "orchestrator_turn",
                (
                    f"AI Orchestrator turn {turn + 1}/{max_turns}: synthesizing correlated findings..."
                    if is_forced_synthesis
                    else f"AI Orchestrator turn {turn + 1}/{max_turns}: selecting forensic tools..."
                ),
                data={"turn": turn + 1, "max_turns": max_turns, "forced_synthesis": is_forced_synthesis},
            )
            response = self.chat_completion(
                messages=messages,
                tools=None if is_forced_synthesis else tools_to_use,
                tool_choice="auto",
            )
            message = response["choices"][0]["message"]
            tool_calls = message.get("tool_calls")

            # Append assistant message to context
            messages.append(message)

            if not tool_calls:
                return {
                    "final_response": message.get("content", ""),
                    "tool_history": executed_tool_calls,
                    "evidence_items": collected_evidence,
                    "turns": turn + 1,
                }

            requested_names = [tc.get("function", {}).get("name", "") for tc in tool_calls]
            _emit(
                "orchestrator_tools_dispatched",
                f"Dispatching {len(tool_calls)} tool(s): {', '.join(requested_names)}",
                data={"tools": requested_names, "parallel": parallel_tools},
            )

            # Execute requested tools (in parallel when multiple calls emitted)
            if parallel_tools and len(tool_calls) > 1:
                workers = min(8, len(tool_calls))
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    batch = list(
                        executor.map(
                            lambda tc: self._run_single_tool_call(tc, turn, tool_dispatcher),
                            tool_calls,
                        )
                    )
            else:
                batch = [
                    self._run_single_tool_call(tc, turn, tool_dispatcher)
                    for tc in tool_calls
                ]

            for history_entry, tool_message, evidence in batch:
                executed_tool_calls.append(history_entry)
                messages.append(tool_message)
                collected_evidence.extend(evidence)
                _emit(
                    "orchestrator_tool_done",
                    f"Tool '{history_entry['tool']}' completed ({history_entry['execution_time_ms']} ms, {len(evidence)} indicator(s))",
                    data={
                        "tool": history_entry["tool"],
                        "arguments": history_entry["arguments"],
                        "execution_time_ms": history_entry["execution_time_ms"],
                        "findings_count": len(evidence),
                    },
                )

        return {
            "final_response": messages[-1].get("content", "") or "",
            "tool_history": executed_tool_calls,
            "evidence_items": collected_evidence,
            "turns": max_turns,
        }

