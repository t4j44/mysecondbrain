"""CI-only synthetic Docker/worker proof against the disposable loopback PG service."""
import asyncio
import os
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    target = os.environ['POSTGRES_TEST_DATABASE_URL']
    if urlparse(target).hostname not in {'127.0.0.1', 'localhost'}:
        raise RuntimeError('Container smoke requires disposable loopback PostgreSQL.')
    owner, job = str(uuid4()), str(uuid4())
    engine = create_async_engine(target)
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000', timeout=5) as client:
        for _ in range(60):
            try:
                if (await client.get('/health/ready')).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError('Container readiness failed.')
        assert (await client.get('/health/live')).json()['status'] == 'alive'
        assert (await client.get('/health')).json()['release_sha'] == os.environ['GITHUB_SHA']
    try:
        async with engine.begin() as db:
            await db.execute(text('INSERT INTO auth.users(id,email) VALUES(CAST(:owner AS uuid),:email)'),
                {'owner': owner, 'email': owner + '@container.synthetic.test'})
            await db.execute(text("""INSERT INTO public.jobs(id,user_id,job_type,status,result_payload)
                VALUES(CAST(:job AS uuid),CAST(:owner AS uuid),'storage_delete','pending',
                jsonb_build_object('bucket','meeting-audio','path',CAST(:path AS text)))"""),
                {'job': job, 'owner': owner, 'path': owner + '/nonexistent-synthetic-object.flac'})
        for _ in range(40):
            async with engine.connect() as db:
                status = await db.scalar(text('SELECT status FROM public.jobs WHERE id=CAST(:job AS uuid)'), {'job': job})
            if status == 'completed':
                print('PASS: Docker liveness/readiness/SHA, migrated PostgreSQL startup, owner-scoped durable worker job')
                break
            if status == 'failed':
                raise RuntimeError('Container worker failed the synthetic deletion job.')
            await asyncio.sleep(1)
        else:
            raise RuntimeError('Container worker did not process the durable job.')
    finally:
        async with engine.begin() as db:
            await db.execute(text('DELETE FROM auth.users WHERE id=CAST(:owner AS uuid)'), {'owner': owner})
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
