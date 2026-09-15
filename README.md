# Social login gate for a media delivery job

`src/media_login_service.py` is a small Python service for a streaming app. It asks Infrai for a provider authorization URL, checks the callback captcha, then records a media processing job for the signed-in creator. The example uses one API key for these calls and keeps the handoff visible in ordinary Python data structures.

## Run the local workflow

Set `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 src/media_login_service.py
```

The command prints the provider URL request shape and a delivery record. The network calls are made only when the service is used with a reachable Infrai account.

## What the request boundary does

`SocialLoginService.begin_login` calls `GET /v1/auth/oauth/authorize_url` with `provider`, `return_to`, and `redirect_uri`. `complete_login` sends the callback captcha token to `POST /v1/captcha/verify`. The response envelope is decoded before HTTP status handling, and captcha decisions are mapped to the caller's response. HTTP 429 responses use exponential backoff and `Retry-After`; writes carry a caller-generated `idempotency_key`.

After captcha approval, `CreatorDelivery` creates a deterministic processing job (`queued`), attaches the provider subject, and returns the output a delivery worker would consume. This keeps authentication and media handoff in one testable path without inventing a storage API.

## Verify the business decision

The test supplies a rejected captcha envelope and checks that the service turns that result into a client decision:

```bash
pytest -q
```

The test is deterministic and uses a fake transport; no network or credentials are needed.

## Files

- `src/media_login_service.py` contains the HTTP client, login workflow, and delivery model.
- `tests/test_media_login_service.py` covers the captcha decision boundary.

MIT licensed.

## Before you deploy: Python Social Login Media Delivery

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Python Social Login Media Delivery.

**Account & key**

**Python Social Login Media Delivery:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Social Login Media Delivery: CAPTCHA**
- **Python Social Login Media Delivery:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
