from mcp.client.streamable_http import streamable_http_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.stdio import stdio_client, StdioServerParameters
import sys
def main():
    # Connect to the dice roll MCP server
    print("\nConnecting to Banking MCP Server...")
    # http_client = streamable_http_client("http://localhost:8080/mcp",verify=False)
    # Configuration du lancement du serveur
    server_params = StdioServerParameters(
        command=sys.executable, # Utilise le Python de votre venv actuel
        args=["src/mcp-server.py"], # Chemin vers votre fichier serveur
        env=None
    )

    try:
        # On utilise stdio_client au lieu de http
        with MCPClient(lambda: stdio_client(server_params)) as mc:
            # TODO: Get available tools from MCP server using list_tools_sync()
            tools = mc.list_tools_sync()
            print(f"Available tools: {[tool.tool_name for tool in tools]}")
            # Create the gamemaster agent with access to dice rolling
            bankmaster = Agent(
                system_prompt="""Tu es un conseiller bancaire expert.
                1. Analyse la demande du client.
                2. Si des informations manquent (Nom, Prénom, DOB), demande-les.
                3. Utilise 'client_lookup' pour trouver l'ID.
                4. Utilise 'client_retrieval' avec cet ID pour obtenir le profil complet.
                5. Ne base tes conseils QUE sur les données réelles de l'Excel. Ne jamais inventer de solde ou de transactions.""",
                tools= mc.list_tools_sync()
            )

            print("\n--- Conseiller Bancaire IA prêt (Tape 'exit' pour quitter) ---")
            
            # Boucle d'interaction (C'est ici que l'IA prend vie)
            while True:
                user_input = input("\n👤 Client: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                # ... à l'intérieur de votre boucle while True
                print("\n🤖 Conseiller: ", end="", flush=True)
                try:
                    # Si 'run' n'existe pas, essayez 'chat' ou vérifiez la méthode de l'objet Agent
                    response = bankmaster(user_input) 
                    print(response)
                except AttributeError:
                    # Si vous utilisez une version de strands qui préfère run_sync
                    print("Une erreur est survenu lors du chargement de l'agent !")
            
           
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure the banking service is running: python mcp-server.py")

if __name__ == "__main__":
    main()