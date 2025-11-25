import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from pathlib import Path
from app.core.config import settings
from app.db.session import init_db
from app.api.v1.endpoints import (
    auth,
    users,
    residences,
    rooms,
    uploads,
    reservations,
    favorites,
    reviews,
    contracts,
    contract_details,
    chat,
)


# --- Manejo de inicio y apagado del servidor ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔹 Evento de inicio (antes: @app.on_event("startup"))
    print("🚀 Iniciando aplicación...")
    init_db()  # Inicializa la BD al arrancar la app

    # 🔹 Crear carpeta 'media' si no existe
    if not os.path.exists("media"):
        os.makedirs("media")

    yield  # Aquí la app se ejecuta normalmente

    # 🔹 Evento de apagado (antes: @app.on_event("shutdown"))
    print("🛑 Apagando aplicación...")


# --- Inicialización principal ---
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
# 👉 ruta base: ajusta si main.py no está en app/
BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "api" / "generated_contracts"
GENERATED_DIR.mkdir(exist_ok=True)

# Sirve /generated_contracts/*.pdf
app.mount(
    "/generated_contracts",
    StaticFiles(directory=str(GENERATED_DIR)),
    name="generated_contracts",
)
# --- Configuración CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Archivos estáticos (media) ---
if not os.path.exists("media"):
    os.makedirs("media")
app.mount("/media", StaticFiles(directory="media"), name="media")


# --- Definir esquema OAuth2 para Swagger ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def custom_openapi():
    """
    Personaliza el esquema OpenAPI para mostrar el botón Authorize (Bearer Token)
    y marcar las rutas protegidas.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="API para alquiler y búsqueda de habitaciones - EstuRooms",
        routes=app.routes,
    )

    # Agrega seguridad global (Bearer JWT)
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Aplica la seguridad a todos los endpoints por defecto
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Asigna el OpenAPI personalizado
app.openapi = custom_openapi


# --- Rutas principales ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(residences.router, prefix="/api/v1/residences", tags=["residences"])
app.include_router(rooms.router, prefix="/api/v1/rooms", tags=["rooms"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])
app.include_router(reservations.router, prefix="/api/v1/reservations", tags=["reservations"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["favorites"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["Contracts"])
app.include_router(
    contract_details.router,
    prefix="/api/v1/contract_details",
    tags=["Contract_details"],
)
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


# --- Punto de entrada ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
