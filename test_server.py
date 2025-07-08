#!/usr/bin/env python3
"""
Simple test server to verify the header template JavaScript fixes.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory=".")

def get_base_template_vars(request: Request):
    """Get base template variables"""
    return {
        "request": request,
        "static_url": "/static",
        "is_debug": True,
        "app_name": "Text Generator",
        "gcloud_static_bucket_url": "https://static.text-generator.io/static",
        "facebook_app_id": "138831849632195",
    }

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    base_vars = get_base_template_vars(request)
    return templates.TemplateResponse("templates/index.jinja2", base_vars)

@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    base_vars = get_base_template_vars(request)
    return templates.TemplateResponse("templates/base.jinja2", base_vars)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
