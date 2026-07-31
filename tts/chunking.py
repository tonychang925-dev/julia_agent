from __future__ import annotations

import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？!?])|(?<!\.)\.(?!\.)")


# Regex: matches a segment that is ONLY TTS voice tags with no spoken content.
# These tags are ElevenLabs SSML-style markers. Alone they cause HTTP 400.
_BARE_TAG_RE = re.compile(
    r"^\s*\[(?:呻吟|尖叫|哭|笑|whispers|sighs|sad|excited|nervously|thoughtfully|"
    r"dramatic|stammers|sarcastically|cheerfully|quietly|gasps|shouts|giggles|laughs|"
    r"exhales\s+softly|sighs\s+softly|screams\s+softly)\]\s*$"
)


_NON_SPEECH_RE = re.compile(r"^\s*[。！？!?\.。…，,；;、：:\-—_~\s]+\s*$")


_ORDINAL_WORDS = {"1": "第一", "2": "第二", "3": "第三", "4": "第四", "5": "第五"}


def _replace_numbered_item(match: re.Match[str]) -> str:
    prefix = match.group(1) or ""
    digit = match.group(2)
    return f"{prefix}{_ORDINAL_WORDS.get(digit, digit)}，"


def _normalize_tts_text(text: str) -> str:
    """Normalize model text before sentence segmentation/TTS.

    DeepSeek often emits ASCII ellipses (``...``) as one streaming chunk.
    If ``.`` is treated as a sentence boundary first, realtime TTS receives
    ``Tony.``, then ``.``, then ``.`` as separate utterances; ElevenLabs may
    return empty audio for the punctuation-only chunks.  Normalize ellipses
    before segmentation so pauses stay attached to spoken text.

    The realtime voice path also needs a spoken-text projection: markdown and
    parenthesized stage directions are useful for screen text, but sound broken
    when read verbatim by ElevenLabs.
    """
    if not text:
        return text
    text = re.sub(r"\.{2,}", "……", text)
    text = re.sub(r"…{3,}", "……", text)
    text = re.sub(r"……\.+", "……", text)
    text = re.sub(r"\.+……", "……", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"(^|[\n。！？!?])\s*([1-5])\.\s*", _replace_numbered_item, text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _sanitize_spoken_chunk(text: str) -> str:
    text = re.sub(r"（[^）]{1,40}）", "", text)
    text = re.sub(r"\([^)]{1,40}\)", "", text)
    return text.strip()


def _is_non_speech_chunk(text: str) -> bool:
    return bool(_NON_SPEECH_RE.match(text))


def _strip_bare_tags(chunks: list[str]) -> list[str]:
    """Remove chunks that are only tags/stage directions/punctuation."""
    cleaned = [_sanitize_spoken_chunk(c) for c in chunks]
    return [c for c in cleaned if c and not _BARE_TAG_RE.match(c) and not _is_non_speech_chunk(c)]


def split_for_tts(text: str, *, max_chars: int = 80) -> list[str]:
    """Split response text into stable TTS chunks.

    Phase 3.2.5.1 favors sentence boundaries, then falls back to max_chars.
    """
    clean = _normalize_tts_text(text).strip()
    if not clean:
        return []

    parts = [p.strip() for p in _SENTENCE_BOUNDARY.split(clean) if p.strip()]
    chunks: list[str] = []
    current = ""
    for part in parts or [clean]:
        if not current:
            current = part
        elif len(current) + len(part) <= max_chars:
            current += part
        else:
            chunks.extend(_hard_split(current, max_chars=max_chars))
            current = part
    if current:
        chunks.extend(_hard_split(current, max_chars=max_chars))
    return _strip_bare_tags(chunks)


def _hard_split(text: str, *, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    remaining = text.strip()
    # Include realtime-friendly pause/format marks.  The previous list missed
    # newlines and ellipses, so long breathy responses were split at an arbitrary
    # character boundary such as ``你每`` / ``一下``.
    soft_marks = ["\n\n", "\n", "……", "…", "，", ",", "；", ";", "——", "—", "：", ":", "]", "）"]
    while len(remaining) > max_chars:
        split_at = -1
        split_len = 0
        for mark in soft_marks:
            search_end = max_chars + len(mark)
            index = remaining.rfind(mark, 0, search_end)
            if index > split_at:
                split_at = index
                split_len = len(mark)
        if split_at < max(12, max_chars // 3):
            whitespace_at = remaining.rfind(" ", 0, max_chars + 1)
            if whitespace_at >= max(12, max_chars // 3):
                split_at = whitespace_at
                split_len = 1
            else:
                split_at = max_chars
                split_len = 0
        else:
            split_at += split_len
        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks

class SentenceSegmenter:
    """Incrementally emits complete sentence-level TTS segments from text chunks."""

    def __init__(self, *, max_chars: int = 120):
        self.max_chars = max_chars
        self._buffer = ""

    def push(self, text: str) -> list[str]:
        self._buffer = _normalize_tts_text(self._buffer + text)
        emitted: list[str] = []
        while True:
            index = self._find_first_boundary(self._buffer)
            if index is None:
                break
            sentence = self._buffer[: index + 1].strip()
            self._buffer = self._buffer[index + 1 :]
            if sentence:
                emitted.extend(_hard_split(sentence, max_chars=self.max_chars))
        if len(self._buffer) >= self.max_chars:
            forced = _hard_split(self._buffer, max_chars=self.max_chars)
            if len(forced) > 1:
                emitted.extend(forced[:-1])
                self._buffer = forced[-1]
        return _strip_bare_tags([item for item in emitted if item])

    def flush(self) -> list[str]:
        if not self._buffer.strip():
            self._buffer = ""
            return []
        chunks = _hard_split(_normalize_tts_text(self._buffer).strip(), max_chars=self.max_chars)
        self._buffer = ""
        return _strip_bare_tags(chunks)

    @staticmethod
    def _find_first_boundary(text: str) -> int | None:
        for index, char in enumerate(text):
            if char in "。！？!?":
                return index
            if char != ".":
                continue
            previous_char = text[index - 1] if index > 0 else ""
            next_char = text[index + 1] if index + 1 < len(text) else ""
            # Do not split inside ASCII ellipses, and wait if a trailing dot may
            # become an ellipsis in the next streaming chunk.
            if previous_char == "." or next_char == "." or previous_char.isdigit() or not next_char:
                continue
            return index
        return None
