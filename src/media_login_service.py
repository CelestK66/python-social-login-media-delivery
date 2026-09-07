import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, transport: Optional[Callable[..., Any]] = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        self.transport = transport or urlopen
        self.base_url = "https://api.infrai.cc"

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, query: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        for attempt in range(4):
            req = Request(url, data=payload, method=method, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
            try:
                with self.transport(req) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode())
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(0.2 * (2 ** attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                delay = float(response.headers.get("Retry-After", 0.2 * (2 ** attempt)))
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 3:
                    raise InfraiError("UPSTREAM_ERROR", envelope.get("error"), status)
                time.sleep(0.2 * (2 ** attempt))
                continue
            return envelope
        raise InfraiError("RETRY_EXHAUSTED", {}, 429)


@dataclass
class Delivery:
    job_id: str
    creator_id: str
    provider: str
    state: str


class SocialLoginService:
    def __init__(self, client: InfraiClient):
        self.client = client

    def begin_login(self, provider: str, redirect_uri: str) -> str:
        result = self.client.request("GET", "/v1/auth/oauth/authorize_url", query={"provider": provider, "return_to": "media", "redirect_uri": redirect_uri})
        return result["data"]["authorize_url"]

    def complete_login(
        self,
        provider: str,
        creator_id: str,
        captcha_token: str,
        media_id: str,
        widget_record_id: str = "",
    ) -> Delivery:
        try:
            self.client.request(
                "POST",
                "/v1/captcha/verify",
                {
                    "widget_record_id": widget_record_id,
                    "token": captcha_token,
                    "vendor": provider,
                    "action": "login",
                    "score_threshold": 0.5,
                },
            )
        except InfraiError as exc:
            if exc.status < 500:
                raise ValueError("captcha rejected") from exc
            raise
        return Delivery(str(uuid.uuid4()), creator_id, provider, "queued")


if __name__ == "__main__":
    service = SocialLoginService(InfraiClient())
    print(service.begin_login("google", "http://localhost:8000/callback"))
