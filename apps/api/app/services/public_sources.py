"""Small public-page adapter. No cookies, redirects, proxy, browser or auth bypass."""
import asyncio
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import quote, urlsplit
from urllib.robotparser import RobotFileParser

from app.core.errors import ValidationError

AGENT = 'SecondBrainPublicResearch/1.0'
MAX_BYTES = 512_000


def public_url(value):
    try:
        parts = urlsplit(value)
        host = (parts.hostname or '').encode('idna').decode('ascii').lower()
        if parts.scheme != 'https' or parts.port not in (None, 443) or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError()
        if not host or '.' not in host or len(value) > 2000 or any(ord(char) < 33 for char in value):
            raise ValueError()
        if host.endswith(('.localhost', '.local', '.internal', '.test', '.invalid')):
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError()
    except (ValueError, UnicodeError) as error:
        raise ValidationError('Use a public HTTPS page on port 443 without sign-in tokens, query parameters or fragments.') from error
    path = quote(parts.path or '/', safe='/%:@!$&\'()*+,;=-._~')
    return host, path


def resolve_public(host):
    results = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addresses = sorted({result[4][0] for result in results})
    if not addresses or any(not ipaddress.ip_address(value).is_global for value in addresses):
        raise ValidationError('This address is not a permitted public source.')
    return addresses[0]


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, timeout):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        # The checked numeric address is used for TCP; the original hostname is
        # still verified by TLS. No second hostname lookup or implicit redirect.
        connection = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(connection, server_hostname=self.host)
        except Exception:
            connection.close()
            raise


def request_page(host, address, path, deadline):
    connection = PinnedHTTPSConnection(host, address, max(.1, min(8, deadline - time.monotonic())))
    try:
        connection.request('GET', path, headers={'Host': host, 'User-Agent': AGENT, 'Accept': 'text/html,text/plain', 'Accept-Encoding': 'identity'})
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise ValidationError('This source redirects. Open the page yourself and supply its final public URL.')
        if response.getheader('Content-Encoding', 'identity') != 'identity':
            raise ValidationError('This source requires an unsupported encoding.')
        body = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            if connection.sock:
                connection.sock.settimeout(min(8, remaining))
            chunk = response.read1(min(16384, MAX_BYTES + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > MAX_BYTES:
                raise ValidationError('This page is too large for a bounded public-source review.')
        return response.status, response.getheader('Content-Type', ''), bytes(body).decode('utf-8', errors='replace')
    finally:
        connection.close()


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
        self.structured = []
        self.json_script = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.hidden += 1
            self.json_script = tag == 'script' and dict(attrs).get('type') == 'application/ld+json'

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self.hidden = max(0, self.hidden - 1)
            self.json_script = False

    def handle_data(self, data):
        if self.json_script:
            try:
                value = json.loads(data)
                self.structured.extend(value if isinstance(value, list) else [value])
            except (ValueError, RecursionError):
                pass
        if not self.hidden:
            self.parts.append(data)


def read_public_page(url, person_name):
    host, path = public_url(url)
    address = resolve_public(host)
    deadline = time.monotonic() + 20
    status, _, robots = request_page(host, address, '/robots.txt', deadline)
    if status not in (200, 404, 410):
        raise ValidationError('Public access rules could not be verified for this site.')
    if status == 200:
        parser = RobotFileParser()
        parser.parse(robots.splitlines())
        if not parser.can_fetch(AGENT, 'https://' + host + path):
            raise ValidationError('This site does not permit this public-page fetch.')
        delay = parser.crawl_delay(AGENT)
        if delay and delay > 0:
            raise ValidationError('This source requires scheduled crawling. Use another permitted public source for this beta.')
    status, content_type, html = request_page(host, address, path, deadline)
    if status != 200 or not any(kind in content_type.lower() for kind in ('text/html', 'text/plain')):
        raise ValidationError('This page is unavailable for public text research.')
    parsed = PageText()
    parsed.feed(html)
    text = re.sub(r'\s+', ' ', ' '.join(parsed.parts)).strip()[:16000]
    if any(term in text.casefold() for term in ('verify you are human', 'sign in to continue', 'access denied', 'complete the captcha')):
        raise ValidationError('This source requires authentication or a human access check.')
    candidates = []
    for item in parsed.structured[:30]:
        nodes = item.get('@graph', [item]) if isinstance(item, dict) else []
        if not isinstance(nodes, list):
            continue
        for node in nodes[:30]:
            if not isinstance(node, dict) or node.get('@type') != 'Person' or str(node.get('name', '')).casefold() != person_name.casefold():
                continue
            company = node.get('worksFor', {})
            for field, value in (('role', node.get('jobTitle')), ('company', company.get('name') if isinstance(company, dict) else company)):
                if isinstance(value, str) and value.strip() and len(value) <= 255 and value.casefold() in text.casefold():
                    candidates.append({'field': field, 'value': value})
    return {'source_url': 'https://' + host + path, 'source_type': 'public_webpage', 'text': text,
        'name_mentioned': person_name.casefold() in text.casefold(), 'candidates': candidates,
        'notice': 'A matching name is not identity verification. Check company, role or another professional identifier.'}


async def fetch_public_page(url, person_name):
    try:
        return await asyncio.wait_for(asyncio.to_thread(read_public_page, url, person_name), timeout=25)
    except (OSError, TimeoutError, http.client.HTTPException) as error:
        raise ValidationError('The public source could not be read safely. Try a different permitted page.') from error
