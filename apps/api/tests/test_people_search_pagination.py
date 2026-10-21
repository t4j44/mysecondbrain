"""CRM search must include contacts beyond the first 100 without crossing tenants."""
from app.models.entities import Person
from tests.conftest import TestingSessionLocal


async def test_people_search_and_pagination_across_full_network(
    async_client, auth_headers, test_user_id, other_user_id
):
    async with TestingSessionLocal() as db:
        db.add_all([
            Person(user_id=test_user_id, name=f'Network Person {i:03d}',
                   relationship_type='mentor' if i % 2 == 0 else 'contact')
            for i in range(110)
        ])
        db.add(Person(user_id=test_user_id, name='Beyond First Page UniqueTail',
                      relationship_type='investor', notes='Introduced at a pitch event'))
        db.add(Person(user_id=other_user_id, name='Private UniqueTail Investor',
                      relationship_type='investor'))
        await db.commit()

    prefix = '/api/v1/people'
    first = await async_client.get(prefix, headers=auth_headers, params={'limit': 30})
    assert first.status_code == 200, first.text
    data = first.json()
    assert data['total'] == 111
    assert len(data['items']) == 30
    assert data['has_more'] is True

    second = await async_client.get(prefix, headers=auth_headers,
                                    params={'limit': 30, 'offset': 30})
    assert second.status_code == 200
    assert set(item['id'] for item in data['items']).isdisjoint(
        item['id'] for item in second.json()['items'])

    found = await async_client.get(prefix, headers=auth_headers,
                                   params={'q': 'UniqueTail', 'limit': 30})
    assert found.status_code == 200, found.text
    assert found.json()['total'] == 1
    assert [row['name'] for row in found.json()['items']] == ['Beyond First Page UniqueTail']

    filtered = await async_client.get(prefix, headers=auth_headers,
                                      params={'q': 'UniqueTail', 'relationship_type': 'mentor'})
    assert filtered.status_code == 200
    assert filtered.json()['total'] == 0

    investors = await async_client.get(prefix, headers=auth_headers,
                                       params={'relationship_type': 'investor'})
    assert investors.status_code == 200
    assert investors.json()['total'] == 1

    invalid = await async_client.get(prefix, headers=auth_headers,
                                     params={'q': 'x' * 101})
    assert invalid.status_code == 422
