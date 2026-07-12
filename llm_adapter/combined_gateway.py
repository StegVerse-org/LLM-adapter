"""Combined governed gateway application for Ecosystem Chat and External Chat."""
from llm_adapter.ecosystem_chat_gateway import app
from llm_adapter.external_chat_api import router as external_chat_router
from llm_adapter.external_review_api import router as external_review_router

app.include_router(external_chat_router)
app.include_router(external_review_router)
