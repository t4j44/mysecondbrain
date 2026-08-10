from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_portfolio,
    founder,
    knowledge,
    mcp,
    network,
    pdf_analysis,
    system,
)

api_router = APIRouter()


@api_router.get("", include_in_schema=False)
async def api_v1_root():
    return {
        "status": "online",
        "service": "Taj's Second Brain API",
        "docs": "/api/docs",
    }

# Register Founder & Dashboard modules
api_router.include_router(founder.router, tags=["Founder & Operations"])

# Register Network & CRM modules
api_router.include_router(network.router, tags=["Network & CRM"])

# Register Knowledge, Memories & Document modules
api_router.include_router(knowledge.router, tags=["Knowledge & Memories"])

# Register AI Intelligence, Portfolio & Content modules
api_router.include_router(ai_portfolio.router, tags=["AI & Portfolio"])

# Register System Integrations, Export & Audit modules
api_router.include_router(system.router, tags=["Integrations & System"])

# Register PDF & Document Analysis modules
api_router.include_router(pdf_analysis.router, tags=["PDF & Document Analysis"])


# Register MCP & External AI Integration modules
api_router.include_router(mcp.router, prefix="/mcp", tags=["MCP & External AI"])
