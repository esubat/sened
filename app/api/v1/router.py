from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.document import router as document_router
from app.api.v1.upload import router as upload_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(document_router)
router.include_router(upload_router)
