# import libraries
import logs
import helpers
import os
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import jinja_partials
import uvicorn
import argparse
import asyncio
import urllib.parse
 
parser = argparse.ArgumentParser(description="Require port and service name",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--port", action="store", help="listen port", required="True", type=int)
args = parser.parse_args()

base_dir = "/opt/ai-dock/fastapi/serviceportal/"

app = FastAPI()

# set template and static file directories for Jinja
templates = Jinja2Templates(directory=str(Path(base_dir, "templates")))
jinja_partials.register_starlette_extensions(templates)

app.mount("/static", StaticFiles(directory=str(Path(base_dir, "static"))), name="static")

@app.get("/")
async def get(request: Request):
    return load_index(request)



@app.get("/login")
async def get(request: Request):
    return templates.TemplateResponse(request, "login.html", {
        "context": {}
        }
    )

def is_secure_context(request: Request):
    """Mirror of Caddy's @secure_ctx matcher in /opt/caddy/share/base_config.

    Keep the two in sync: the portal and Caddy issue the same session cookie,
    so they must agree on whether it carries Secure or the two paths produce
    cookies that overwrite each other with different flags.

    Host is checked because RunPod and trycloudflare terminate TLS at the edge
    and speak http to this container. X-Forwarded-Proto is not dependable here
    either — Caddy rewrites it from its own scheme unless the sender is a
    configured trusted_proxy — but Caddy does preserve Host, so that check is
    the one that actually fires behind the proxy. Defaults to False, because a
    wrongly-set Secure flag locks the operator out of the login form.
    """
    host = request.headers.get('host', '').split(':')[0].lower()
    return (
        request.url.scheme == 'https'
        or request.headers.get('x-forwarded-proto', '').lower() == 'https'
        or host.endswith('.proxy.runpod.net')
        or host.endswith('.trycloudflare.com')
    )

@app.post("/login")
async def post(request: Request):
    form = await request.form()
    user = urllib.parse.unquote(form['user'])
    password = urllib.parse.unquote(form['password'])
    response = RedirectResponse(url="/", status_code=303)
    if user == os.environ.get('WEB_USER') and password == os.environ.get('WEB_PASSWORD'):
        # Session value is the opaque WEB_TOKEN, never WEB_PASSWORD_B64 —
        # the latter is base64(user:password), i.e. reversible to the password.
        response.set_cookie(key=os.environ.get('CADDY_AUTH_COOKIE_NAME'),
            value=os.environ.get('WEB_TOKEN'),
            path="/",
            max_age=604800,
            httponly=True,
            samesite="lax",
            secure=is_secure_context(request)
        )
    return response
        
@app.post("/ajax/index")
async def post(request: Request):
    return templates.TemplateResponse(request, "partials/index/ajax.html", {
        "context": get_index_context(request)
        }
    )

def load_index(request: Request, message: str = "", status_code: int = 200):
    context = get_index_context(request, message)
    return templates.TemplateResponse(request, "index.html", {
        "context": context,
        "status": status_code
        }
    )

def get_index_context(request, message=None):
    services = helpers.get_services()
    return {
        "message": message,
        "request": request,
        "page": "index",
        "auth_token": request.cookies.get(os.environ.get('CADDY_AUTH_COOKIE_NAME')),
        "services": services,
        "urlslug": os.environ.get('IMAGE_SLUG'),
        "direct_address": False if os.environ.get('DIRECT_ADDRESS', 'true').lower() == "false" else True,
        'quicktunnels': False if os.environ.get('CF_QUICK_TUNNELS', 'true').lower() == "false" else True,
        'namedtunnels': False if not os.environ.get('CF_TUNNEL_TOKEN') else True
    }

@app.get("/namedtunnel/{port}")
async def get(request: Request, port: str):
    try:
        if not helpers.is_valid_port(int(port)):
            return load_index(request, "Port not valid", 400)
        url = helpers.get_cfnt_url(port)
        if url:
            return RedirectResponse(url)
        else:
            return load_index(request, "Unable to load Cloudflare tunnel for port " + port, 404)
    except:
        return load_index(request, "Unable to load Cloudflare tunnel for port " + port, 404)

@app.post("/namedtunnel")
async def post(request: Request):
    form = await request.form()
    port = urllib.parse.unquote(form['port'])
    path = urllib.parse.unquote(form['path'])
    url = helpers.get_cfnt_url(port, path)
    return templates.TemplateResponse(request, "partials/index/cfnt_link.html", {
        "context": {"url":url, "port":port}
        }
    )


@app.get("/quicktunnel/{port}")
async def get(request: Request, port: str):
    try:
        if not helpers.is_valid_port(int(port)):
            return load_index(request, "Port not valid", 400)
        url = helpers.get_cfqt_url(port)
        if url:
            return RedirectResponse(url)
        else:
            return load_index(request, "Unable to load Cloudflare quick tunnel for port " + port, 404)
    except:
        return load_index(request, "Unable to load Cloudflare quick tunnel for port " + port, 404)

@app.post("/quicktunnel")
async def post(request: Request):
    form = await request.form()
    port = urllib.parse.unquote(form['port'])
    path = urllib.parse.unquote(form['path'])
    url = helpers.get_cfqt_url(port, path)
    return templates.TemplateResponse(request, "partials/index/cfqt_link.html", {
        "context": {"url":url, "port":port}
        }
    )

    
@app.get("/direct/{port}")
async def get(request: Request, port: str):
    try:
        if not helpers.is_valid_port(int(port)):
            return load_index(request, "Port not valid", 400)
        url = helpers.get_direct_url(port)
        if url:
            return RedirectResponse(url)
    except:
        return load_index(request, "Port not valid", 400)
        
    return load_index(request, "Unable to complete redirect for port " + port, 400)

@app.post("/direct")
async def post(request: Request):
    form = await request.form()
    port = urllib.parse.unquote(form['port'])
    path = urllib.parse.unquote(form['path'])
    url = helpers.get_direct_url(port, path)
    return templates.TemplateResponse(request, "partials/index/direct_link.html", {
        "context": {"url":url, "port":port}
        }
    )

@app.get("/logs")
async def get(request: Request):
    return templates.TemplateResponse(request, "logs.html", {
        "context": get_logs_context()
        }
    )
    
@app.post("/ajax/logs")
async def post(request: Request):
    return templates.TemplateResponse(request, "partials/logs/ajax.html", {
        "context": get_logs_context()
        }
    )

def get_logs_context():
    return {
        "title": "Container Logs",
        "page": "logs",
        "urlslug": os.environ.get('IMAGE_SLUG'),
        "log_file": "/var/log/logtail.log",
        "refresh": 5,
        "cloud": os.environ.get('CLOUD_PROVIDER')
    }

@app.websocket("/ai-dock/logtail.sh")
async def websocket_endpoint_log(websocket: WebSocket) -> None:
    last_logs = []
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(1)
            logs = await helpers.log_reader(250)
            if not logs == last_logs:
                await websocket.send_text(logs)
                last_logs = logs
            else:
                await websocket.send_text("")
    except Exception as e:
        print(e)
    finally:
        await websocket.close()
        
@app.get("/processes")
async def get(request: Request):
    return templates.TemplateResponse(request, "processes.html", {
        "context": get_processes_context()
        }
    )

@app.post("/ajax/processes")
async def post(request: Request):
    return templates.TemplateResponse(request, "partials/processes/ajax.html", {
        "context": get_processes_context()
        }
    )

@app.post("/ajax/processes/stop")
async def post(request: Request):
    form = await request.form()
    name = urllib.parse.unquote(form['process'])
    helpers.stop_process(name)
    return templates.TemplateResponse(request, "partials/processes/row.html", {
        "context": get_process_context(name)
        }
    )

@app.post("/ajax/processes/start")
async def post(request: Request):
    form = await request.form()
    name = urllib.parse.unquote(form['process'])
    helpers.start_process(name)
    return templates.TemplateResponse(request, "partials/processes/row.html", {
        "context": get_process_context(name)
        }
    )

@app.post("/ajax/processes/restart")
async def post(request: Request):
    form = await request.form()
    name = urllib.parse.unquote(form['process'])
    helpers.restart_process(name)
    return templates.TemplateResponse(request, "partials/processes/row.html", {
        "context": get_process_context(name)
        }
    )

def get_processes_context():
    return {
        "page": "processes",
        "processes": helpers.get_all_processes(),
        "urlslug": os.environ.get('IMAGE_SLUG'),
    }

def get_process_context(name):
    return {
        "process": helpers.get_single_process(name)
    }
   
@app.get("/{catch_all:path}")
async def get(request: Request):
    return RedirectResponse("/")

# set parameters to run uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=args.port,
        log_level="info",
        reload=True,
        workers=1,
    )
