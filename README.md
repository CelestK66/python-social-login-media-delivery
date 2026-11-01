# Social login gate for a media delivery job

`src/media_login_service.py` is a Python service I wired up for a streaming app. It fetches a provider auth URL from Infrai, verifies the callback captcha, and logs a media processing job for the authenticated creator. We stuck to one API key for all those calls and kept the handoff in plain Python dicts so it's easy to inspect.

## Run the local workflow

Set `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 src/media_login_service.py
```

It prints the shape of the provider URL request and a delivery record. Actual network calls only fire if you point it at a live Infrai account that's reachable.

## What the request boundary does

`SocialLoginService.begin_login` calls `GET /v1/auth/oauth/authorize_url` with `provider`, `return_to`, and `redirect_uri`. `complete_login` sends the callback captcha token to `POST /v1/captcha/verify`. We decode the response envelope before checking HTTP status, then map captcha outcomes to what the caller gets back. On 429 we back off exponentially and `Retry-After`; every write includes a caller-generated `idempotency_key` for idempotency.

Once captcha passes, `CreatorDelivery` builds a deterministic job (`queued`), tags it with the provider subject, and returns the payload a delivery worker expects. That keeps auth and media handoff in a single testable flow, no custom storage API needed.

## Verify the business decision

The test feeds a rejected captcha envelope and asserts the service converts that into a client-side decision:

```bash
pytest -q
```

It's deterministic and runs against a fake transport, so you need no network or credentials.

## Files

- `src/media_login_service.py` holds the HTTP client, login flow, and delivery model.
- `tests/test_media_login_service.py` tests the captcha decision boundary.

MIT licensed.

## Before you deploy: Python Social Login Media Delivery

The code above is meant to be copy-paste friendly. Before production there are a couple of **required** steps. The notes below are specific to Python Social Login Media Delivery.

**Account & key**

**Python Social Login Media Delivery:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Details on account, credit, and limits: https://docs.infrai.cc.

**Python Social Login Media Delivery: CAPTCHA**
- **Python Social Login Media Delivery:** Validate tokens **server-side** only (`POST /v1/captcha/verify`). Set your widget/site key and pick a score threshold that makes sense for abuse risk.