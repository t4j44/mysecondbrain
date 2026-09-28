# Remote MCP client setup — V1.5

The supported server is the official MCP SDK mounted in the FastAPI process at
`https://<api-host>/mcp` using Streamable HTTP. There is no second deployed MCP process.
The older `apps/mcp-server` examples are historical and are not this release's setup.

## Operator configuration

Apply migrations through `20260927000031_mcp_oauth.sql` to isolated staging first.
Set `MCP_ISSUER_URL` to the API origin (no `/mcp` suffix),
`MCP_RESOURCE_SERVER_URL` to the exact HTTPS `/mcp` URL, `MCP_ALLOWED_HOSTS` to
that host, and `FRONTEND_URL` / `CORS_ORIGINS` to the frontend origin.
Supabase login must work on that frontend. Do not change the issuer or resource
for an existing connection: reconnect after an origin change. No paid AI is required.

## OAuth connection

1. Configure a remote MCP connector with the exact `/mcp` URL and OAuth.
2. Use dynamic client registration (DCR). The server advertises `/oauth/register`.
   Supported client authentication is `none`, `client_secret_post`, or `client_secret_basic`.
3. The client follows protected-resource and authorization-server metadata, requests
   an authorization code using PKCE S256 and the exact resource and registered callback.
4. Sign in to Second Brain and inspect the requesting client's name and callback.
   Names are client supplied, not a certification of that app's identity.
5. Read scopes are selected first. Writes and `offline_access` require selection.
   Full session finalization needs all five write scopes listed in the permissions guide.
6. Approve only a connection you initiated. Settings → AI assistant access lists the
   connection, permissions, expiry and last use; Revoke blocks subsequent requests.

Discovery is public at `/.well-known/oauth-protected-resource/mcp` and
`/.well-known/oauth-authorization-server`. Unauthenticated `/mcp` returns a 401
challenge with resource metadata. `/mcp/info` and `/mcp/tools` are public capability
manifests without user data. `/mcp/invoke` is a legacy API-key compatibility endpoint;
OAuth clients use the official `/mcp` transport.

Access tokens last 15 minutes. Optional rotating refresh tokens last no longer than
the 30-day grant. A reused refresh token revokes the connection. Clients must serialize
refreshes and restart authorization after expiry or revocation. Codes last two minutes;
consent requests last ten minutes. No Google or Supabase token is forwarded to an AI client.

## Client compatibility boundary

DCR is implemented for initial ChatGPT/Claude compatibility; live acceptance is still
required on the exact staging SHA. This is not a claim that those hosted clients passed.
The current MCP spec prefers Client ID Metadata Documents (CIMD) and deprecates DCR;
CIMD is explicitly advertised as unsupported in this release. We chose DCR because
both official client guides support it, avoiding an additional remote metadata fetch
and SSRF boundary during this sprint. Configure DCR when the client offers the choice.

Official references checked September 2026:
- [MCP authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [OpenAI connector authentication](https://developers.openai.com/plugins/build/auth)
- [Claude remote MCP integrations](https://support.anthropic.com/en/articles/11503834-building-custom-integrations-via-remote-mcp-servers)

## Legacy bearer keys

Settings still creates separate `sb_mcp_…` keys, displays the secret once, and supports
revocation. Use `Authorization: Bearer <key>` with `/mcp`; never put a key in a URL.
Read access remains the default. Existing keys do not become OAuth grants and are not
silently broadened. Keep secrets in the client's secret manager. Do not commit them.

## Staging acceptance

Run `apps/web/e2e/v15-context.spec.ts` using the runbook's two synthetic users.
It covers browser consent, HTTP token exchange, scoped reads, explicitly approved session
save/retry/retrieval, original source/timezone, revocation and rejection. Merely collecting
the test suite is not evidence these hosted flows passed.
Then test ChatGPT and Claude themselves: connect, read only owned synthetic evidence,
explicitly permit writes, finalize a session with a stable request ID, retry, retrieve
from the other AI client, and revoke. Record client version, date and deployed SHA;
never tokens, codes, private prompts or callback URLs containing codes.
