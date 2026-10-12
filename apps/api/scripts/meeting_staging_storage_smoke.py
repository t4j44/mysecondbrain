"""Explicit staging-only opt-in. Uses two USER JWTs, never a service credential.

Creates one synthetic, unprocessed WAV, checks API + Storage isolation, deletes it.
The permanent provider is never called. See docs/meetings/HANDOFF.md for variables.
"""
import asyncio
import io
import os
import wave
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

import httpx


async def main():
    if os.getenv('RUN_MEETING_STAGING_SMOKE') != '1' or os.getenv('MEETING_SMOKE_STAGING_CONFIRMED') != '1':
        raise SystemExit('BLOCKED: this writes synthetic staging data; both explicit staging opt-in flags are required.')
    base = os.environ['MEETING_STAGING_API_URL'].rstrip('/')
    if any(word in urlsplit(base).hostname.lower() for word in ('production','prod.','taj-secondbrain-api.')):
        raise SystemExit('BLOCKED: production host rejected. Use the separate staging API.')
    storage = os.environ['MEETING_STAGING_SUPABASE_URL'].rstrip('/')+'/storage/v1'
    public = os.environ['MEETING_STAGING_PUBLISHABLE_KEY']
    a, b = [os.environ[name] for name in ('MEETING_SMOKE_USER_A_TOKEN','MEETING_SMOKE_USER_B_TOKEN')]
    if a == b:
        raise SystemExit('BLOCKED: two different signed-in users are required.')
    buffer = io.BytesIO()
    with wave.open(buffer,'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\0'*32000)
    async with httpx.AsyncClient(timeout=60) as client:
        headers_a, headers_b = {'Authorization':'Bearer '+a}, {'Authorization':'Bearer '+b}
        create = await client.post(base+'/meetings/captures',headers=headers_a,json={
            'request_id':str(uuid4()),'title':'Synthetic storage isolation smoke',
            'meeting_date':datetime.now(timezone.utc).isoformat(),
            'recording_permission':True,'provider_terms_accepted':True})
        create.raise_for_status()
        identity = create.json()['id']
        try:
            response = await client.post(base+f'/meetings/{identity}/upload-authorization',headers=headers_a,json={'mime_type':'audio/wav'})
            response.raise_for_status()
            url = response.json()['upload_url']
            assert url and '/object/upload/sign/meeting-audio/' in url
            uploaded = await client.put(url,content=buffer.getvalue(),headers={'Content-Type':'audio/wav','x-upsert':'false'})
            uploaded.raise_for_status()
            # Do not finalize: no AI call, quota charge, or false transcript proof.
            object_path = urlsplit(url).path.split('/meeting-audio/',1)[1]
            for suffix in ('','/recording'):
                assert (await client.get(base+f'/meetings/{identity}'+suffix,headers=headers_b)).status_code == 404
            own = await client.get(storage+'/object/authenticated/meeting-audio/'+object_path,
                headers={**headers_a,'apikey':public})
            own.raise_for_status()
            assert own.content == buffer.getvalue()
            other = await client.get(storage+'/object/authenticated/meeting-audio/'+object_path,
                headers={**headers_b,'apikey':public})
            assert other.status_code in {400,401,403,404} and other.content != own.content
            anonymous = await client.get(storage+'/object/public/meeting-audio/'+object_path,headers={'apikey':public})
            assert anonymous.status_code in {400,401,403,404}
            print('PASS: authenticated owner reads; other user and public reads denied. No service-role boundary proof used.')
        finally:
            deleted = await client.delete(base+f'/meetings/{identity}',headers=headers_a)
            deleted.raise_for_status()
            print('Cleanup queued through the existing worker; verify physical object deletion in staging Storage.')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        raise SystemExit('FAIL: staging user/storage check failed. No tokens or response content printed. Check credentials and clean up the synthetic meeting if necessary.') from None
