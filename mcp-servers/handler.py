from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

print("MCP server started")

app = FastAPI()
driver: Optional[webdriver.Chrome] = None
TOOLS_PATH = Path(__file__).parent / "tools.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

def get_driver() -> webdriver.Chrome:
    global driver
    if driver is None:
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
    return driver

@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp(request: MCPRequest) -> MCPResponse:
    method_name = request.method
    params = request.params
    logger.info(f"Received MCP request: method={method_name}, params={params}")
    try:
        if method_name == "navigate":
            url = params.get("url")
            logger.info(f"Navigating to URL: {url}")
            if not url:
                logger.error("URL is required for navigate method")
                return MCPResponse(error={"code": -32602, "message": "URL is required"})
            get_driver().get(url)
            logger.info(f"Current URL after navigation: {get_driver().current_url}")
            return MCPResponse(result=True)

        elif method_name == "findElement":
            using, value = params.get("using"), params.get("value")
            logger.info(f"Finding element: using={using}, value={value}")
            if not using or not value:
                logger.error("using and value are required for findElement")
                return MCPResponse(error={"code": -32602, "message": "using and value are required"})
            elt = get_driver().find_element(using, value)
            logger.info(f"Found element: id={elt.id}")
            return MCPResponse(result={"elementId": elt.id})

        # ... repeat for each other method, identical logic ...

        else:
            logger.error(f"Unknown method: {method_name}")
            return MCPResponse(error={"code": -32601, "message": f"Unknown method {method_name}"})
    except Exception as e:
        logger.exception(f"Error processing MCP request: method={method_name}, params={params}")
        return MCPResponse(error={"code": -32000, "message": str(e)})

@app.get("/tools")
async def get_tools():
    try:
        data = json.loads(TOOLS_PATH.read_text())
        return {"tools": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load tools.json: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    global driver
    if driver:
        driver.quit()
        driver = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
