import json
import time
import uuid
from typing import AsyncGenerator, Dict, Any, List
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from core.database import async_session_factory
from core.models.factory import get_llm_client
from core.redis import get_redis
from models.chat import AssistantTurn, Conversation, Message, Verdict
from models.document import Document
from modules.chat.citation_validator import validate_citations_sync
from modules.chat.response_parser import extract_llm_json_response
from modules.confidence.service import compute_composite_confidence, judge_faithfulness
from modules.projects.service import verify_project_access
from modules.retrieval.hybrid import hybrid_retrieve
from modules.retrieval.query_rewrite import rewrite_query_if_needed
from modules.retrieval.rerank import rerank_and_assemble_context

settings = get_settings()


async def stream_chat_response(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    query_text: str,
    debug: bool = False,
) -> AsyncGenerator[str, None]:
    start_time = time.perf_counter()
    conv_id_str = str(conversation_id)

    async with async_session_factory() as db:
        conv = (await db.execute(select(Conversation).where(Conversation.id == conversation_id))).scalar_one_or_none()
        if not conv:
            yield f"event: error\ndata: {json.dumps({'code': 'NOT_FOUND', 'message': 'Conversation not found'})}\n\n"
            return
        await verify_project_access(db, conv.project_id, user_id)
        project_id = conv.project_id

        # Save User Message
        user_msg = Message(conversation_id=conversation_id, role="user", content_md=query_text)
        db.add(user_msg)
        await db.commit()

    # 1. Retrieval
    yield f"event: status\ndata: {json.dumps({'stage': 'retrieving'})}\n\n"
    rewritten_query = await rewrite_query_if_needed(conv_id_str, query_text)

    async with async_session_factory() as db:
        retrieved_chunks, debug_retrieval = await hybrid_retrieve(db, project_id, rewritten_query)

        # 2. Reranking
        yield f"event: status\ndata: {json.dumps({'stage': 'reranking'})}\n\n"
        contexts, debug_rerank, top_score = await rerank_and_assemble_context(db, rewritten_query, retrieved_chunks)

        if debug:
            debug_retrieval["reranked"] = debug_rerank
            yield f"event: retrieval\ndata: {json.dumps(debug_retrieval)}\n\n"

        # Check Insufficiency Gate
        if top_score < settings.RERANK_MIN_SCORE or not contexts:
            docs_stmt = select(Document.id, Document.filename).where(Document.project_id == project_id)
            searched_docs = [{"document_id": str(r[0]), "filename": r[1]} for r in (await db.execute(docs_stmt)).all()]
            insufficient_md = "I don't have enough evidence in this project's documents to answer that."

            assistant_msg = Message(conversation_id=conversation_id, role="assistant", content_md=insufficient_md)
            db.add(assistant_msg)
            await db.flush()

            turn = AssistantTurn(
                message_id=assistant_msg.id,
                verdict=Verdict.INSUFFICIENT_EVIDENCE,
                confidence=0.31,
                top_rerank_score=top_score,
                latency_ms=int((time.perf_counter() - start_time) * 1000),
                model_provider=settings.LLM_PROVIDER,
                model_name=settings.LLM_MODEL,
            )
            db.add(turn)
            await db.commit()

            yield f"event: final\ndata: {json.dumps({'verdict': 'insufficient_evidence', 'confidence': 0.31, 'searched_documents': searched_docs, 'content_md': insufficient_md})}\n\n"
            return

    # 3. Generation
    yield f"event: status\ndata: {json.dumps({'stage': 'generating', 'provider': settings.LLM_PROVIDER, 'model': settings.LLM_MODEL})}\n\n"
    llm = get_llm_client()
    context_str = "\n\n".join(
        [f"[Doc: {c['document_name']} | Chunk ID: {c['chunk_id']}]\n{c['content']}" for c in contexts]
    )
    prompt = f"Context:\n{context_str}\n\nUser Question:\n{query_text}"

    try:
        llm_resp = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            system_prompt='Answer strictly from context in JSON format: {"answer_md": "...", "claims": [{"text": "...", "citation_ids": ["uuid"]}]}',
            temperature=0.2,
            json_mode=True,
        )
    except Exception as e:
        error_msg = str(e)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        async with async_session_factory() as db:
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content_md=f"Error generating response: {error_msg}",
            )
            db.add(assistant_msg)
            await db.flush()

            turn = AssistantTurn(
                message_id=assistant_msg.id,
                verdict=Verdict.ERROR,
                confidence=0.0,
                latency_ms=latency_ms,
                model_provider=settings.LLM_PROVIDER,
                model_name=settings.LLM_MODEL,
            )
            db.add(turn)
            await db.commit()

        yield f"event: error\ndata: {json.dumps({'code': 'LLM_ERROR', 'message': error_msg})}\n\n"
        yield f"event: final\ndata: {json.dumps({'message_id': str(assistant_msg.id), 'verdict': 'error', 'confidence': 0.0, 'content_md': assistant_msg.content_md})}\n\n"
        return

    answer_md, claims = extract_llm_json_response(llm_resp.content)

    # Stream tokens
    for word in answer_md.split(" "):
        yield f"event: token\ndata: {json.dumps({'t': word + ' '})}\n\n"

    # Citation Validation
    all_valid, valid_citations, coverage = validate_citations_sync(claims, contexts)
    for cit in valid_citations:
        yield f"event: citation\ndata: {json.dumps(cit)}\n\n"

    # 4. Verifying
    yield f"event: status\ndata: {json.dumps({'stage': 'verifying'})}\n\n"
    faithfulness, _ = await judge_faithfulness(contexts, answer_md)
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    confidence = compute_composite_confidence(faithfulness, top_score, coverage, latency_ms)

    verdict = Verdict.ANSWERED if all_valid else Verdict.UNVERIFIED
    if not all_valid:
        confidence = min(0.49, confidence)

    # Persist Assistant Turn
    async with async_session_factory() as db:
        assistant_msg = Message(conversation_id=conversation_id, role="assistant", content_md=answer_md)
        db.add(assistant_msg)
        await db.flush()

        turn = AssistantTurn(
            message_id=assistant_msg.id,
            verdict=verdict,
            confidence=confidence,
            faithfulness=faithfulness,
            top_rerank_score=top_score,
            coverage=coverage,
            latency_ms=latency_ms,
            prompt_tokens=llm_resp.prompt_tokens,
            completion_tokens=llm_resp.completion_tokens,
            cost_usd=llm_resp.cost_usd,
            model_provider=llm_resp.provider,
            model_name=llm_resp.model,
            citations=valid_citations,
        )
        db.add(turn)
        await db.commit()

        # Update Redis memory
        redis_cli = await get_redis()
        await redis_cli.rpush(
            f"conv:{conv_id_str}:last_turns",
            json.dumps({"role": "user", "content": query_text}),
            json.dumps({"role": "assistant", "content": answer_md}),
        )
        await redis_cli.ltrim(f"conv:{conv_id_str}:last_turns", -12, -1)

    final_payload = {
        "message_id": str(assistant_msg.id),
        "verdict": verdict.value,
        "confidence": confidence,
        "faithfulness": faithfulness,
        "coverage": coverage,
        "top_rerank_score": top_score,
        "latency_ms": latency_ms,
        "prompt_tokens": llm_resp.prompt_tokens,
        "completion_tokens": llm_resp.completion_tokens,
        "cost_usd": llm_resp.cost_usd,
        "model_provider": llm_resp.provider,
        "model_name": llm_resp.model,
    }
    yield f"event: final\ndata: {json.dumps(final_payload)}\n\n"
