from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.lifespan import lifespan
from server.routers import rpc
from server.routers import web

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(rpc.router, prefix="/rpc")
app.include_router(web.router)

@app.get("/")
async def get_root():
  return {"message": "You should not be here."}
