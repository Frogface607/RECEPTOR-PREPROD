# Заготовки prompt-текстов (пока не вызываем LLM)
DRAFT_PROMPT = """You are a culinary R&D assistant... (short)"""
NORMALIZE_PROMPT = """Normalize ingredient names and units to canonical dictionary..."""
QUANTIFY_PROMPT = """Compute gross/net/loss for each ingredient with bounds and yield balance..."""
HACCP_PROMPT = """Generate HACCP blocks: hazards, CCPs, limits, monitoring, corrective actions..."""
CRITIC_PROMPT = """Review JSON for consistency and return issues + minimal patch..."""