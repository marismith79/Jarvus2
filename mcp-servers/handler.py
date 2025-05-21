from fastapi import FastAPI, HTTPException
from jsonrpcserver import method, Result, Success, Error
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import base64
import json
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel

app = FastAPI()
driver: Optional[webdriver.Chrome] = None

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

def get_driver() -> webdriver.Chrome:
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp(request: MCPRequest) -> MCPResponse:
    method_name = request.method
    params = request.params
    
    try:
        if method_name == "navigate":
            url = params.get("url")
            if not url:
                return MCPResponse(error={"code": -32602, "message": "URL parameter is required"})
            get_driver().get(url)
            return MCPResponse(result=True)
            
        elif method_name == "findElement":
            using = params.get("using")
            value = params.get("value")
            if not using or not value:
                return MCPResponse(error={"code": -32602, "message": "Using and value parameters are required"})
            element = get_driver().find_element(using, value)
            return MCPResponse(result={"elementId": element.id})
            
        elif method_name == "findElements":
            using = params.get("using")
            value = params.get("value")
            if not using or not value:
                return MCPResponse(error={"code": -32602, "message": "Using and value parameters are required"})
            elements = get_driver().find_elements(using, value)
            return MCPResponse(result=[{"elementId": element.id} for element in elements])
            
        elif method_name == "click":
            element_id = params.get("elementId")
            if not element_id:
                return MCPResponse(error={"code": -32602, "message": "ElementId parameter is required"})
            element = get_driver().find_element(By.ID, element_id)
            element.click()
            return MCPResponse(result=True)
            
        elif method_name == "sendKeys":
            element_id = params.get("elementId")
            text = params.get("text")
            if not element_id or not text:
                return MCPResponse(error={"code": -32602, "message": "ElementId and text parameters are required"})
            element = get_driver().find_element(By.ID, element_id)
            element.send_keys(text)
            return MCPResponse(result=True)
            
        elif method_name == "clear":
            element_id = params.get("elementId")
            if not element_id:
                return MCPResponse(error={"code": -32602, "message": "ElementId parameter is required"})
            element = get_driver().find_element(By.ID, element_id)
            element.clear()
            return MCPResponse(result=True)
            
        elif method_name == "waitForElement":
            using = params.get("using")
            value = params.get("value")
            timeout = params.get("timeout", 10000) / 1000  
            if not using or not value:
                return MCPResponse(error={"code": -32602, "message": "Using and value parameters are required"})
            element = WebDriverWait(get_driver(), timeout).until(
                EC.presence_of_element_located((using, value))
            )
            return MCPResponse(result={"elementId": element.id})
            
        elif method_name == "takeScreenshot":
            screenshot = get_driver().get_screenshot_as_base64()
            return MCPResponse(result=screenshot)
            
        elif method_name == "getCurrentUrl":
            return MCPResponse(result=get_driver().current_url)
            
        elif method_name == "getTitle":
            return MCPResponse(result=get_driver().title)
            
        elif method_name == "refresh":
            get_driver().refresh()
            return MCPResponse(result=True)
            
        elif method_name == "goBack":
            get_driver().back()
            return MCPResponse(result=True)
            
        elif method_name == "goForward":
            get_driver().forward()
            return MCPResponse(result=True)
            
        else:
            return MCPResponse(error={"code": -32601, "message": f"Method {method_name} not found"})
            
    except Exception as e:
        return MCPResponse(error={"code": -32000, "message": str(e)})

@app.get("/tools")
async def get_tools():
    with open("handler.py", "r") as f:
        content = f.read()
        # Extract the tools section from the JSON at the top of the file
        tools_section = content.split('"tools":')[1].split(']')[0] + ']'
        tools = json.loads(tools_section)
        return {"tools": tools}

@app.on_event("shutdown")
async def shutdown_event():
    global driver
    if driver:
        driver.quit()
        driver = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
