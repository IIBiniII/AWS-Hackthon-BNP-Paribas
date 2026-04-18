import random
import logging
from mcp.server import FastMCP

import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Bancking informations",
    port=8080
)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

EXCEL_FILE_PATH = project_root / "banking_customers.xlsx"

def load_excel_data():
    """Load banking customers data from Excel file."""
    try:
        if not EXCEL_FILE_PATH.exists():
            raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE_PATH}")
        
        import pandas as pd
        df = pd.read_excel(EXCEL_FILE_PATH)
        logger.info(f"Successfully loaded {len(df)} customer records")
        return df
    except Exception as e:
        logger.error(f"Failed to load Excel file: {e}")
        raise
# Load data on server initialization
try:
    customers_data = load_excel_data()
except FileNotFoundError as e:
    logger.error(f"Server initialization failed: {e}")
    customers_data = None

    



@mcp.tool()
def lookup_client(nom: str, prenom: str, date_naissance: str) -> str:
    """
    Lookup client ID by personal information.
    
    Args:
        nom: Client's last name
        prenom: Client's first name
        date_naissance: Client's date of birth (YYYY-MM-DD)
    
    Returns:
        str: Client ID or error message
    """
    if customers_data is None:
        return {"error": "Data not loaded", "message": "Excel file could not be loaded"}
    
    try:
        mask = (
            (customers_data['nom'].str.lower() == nom.lower()) &
            (customers_data['prenom'].str.lower() == prenom.lower()) &
            (customers_data['date_naissance'] == date_naissance)
        )
        matches = customers_data[mask]
        
        if len(matches) == 0:
            return {"error": "CLIENT_NOT_FOUND", "message": "No client found matching the criteria"}
        elif len(matches) > 1:
            return {
                "error": "MULTIPLE_CLIENTS_FOUND",
                "message": f"Found {len(matches)} clients matching the criteria",
                "client_ids": matches['client_id'].tolist()
            }
        else:
            return {"client_id": str(matches.iloc[0]['client_id'])}
    except KeyError as e:
        return {"error": "DATA_LOAD_ERROR", "message": f"Missing expected column: {e}"}


@mcp.tool()
def get_client_profile(client_id: str) -> dict:
    """
    Get complete client profile by ID.
    
    Args:
        client_id: Unique client identifier
    
    Returns:
        dict: Complete client profile or error message
    """
    if customers_data is None:
        return {"error": "Data not loaded", "message": "Excel file could not be loaded"}
    
    try:
        client = customers_data[customers_data['client_id'] == client_id]
        
        if len(client) == 0:
            return {"error": "CLIENT_NOT_FOUND", "message": f"Client with ID {client_id} not found"}
        else:
            return client.iloc[0].to_dict()
    except KeyError as e:
        return {"error": "DATA_LOAD_ERROR", "message": f"Missing expected column: {e}"}


@mcp.tool()
def list_data_fields() -> dict:
    """
    List all available data fields from the Excel file.
    
    Returns:
        dict: List of column names
    """
    if customers_data is None:
        return {"error": "Data not loaded", "message": "Excel file could not be loaded"}
    
    return {"fields": customers_data.columns.tolist()}


@mcp.tool()
def get_sample_data() -> dict:
    """
    Get sample data from the Excel file.
    
    Returns:
        dict: Sample of 5 records
    """
    if customers_data is None:
        return {"error": "Data not loaded", "message": "Excel file could not be loaded"}
    
    sample = customers_data.head(5).to_dict(orient='records')
    return {"sample": sample}


# Start the MCP server
if __name__ == "__main__":
    logger.info("Starting BankingServer MCP...")
    mcp.run()