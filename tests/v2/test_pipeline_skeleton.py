from receptor_agent.llm.pipeline import run_pipeline, ProfileInput

def test_pipeline_minimal():
    p = ProfileInput(name="EDISON", cuisine="мексиканская", equipment=["oven"], budget=350.0, dietary=[])
    res = run_pipeline(p)
    assert res.card.meta.name
    assert res.card.yield_.total_net_g > 0
    assert res.card.ingredients