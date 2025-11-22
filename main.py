from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from routers import user_router, post_router, comment_router, like_router, follow_router, hashtag_router

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "https://db-project-fe-nltd.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(user_router.router)
app.include_router(post_router.router)
app.include_router(comment_router.router)
app.include_router(like_router.router)
app.include_router(follow_router.router)
app.include_router(hashtag_router.router)



@app.get("/")
async def read_root():
    return {"message": "Welcome to Micro SNS Backend!"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Micro SNS API",
        version="1.0.0",
        description="API for a Micro SNS service",
        routes=app.routes,
    )
    # Manually define the security scheme to force a simple bearer token input
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token in the format: Bearer &lt;token&gt;"
        }
    }
    # Apply the security scheme to all paths that need it
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            if operation.get("security") is not None:
                operation["security"] = [{
                    "BearerAuth": []
                }]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi