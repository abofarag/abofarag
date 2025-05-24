import os
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment variables
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

print("URL:", weaviate_url)
print("API Key:", weaviate_api_key)

try:
    # Connect to Weaviate Cloud
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )

    # Test connection
    if client.is_ready():
        print("[SUCCESS] Connected to Weaviate successfully!")
        print(f"Server version: {client.get_meta()['version']}")
    else:
        print("[ERROR] Could not connect to Weaviate")
except Exception as e:
    print(f"[ERROR] {str(e)}")
finally:
    if 'client' in locals():
        client.close()
