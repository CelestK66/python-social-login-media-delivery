import json
from io import BytesIO

import pytest

from src.media_login_service import InfraiClient, InfraiError, SocialLoginService


class FakeResponse:
    status = 422
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"ok": False, "data": None, "error": {"code": "CAPTCHA_SCORE_TOO_LOW"}, "metadata": {}}).encode()


def fake_transport(_request):
    return FakeResponse()


def test_rejected_captcha_maps_to_client_decision():
    service = SocialLoginService(InfraiClient(api_key="test", transport=fake_transport))
    with pytest.raises(ValueError, match="captcha rejected"):
        service.complete_login("google", "creator-7", "token", "media-9")
