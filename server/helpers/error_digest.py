from __future__ import annotations

from dataclasses import dataclass
import os
import traceback
from types import TracebackType

OUR_CODE_MARKERS = (
  '/rpc/',
  '/server/',
  '/queryregistry/',
  '/scripts/',
  '/tests/',
)


@dataclass(frozen=True)
class ErrorDigest:
  exception_type: str
  message: str
  origin_function: str
  origin_file: str
  origin_line: int
  our_frames: list[str]
  full_traceback: str

  @classmethod
  def from_exception(
    cls,
    exc: BaseException,
    tb: TracebackType | None = None,
  ) -> 'ErrorDigest':
    source_tb = tb if tb is not None else exc.__traceback__
    traceback_lines = traceback.format_exception(type(exc), exc, source_tb)
    full_traceback = ''.join(traceback_lines)

    extracted = traceback.extract_tb(source_tb) if source_tb else []
    our_code_frames: list[traceback.FrameSummary] = []
    for frame in extracted:
      normalized = frame.filename.replace('\\', '/').lower()
      if 'main.py' in normalized or any(marker in normalized for marker in OUR_CODE_MARKERS):
        our_code_frames.append(frame)

    selected_frames = our_code_frames[-3:]
    if selected_frames:
      origin = selected_frames[-1]
    elif extracted:
      origin = extracted[-1]
    else:
      origin = None

    if origin:
      origin_function = origin.name
      origin_file = origin.filename
      origin_line = origin.lineno
    else:
      origin_function = '<unknown>'
      origin_file = '<unknown>'
      origin_line = 0

    our_frames = [
      f"{frame.filename}:{frame.lineno} in {frame.name}"
      for frame in selected_frames
    ]

    return cls(
      exception_type=exc.__class__.__name__,
      message=str(exc),
      origin_function=origin_function,
      origin_file=origin_file,
      origin_line=origin_line,
      our_frames=our_frames,
      full_traceback=full_traceback,
    )

  @property
  def short(self) -> str:
    filename = os.path.basename(self.origin_file)
    message = self.message.strip().replace('\n', ' ')
    if len(message) > 200:
      message = f"{message[:197]}..."
    return (
      f"[{self.exception_type}] {filename}:{self.origin_line} "
      f"in {self.origin_function} — {message}"
    )

  @property
  def detail(self) -> str:
    details = [self.short]
    for frame in self.our_frames:
      details.append(f"  → {frame}")
    return '\n'.join(details)
