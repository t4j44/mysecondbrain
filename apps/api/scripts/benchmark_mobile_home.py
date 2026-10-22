"""Reproducible SQL count/timing audit on synthetic in-memory data, never production.

Run from apps/api with its test env: python scripts/benchmark_mobile_home.py
Timings are SQLite harness measurements, not hosted PostgreSQL/API latencies.
"""
import ast
import asyncio
import json
import subprocess
import time
from pathlib import Path

from sqlalchemy import event

import app.services.relationship_metrics as metrics
import app.services.relationships as relationships
from app.models import (
    interactions as _interaction_models,  # noqa: F401 - register production eager-load mappings
)
from app.models.entities import Base
from tests.conftest import TestingSessionLocal, test_engine
from tests.test_mobile_home import seed_home


def baseline_function(path, name):
    content = subprocess.check_output(['git', 'show', '1c4d537:'+path], text=True)
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            namespace = dict(vars(relationships if 'relationships.py' in path else metrics))
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<release-baseline>', 'exec'), namespace)
            return namespace[name]
    raise ValueError(name)


async def main():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    owner, other = '00000000-0000-4000-a000-000000000001', '99999999-9999-4000-a999-999999999999'
    class ReleaseService(relationships.RelationshipService):
        rows = baseline_function('apps/api/app/services/relationships.py', 'rows')
        home = baseline_function('apps/api/app/services/relationships.py', 'home')
        people_for_record = baseline_function('apps/api/app/services/relationships.py', 'people_for_record')
    old_activation = baseline_function('apps/api/app/services/relationship_metrics.py', 'activation')
    output = []
    reference = None
    async with TestingSessionLocal() as db:
        await seed_home(db, owner, other)
        for phase, service, activation in [('before', ReleaseService, old_activation), ('after', relationships.RelationshipService, metrics.activation)]:
            for run in range(4):
                queries = []
                def before(conn, _cursor, _sql, _params, _context, _many):
                    conn.info['mobile_start'] = time.perf_counter()
                def after(conn, _cursor, sql, _params, _context, _many, queries=queries):
                    queries.append({'operation':sql.split()[0], 'ms':round((time.perf_counter()-conn.info['mobile_start'])*1000,3)})
                event.listen(test_engine.sync_engine,'before_cursor_execute',before)
                event.listen(test_engine.sync_engine,'after_cursor_execute',after)
                started=time.perf_counter()
                try:
                    result=await service(db,owner).home()
                    result['activation']=await activation(db,owner)
                finally:
                    event.remove(test_engine.sync_engine,'before_cursor_execute',before)
                    event.remove(test_engine.sync_engine,'after_cursor_execute',after)
                canonical = json.dumps(result, default=str, sort_keys=True)
                if reference is None:
                    reference = canonical
                assert canonical == reference, 'Home response changed between release and overhaul'
                output.append({'phase':phase,'run':run,'query_count':len(queries),'sql_ms':round(sum(row['ms'] for row in queries),3),'wall_ms':round((time.perf_counter()-started)*1000,3),'payload_bytes':len(json.dumps(result,default=str).encode()),'response_equal':True,'queries':queries})
    target=Path('../../.test-tmp/mobile-overhaul/sql-benchmark.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(output,indent=2))
    print(json.dumps([{key:value for key,value in row.items() if key!='queries'} for row in output],indent=2))


asyncio.run(main())
