from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.techcards_v2.validators import validate_card

def test_pipeline_finalize_ok():
    p = ProfileInput(name="EDISON", cuisine="мексиканская", equipment=["oven"])
    res = run_pipeline(p)
    ok, issues = validate_card(res.card)
    assert ok, issues
    assert res.card.haccp.hazards  # шаблоны подставились