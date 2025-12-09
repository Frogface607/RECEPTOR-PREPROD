
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.llm.client import OpenAIClient
from app.services.rag.search import search_knowledge_base
from app.services.iiko.iiko_rms_service import IikoRmsService
from app.core.config import settings

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    venue_profile: Optional[Dict[str, Any]] = None

@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Main chat endpoint for Receptor Copilot.
    """
    user_query = request.messages[-1].content
    
    # Simple Intent Detection (Hardcoded for MVP, later use LLM function calling)
    intent = detect_intent(user_query)
    
    context = ""
    
    if intent == "knowledge_base":
        print(f"🔍 Searching Knowledge Base for: {user_query}")
        results = search_knowledge_base(user_query, top_k=3)
        if results:
            context += "\n\nRELEVANT KNOWLEDGE BASE INFO:\n"
            for res in results:
                context += f"- {res['content'][:500]}...\n"
                
    elif intent == "iiko_analytics":
        print(f"📊 Querying iiko for: {user_query}")
        # Placeholder for iiko tool call
        # iiko_service = IikoRmsService()
        # data = iiko_service.get_some_data(...)
        context += "\n\nIIKO DATA: [Placeholder for iiko analytics data]\n"

    # Call LLM
    try:
        client = OpenAIClient(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """You are RECEPTOR, an expert AI Copilot for Restaurant Business.
Your goal is to help restaurateurs, chefs, and managers run their business efficiently.
You have access to a deep knowledge base of HACCP, SanPiN, HR, Finance, and Marketing standards for Russia (2025).
You can also generate tech cards and analyze iiko data.

Use the provided context to answer the user's question accurately.
If you don't know the answer, say so, but offer to research it.
Always answer in Russian."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context to the last user message
        final_user_message = request.messages[-1].content
        if context:
            final_user_message += f"\n\nCONTEXT:{context}"
            
        # Add history (excluding the last one which we just modified)
        for msg in request.messages[:-1]:
            messages.append({"role": msg.role, "content": msg.content})
            
        messages.append({"role": "user", "content": final_user_message})
        
        response = await client.chat_completion(
            messages=messages,
            model="gpt-4o", # Or gpt-5-mini if available in your client mapping
            temperature=0.7
        )
        
        return {"role": "assistant", "content": response}
        
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def detect_intent(query: str) -> str:
    query = query.lower()
    if any(w in query for w in ["haccp", "санпин", "норм", "правил", "закон", "hr", "найм", "зарплат", "маркетинг", "smm"]):
        return "knowledge_base"
    if any(w in query for w in ["выручк", "продаж", "фудкост", "iiko", "айко", "отчет"]):
        return "iiko_analytics"
    return "general"

