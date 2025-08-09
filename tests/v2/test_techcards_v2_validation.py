import pytest
from receptor_agent.techcards_v2.schemas import TechCardV2

def mk_sample():
    return {
        "meta": {"name":"Курица с лаймом","category":"Горячее","cuisine":"мексиканская"},
        "yield": {"portions":10,"per_portion_g":250,"total_net_g":2500},
        "ingredients":[
            {"name":"Куриное бедро без кожи","uom":"g","gross_g":3000,"net_g":2500,"loss_pct":16.7},
            {"name":"Соль","uom":"g","gross_g":20,"net_g":20,"loss_pct":0}
        ],
        "process":[{"step":1,"desc":"Маринование 60 мин","temp_c":4,"time_min":60}],
        "haccp":{"hazards":["bio"],"ccp":[{"name":"Internal temp","limit":"≥75°C","monitoring":"термометр","corrective":"доготовить"}]},
        "allergens":[]
    }

def test_balance_ok():
    from receptor_agent.techcards_v2.validators import validate_card
    card = TechCardV2.model_validate(mk_sample())
    ok, issues = validate_card(card)
    assert ok, issues

def test_balance_fail_total():
    from receptor_agent.techcards_v2.validators import validate_card
    bad = mk_sample()
    bad["yield"]["total_net_g"] = 2400
    card = TechCardV2.model_validate(bad)
    ok, issues = validate_card(card)
    assert not ok and "total_net_g mismatch" in " ".join(issues)

def test_allergen_detect():
    from receptor_agent.techcards_v2.validators import recompute_allergens
    sample = mk_sample()
    sample["ingredients"].append({"name":"Сливки 33%","uom":"g","gross_g":100,"net_g":100,"loss_pct":0})
    card = TechCardV2.model_validate(sample)
    tags = recompute_allergens(card)
    assert "milk" in tags