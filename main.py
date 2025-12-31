import logging
import re

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from routers.vlr_router import router as vlr_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Valorant Esports API",
    description="An Unofficial REST API for [vlr.gg](https://www.vlr.gg/), a site for Valorant Esports match and news coverage. Made by [axsddlr](https://github.com/axsddlr)",
    docs_url="/",
    redoc_url=None,
    swagger_ui_parameters={"faviconUrl": "/favicon.svg"},
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.svg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.svg")


# 中间件：替换 Swagger UI 中的 fastapi favicon
@app.middleware("html")
async def replace_faviconMiddleware(request, call_next):
    response = await call_next(request)
    if hasattr(response, "body") and b"fastapi.tiangolo.com/img/favicon.png" in response.body:
        response.body = response.body.replace(
            b"https://fastapi.tiangolo.com/img/favicon.png",
            b"/favicon.svg"
        )
    return response


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(vlr_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3001)
