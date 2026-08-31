"""LangGraph 工作流定义（可选依赖）。

安装 langgraph 后，此模块提供标准的多节点 Agent 图：
    classify -> route -> {rag_answer | order_query | translation | human_handoff}
"""
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    query: str
    intent: str
    answer: str
    sources: list
    need_human: bool


def _node_classify(state: AgentState) -> AgentState:
    from .workflow import classify_intent, need_human

    state["intent"] = classify_intent(state["query"])
    state["need_human"] = need_human(state["query"])
    return state


def _route(state: AgentState) -> str:
    if state.get("need_human"):
        return "human_handoff"
    return state.get("intent", "rag_answer")


def _node_rag_answer(state: AgentState) -> AgentState:
    state["answer"] = "（LangGraph 节点）rag_answer"
    return state


def _node_order_query(state: AgentState) -> AgentState:
    state["answer"] = "（LangGraph 节点）order_query"
    return state


def _node_translation(state: AgentState) -> AgentState:
    state["answer"] = "（LangGraph 节点）translation"
    return state


def _node_human_handoff(state: AgentState) -> AgentState:
    state["answer"] = "（LangGraph 节点）human_handoff：已为您转接人工客服。"
    return state


def build_workflow():
    """构建并编译 LangGraph 状态图。"""
    try:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(AgentState)
        graph.add_node("classify", _node_classify)
        graph.add_node("rag_answer", _node_rag_answer)
        graph.add_node("order_query", _node_order_query)
        graph.add_node("translation", _node_translation)
        graph.add_node("human_handoff", _node_human_handoff)

        graph.set_entry_point("classify")
        graph.add_conditional_edges("classify", _route, {
            "rag_answer": "rag_answer",
            "order_query": "order_query",
            "translation": "translation",
            "human_handoff": "human_handoff",
        })
        for node in ("rag_answer", "order_query", "translation", "human_handoff"):
            graph.add_edge(node, END)

        return graph.compile()
    except ImportError as e:  # noqa: BLE001
        logger.info("langgraph 未安装：%s", e)
        return None
