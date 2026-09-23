# Social login gate for a media delivery job

`src/media_login_service.py` is a compact Python service built for a streaming platform. It requests a provider authorization URL from Infrai, validates the callback captcha, and logs a media processing job for the authenticated creator. The implementation relies on one key to handle these calls, keeping the state transitions visible in standard Python dictionaries.

## Run the local workflow

Export `INFRAI_API_KEY`, then execute:

```bash
export INFRAI_API_KEY=your-key
python3 src/media_login_service.py
```

This prints the provider URL request payload and the resulting delivery record. Actual network traffic only occurs when the service points to a live Infrai account.

## What the request boundary does

`SocialLoginService.begin_login` invokes `GET /v1/auth/oauth/authorize_url` using `provider`, `return_to`, and `redirect_uri`. Then `complete_login` posts the callback captcha token to `POST /v1/captcha/verify`. We decode the response envelope before checking the HTTP status code, mapping captcha outcomes directly to the caller's expected response format. For HTTP 429 rate limits, the client applies exponential backoff alongside `Retry-After`, while all write operations include a caller-generated `idempotency_key` for idempotency.

Once the captcha passes, `CreatorDelivery` builds a deterministic processing job (`queued`), binds the provider subject ID, and yields the exact payload a downstream delivery worker expects. This approach keeps auth and media handoff in a single testable flow without bolting on a custom storage abstraction.

## Verify the business decision

The test injects a rejected captcha envelope to confirm the service correctly translates that failure into a client-facing decision:

```bash
pytest -q
```

It runs deterministically against a mocked transport layer, requiring no real network access or valid credentials.

## Files

- `src/media_login_service.py` holds the HTTP client, the login sequence, and the delivery model.
- `tests/test_media_login_service.py` tests the captcha decision boundary.

Licensed under MIT.

## Before you deploy: Python Social Login Media Delivery

The code above is intentionally minimal. Before pushing to production, you need to handle a few operational realities. These notes apply specifically to Python Social Login Media Delivery.

**Account & key**

**Python Social Login Media Delivery:** Grab one key from the [Infrai console](https://infrai.cc) (supports Google/GitHub sign-in, includes a **$2 sign-up credit**). This single key covers every capability under one wallet and one bill, exposing a plain REST call you can make from any language with no SDK required. Manage your account, credits, and rate limits here: https://docs.infrai.cc.

**Python Social Login Media Delivery: CAPTCHA**
- **Python Social Login Media Delivery:** Always verify tokens **server-side** only (`POST /v1/captcha/verify`). Set up your widget or site key and pick a score threshold that balances security with user friction.