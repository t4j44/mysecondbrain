from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.meeting_outputs import export_markdown
from tests.test_meeting_intelligence import capture


def meeting():
    ref = {'segment_id': 'c0:0', 'speaker_id': 'speaker-a', 'start_seconds': 12,
        'end_seconds': 16, 'quote': 'If approved, I will send the report.'}
    item = {'description': 'Send the report', 'evidence_text': ref['quote'],
        'condition': 'If approved', 'from_speaker': 'speaker-a', 'evidence': [ref]}
    return SimpleNamespace(id='synthetic', title='Synthetic', start_time=datetime(2026, 11, 13, tzinfo=timezone.utc), meta={},
        capture=SimpleNamespace(intelligence={'commitments': [item]}, receipt={}, confirmed_at=None,
            speaker_mappings={'speaker-a': {'kind': 'me'}}, transcript_segments=[{
                'segment_id': ref['segment_id'], 'speaker_local_id': ref['speaker_id'],
                'start_offset': 12, 'end_offset': 16, 'text': ref['quote']}]))


@pytest.mark.parametrize('kind,title', [('founder', 'Founder meeting'), ('client', 'Client call'), ('interview', 'User interview')])
def test_templates_preserve_sources_conditions_and_missing_information(kind, title):
    source = meeting()
    before = deepcopy(source.capture.__dict__)
    result = export_markdown(source, kind)
    assert title in result and 'Proposal — not confirmed' in result
    assert 'Condition: If approved' in result and 'Source speaker: You' in result
    assert '/meetings/synthetic#segment-c0%3A0' in result
    assert 'No supported information available' in result
    assert source.capture.__dict__ == before
    if kind == 'interview':
        assert 'participant claims, not product facts' in result
        assert 'Obtain permission before reusing quotations' in result


@pytest.mark.parametrize('change', ['missing', 'speaker', 'timestamp', 'empty'])
def test_templates_withhold_unverifiable_claims(change):
    source = meeting()
    item = source.capture.intelligence['commitments'][0]
    if change == 'missing':
        item['evidence'] = []
    elif change == 'speaker':
        item['from_speaker'] = 'another-speaker'
    elif change == 'timestamp':
        item['evidence'][0]['start_seconds'] = 999
    else:
        item['evidence_text'] = ' \t '
    result = export_markdown(source, 'founder')
    assert 'Send the report' not in result and 'withheld' in result


def test_confirmed_template_excludes_unselected_and_labels_corrected_assertions():
    source = meeting()
    source.capture.confirmed_at = source.start_time
    source.capture.intelligence['commitments'].append({'description': 'Rejected claim'})
    source.capture.receipt = {'selected': ['commitments:0'], 'corrections': [{
        'candidate_id': 'commitments:0', 'at': 'synthetic', 'reason': 'Owner correction',
        'before': {'description': 'Old description'}, 'after': {'description': 'New description', 'due_at': None}}]}
    source.capture.intelligence['commitments'][0]['description'] = 'New description'
    result = export_markdown(source, 'client')
    assert 'Owner-corrected assertion' in result and 'New description' in result
    assert 'Original quotation: If approved' in result
    assert 'Rejected claim' not in result


@pytest.mark.parametrize('kind', ['founder', 'client', 'interview'])
async def test_template_export_uses_existing_owner_boundary(async_client, auth_headers, other_auth_headers, kind):
    saved = await capture(async_client, auth_headers)
    path = f'/api/v1/meetings/{saved["id"]}/export/markdown?kind={kind}'
    own = await async_client.get(path, headers=auth_headers)
    assert own.status_code == 200
    assert own.headers['cache-control'] == 'no-store'
    assert own.headers['x-content-type-options'] == 'nosniff'
    assert 'No supported information' in own.text
    assert (await async_client.get(path, headers=other_auth_headers)).status_code == 404
    assert (await async_client.get(path)).status_code == 401
