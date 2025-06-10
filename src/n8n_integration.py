"""
N8N workflow integration module - handles communication with N8N platform.
"""
from typing import Dict, Any
import aiohttp
from . import config


async def trigger_n8n_workflow(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triggers a N8N workflow with the given data.
    
    Args:
        data: The data to send to N8N including user message, response, and contact info
        
    Returns:
        Dict with status of the workflow execution
    """
    url = f"{config.N8N_BASE_URL}/api/v1/workflows/{config.N8N_WORKFLOW_ID}/trigger"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-N8N-API-KEY": config.N8N_API_KEY
    }
    
    print(f"[N8N] Triggering workflow {config.N8N_WORKFLOW_ID} with data: {data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[N8N] Error triggering workflow: {response.status}, {error_text}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": error_text
                    }
                
                result = await response.json()
                print(f"[N8N] Workflow triggered successfully: {result}")
                return {
                    "success": True,
                    "result": result
                }
    except Exception as e:
        print(f"[N8N] Exception triggering workflow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
