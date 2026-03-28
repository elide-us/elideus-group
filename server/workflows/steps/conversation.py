from __future__ import annotations

import logging
import uuid
from typing import Any

from server.workflows import StepResult, WorkflowStep


class ResolvePersonaStep(WorkflowStep):
  step_type = "pipe"
  disposition = "harmless"

  async def try_step(self, app: Any, payload: dict[str, Any], context: dict[str, Any]) -> StepResult:
    openai = app.state.openai
    await openai.on_ready()

    details = await openai.get_persona_definition(payload["persona_name"])
    if details is None:
      raise ValueError(f"Persona '{payload['persona_name']}' not found")
    if details.get("models_recid") is None:
      raise ValueError(f"Persona '{payload['persona_name']}' is missing model configuration")

    return StepResult(
      output={
        "persona_recid": details["recid"],
        "persona_name": details.get("name", payload["persona_name"]),
        "models_recid": int(details["models_recid"]),
        "system_prompt": details.get("prompt", ""),
        "model": details.get("model"),
        "max_tokens": int(details.get("tokens", 0) or 0),
      }
    )


class GatherStoredContextStep(WorkflowStep):
  step_type = "pipe"
  disposition = "harmless"

  async def try_step(self, app: Any, payload: dict[str, Any], context: dict[str, Any]) -> StepResult:
    openai = app.state.openai
    await openai.on_ready()

    if not payload.get("guild_id") or not payload.get("channel_id"):
      return StepResult(output={"stored_context": []})

    try:
      stored = await openai.get_channel_context(payload["guild_id"], payload["channel_id"], limit=20)
    except Exception:
      logging.warning(
        "[GatherStoredContextStep] failed to load stored context",
        exc_info=True,
        extra={"guild_id": payload.get("guild_id"), "channel_id": payload.get("channel_id")},
      )
      stored = []

    return StepResult(output={"stored_context": stored or []})


class AssemblePromptStep(WorkflowStep):
  step_type = "pipe"
  disposition = "harmless"

  async def try_step(self, app: Any, payload: dict[str, Any], context: dict[str, Any]) -> StepResult:
    sections: list[str] = []

    stored_context = context.get("stored_context") or []
    if stored_context:
      lines = []
      for entry in stored_context[-15:]:
        role = entry.get("role") or "user"
        content = entry.get("content") or ""
        if content:
          lines.append(f"{role}: {content}")
      if lines:
        sections.append("Recent stored conversation context:\n" + "\n".join(lines))

    channel_history = payload.get("channel_history") or []
    if channel_history:
      lines = []
      for entry in channel_history[-20:]:
        author = entry.get("author") or "unknown"
        content = entry.get("content") or ""
        if content:
          lines.append(f"{author}: {content}")
      if lines:
        sections.append("Recent channel activity:\n" + "\n".join(lines))

    prompt_context = "\n\n".join(sections)
    thread_id = (
      f"{payload.get('source', 'workflow')}:"
      f"{payload.get('guild_id', '0')}:"
      f"{payload.get('channel_id', '0')}:"
      f"{uuid.uuid4().hex[:12]}"
    )

    return StepResult(output={"prompt_context": prompt_context, "thread_id": thread_id})


class GenerateResponseStep(WorkflowStep):
  step_type = "pipe"
  disposition = "harmless"

  async def try_step(self, app: Any, payload: dict[str, Any], context: dict[str, Any]) -> StepResult:
    openai = app.state.openai
    await openai.on_ready()

    response = await openai.generate_chat(
      system_prompt=context["system_prompt"],
      user_prompt=payload["user_message"],
      model=context.get("model"),
      max_tokens=context.get("max_tokens") if context.get("max_tokens") else None,
      prompt_context=context.get("prompt_context", ""),
      persona=None,
      persona_details=None,
      guild_id=int(payload["guild_id"]) if payload.get("guild_id") else None,
      channel_id=int(payload["channel_id"]) if payload.get("channel_id") else None,
      user_id=int(payload["user_id"]) if payload.get("user_id") else None,
      input_log=payload["user_message"],
      token_count=None,
    )

    content = response.get("content", "")
    model_used = response.get("model", "")
    usage = response.get("usage")

    if not content:
      raise ValueError("OpenAI returned an empty response")

    return StepResult(output={"response_text": content, "model_used": model_used, "usage": usage})


class LogConversationStep(WorkflowStep):
  step_type = "stack"
  disposition = "reversible"

  async def try_step(self, app: Any, payload: dict[str, Any], context: dict[str, Any]) -> StepResult:
    openai = app.state.openai
    await openai.on_ready()

    user_recid = await openai.log_message(
      personas_recid=context["persona_recid"],
      models_recid=context["models_recid"],
      role="user",
      content=payload["user_message"],
      guild_id=payload.get("guild_id"),
      channel_id=payload.get("channel_id"),
      user_id=payload.get("user_id"),
      users_guid=payload.get("users_guid"),
      thread_id=context.get("thread_id"),
    )

    assistant_recid = None
    if context.get("response_text"):
      assistant_recid = await openai.log_message(
        personas_recid=context["persona_recid"],
        models_recid=context["models_recid"],
        role="assistant",
        content=context["response_text"],
        guild_id=payload.get("guild_id"),
        channel_id=payload.get("channel_id"),
        user_id=payload.get("user_id"),
        users_guid=payload.get("users_guid"),
        thread_id=context.get("thread_id"),
      )

    recids_to_delete = [recid for recid in [user_recid, assistant_recid] if recid is not None]
    return StepResult(
      output={
        "user_message_recid": user_recid,
        "assistant_message_recid": assistant_recid,
      },
      compensation={"recids_to_delete": recids_to_delete},
    )

  async def compensate_step(self, app: Any, payload: dict[str, Any], compensation: dict[str, Any]) -> None:
    db = app.state.db
    await db.on_ready()

    for recid in compensation.get("recids_to_delete", []):
      try:
        await db.run_exec("DELETE FROM assistant_conversations WHERE recid = ?", [recid])
      except Exception:
        logging.warning(
          "[LogConversationStep] failed to compensate logged message",
          exc_info=True,
          extra={"recid": recid},
        )
