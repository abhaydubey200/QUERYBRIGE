from fastapi import APIRouter, Depends
from app.services.ai_service import AIService
from pydantic import BaseModel

router = APIRouter()

class AIRequest(BaseModel):
    prompt: str
    context: str = ""

@router.post("/generate")
async def generate(request: AIRequest):
    service = AIService()
    response = await service.generate_sql(request.context, request.prompt)
    return {"status": "success", "response": response}
