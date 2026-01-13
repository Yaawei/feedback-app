from fastapi import FastAPI
from api.routes import router as inbox_router

app = FastAPI(title="Feedback app")
app.include_router(inbox_router)

@app.get("/")
def health_check():
    return {"status": "ok"}
