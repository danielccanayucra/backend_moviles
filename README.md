# EstuRooms — Backend (FastAPI + JWT + SQLAlchemy)

API REST para app móvil de alquiler/búsqueda de cuartos enfocada en estudiantes y propietarios.

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.x + Pydantic v2
- MySQL o PostgreSQL (config por `DB_URL`)
- JWT (access/refresh)
- Subida de imágenes local (`/media`) en dev
- SMTP para correos
- Endpoints incluidos: auth, users, residences, rooms, uploads, **reservations**, **favorites**, **reviews**

## Setup
```bash
cd esturooms-backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ajusta DB_URL y SECRET_KEY
uvicorn app.main:app --reload
```
Docs: http://127.0.0.1:8000/docs
