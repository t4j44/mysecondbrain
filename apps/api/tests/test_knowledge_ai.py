from io import BytesIO

import pytest


@pytest.mark.asyncio
async def test_memory_creation_and_listing(async_client, auth_headers):
    res = await async_client.post(
        "/api/v1/memories",
        json={
            "title": "Meeting Note: Architect Discussion",
            "body": "Discussed RAG vector indexing",
            "type": "meeting",
            "importance": 9,
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    assert res.json()["title"] == "Meeting Note: Architect Discussion"

    list_res = await async_client.get("/api/v1/memories?type=meeting", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) == 1


@pytest.mark.asyncio
async def test_idea_registration_and_conversion(async_client, auth_headers):
    # 1. Create Idea
    idea_res = await async_client.post(
        "/api/v1/ideas",
        json={
            "title": "Automated RAG Engine",
            "problem": "Information overload",
            "solution": "Vector search indexing",
        },
        headers=auth_headers,
    )
    assert idea_res.status_code == 201
    idea_id = idea_res.json()["id"]

    # 2. Convert Idea to Actionable Project (Task 19)
    conv_res = await async_client.post(f"/api/v1/ideas/{idea_id}/convert", headers=auth_headers)
    assert conv_res.status_code == 200
    data = conv_res.json()
    assert data["idea_id"] == idea_id
    assert "project_id" in data

    # 3. Verify Idea status is now 'converted' and second attempt fails
    second_conv = await async_client.post(f"/api/v1/ideas/{idea_id}/convert", headers=auth_headers)
    assert second_conv.status_code == 409  # Conflict!


@pytest.mark.asyncio
async def test_document_upload_and_processing(async_client, auth_headers):
    file_content = b"Tajs Second Brain Architecture Details: RAG hybrid search with Gemini LLM."
    files = {"file": ("architecture_overview.pdf", BytesIO(file_content), "application/pdf")}

    res = await async_client.post("/api/v1/documents", files=files, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "architecture_overview.pdf"
    assert data["processing_status"] in {"pending", "processing", "completed"}


@pytest.mark.asyncio
async def test_ai_search_and_generation(async_client, auth_headers):
    # Test semantic RAG search endpoint
    search_res = await async_client.post(
        "/api/v1/ai/search", json={"query": "architecture details"}, headers=auth_headers
    )
    assert search_res.status_code == 200
    assert "results" in search_res.json()

    # Test AI grounded content generate endpoint
    gen_res = await async_client.post(
        "/api/v1/ai/content-generate",
        json={"prompt": "Summarize key architecture deliverables."},
        headers=auth_headers,
    )
    assert gen_res.status_code == 200
    assert "generated_text" in gen_res.json()
    assert "source_citations" in gen_res.json()


@pytest.mark.asyncio
async def test_ai_cover_letter_and_linkedin(async_client, auth_headers):
    # 1. Record an achievement first
    ach_res = await async_client.post(
        "/api/v1/achievements",
        json={
            "title": "Architected Taj's Second Brain",
            "role": "Founder & AI Product Manager",
            "category": "technical",
            "responsibilities": ["Lead FastAPI, Supabase RLS, and AI RAG pipelines"],
            "impact": "Delivered production-grade system 2x ahead of schedule",
        },
        headers=auth_headers,
    )
    assert ach_res.status_code == 201
    ach_id = ach_res.json()["id"]

    # 2. Test Cover Letter synthesis
    cl_res = await async_client.post(
        "/api/v1/ai/cover-letter",
        json={
            "achievement_id": ach_id,
            "target_role": "Principal Engineer",
            "company_name": "Google DeepMind",
        },
        headers=auth_headers,
    )
    assert cl_res.status_code == 200
    assert "cover_letter_text" in cl_res.json()

    # 3. Test LinkedIn Post synthesis
    li_res = await async_client.post(
        "/api/v1/ai/linkedin-post",
        json={"achievement_id": ach_id, "tone": "engaging", "include_hashtags": True},
        headers=auth_headers,
    )
    assert li_res.status_code == 200
    assert "post_text" in li_res.json()
