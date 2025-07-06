from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from server.lifespan import lifespan
from server.routers import rpc_router
from server.routers import web_router

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(rpc_router.router, prefix="/rpc")
app.include_router(web_router.router)

@app.get("/")
async def get_root():
  return {"message": "You should not be here."}
