"""Authenticated transcription-only relay, with server metering and automatic rotation."""
import asyncio
import base64
import json
from contextlib import suppress
from uuid import UUID

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from websockets.asyncio.client import connect

from app.ai.provider import GeminiLLMProvider
from app.core.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.database import rls_db_session
from app.services.meeting_intelligence import capture_for, ensure_audio_consent, meter_live


async def live_transcript(socket: WebSocket, identity: UUID):
    # Native clients omit Origin; browser origins must be from configured CORS.
    origin = socket.headers.get('origin')
    if origin and origin not in {*settings.CORS_ORIGINS, *settings.CORS_ALLOWED_ORIGINS}:
        await socket.close(code=1008)
        return
    await socket.accept()
    try:
        async with asyncio.timeout(10):
            auth = await socket.receive_json()
        request = Request({**socket.scope, 'type': 'http'})
        user = await get_current_user(request, HTTPAuthorizationCredentials(scheme='Bearer', credentials=auth.get('token', '')))
        async with rls_db_session(user.id) as db:
            _, capture = await capture_for(db, user.id, str(identity))
            if capture.state not in {'draft', 'recording'}:
                raise ValueError('Recording ended')
            ensure_audio_consent(capture)
        provider = GeminiLLMProvider()
        if provider._is_unconfigured():
            raise ValueError('Provider unavailable')
        url = 'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent'
        # Key goes in a server-only header, never a browser URL or log.
        async with connect(url, additional_headers={'x-goog-api-key': provider.api_key}, max_size=1048576) as remote:
            await remote.send(json.dumps({'setup': {'model': 'models/' + settings.GEMINI_LIVE_TRANSCRIBE_MODEL,
                'generationConfig': {'responseModalities': ['TEXT']},
                'inputAudioTranscription': {'languageCodes': [], 'mode': 'VERBATIM'}}}))
            async with asyncio.timeout(20):
                setup = json.loads(await remote.recv())
                if 'setupComplete' not in setup:
                    raise ValueError('Provider setup failed')
            await socket.send_json({'type': 'ready', 'session_seconds': settings.MEETING_LIVE_SESSION_SECONDS})
            sent_samples = 0

            async def send_audio():
                nonlocal sent_samples
                while True:
                    packet = await socket.receive_bytes()
                    if not packet or len(packet) > 32000 or len(packet) % 2:
                        raise ValueError('Invalid PCM frame')
                    # Reserve each crossed second before any provider transmission.
                    before = (sent_samples + 15999) // 16000
                    sent_samples += len(packet) // 2
                    after = (sent_samples + 15999) // 16000
                    if after > before:
                        async with rls_db_session(user.id) as db:
                            await meter_live(db, user.id, str(identity), after-before)
                            await db.commit()
                    await remote.send(json.dumps({'realtimeInput': {'audio': {
                        'data': base64.b64encode(packet).decode(), 'mimeType': 'audio/pcm;rate=16000'}}}))

            async def receive_text():
                async for message in remote:
                    data = json.loads(message)
                    transcription = data.get('serverContent', {}).get('inputTranscription', {})
                    if transcription.get('text'):
                        await socket.send_json({'type': 'transcript', 'text': transcription['text'],
                            'end_offset': sent_samples / 16000})
                    if data.get('goAway'):
                        await socket.send_json({'type': 'rotate'})
                        return

            async with asyncio.timeout(settings.MEETING_LIVE_SESSION_SECONDS):
                tasks = [asyncio.create_task(send_audio()), asyncio.create_task(receive_text())]
                try:
                    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        task.result()
                finally:
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
    except (TimeoutError, WebSocketDisconnect):
        pass
    except Exception:
        # No provider exception, auth material or transcript reaches logs/errors.
        with suppress(Exception):
            await socket.send_json({'type': 'unavailable', 'message': 'Live transcript reconnecting... Recording continues.'})
    finally:
        with suppress(Exception):
            await socket.close()
