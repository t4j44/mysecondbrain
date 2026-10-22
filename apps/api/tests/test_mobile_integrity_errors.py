import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from app.middleware.error_handling import setup_exception_handlers


@pytest.mark.parametrize('sqlstate,status,code', [('23502', 500, 'INTERNAL_ERROR'), ('23514', 500, 'INTERNAL_ERROR'), ('23505', 409, 'CONFLICT')])
@pytest.mark.asyncio
async def test_constraint_errors_are_classified_without_exposing_sql(sqlstate, status, code):
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get('/fixture')
    async def fixture():
        original = Exception('PRIVATE database detail')
        original.sqlstate = sqlstate
        raise IntegrityError('PRIVATE SQL', {'private': 'PRIVATE parameter'}, original)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
        response = await client.get('/fixture')
    assert response.status_code == status
    assert response.json()['error']['code'] == code
    assert response.json()['error']['request_id'] == 'N/A'
    assert 'PRIVATE' not in response.text
