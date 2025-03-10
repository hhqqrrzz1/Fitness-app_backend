import uvicorn
from fastapi import FastAPI
from app.routers import router_user, router_training, router_muscle_group

app = FastAPI()

app.include_router(router_user)
app.include_router(router_training)
app.include_router(router_muscle_group)

if __name__ == "__main__":
	uvicorn.run("main:app", reload=True)