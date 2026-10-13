import pytest

from app.config import Settings
from app.services import vision_check


@pytest.mark.parametrize(
    "settings",
    [
        Settings(groq_api_key="test-key", enable_vision_crosscheck=False, groq_vision_model="vision-model"),
        Settings(groq_api_key="test-key", enable_vision_crosscheck=True, groq_vision_model=""),
    ],
)
def test_vision_check_is_quietly_skipped_when_disabled_or_unconfigured(monkeypatch, settings):
    def unexpected_groq_call(**_):
        raise AssertionError("Groq vision client should not be created when the check is skipped.")

    monkeypatch.setattr(vision_check, "Groq", unexpected_groq_call)

    findings = vision_check.check_image_fields(
        b"not-used",
        "invoice",
        {"total_amount": 100},
        settings,
    )

    assert findings == []
