import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from server import lifespan, rpc_router, web_router, configure_root_logging

configure_root_logging(4)

app = FastAPI(lifespan=lifespan.lifespan)
app.mount("/static", web_router.app)
app.include_router(rpc_router.router, prefix="/rpc")


@app.get("/")
async def get_root():
  return {"message": "Static assets are served from /static/."}


@app.exception_handler(Exception)
async def log_exceptions(request: Request, exc: Exception):
  logging.exception("Unhandled exception")
  return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
