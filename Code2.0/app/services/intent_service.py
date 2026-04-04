import json
import logging
import os
import re
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class IntentService:
    _supported_intents = {
        "generate_ppt",
        "modify_ppt",
        "generate_word",
        "modify_word",
        "normal_chat",
    }

    def __init__(self) -> None:
        self.llm = self._build_llm()

    def _build_llm(self) -> Optional[Any]:
        api_key = (os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "") or "").strip()
        model_name = (os.getenv("OPENAI_MODEL") or getattr(settings, "OPENAI_MODEL", "") or "").strip()
        base_url = (os.getenv("OPENAI_BASE_URL") or getattr(settings, "OPENAI_BASE_URL", "") or "").strip()
        dash_key = (os.getenv("DASHSCOPE_API_KEY") or getattr(settings, "DASHSCOPE_API_KEY", "") or "").strip()
        try:
            from langchain_openai import ChatOpenAI
            effective_api_key = api_key or (dash_key if base_url else "")
            if effective_api_key and model_name and (base_url or "gpt" in model_name or "o1" in model_name):
                kwargs: Dict[str, Any] = {"model": model_name, "api_key": effective_api_key, "temperature": 0.2}
                if base_url:
                    kwargs["base_url"] = base_url
                return ChatOpenAI(**kwargs)
        except Exception:
            logger.warning("ChatOpenAI initialization failed", exc_info=True)
        try:
            if dash_key:
                from langchain_community.chat_models.tongyi import ChatTongyi
                qwen_model = model_name or "qwen-turbo"
                return ChatTongyi(model=qwen_model, api_key=dash_key)
        except Exception:
            logger.warning("ChatTongyi initialization failed (ensure `pip install dashscope`)", exc_info=True)
        return None

    def detect_user_intent(self, query: str) -> Dict[str, Any]:
        text = (query or "").strip()
        if not text:
            return {
                "query": query,
                "intent": "normal_chat",
                "confidence": 0.0,
                "reason": "输入为空，返回默认意图",
                "source": "default",
                "error": "empty_query",
            }
        rule_result = self._classify_intent_by_rules(text)
        if self.llm is None:
            self.llm = self._build_llm()
        if self.llm is None:
            if rule_result is not None:
                return {
                    "query": query,
                    "intent": rule_result["intent"],
                    "confidence": rule_result["confidence"],
                    "reason": rule_result["reason"],
                    "source": "rule_fallback",
                    "error": "llm_unavailable",
                }
            return {
                "query": query,
                "intent": "normal_chat",
                "confidence": 0.45,
                "reason": "LLM不可用且规则无法明确判断，降级为正常对话",
                "source": "default",
                "error": "llm_unavailable",
            }
        system_text = (
            "你是意图分类器。"
            "请将用户输入准确分类到以下五类之一："
            "generate_ppt、modify_ppt、generate_word、modify_word、normal_chat。"
            "判定规则："
            "1) 明确要求新建/生成PPT归类为generate_ppt；"
            "2) 明确要求改已有PPT归类为modify_ppt；"
            "3) 明确要求新建/生成Word文档归类为generate_word；"
            "4) 明确要求改已有Word文档归类为modify_word；"
            "5) 非文档生产任务、闲聊、问答、含糊请求归类为normal_chat。"
            "仅输出JSON对象，字段必须是intent、confidence、reason。"
            "confidence范围是0到1。"
        )
        hint = "none"
        if rule_result is not None:
            hint = json.dumps(rule_result, ensure_ascii=False)
        user_text = (
            f"用户输入：{text}\n"
            f"规则候选：{hint}\n"
            "请严格输出JSON，不要包含代码块标记。"
        )
        try:
            response = self.llm.invoke([SystemMessage(content=system_text), HumanMessage(content=user_text)])
            raw_text = self._extract_llm_text(response)
            parsed = self._parse_intent_output(raw_text)
            if parsed is not None:
                llm_intent = parsed["intent"]
                llm_confidence = parsed["confidence"]
                llm_reason = parsed["reason"]
                if rule_result is not None:
                    same_intent = rule_result["intent"] == llm_intent
                    if same_intent:
                        llm_confidence = max(float(llm_confidence), float(rule_result["confidence"]))
                        llm_reason = f"{llm_reason}；规则校验一致"
                    elif float(rule_result["confidence"]) >= 0.93 and float(llm_confidence) <= 0.7:
                        return {
                            "query": query,
                            "intent": rule_result["intent"],
                            "confidence": rule_result["confidence"],
                            "reason": f"{rule_result['reason']}；LLM置信度较低，采用规则结果",
                            "source": "rule_override",
                            "error": None,
                        }
                return {
                    "query": query,
                    "intent": llm_intent,
                    "confidence": llm_confidence,
                    "reason": llm_reason,
                    "source": "llm",
                    "error": None,
                }
        except Exception:
            logger.exception("Intent detection with LLM failed")
        if rule_result is not None:
            return {
                "query": query,
                "intent": rule_result["intent"],
                "confidence": rule_result["confidence"],
                "reason": f"{rule_result['reason']}；LLM响应异常，降级使用规则分类",
                "source": "rule_fallback",
                "error": "llm_invoke_failed",
            }
        return {
            "query": query,
            "intent": "normal_chat",
            "confidence": 0.4,
            "reason": "LLM响应异常且规则无法明确判断，降级为正常对话",
            "source": "default",
            "error": "llm_invoke_failed",
        }

    def _classify_intent_by_rules(self, query: str) -> Optional[Dict[str, Any]]:
        text = (query or "").strip()
        lowered = text.lower()
        if not text:
            return None
        generate_words = ["生成", "创建", "制作", "新建", "产出", "起草", "写一份", "做一个", "输出"]
        modify_words = ["修改", "改", "调整", "优化", "编辑", "重写", "更新", "补充", "删减", "替换"]
        existing_words = ["现有", "已有", "当前", "这份", "这个", "刚才", "上面", "原来", "原文", "原稿"]
        ppt_words = ["ppt", "幻灯片", "课件", "演示文稿", "powerpoint", "slides"]
        word_words = ["word", ".doc", ".docx", "文档", "报告", "论文", "说明书", "公文", "合同"]
        has_generate = any(word in lowered or word in text for word in generate_words)
        has_modify = any(word in lowered or word in text for word in modify_words)
        has_existing = any(word in lowered or word in text for word in existing_words)
        has_ppt = any(word in lowered or word in text for word in ppt_words)
        has_word = any(word in lowered or word in text for word in word_words)
        if has_ppt and has_word:
            return {
                "intent": "normal_chat",
                "confidence": 0.55,
                "reason": "同时出现PPT与Word对象，任务目标不明确",
            }
        if has_ppt:
            if has_modify or has_existing:
                return {"intent": "modify_ppt", "confidence": 0.95, "reason": "识别到PPT修改意图关键词"}
            if has_generate:
                return {"intent": "generate_ppt", "confidence": 0.93, "reason": "识别到PPT生成意图关键词"}
            if any(token in lowered for token in ["怎么做ppt", "做ppt", "帮我做ppt"]):
                return {"intent": "generate_ppt", "confidence": 0.84, "reason": "识别到PPT制作表达"}
            return {"intent": "normal_chat", "confidence": 0.6, "reason": "仅提及PPT但缺乏明确生成或修改动作"}
        if has_word:
            if has_modify or has_existing:
                return {"intent": "modify_word", "confidence": 0.95, "reason": "识别到Word修改意图关键词"}
            if has_generate:
                return {"intent": "generate_word", "confidence": 0.93, "reason": "识别到Word生成意图关键词"}
            if any(token in lowered for token in ["写word", "写文档", "写报告"]):
                return {"intent": "generate_word", "confidence": 0.84, "reason": "识别到Word写作表达"}
            return {"intent": "normal_chat", "confidence": 0.6, "reason": "仅提及Word但缺乏明确生成或修改动作"}
        return None

    def _extract_llm_text(self, response: Any) -> str:
        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue
                if isinstance(item, dict):
                    value = item.get("text")
                    if isinstance(value, str):
                        parts.append(value)
            return "\n".join(parts).strip()
        return str(content).strip()

    def _parse_intent_output(self, text: str) -> Optional[Dict[str, Any]]:
        cleaned = (text or "").strip()
        if not cleaned:
            return None
        payload: Optional[Dict[str, Any]] = None
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                payload = data
        except Exception:
            payload = None
        if payload is None:
            matched = re.search(r"\{[\s\S]*\}", cleaned)
            if matched:
                try:
                    data = json.loads(matched.group(0))
                    if isinstance(data, dict):
                        payload = data
                except Exception:
                    payload = None
        if payload is None:
            return None
        raw_intent = str(payload.get("intent", "")).strip().lower()
        if raw_intent not in self._supported_intents:
            return None
        try:
            confidence = float(payload.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        reason = str(payload.get("reason", "")).strip() or "LLM完成语义分类"
        return {"intent": raw_intent, "confidence": confidence, "reason": reason}
