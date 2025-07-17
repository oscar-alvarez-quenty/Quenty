from fastapi import FastAPI
from src.api.controllers import customer_controller, order_controller
from src.infrastructure.database.database import engine, Base

app = FastAPI(
    title="Quenty Logistics Platform",
    description="DDD-based logistics platform with FastAPI and SQLAlchemy",
    version="1.0.0"
)

# Create database tables
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Include routers
app.include_router(customer_controller.router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(order_controller.router, prefix="/api/v1/orders", tags=["orders"])

@app.get("/")
async def root():
    return {"message": "Quenty Logistics Platform API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)