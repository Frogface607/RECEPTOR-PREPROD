import os
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput

def test_pipeline_runs_without_key_fallback():
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["TECHCARDS_V2_USE_LLM"] = "true"
    res = run_pipeline(ProfileInput(name="EDISON", cuisine="итальянская"))
    assert res.card.meta.name and res.card.ingredients

def test_pipeline_runs_llm_disabled():
    os.environ["TECHCARDS_V2_USE_LLM"] = "false"
    res = run_pipeline(ProfileInput(name="EDISON", cuisine="итальянская"))
    assert res.card.yield_.total_net_g > 0