import logging
import re

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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


# 中间件：替换 Swagger UI 中的 fastapi favicon 和标题，注入系统字体
SYSTEM_FONTS_CSS = b"""
<style>
    body, body *, .swagger-ui, .swagger-ui *, .renderedMarkdown, .renderedMarkdown * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    code, code *, pre, pre *, .monospace, .monospace *, .microlight, .microlight *, textarea, input[type="text"] {
        font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace !important;
    }
</style>
"""

class CustomHTMLMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # 只处理 HTML 响应
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            try:
                # 读取响应体
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                logger.info(f"Processing HTML response for {request.url.path}")

                # 替换 favicon
                if b"fastapi.tiangolo.com/img/favicon.png" in body:
                    body = body.replace(
                        b"https://fastapi.tiangolo.com/img/favicon.png",
                        b"/favicon.svg"
                    )
                    logger.info("Replaced favicon URL")

                # 去掉标题中的 " - Swagger UI"
                if b"Valorant Esports API - Swagger UI" in body:
                    body = body.replace(
                        b"Valorant Esports API - Swagger UI",
                        b"Valorant Esports API"
                    )
                    logger.info("Replaced page title")

                # 注入系统字体样式
                if b"</head>" in body:
                    body = body.replace(b"</head>", SYSTEM_FONTS_CSS + b"</head>")
                    logger.info("Injected system fonts CSS")

                # 更新 Content-Length header
                headers = dict(response.headers)
                headers["content-length"] = str(len(body))

                # 创建新的响应
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=headers,
                    media_type=response.media_type
                )
            except Exception as e:
                logger.error(f"Error processing HTML: {e}")
                return response

        return response

app.add_middleware(CustomHTMLMiddleware)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.svg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.svg")


limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(vlr_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3001)
