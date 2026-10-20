"""Opt-in, nonconfidential audio only. No transcript or credential is printed.

RUN_MEETING_PROVIDER_SMOKE=1 MEETING_SMOKE_AUDIO=/path/to/consented-sample.wav
Use the same API environment and run from apps/api. Does not write app records.
"""
import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.meeting_provider import GeminiMeetingProvider, extract_intelligence
from app.ai.privacy import private_ai_scope
from app.ai.provider import GeminiLLMProvider
from app.core.config import settings
from app.services.meeting_audio import audio_chunks, audio_mime, inspect_audio


async def main():
    if os.getenv('RUN_MEETING_PROVIDER_SMOKE') != '1':
        raise SystemExit('BLOCKED: set RUN_MEETING_PROVIDER_SMOKE=1 and provide a nonconfidential recording you have permission to process.')
    path = Path(os.environ['MEETING_SMOKE_AUDIO']).resolve(strict=True)
    if GeminiLLMProvider()._is_unconfigured():
        raise SystemExit('BLOCKED: a valid GEMINI_API_KEY is required.')
    mime = audio_mime(os.getenv('MEETING_SMOKE_MIME', 'audio/wav'))
    duration = await inspect_audio(path.read_bytes(), mime)
    segments = []
    async for index, offset, chunk in audio_chunks(path.read_bytes(), mime, duration):
        segments.extend(await GeminiMeetingProvider().transcribe(chunk, index, offset))
    # No personal database context: synthetic request identity and supplied audio only.
    with private_ai_scope(str(uuid4())):
        details = await extract_intelligence('\n'.join(s['text'] for s in segments),
            date=os.getenv('MEETING_SMOKE_DATE', '2026-10-20'),
            speakers=sorted({s['speaker_local_id'] for s in segments}), segments=segments)
    print(f'PASS: duration={duration}s segments={len(segments)} sections={len(details.discussion_sections)} detailed_chars={len(details.detailed_summary)}')
    print(f'Models: final={settings.GEMINI_TRANSCRIBE_MODEL} text={settings.GEMINI_MODEL}; data_mode={settings.AI_DATA_MODE}')
    print('Live streaming, Bangla accuracy and real user storage boundaries still require the phone/staging test.')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        # Provider HTTP errors can contain private text or credentials; never echo.
        raise SystemExit('FAIL: provider or audio setup check failed. No app records were written; inspect model access, API key and audio tools.') from None
