from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.stdio import stdio_client, StdioServerParameters
import sys

# Modèle pour la requête du site web
class ChatRequest(BaseModel):
    message: str

# Gestion globale de l'agent et du client MCP
state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage du client MCP en mode stdio
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["src/mcp-server.py"]
    )
    
    # On garde le context manager ouvert durant toute la vie de l'API
    mc_context = MCPClient(lambda: stdio_client(server_params))
    mc = mc_context.__enter__()
    
    # Création de l'agent
    state["agent"] = Agent(
        system_prompt="Tu es un conseiller bancaire expert...",
        tools=mc.list_tools_sync()
    )
    state["mcp_context"] = mc_context
    
    yield
    # Fermeture propre à l'arrêt
    state["mcp_context"].__exit__(None, None, None)

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(request: ChatRequest):
    if "agent" not in state:
        raise HTTPException(status_code=503, detail="Agent non prêt")
    
    try:
        # Utilisation de la méthode chat() (ou run_sync selon votre version de strands)
        response = state["agent"].chat(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)