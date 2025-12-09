HACCP_ONLY_SCHEMA = {
  "type":"object","additionalProperties":False,
  "properties":{
    "haccp":{"type":"object","additionalProperties":False,"properties":{
      "hazards":{"type":"array","items":{"type":"string"}},
      "ccp":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{
        "name":{"type":"string"},
        "limit":{"type":"string"},
        "monitoring":{"type":"string"},
        "corrective":{"type":"string"}
      },"required":["name","limit","monitoring","corrective"]}},
      "storage":{"type":["string","null"]}
    },"required":["hazards","ccp"]},
    "allergens":{"type":"array","items":{"type":"string"}}
  },
  "required":["haccp","allergens"]
}

HACCP_AUDIT_SCHEMA = {
  "type":"object","additionalProperties":False,
  "properties":{
    "issues":{"type":"array","items":{"type":"string"}},
    "patch":{"type":"object"}  # full card JSON; we validate later with TechCardV2
  },
  "required":["issues","patch"]
}