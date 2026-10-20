"""Guard against SQL RPC access to trigger-only SECURITY DEFINER functions."""
import pytest
from sqlalchemy import text

from .conftest import requires_postgres

pytestmark = [pytest.mark.postgres, requires_postgres]

async def test_trigger_definers_not_executable_by_api_roles(pg_engine):
    async with pg_engine.connect() as conn:
        rows = (await conn.execute(text("""
            SELECT p.oid::regprocedure::text AS signature,
                   has_function_privilege('anon', p.oid, 'EXECUTE') AS anonymous,
                   has_function_privilege('authenticated', p.oid, 'EXECUTE') AS signed_in
              FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
             WHERE n.nspname='public' AND p.prosecdef
               AND p.prorettype = 'pg_catalog.trigger'::regtype
        """))).all()
        assert rows
        assert all(not anon and not auth for _, anon, auth in rows)

async def test_rls_helper_and_trigger_search_paths(pg_engine):
    async with pg_engine.connect() as conn:
        r = (await conn.execute(text("""
            SELECT has_function_privilege('anon','public.account_active(uuid)','EXECUTE'),
                   has_function_privilege('authenticated','public.account_active(uuid)','EXECUTE')
        """))).one()
        assert tuple(r) == (False, True)
        rows = (await conn.execute(text("""
            SELECT p.proname, p.proconfig
              FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
             WHERE n.nspname='public'
               AND p.proname IN ('set_updated_at','handle_task_completion','update_person_last_interaction')
        """))).all()
        assert len(rows) == 3
        assert all(any(setting.startswith('search_path=') for setting in (config or []))
                   for _, config in rows)
