from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks

from app.schemas.knowledge_base import (
    AnswerRequest,
    AnswerResponse,
    IntentDetectRequest,
    IntentDetectResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.intent_service import IntentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.api.v1.endpoints.generate import (
    DocxAutoRequest,
    PPTEditRequest,
    PPTLayoutAutoRequest,
    edit_ppt,
    generate_docx_auto,
    generate_ppt_auto_layout,
)

router = APIRouter()
kb_service = KnowledgeBaseService()
intent_service = IntentService()

_SUPPORTED_INTENTS = {
    "normal_chat",
    "generate_ppt",
    "modify_ppt",
    "generate_word",
    "modify_word",
}


def _base_qa_response(query: str, intent_meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "query": query,
        "answer": "",
        "citations": [],
        "intent": intent_meta.get("intent"),
        "intent_confidence": intent_meta.get("confidence"),
        "intent_reason": intent_meta.get("reason"),
        "intent_source": intent_meta.get("source"),
        "route": None,
        "task_result": None,
        "error": intent_meta.get("error"),
    }


def _merge_route_result(resp: Dict[str, Any], route: str, answer: str, task_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    resp["route"] = route
    resp["answer"] = answer
    if task_result is not None:
        resp["task_result"] = task_result
    return resp


async def _route_generate_ppt(request: AnswerRequest) -> Dict[str, Any]:
    payload = dict(request.task_payload or {})
    layout = str(payload.get("layout") or "").strip() or "general"
    source_text = str(payload.get("source_text") or request.query).strip()
    if not source_text:
        return {"ok": False, "message": "source_text 不能为空。", "result": None}
    req = PPTLayoutAutoRequest(
        layout=layout,
        source_text=source_text,
        slides_total=int(payload.get("slides_total") or 10),
        title=payload.get("title"),
        subtitle=payload.get("subtitle"),
        extra_instructions=payload.get("extra_instructions"),
        with_mp4=bool(payload.get("with_mp4", False)),
        mp4_portrait=payload.get("mp4_portrait"),
        mp4_max_wait_seconds=payload.get("mp4_max_wait_seconds"),
        mp4_pages=payload.get("mp4_pages"),
    )
    result = await generate_ppt_auto_layout(req, BackgroundTasks())
    return {
        "ok": True,
        "message": "已完成PPT生成任务。",
        "result": result if isinstance(result, dict) else {"raw": result},
    }


async def _route_modify_ppt(request: AnswerRequest) -> Dict[str, Any]:
    payload = dict(request.task_payload or {})
    ppt_id = str(payload.get("ppt_id") or "").strip()
    base_version = payload.get("base_version")
    if not ppt_id or base_version is None:
        return {
            "ok": False,
            "message": "检测到PPT修改意图，请补充 task_payload.ppt_id 和 task_payload.base_version。",
            "result": None,
        }
    req = PPTEditRequest(
        ppt_id=ppt_id,
        base_version=int(base_version),
        session_id=request.session_id,
        instructions=str(payload.get("instructions") or request.query).strip() or "请根据要求优化内容",
        patch=payload.get("patch") if isinstance(payload.get("patch"), dict) else None,
        title=payload.get("title"),
        subtitle=payload.get("subtitle"),
        with_mp4=bool(payload.get("with_mp4", False)),
        mp4_portrait=payload.get("mp4_portrait"),
        mp4_max_wait_seconds=payload.get("mp4_max_wait_seconds"),
        mp4_pages=payload.get("mp4_pages"),
    )
    result = await edit_ppt(req, BackgroundTasks())
    return {
        "ok": True,
        "message": "已完成PPT修改任务。",
        "result": result if isinstance(result, dict) else {"raw": result},
    }


async def _route_generate_word(request: AnswerRequest) -> Dict[str, Any]:
    payload = dict(request.task_payload or {})
    topic = str(payload.get("topic") or request.query).strip()
    if not topic:
        return {"ok": False, "message": "检测到Word生成意图，请补充 task_payload.topic 或 query。", "result": None}
    req = DocxAutoRequest(
        topic=topic,
        title=payload.get("title"),
        extra_instructions=payload.get("extra_instructions"),
    )
    result = await generate_docx_auto(req)
    return {
        "ok": True,
        "message": "已完成Word生成任务。",
        "result": result if isinstance(result, dict) else {"raw": result},
    }


async def _route_modify_word(request: AnswerRequest) -> Dict[str, Any]:
    payload = dict(request.task_payload or {})
    source_text = str(payload.get("source_text") or "").strip()
    extra = str(payload.get("extra_instructions") or "").strip()
    if not source_text:
        return {
            "ok": False,
            "message": "检测到Word修改意图，请补充 task_payload.source_text（原文）后再执行修改。",
            "result": None,
        }
    topic = str(payload.get("topic") or "原文改写").strip() or "原文改写"
    merged_extra = (
        f"请基于以下原文执行修改，不要丢失核心信息。原文：{source_text}\n"
        f"修改要求：{request.query}\n"
        f"补充要求：{extra}"
    )
    req = DocxAutoRequest(
        topic=topic,
        title=payload.get("title"),
        extra_instructions=merged_extra,
    )
    result = await generate_docx_auto(req)
    return {
        "ok": True,
        "message": "已按修改要求重生成Word文档。",
        "result": result if isinstance(result, dict) else {"raw": result},
    }


@router.post("/search/fulltext", response_model=SearchResponse)
async def fulltext_search(request: SearchRequest) -> SearchResponse:
    results = kb_service.fulltext_search(request.query, request.top_k, request.document_id)
    return SearchResponse(mode="fulltext", query=request.query, results=results)


@router.post("/search/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest) -> SearchResponse:
    results = kb_service.semantic_search(request.query, request.top_k, request.document_id)
    return SearchResponse(mode="semantic", query=request.query, results=results)


@router.post("/search/hybrid", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest) -> SearchResponse:
    results = kb_service.hybrid_search(request.query, request.top_k, request.document_id)
    return SearchResponse(mode="hybrid", query=request.query, results=results)


@router.post("/qa", response_model=AnswerResponse)
async def qa(request: AnswerRequest) -> AnswerResponse:
    query = str(request.query or "").strip()
    forced_intent = str(request.intent or "").strip().lower()
    if forced_intent in _SUPPORTED_INTENTS:
        intent_meta: Dict[str, Any] = {
            "query": query,
            "intent": forced_intent,
            "confidence": 1.0,
            "reason": "客户端显式指定意图",
            "source": "client_override",
            "error": None,
        }
    else:
        intent_meta = intent_service.detect_user_intent(query)

    intent = str(intent_meta.get("intent") or "normal_chat")
    response = _base_qa_response(query, intent_meta)

    if intent == "normal_chat":
        result = kb_service.answer(
            query,
            request.top_k,
            request.document_id,
            request.temporary_document_ids,
            request.session_id,
        )
        response["answer"] = str(result.get("answer") or "")
        response["citations"] = result.get("citations") or []
        response["route"] = "knowledge_base_answer"
        return AnswerResponse(**response)

    try:
        if intent == "generate_ppt":
            routed = await _route_generate_ppt(request)
            return AnswerResponse(**_merge_route_result(response, "generate_ppt", routed["message"], routed.get("result")))
        if intent == "modify_ppt":
            routed = await _route_modify_ppt(request)
            return AnswerResponse(**_merge_route_result(response, "modify_ppt", routed["message"], routed.get("result")))
        if intent == "generate_word":
            routed = await _route_generate_word(request)
            return AnswerResponse(**_merge_route_result(response, "generate_word", routed["message"], routed.get("result")))
        if intent == "modify_word":
            routed = await _route_modify_word(request)
            return AnswerResponse(**_merge_route_result(response, "modify_word", routed["message"], routed.get("result")))
    except Exception as e:
        response["route"] = f"{intent}_failed"
        response["error"] = str(e)
        response["answer"] = f"意图识别为 {intent}，但任务执行失败：{e}"
        return AnswerResponse(**response)

    # Defensive fallback for unexpected intents
    result = kb_service.answer(
        query,
        request.top_k,
        request.document_id,
        request.temporary_document_ids,
        request.session_id,
    )
    response["answer"] = str(result.get("answer") or "")
    response["citations"] = result.get("citations") or []
    response["route"] = "fallback_knowledge_base_answer"
    return AnswerResponse(**response)


@router.post("/intent/detect", response_model=IntentDetectResponse)
async def detect_user_intent(request: IntentDetectRequest) -> IntentDetectResponse:
    result = intent_service.detect_user_intent(request.query)
    return IntentDetectResponse(**result)
