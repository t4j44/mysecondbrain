"""
Unit and Integration Tests for AI Content Engine & Version Ledger
Module Owner: Agent 9
Verifies zero auto-publishing, pre-generation privacy scans, and claim validation.
"""

import pytest

from app.repositories.content import ContentRepository
from app.services.content.content_service import ContentService


class MockContentDbTable:
    def __init__(self, store: dict, name: str):
        self.store = store
        self.name = name
        self.filters = {}
        self._insert_rec = None
        self._updates = None

    def select(self, *args):
        return self

    def eq(self, k, v):
        self.filters[k] = v
        return self

    def is_(self, k, v):
        return self

    def order(self, *args, **kwargs):
        return self

    def insert(self, record):
        self._insert_rec = record
        return self

    def update(self, updates):
        self._updates = updates
        return self

    async def execute(self):
        if self._insert_rec is not None:
            self.store.setdefault(self.name, []).append(self._insert_rec)

            class Result:
                pass

            res = Result()
            res.data = [self._insert_rec]
            return res

        records = self.store.get(self.name, [])
        if self._updates is not None:
            updated = []
            for r in records:
                if all(r.get(k) == v for k, v in self.filters.items()):
                    r.update(self._updates)
                    updated.append(r)

            class Result:
                pass

            res = Result()
            res.data = updated
            return res

        filtered = [r for r in records if all(r.get(k) == v for k, v in self.filters.items())]

        class Result:
            pass

        res = Result()
        res.data = filtered
        return res


class MockContentDb:
    def __init__(self):
        self.data = {"content_items": [], "content_versions": []}

    def table(self, name: str):
        return MockContentDbTable(self.data, name)


@pytest.mark.asyncio
async def test_zero_auto_publishing_and_version_tracking():
    db = MockContentDb()
    repo = ContentRepository(db)
    service = ContentService(repo)
    user_id = "usr-taj"

    # 1. Verify generation results in draft status
    payload = {"content_type": "linkedin_post", "source_record_ids": ["mem-101"]}
    sources = [
        {"id": "mem-101", "title": "Memory #101", "excerpt": "Verified runtime execution stream."}
    ]

    created = await service.generate_grounded_content(user_id, payload, sources)
    assert created["status"] == "draft"
    assert created["latest_version_number"] == 1
    assert len(db.data["content_versions"]) == 1

    content_id = created["id"]

    # 2. Update body -> trigger version increment
    updated = await service.update_content(
        user_id,
        content_id,
        {"current_body": "Updated draft content test", "change_note": "Added refinement"},
    )
    assert updated["latest_version_number"] == 2
    assert len(db.data["content_versions"]) == 2

    # 3. Restore older version -> does not erase intervention history, creates version 3
    restored = await service.restore_version(user_id, content_id, version_number=1)
    assert restored["latest_version_number"] == 3
    assert "Verified runtime execution stream." in restored["current_body"]
    assert len(db.data["content_versions"]) == 3


def test_pre_generation_privacy_scan_and_claim_validation():
    service = ContentService(repo=None)

    # 1. Privacy scan catches private phone and email
    sources_with_pii = [
        {
            "id": "rec-1",
            "title": "Meeting with John",
            "content": "His private phone is +1 (415) 555-0199 and email john.doe@venture.vc.",
        }
    ]
    warnings = service.perform_privacy_scan(sources_with_pii)
    assert len(warnings) == 1
    assert "Contains private contact information" in warnings[0]["privacy_flag"]

    # 2. Claim verification flags unsupported numbers
    draft = "Our platform achieved 500% growth and enrolled 10,000 users this month."
    clean_sources = [{"id": "s1", "excerpt": "Platform runtime verified without errors."}]

    results = service.validate_authenticity_claims(draft, clean_sources)
    assert any(r["status"] == "unsupported_metric" for r in results)
