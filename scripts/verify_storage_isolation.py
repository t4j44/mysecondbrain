"""Synthetic A/B/anonymous Storage proof. Requires an explicitly isolated staging project.

Set STAGING_STORAGE_TEST=1, STAGING_SUPABASE_URL, STAGING_SUPABASE_PUBLIC_KEY,
STAGING_USER_A_JWT, STAGING_USER_B_JWT. Values and signed URLs are never printed.
"""
import os
from uuid import uuid4

import httpx


def expect_denied(response):
    # Outages, redirects and rate limits cannot count as proof of authorization.
    assert response.status_code in {400, 401, 403, 404}, 'Expected an explicit access denial'


def verify():
    if os.environ.get('STAGING_STORAGE_TEST') != '1':
        raise SystemExit('Set STAGING_STORAGE_TEST=1 only for an isolated staging project.')
    names = ['STAGING_SUPABASE_URL', 'STAGING_SUPABASE_PUBLIC_KEY', 'STAGING_USER_A_JWT', 'STAGING_USER_B_JWT']
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise SystemExit('Missing configuration: ' + ', '.join(missing))
    base, key, token_a, token_b = [os.environ[name].rstrip('/') for name in names]
    if not base.startswith('https://'):
        raise SystemExit('Staging must use HTTPS.')
    def headers(token=None):
        return {'apikey': key, **({'Authorization': 'Bearer ' + token} if token else {})}
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        owners = []
        for token in [token_a, token_b]:
            response = client.get(base + '/auth/v1/user', headers=headers(token))
            assert response.status_code == 200, 'Test user authentication failed'
            owners.append(response.json()['id'])
        assert owners[0] != owners[1], 'Two distinct users are required'
        path = owners[0] + '/isolation-' + str(uuid4()) + '.txt'
        object_url = base + '/storage/v1/object/brain-documents/' + path
        uploaded = False
        try:
            response = client.post(object_url, headers={**headers(token_a), 'Content-Type': 'text/plain'}, content=b'synthetic storage isolation evidence')
            assert response.status_code in (200, 201), 'Owner upload failed'
            uploaded = True
            assert client.get(object_url, headers=headers(token_a)).status_code == 200, 'Owner read failed'
            for token in [token_b, None]:
                expect_denied(client.get(object_url, headers=headers(token)))
                response = client.post(base + '/storage/v1/object/sign/brain-documents/' + path,
                                       headers=headers(token), json={'expiresIn': 60})
                expect_denied(response)
                response = client.put(object_url, headers={**headers(token), 'Content-Type': 'text/plain'}, content=b'forbidden replacement')
                expect_denied(response)
                response = client.request('DELETE', base + '/storage/v1/object/brain-documents',
                                          headers=headers(token), json={'prefixes': [path]})
                # Supabase may return an empty success list for an invisible object.
                if response.status_code not in (200, 204):
                    expect_denied(response)
                original = client.get(object_url, headers=headers(token_a))
                assert original.status_code == 200 and original.content == b'synthetic storage isolation evidence', 'Foreign mutation changed the object'
            public = client.get(base + '/storage/v1/object/public/brain-documents/' + path, headers=headers())
            expect_denied(public)
            response = client.post(base + '/storage/v1/object/sign/brain-documents/' + path,
                                   headers=headers(token_a), json={'expiresIn': 60})
            assert response.status_code == 200, 'Owner signed URL creation failed'
            signed = response.json().get('signedURL') or response.json().get('signedUrl')
            assert isinstance(signed, str) and signed.startswith('/'), 'Unexpected signed URL'
            assert client.get(base + '/storage/v1' + signed).status_code == 200, 'Signed URL read failed'
            # A bearer signed URL is usable by anyone holding it until expiry; it is not an identity check.
            print('PASS: owner upload/read/sign; foreign and anonymous read/sign/update/delete isolated; public read denied.')
        finally:
            if uploaded:
                response = client.request('DELETE', base + '/storage/v1/object/brain-documents',
                                          headers=headers(token_a), json={'prefixes': [path]})
                if response.status_code not in (200, 204):
                    raise RuntimeError('Synthetic fixture cleanup failed; review staging storage.')


if __name__ == '__main__':
    try:
        verify()
    except (httpx.HTTPError, AssertionError, RuntimeError):
        raise SystemExit('Storage verification FAILED. Inspect staging policies and connectivity; no private values were logged.') from None
