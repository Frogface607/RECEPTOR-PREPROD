import os
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.llm.haccp import generate_haccp, audit_haccp
from receptor_agent.techcards_v2.validators import validate_card

def _card():
    os.environ["TECHCARDS_V2_USE_LLM"] = "false"  # гарантируем локальный режим для теста
    return run_pipeline(ProfileInput(name="EDISON", cuisine="мексиканская")).card.model_dump(by_alias=True)

def test_generate_haccp_local_ok():
    c = _card()
    out = generate_haccp(c)
    # валидируем через модель
    from receptor_agent.techcards_v2.schemas import TechCardV2
    tc = TechCardV2.model_validate(out)
    ok, issues = validate_card(tc)
    assert ok, f"Validation failed: {issues}"
    assert tc.haccp.hazards, "HACCP hazards should not be empty"

def test_audit_local_ok():
    c = _card()
    out = audit_haccp(c)
    assert "issues" in out and "patch" in out