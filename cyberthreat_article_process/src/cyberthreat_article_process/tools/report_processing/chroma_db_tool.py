from crewai.tools import tool
import chromadb
import json

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./db/threats")
collection = client.get_or_create_collection(name="cyber_threats")

@tool
def store_in_chromadb(threat_data: dict) -> str:
    """
    Stores extracted threat intelligence in ChromaDB.
    - threat_data: A dictionary containing known and emerging cybersecurity threats.
    
    Returns: Confirmation message.
    """
    try:
        # Convert dictionary to JSON string for storage
        json_data = json.dumps(threat_data, indent=2)

        # Store in ChromaDB
        collection.add(
            documents=[json_data],  # Store as JSON string
            metadatas=[{"source": "cybersecurity_report"}],
            ids=[str(hash(json_data))]
        )

        return "Threat intelligence successfully stored in ChromaDB."

    except Exception as e:
        return f"Error storing data in ChromaDB: {str(e)}"

