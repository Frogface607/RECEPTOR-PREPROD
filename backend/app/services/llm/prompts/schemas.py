# TechCardV2 JSON Schema для OpenAI Structured Output
TECHCARD_CORE_SCHEMA = {
  "type": "object",
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "title": {"type": "string", "minLength": 2, "maxLength": 200},
        "version": {"type": "string", "default": "2.0"},
        "cuisine": {"type": ["string", "null"]},
        "tags": {"type": "array", "items": {"type": "string"}, "default": []}
      },
      "required": ["title"]
    },
    "portions": {"type": "integer", "minimum": 1},
    "yield": {
      "type": "object", 
      "properties": {
        "perPortion_g": {"type": "number", "minimum": 0.1},
        "perBatch_g": {"type": "number", "minimum": 0.1}
      },
      "required": ["perPortion_g", "perBatch_g"]
    },
    "ingredients": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "minLength": 1},
          "skuId": {"type": ["string", "null"]},
          "unit": {"type": "string", "enum": ["g", "ml", "pcs"]},
          "brutto_g": {"type": "number", "minimum": 0},
          "loss_pct": {"type": "number", "minimum": 0, "maximum": 100},
          "netto_g": {"type": "number", "minimum": 0},
          "allergens": {"type": "array", "items": {"type": "string"}, "default": []}
        },
        "required": ["name", "unit", "brutto_g", "loss_pct", "netto_g"]
      }
    },
    "process": {
      "type": "array",
      "minItems": 3,
      "items": {
        "type": "object",
        "properties": {
          "n": {"type": "integer", "minimum": 1},
          "action": {"type": "string", "minLength": 1},
          "time_min": {"type": ["number", "null"]},
          "temp_c": {"type": ["number", "null"]},
          "equipment": {"type": "array", "items": {"type": "string"}, "default": []},
          "ccp": {"type": "boolean", "default": False},
          "note": {"type": ["string", "null"]}
        },
        "required": ["n", "action"]
      }
    },
    "storage": {
      "type": "object",
      "properties": {
        "conditions": {"type": "string", "minLength": 1},
        "shelfLife_hours": {"type": "number", "minimum": 0.1},
        "servingTemp_c": {"type": ["number", "null"]}
      },
      "required": ["conditions", "shelfLife_hours"]
    },
    "nutrition": {
      "type": "object",
      "properties": {
        "per100g": {"type": "null"},
        "perPortion": {"type": "null"}
      },
      "required": ["per100g", "perPortion"]
    },
    "cost": {
      "type": "object", 
      "properties": {
        "rawCost": {"type": "null"},
        "costPerPortion": {"type": "null"},
        "markup_pct": {"type": "null"},
        "vat_pct": {"type": "null"}
      },
      "required": ["rawCost", "costPerPortion"]
    },
    "printNotes": {"type": "array", "items": {"type": "string"}, "default": []}
  },
  "required": ["meta", "portions", "yield", "ingredients", "process", "storage", "nutrition", "cost"]
}