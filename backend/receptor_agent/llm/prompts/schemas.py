# Минимальные схемы для шагов, совместимые с TechCardV2
TECHCARD_CORE_SCHEMA = {
  "type":"object",
  "additionalProperties": False,
  "properties":{
    "meta":{"type":"object","additionalProperties": False,"properties":{
      "name":{"type":"string","minLength":2},
      "category":{"type":["string","null"]},
      "cuisine":{"type":["string","null"]},
      "description":{"type":["string","null"]}
    },"required":["name"]},
    "yield":{"type":"object","properties":{
      "portions":{"type":"integer","minimum":1},
      "per_portion_g":{"type":"integer","minimum":1},
      "total_net_g":{"type":"integer","minimum":1}
    },"required":["portions","per_portion_g","total_net_g"]},
    "ingredients":{"type":"array","items":{
      "type":"object","additionalProperties": False,"properties":{
        "name":{"type":"string"},
        "uom":{"type":"string","enum":["g","ml","pcs"]},
        "gross_g":{"type":"number","minimum":0},
        "net_g":{"type":"number","minimum":0},
        "loss_pct":{"type":"number","minimum":0,"maximum":95},
        "canonical":{"type":["string","null"]},
        "needs_review":{"type":"boolean"}
      },"required":["name","uom","gross_g","net_g","loss_pct"]
    }},
    "process":{"type":"array","items":{
      "type":"object","properties":{
        "step":{"type":"integer","minimum":1},
        "desc":{"type":"string"},
        "temp_c":{"type":["integer","null"]},
        "time_min":{"type":["integer","null"]}
      },"required":["step","desc"]
    }},
    "haccp":{"type":"object","properties":{
      "hazards":{"type":"array","items":{"type":"string"}},
      "ccp":{"type":"array","items":{"type":"object","properties":{
        "name":{"type":"string"},
        "limit":{"type":"string"},
        "monitoring":{"type":"string"},
        "corrective":{"type":"string"}
      },"required":["name","limit","monitoring","corrective"]}},
      "storage":{"type":["string","null"]}
    },"required":["hazards","ccp"]},
    "allergens":{"type":"array","items":{"type":"string"}},
    "pricing":{"type":["object","null"]}
  },
  "required":["meta","yield","ingredients","process","haccp","allergens"]
}