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


# Middleware: Replace fastapi favicon and title in Swagger UI, inject system fonts
SYSTEM_FONTS_CSS = b"""
<style>
    body, body *, .swagger-ui, .swagger-ui *, .renderedMarkdown, .renderedMarkdown * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    code, code *, pre, pre *, .monospace, .monospace *, .microlight, .microlight *, textarea, input[type="text"] {
        font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace !important;
    }

    /* Swagger UI Dark Mode */
    @media (prefers-color-scheme: dark) {
        body {
            background-color: #1b1b1b !important;
            color: #fff !important;
        }

        /* Swagger UI container */
        .swagger-ui {
            background-color: #1b1b1b !important;
            color: #fff !important;
        }

        /* Top bar */
        .swagger-ui .topbar {
            background-color: #1b1b1b !important;
            border-bottom: 1px solid #404040 !important;
        }

        .swagger-ui .topbar .topbar-wrapper a {
            color: #fff !important;
        }

        /* Sidebar */
        .swagger-ui .sidebar {
            background-color: #1b1b1b !important;
        }

        .swagger-ui .sidebar .sidebar-list {
            background-color: #1b1b1b !important;
        }

        /* Sidebar items */
        .swagger-ui .opblock-tag {
            background-color: #1b1b1b !important;
            border-bottom: 1px solid #404040 !important;
            color: #fff !important;
        }

        .swagger-ui .opblock-tag:hover {
            background-color: #2a2a2a !important;
        }

        /* Endpoint blocks */
        .swagger-ui .opblock {
            border: 1px solid #404040 !important;
            border-radius: 4px !important;
            background: #1b1b1b !important;
            margin: 0 0 10px !important;
        }

        .swagger-ui .opblock.opblock-get {
            border-color: #49cc90 !important;
            background: rgba(73, 204, 144, 0.1) !important;
        }

        .swagger-ui .opblock.opblock-post {
            border-color: #49cc90 !important;
            background: rgba(73, 204, 144, 0.1) !important;
        }

        .swagger-ui .opblock.opblock-put {
            border-color: #fca130 !important;
            background: rgba(252, 161, 48, 0.1) !important;
        }

        .swagger-ui .opblock.opblock-delete {
            border-color: #f93e3e !important;
            background: rgba(249, 62, 62, 0.1) !important;
        }

        .swagger-ui .opblock.opblock-patch {
            border-color: #50e3c2 !important;
            background: rgba(80, 227, 194, 0.1) !important;
        }

        /* Open operations */
        .swagger-ui .opblock.opblock-open .opblock-summary {
            border-bottom: 1px solid #404040 !important;
        }

        /* Operation summary */
        .swagger-ui .opblock .opblock-summary {
            color: #fff !important;
        }

        .swagger-ui .opblock .opblock-summary:hover {
            background-color: rgba(255, 255, 255, 0.05) !important;
        }

        /* Operation path */
        .swagger-ui .opblock .opblock-summary-path,
        .swagger-ui .opblock .opblock-summary-path a,
        .swagger-ui .opblock .opblock-summary-description {
            color: #fff !important;
        }

        /* Parameters */
        .swagger-ui .parameters-container .parameters-wrapper {
            background: #1b1b1b !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .parameters-container .parameters .parameter__name {
            color: #fff !important;
        }

        .swagger-ui .parameters-container .parameters .parameter__in {
            color: #49cc90 !important;
        }

        /* Request body */
        .swagger-ui .request-body .request-body-editor {
            background: #2a2a2a !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .request-body .request-body-editor textarea {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        /* Responses */
        .swagger-ui .responses-inner {
            background: #1b1b1b !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .responses-inner .response-col_status {
            color: #fff !important;
        }

        .swagger-ui .responses-inner .response-col_description {
            color: #fff !important;
        }

        .swagger-ui .responses-inner .response-content .response-col_description {
            color: #fff !important;
        }

        /* Models */
        .swagger-ui .model-box {
            background: #1b1b1b !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .model-box .model-title {
            color: #fff !important;
        }

        .swagger-ui .model .prop-type {
            color: #49cc90 !important;
        }

        .swagger-ui .model .prop-format {
            color: #e0e0e0 !important;
        }

        /* Input fields */
        .swagger-ui input,
        .swagger-ui select,
        .swagger-ui textarea {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui input:focus,
        .swagger-ui select:focus,
        .swagger-ui textarea:focus {
            border-color: #49cc90 !important;
            outline: none !important;
            box-shadow: 0 0 5px rgba(73, 204, 144, 0.5) !important;
        }

        /* Buttons */
        .swagger-ui .btn {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .btn:hover {
            background: #3a3a3a !important;
        }

        .swagger-ui .execute-wrapper .btn.execute {
            background: #49cc90 !important;
            color: #000 !important;
            border: none !important;
        }

        .swagger-ui .execute-wrapper .btn.execute:hover {
            background: #3ea876 !important;
        }

        /* Code blocks */
        .swagger-ui .microlight,
        .swagger-ui .highlight-code,
        .swagger-ui .highlight-code pre {
            background: #2a2a2a !important;
            color: #fff !important;
        }

        /* Headings */
        .swagger-ui h1,
        .swagger-ui h2,
        .swagger-ui h3,
        .swagger-ui h4,
        .swagger-ui h5,
        .swagger-ui h6 {
            color: #fff !important;
        }

        /* Links */
        .swagger-ui a {
            color: #49cc90 !important;
        }

        .swagger-ui a:hover {
            color: #3ea876 !important;
        }

        /* Horizontal rules */
        .swagger-ui hr {
            border-color: #404040 !important;
            background-color: #404040 !important;
        }

        /* Model toggles */
        .swagger-ui .model-toggle {
            color: #fff !important;
        }

        .swagger-ui .model-toggle.collapsed {
            color: #e0e0e0 !important;
        }

        /* Filter */
        .swagger-ui .filter-container input {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        /* Scheme container */
        .swagger-ui .scheme-container {
            background: #1b1b1b !important;
            border-bottom: 1px solid #404040 !important;
        }

        .swagger-ui .scheme-container .scheme-wrapper {
            color: #fff !important;
        }

        /* Info section */
        .swagger-ui .info {
            color: #fff !important;
        }

        .swagger-ui .info .title {
            color: #fff !important;
        }

        .swagger-ui .info .description {
            color: #e0e0e0 !important;
        }

        .swagger-ui .info p,
        .swagger-ui .info li {
            color: #e0e0e0 !important;
        }

        /* Expanded operation body */
        .swagger-ui .opblock-body {
            background: #1b1b1b !important;
            color: #fff !important;
        }

        .swagger-ui .opblock-body pre {
            background: #2a2a2a !important;
            color: #fff !important;
        }

        .swagger-ui .opblock-body pre .headerline {
            color: #fff !important;
        }

        /* Section headers - CRITICAL FIX */
        .swagger-ui .opblock .opblock-section-header {
            background: #2a2a2a !important;
            border-bottom: 1px solid #404040 !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        }

        .swagger-ui .opblock .opblock-section-header > label {
            color: #fff !important;
        }

        .swagger-ui .opblock .opblock-section-header h4 {
            color: #fff !important;
        }

        .swagger-ui .opblock .opblock-section-header > label {
            color: #e0e0e0 !important;
        }

        /* Tab headers */
        .swagger-ui .tab {
            background: #2a2a2a !important;
            color: #e0e0e0 !important;
        }

        .swagger-ui .tab li {
            color: #e0e0e0 !important;
        }

        .swagger-ui .tab li.active {
            background: #1b1b1b !important;
            color: #fff !important;
        }

        .swagger-ui .tab li button {
            color: #e0e0e0 !important;
        }

        .swagger-ui .tab li.active button {
            color: #fff !important;
        }

        /* Tables - COMPREHENSIVE FIX */
        .swagger-ui table {
            background: #1b1b1b !important;
        }

        .swagger-ui table thead tr,
        .swagger-ui table thead tr th,
        .swagger-ui .table-wrapper table thead tr th {
            background: #2a2a2a !important;
            color: #fff !important;
            border-color: #404040 !important;
        }

        .swagger-ui table tbody tr,
        .swagger-ui table tbody tr td,
        .swagger-ui .table-wrapper table tbody tr td {
            background: #1b1b1b !important;
            color: #e0e0e0 !important;
            border-color: #404040 !important;
        }

        .swagger-ui table tbody tr:hover,
        .swagger-ui table tbody tr:hover td {
            background: #2a2a2a !important;
        }

        /* "No parameters" and similar messages */
        .swagger-ui .opblock-description-wrapper,
        .swagger-ui .opblock-description,
        .swagger-ui .opblock-body .opblock-description-wrapper p {
            color: #e0e0e0 !important;
        }

        /* Response table */
        .swagger-ui .responses-wrapper {
            background: #1b1b1b !important;
        }

        .swagger-ui .responses-wrapper .responses-inner {
            background: #1b1b1b !important;
        }

        .swagger-ui .responses-wrapper .responses-inner > div > table,
        .swagger-ui .response-col_status,
        .swagger-ui .response-col_description {
            background: #1b1b1b !important;
        }

        /* Response description and content */
        .swagger-ui .response-col_description {
            color: #fff !important;
        }

        .swagger-ui .response-col_description .markdown,
        .swagger-ui .response-col_description p {
            color: #e0e0e0 !important;
        }

        /* Response links */
        .swagger-ui .response-col_links {
            color: #e0e0e0 !important;
        }

        /* Example sections */
        .swagger-ui .example-wrapper {
            background: #2a2a2a !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .example-section {
            background: #2a2a2a !important;
        }

        .swagger-ui .example-section .example {
            color: #e0e0e0 !important;
        }

        /* Try it out section */
        .swagger-ui .try-out {
            background: #1b1b1b !important;
            border-top: 1px solid #404040 !important;
        }

        .swagger-ui .try-out .execute-wrapper {
            background: #1b1b1b !important;
        }

        /* Response samples */
        .swagger-ui .responses-inner .response {
            background: #1b1b1b !important;
        }

        .swagger-ui .response.response_current .response-col_status {
            color: #49cc90 !important;
        }

        .swagger-ui .response.response_current .response-col_description {
            color: #fff !important;
        }

        /* Operation path and method */
        .swagger-ui .opblock-summary-method {
            color: #fff !important;
            background: transparent !important;
        }

        /* Parameter details */
        .swagger-ui .parameter__name,
        .swagger-ui .parameter__type,
        .swagger-ui .parameter__deprecated,
        .swagger-ui .parameter__in {
            color: #e0e0e0 !important;
        }

        .swagger-ui .parameter__in {
            color: #49cc90 !important;
        }

        /* Schema definitions */
        .swagger-ui .prop-format,
        .swagger-ui .prop-extension,
        .swagger-ui .prop-example {
            color: #e0e0e0 !important;
        }

        /* Property names and types */
        .swagger-ui .model .property {
            color: #e0e0e0 !important;
        }

        .swagger-ui .model .property.primitive {
            color: #49cc90 !important;
        }

        /* Errors */
        .swagger-ui .errors-wrapper {
            background: #1b1b1b !important;
            border: 1px solid #f93e3e !important;
        }

        .swagger-ui .errors-wrapper .error-wrapper {
            color: #fff !important;
        }

        /* Loading animation */
        .swagger-ui .loading-container .loading {
            background: #1b1b1b !important;
        }

        /* Modal dialogs */
        .swagger-ui .dialog-ux .modal-ux {
            background: #1b1b1b !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .dialog-ux .modal-ux-header {
            background: #2a2a2a !important;
            border-bottom: 1px solid #404040 !important;
            color: #fff !important;
        }

        .swagger-ui .dialog-ux .modal-ux-content {
            background: #1b1b1b !important;
            color: #e0e0e0 !important;
        }

        /* Content type selector */
        .swagger-ui .content-type-wrapper select,
        .swagger-ui select {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        /* Version badge */
        .swagger-ui .version-badge {
            background: #2a2a2a !important;
            color: #fff !important;
        }

        /* Authorizations */
        .swagger-ui .auth-wrapper {
            background: #1b1b1b !important;
            border-bottom: 1px solid #404040 !important;
        }

        .swagger-ui .auth-container {
            background: #1b1b1b !important;
        }

        /* Server selector */
        .swagger-ui .servers {
            background: #1b1b1b !important;
        }

        .swagger-ui .servers-title {
            color: #fff !important;
        }

        .swagger-ui .servers select {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        /* Download button */
        .swagger-ui .download-contents {
            background: #2a2a2a !important;
            color: #fff !important;
            border: 1px solid #404040 !important;
        }

        /* Markdown rendered content */
        .swagger-ui .markdown p,
        .swagger-ui .markdown code,
        .swagger-ui .renderedMarkdown p,
        .swagger-ui .renderedMarkdown code {
            color: #e0e0e0 !important;
        }

        .swagger-ui .markdown code,
        .swagger-ui .renderedMarkdown code {
            background: #2a2a2a !important;
            border: 1px solid #404040 !important;
        }

        /* Copy to clipboard button */
        .swagger-ui .copy-to-clipboard {
            background: #2a2a2a !important;
            border: 1px solid #404040 !important;
        }

        .swagger-ui .copy-to-clipboard button {
            color: #fff !important;
        }

        /* All text elements fallback */
        .swagger-ui span,
        .swagger-ui p,
        .swagger-ui div:not([class*="bg-"]):not([class*="opblock-summary-method"]) {
            color: inherit !important;
        }

        /* Wrapper backgrounds */
        .swagger-ui .wrapper {
            background: #1b1b1b !important;
        }

        .swagger-ui .col-12 {
            color: #fff !important;
        }
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
