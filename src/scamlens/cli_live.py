"""Claude/Antigravity-style live verbose terminal progress renderer for ScamLens-AI CLI."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from rich.console import Console, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

# Stages that represent an ongoing operation (shown with an active spinner until completed)
_ACTIVE_STAGES = {
    "gmail_auth",
    "gmail_search",
    "reading_email",
    "email_forensics",
    "contact_check",
    "analyzing_image",
    "text_analysis",
    "analyzing_url",
    "analyzing_qr",
    "orchestrator_turn",
    "scoring",
}

# Stages that complete the preceding active operation
_DONE_STAGE_PAIRS = {
    "email_forensics_done": "email_forensics",
    "contact_check_done": "contact_check",
    "image_analyzed": "analyzing_image",
    "text_analysis_done": "text_analysis",
    "url_analyzed": "analyzing_url",
    "qr_analyzed": "analyzing_qr",
    "llm_call_done": "orchestrator_turn",
    "completed": "scoring",
}


class _ActiveSpinnerRenderable:
    """Dynamic Rich renderable showing a live spinner, elapsed time, and active task."""

    def __init__(self, display: "LiveProgressDisplay") -> None:
        self._display = display
        self._spinner = Spinner("dots", style="cyan")

    def __rich_console__(self, console: Console, options: Any) -> Any:
        snapshot = self._display._get_active_snapshot()
        if snapshot is None:
            return
        stage, message, detail, started_at = snapshot
        elapsed = max(0.0, time.perf_counter() - started_at)
        is_llm = stage in ("orchestrator_turn", "analyzing_image")

        grid = Table.grid(padding=(0, 1))
        grid.add_column(no_wrap=True)
        grid.add_column()
        grid.add_column(no_wrap=True, justify="right")

        spin_render = self._spinner.render(console.get_time())
        msg_text = Text(message, style="bold bright_magenta" if is_llm else "bold cyan")
        time_text = Text(f"({elapsed:.1f}s)", style="magenta" if is_llm else "dim")
        grid.add_row(spin_render, msg_text, time_text)

        if detail:
            grid.add_row(Text(" "), Text(f"└─ {detail}", style="dim"))

        yield grid


class LiveProgressDisplay:
    """Thread-safe live terminal logger inspired by Claude / Antigravity task feeds.

    In interactive terminals (TTY), maintains a transient animated spinner at the bottom
    while committing completed steps and nested tool outputs cleanly to scrollback.
    In non-TTY environments, prints each event line immediately without cursor control.
    """

    def __init__(self, stderr: bool = False) -> None:
        self.console = Console(stderr=stderr, highlight=False)
        # Lock ordering is strictly: _print_lock -> (Rich Live._lock) -> _state_lock.
        # _ActiveSpinnerRenderable only ever acquires _state_lock, preventing AB-BA deadlocks.
        self._state_lock = threading.Lock()
        self._print_lock = threading.Lock()
        self._live: Optional[Live] = None
        self._run_started_at = time.perf_counter()
        self._active_stage: Optional[str] = None
        self._active_message: Optional[str] = None
        self._active_detail: Optional[str] = None
        self._active_started_at: float = 0.0
        self._step_count = 0
        self._llm_calls_count = 0
        self._llm_total_ms = 0.0
        self._llm_total_tokens = 0

    def __enter__(self) -> "LiveProgressDisplay":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self) -> None:
        """Initialize the live spinner when attached to an interactive terminal."""
        with self._print_lock:
            with self._state_lock:
                self._run_started_at = time.perf_counter()
            if self.console.is_terminal and self._live is None:
                self._live = Live(
                    _ActiveSpinnerRenderable(self),
                    console=self.console,
                    transient=True,
                    refresh_per_second=12,
                    redirect_stdout=False,
                    redirect_stderr=False,
                )
                self._live.start()

    def stop(self) -> None:
        """Flush any pending active step and stop the live spinner."""
        with self._print_lock:
            self._flush_active(status="ok")
            if self._live is not None:
                self._live.stop()
                self._live = None

    def _get_active_snapshot(self) -> Optional[Tuple[str, str, Optional[str], float]]:
        with self._state_lock:
            if not self._active_message:
                return None
            return (
                self._active_stage or "",
                self._active_message,
                self._active_detail,
                self._active_started_at,
            )

    def _emit_line(self, renderable: Union[RenderableType, str]) -> None:
        """Print a persistent line above any active Live spinner, safe from Rich markup errors."""
        safe_renderable: RenderableType = (
            Text(renderable) if isinstance(renderable, str) else renderable
        )
        if self._live is not None:
            self._live.console.print(safe_renderable)
        else:
            self.console.print(safe_renderable)

    def print_text(self, text: str) -> None:
        """Public thread-safe helper to print plain text cleanly alongside live progress."""
        with self._print_lock:
            self._emit_line(Text(text))

    def _pop_active_state(
        self, expected_stage: Optional[str] = None
    ) -> Optional[Tuple[str, str, Optional[str], float]]:
        with self._state_lock:
            if not self._active_message:
                return None
            if expected_stage is not None and self._active_stage != expected_stage:
                return None
            snapshot = (
                self._active_stage or "",
                self._active_message,
                self._active_detail,
                self._active_started_at,
            )
            self._active_stage = None
            self._active_message = None
            self._active_detail = None
            return snapshot

    def _flush_active(
        self,
        status: str = "ok",
        override_message: Optional[str] = None,
        override_detail: Optional[str] = None,
    ) -> None:
        snapshot = self._pop_active_state()
        if snapshot is None:
            return
        _, active_msg, active_detail, started_at = snapshot
        elapsed = max(0.0, time.perf_counter() - started_at)
        msg = override_message or active_msg
        detail = override_detail if override_detail is not None else active_detail
        self._print_step(
            message=msg,
            detail=detail,
            status=status,
            elapsed_s=elapsed,
        )

    def _print_step(
        self,
        message: str,
        detail: Optional[str] = None,
        status: str = "ok",
        elapsed_s: Optional[float] = None,
        indent: int = 0,
        sub_items: Optional[Sequence[str]] = None,
    ) -> None:
        glyph_map = {
            "ok": ("✓", "bold green"),
            "info": ("●", "bold cyan"),
            "orchestrator": ("◆", "bold magenta"),
            "llm": ("🤖", "bold bright_magenta"),
            "dispatch": ("⚡", "bold yellow"),
            "warn": ("⚠", "bold yellow"),
            "error": ("✗", "bold red"),
        }
        glyph, glyph_style = glyph_map.get(status, ("●", "cyan"))
        with self._state_lock:
            rel_s = max(0.0, time.perf_counter() - self._run_started_at)
        prefix = "  " * indent

        line = Text()
        line.append(f"[{rel_s:6.2f}s] ", style="dim")
        line.append(prefix)
        line.append(f"{glyph} ", style=glyph_style)
        if status == "llm":
            line.append(message, style="bold bright_magenta")
        else:
            line.append(
                message,
                style="bold" if status in ("orchestrator", "ok") and indent == 0 else "",
            )
        if elapsed_s is not None:
            line.append(
                f" ({elapsed_s:.2f}s)",
                style="magenta" if status == "llm" else "dim",
            )
        self._emit_line(line)

        details_to_render: List[str] = []
        if detail:
            details_to_render.append(detail)
        if sub_items:
            details_to_render.extend(sub_items)

        detail_style = "bright_magenta" if status == "llm" else "dim"
        for idx, item in enumerate(details_to_render):
            branch = "└─" if idx == len(details_to_render) - 1 else "├─"
            sub = Text()
            sub.append(" " * 10 + prefix)
            sub.append(f"  {branch} ", style="dim")
            sub.append(item, style=detail_style)
            self._emit_line(sub)

    def print_header(self, title: str, meta_lines: Sequence[str]) -> None:
        """Render a clean task header banner at the start of the live process."""
        with self._print_lock:
            body = Text("\n".join(meta_lines), style="dim")
            panel = Panel(
                body,
                title=Text(title, style="bold cyan"),
                border_style="cyan",
                padding=(0, 1),
            )
            self._emit_line(panel)

    def begin_step(
        self,
        stage: str,
        message: str,
        detail: Optional[str] = None,
    ) -> None:
        """Start an active step (animated spinner on TTY, instant line on non-TTY)."""
        is_llm = stage in ("orchestrator_turn", "analyzing_image")
        with self._print_lock:
            self._flush_active(status="ok")
            with self._state_lock:
                self._step_count += 1
                self._active_stage = stage
                self._active_message = message
                self._active_detail = detail
                self._active_started_at = time.perf_counter()
                rel_s = max(0.0, self._active_started_at - self._run_started_at)

            if not self.console.is_terminal:
                line = Text()
                line.append(f"[{rel_s:6.2f}s] ", style="dim")
                line.append("▸ ", style="bold bright_magenta" if is_llm else "cyan")
                line.append(message, style="bold bright_magenta" if is_llm else "cyan")
                self._emit_line(line)
                if detail:
                    sub = Text(" " * 12 + f"└─ {detail}", style="dim")
                    self._emit_line(sub)

    def complete_step(
        self,
        message: str,
        detail: Optional[str] = None,
        status: str = "ok",
        sub_items: Optional[Sequence[str]] = None,
        indent: int = 0,
    ) -> None:
        """Complete the current active step (if any) or emit a standalone milestone."""
        with self._print_lock:
            elapsed: Optional[float] = None
            snapshot = self._pop_active_state()
            if snapshot is not None:
                elapsed = max(0.0, time.perf_counter() - snapshot[3])
            self._print_step(
                message=message,
                detail=detail,
                status=status,
                elapsed_s=elapsed,
                indent=indent,
                sub_items=sub_items,
            )

    def log_email_loaded(self, index: int, total: int, msg: Any) -> None:
        """Display a concise structured snapshot of a freshly fetched email."""
        spf = (getattr(msg, "spf_status", None) or "unknown").upper()
        dkim = (getattr(msg, "dkim_status", None) or "unknown").upper()
        dmarc = (getattr(msg, "dmarc_status", None) or "unknown").upper()
        subject = getattr(msg, "subject", None) or "(No Subject)"
        sender = getattr(msg, "sender", None) or getattr(msg, "sender_email", None) or "(unknown)"
        urls = getattr(msg, "extracted_urls", None) or []
        attachments = getattr(msg, "attachments", None) or []

        auth = f"SPF={spf} | DKIM={dkim} | DMARC={dmarc}"
        sub_items = [
            f"From: {sender}",
            f"Auth: {auth}",
            f"Artifacts: {len(urls)} URL(s), {len(attachments)} attachment(s)",
        ]
        self.complete_step(
            f'[{index}/{total}] Email parsed: "{subject}"',
            status="info",
            sub_items=sub_items,
        )

    def handle_event(self, ev: Dict[str, Any]) -> None:
        """Translate a ScamInvestigator / OpenAICompatibleClient progress event into live UI."""
        stage = str(ev.get("stage") or "status")
        message = str(ev.get("message") or "")
        detail = ev.get("detail")
        data = ev.get("data") or {}

        if stage in _ACTIVE_STAGES:
            self.begin_step(stage, message, detail=detail)
            return

        if stage in _DONE_STAGE_PAIRS:
            expected_active = _DONE_STAGE_PAIRS[stage]
            with self._print_lock:
                elapsed: Optional[float] = None
                matched = self._pop_active_state(expected_stage=expected_active)
                if matched is not None:
                    elapsed = max(0.0, time.perf_counter() - matched[3])
                else:
                    self._flush_active(status="ok")

                if stage in ("llm_call_done", "image_analyzed"):
                    usage = data.get("usage") or {}
                    prompt_tok = usage.get("prompt_tokens")
                    comp_tok = usage.get("completion_tokens")
                    total_tok = usage.get("total_tokens")
                    latency_ms = data.get("latency_ms")
                    with self._state_lock:
                        self._llm_calls_count += 1
                        if isinstance(latency_ms, (int, float)):
                            self._llm_total_ms += float(latency_ms)
                        elif elapsed is not None:
                            self._llm_total_ms += elapsed * 1000.0
                        if isinstance(total_tok, int):
                            self._llm_total_tokens += total_tok

                    token_bits: List[str] = []
                    if prompt_tok is not None and comp_tok is not None:
                        token_bits.append(f"in={prompt_tok}, out={comp_tok}")
                    if total_tok is not None:
                        token_bits.append(f"total={total_tok}")
                    sub_items: List[str] = []
                    if token_bits:
                        sub_items.append(f"Tokens: {', '.join(token_bits)}")
                    if data.get("finish_reason"):
                        sub_items.append(f"Finish: {data['finish_reason']}")

                    # Prefer explicit API latency when provided
                    shown_elapsed = (
                        float(latency_ms) / 1000.0
                        if isinstance(latency_ms, (int, float))
                        else elapsed
                    )
                    self._print_step(
                        message=message,
                        detail=detail,
                        status="llm",
                        elapsed_s=shown_elapsed,
                        sub_items=sub_items or None,
                    )
                    return

                status = "ok"
                if stage == "completed":
                    verdict = str(data.get("verdict", "")).lower()
                    if "scam" in verdict:
                        status = "warn"

                self._print_step(
                    message=message,
                    detail=detail,
                    status=status,
                    elapsed_s=elapsed,
                )
            return

        if stage == "orchestrator_start":
            self.complete_step(message, detail=detail, status="orchestrator")
            return

        if stage == "orchestrator_tools_dispatched":
            self.complete_step(message, detail=detail, status="dispatch")
            return

        if stage == "orchestrator_tool_done":
            args = data.get("arguments") or {}
            args_preview = ", ".join(
                f"{k}={repr(v)[:60]}" for k, v in args.items()
            )
            sub_items: List[str] = []
            if args_preview:
                sub_items.append(f"args: {args_preview}")
            findings_summary = data.get("findings_summary") or []
            for fs in findings_summary[:3]:
                sub_items.append(f"signal: {fs}")
            if len(findings_summary) > 3:
                sub_items.append(f"... +{len(findings_summary) - 3} more indicator(s)")

            with self._print_lock:
                self._print_step(
                    message=message,
                    detail=detail,
                    status="ok",
                    indent=1,
                    sub_items=sub_items or None,
                )
            return

        if stage in ("orchestrator_fallback", "incident_stage"):
            self.complete_step(message, detail=detail, status="warn")
            return

        if stage in ("privacy_guard", "urls_extracted"):
            self.complete_step(message, detail=detail, status="info")
            return

        # Generic fallback for any custom event stage
        self.complete_step(message, detail=detail, status="info")

    def print_footer(self, scanned_count: int) -> None:
        """Print final elapsed time and LLM call summary for the entire CLI run."""
        with self._print_lock:
            self._flush_active(status="ok")
            with self._state_lock:
                total_s = max(0.0, time.perf_counter() - self._run_started_at)
                llm_count = self._llm_calls_count
                llm_s = self._llm_total_ms / 1000.0
                llm_tokens = self._llm_total_tokens
            line = Text()
            line.append(f"[{total_s:6.2f}s] ", style="dim")
            line.append("✓ ", style="bold green")
            line.append(
                f"Live process finished: {scanned_count} email(s) scanned in {total_s:.2f}s",
                style="bold green",
            )
            if llm_count > 0:
                tok_suffix = f", {llm_tokens} tokens" if llm_tokens > 0 else ""
                line.append(" | ", style="dim")
                line.append(
                    f"LLM Calls: {llm_count} ({llm_s:.2f}s{tok_suffix})",
                    style="bold bright_magenta",
                )
            self._emit_line(line)
