from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.stdio import stdio_client, StdioServerParameters
import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query
import pandas as pd

# Modèle pour la requête du site web
class ChatRequest(BaseModel):
    message: str

# Gestion globale de l'agent et du client MCP
state = {}

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

EXCEL_FILE_PATH = project_root / "banking_customers.xlsx"

def load_excel_data():
    """Load banking customers data from Excel file."""
    try:
        if not EXCEL_FILE_PATH.exists():
            raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE_PATH}")
        
        df = pd.read_excel(EXCEL_FILE_PATH)
        return df
    except Exception as e:
        print(f"Failed to load Excel file: {e}")
        raise
# Load data on server initialization
try:
    customers_data = load_excel_data()
except FileNotFoundError as e:
    print(f"Server initialization failed: {e}")
    customers_data = None

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
        system_prompt="""Tu es un conseiller bancaire expert.
                1. Analyse la demande du client.
                2. Si des informations manquent (Nom, Prénom, DOB), demande-les.
                3. Utilise 'client_lookup' pour trouver l'ID.
                4. Utilise 'client_retrieval' avec cet ID pour obtenir le profil complet.
                5. Ne base tes conseils QUE sur les données réelles de l'Excel. Ne jamais inventer de solde ou de transactions.""",
        tools=mc.list_tools_sync()
    )
    state["mcp_context"] = mc_context
    
    yield
    # Fermeture propre à l'arrêt
    state["mcp_context"].__exit__(None, None, None)

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(lifespan=lifespan)


# Configuration du CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Autorise ton site web à accéder à l'API
    allow_credentials=True,
    allow_methods=["*"],           # Autorise POST, OPTIONS, GET, etc.
    allow_headers=["*"],           # Autorise les headers comme Content-Type
)

@app.get("/client/accounts")
def get_client_accounts(client_id: str, sheet_name: str = "04_Contrats_Produits"):
    # 1. Vérification de la source de données
    df = pd.read_excel(EXCEL_FILE_PATH,sheet_name=None)

    if df is None:
        raise HTTPException(status_code=500, detail="Base de données non chargée")
    print(df.keys())
    if sheet_name not in df:
        raise HTTPException(status_code=404, detail=f"Feuille '{sheet_name}' introuvable")

    df_accounts = df[sheet_name]
    
    try:
        # 2. Filtrage (le astype(str) est vital si l'ID est numérique dans Excel)
        mask = df_accounts['client_id'].astype(str) == str(client_id)
        accounts = df_accounts[mask].copy() # .copy() pour éviter les warnings Pandas
        
        if accounts.empty:
            return [] # Un tableau vide est plus facile à gérer pour le frontend qu'un message d'erreur

        # 3. Nettoyage des types pour JSON
        # Conversion des colonnes de dates en strings (format ISO)
        for col in accounts.select_dtypes(include=['datetime64']).columns:
            accounts[col] = accounts[col].dt.strftime('%Y-%m-%d')
            
        # 4. Gestion des NaN (Not a Number) qui font planter le JSON standard
        # On remplace les NaN par None (qui devient null en JSON)
        return accounts.where(pd.notnull(accounts), None).to_dict(orient="records")
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"La colonne {e} est absente de la feuille")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

@app.get("/clients/search")
async def search_clients(
    client_id: Optional[str] = None,
    nom: Optional[str] = None,
    prenom: Optional[str] = None,
    date_naissance: Optional[str] = None,  # Format attendu: YYYY-MM-DD
    ville: Optional[str] = None,
    limit: int = Query(default=10, le=100)
):
    if customers_data is None:
        raise HTTPException(status_code=500, detail="Base de données Excel non chargée")

    results = customers_data.copy()

    # Filtre par ID Client (exact)
    if client_id:
        # On convertit en string pour éviter les erreurs si l'ID est numérique dans Excel
        results = results[results['client_id'].astype(str) == client_id]

    # Filtre par Nom (partiel, insensible à la casse)
    if nom:
        results = results[results['nom'].str.contains(nom, case=False, na=False)]
    
    # Filtre par Prénom (partiel, insensible à la casse)
    if prenom:
        results = results[results['prenom'].str.contains(prenom, case=False, na=False)]
    
    # Filtre par Date de Naissance (exact)
    if date_naissance:
        # On s'assure que la colonne Excel et l'entrée utilisateur sont comparées en string
        results = results[results['date_naissance'].astype(str).str.contains(date_naissance, na=False)]
    
    # Filtre par Ville
    if ville:
        results = results[results['ville'].str.contains(ville, case=False, na=False)]

    # Conversion en dictionnaire pour la réponse JSON
    final_data = results.head(limit).to_dict(orient="records")

    return {
        "count": len(final_data),
        "total_matches": len(results),
        "clients": final_data
    }

from typing import List, Dict, Any

@app.get("/client/events")
def get_client_events(client_id: str, sheet_name: str = "11_Evenements_Interact"):
    """
    Récupère les 5 derniers événements/interactions d'un client, triés par date décroissante.
    """
    df = pd.read_excel(EXCEL_FILE_PATH,sheet_name=None)

    if df is None:
        raise HTTPException(status_code=500, detail="Base de données non initialisée")
    
    if sheet_name not in df:
        raise HTTPException(status_code=404, detail=f"Feuille '{sheet_name}' introuvable")

    df_events = df[sheet_name]
    
    try:
        # 1. Filtrage par client_id
        mask = df_events['client_id'].astype(str) == str(client_id)
        events = df_events[mask].copy()
        
        if events.empty:
            return []

        # 2. Conversion de la colonne 'date' en format datetime pour assurer un tri correct
        if 'date' in events.columns:
            events['date'] = pd.to_datetime(events['date'])
            # Tri : du plus récent au plus ancien
            events = events.sort_values(by='date', ascending=False)
            # Conversion en string pour le JSON après le tri
            events['date'] = events['date'].dt.strftime('%Y-%m-%d %H:%M')

        # 3. Récupération des 5 premiers (les plus récents suite au tri)
        latest_events = events.head(5)

        # 4. Nettoyage des NaN pour le JSON
        return latest_events.where(pd.notnull(latest_events), None).to_dict(orient="records")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des événements : {str(e)}")
    
    

@app.post("/chat")
async def chat(request: ChatRequest):
    if "agent" not in state:
        raise HTTPException(status_code=503, detail="Agent non prêt")
    
    try:
        # Utilisation de la méthode chat() (ou run_sync selon votre version de strands)
        response = state["agent"](request.message)
        print(response)
        prompt = response
        response2 = state["agent"](prompt)

        return {"response": response2}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)