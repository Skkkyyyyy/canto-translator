from fastapi import FastAPI
from pydantic import BaseModel
from llm_service import llm
from fastapi.middleware.cors import CORSMiddleware
from contributions import router as contributions_router
from db import init_db

app = FastAPI()

init_db()
app.include_router(contributions_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#shape of the data (template)
#it is a pydantic model, and it inherits from BaseModel
class ChatRequest(BaseModel):
    text: str 

@app.post("/api/chat")
def chat(request: ChatRequest):
    result = llm(request.text)
    print("result",result)
    return {"response": result}

