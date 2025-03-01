import uvicorn
from fastapi import FastAPI
from app.routers import router_user, router_training

app = FastAPI()

app.include_router(router_user)
app.include_router(router_training)

if __name__ == "__main__":
	uvicorn.run("main:app", reload=True)