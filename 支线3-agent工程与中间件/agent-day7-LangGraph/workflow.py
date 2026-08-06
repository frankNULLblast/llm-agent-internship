# 教材 Day 7 的 workflow.py（需合并进工程）。
#
# ⚠️ 可运行代码位置说明：
#   当天真实跑通的代码在培训 VM 的 patent-agent-service（Day 3 提交 e13000b 之上的演进）。
#   本仓库仅保留教材对应的设计与配置，未含 VM 实跑代码与输出。

from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from fee_calc import calculate
from patent_bill import build_result


Extractor = Callable[[str], tuple[dict, dict]]


class AgentState(TypedDict, total=False):
    ocr_text: str
    fee_records: list[dict]
    request_id: str
    bill_record: dict
    model_usage: dict
    review_result: dict
    fee_summary: dict
    human_review: dict
    final_result: dict


def build_graph(extractor: Extractor, checkpointer):
    def extract_bill(state: AgentState) -> dict:
        record, usage = extractor(state["ocr_text"])
        return {"bill_record": record, "model_usage": usage}

    def review_bill(state: AgentState) -> dict:
        return {"review_result": build_result(state["bill_record"])}

    def summarize_fees(state: AgentState) -> dict:
        return {"fee_summary": calculate(state["fee_records"])}

    def await_human_review(state: AgentState) -> dict:
        review = interrupt(
            {
                "kind": "patent_bill_human_review",
                "bill_review": state["review_result"],
                "fee_summary": state["fee_summary"],
            }
        )
        if not isinstance(review, dict):
            raise ValueError("人工复核值必须是对象")
        decision = review.get("decision")
        comment = review.get("comment")
        if decision not in {"approve", "reject"}:
            raise ValueError("人工决定必须是 approve 或 reject")
        if not isinstance(comment, str) or len(comment) > 500:
            raise ValueError("人工备注必须是最多 500 字的字符串")
        return {
            "human_review": {
                "decision": decision,
                "comment": comment,
            }
        }

    def choose_final_node(state: AgentState) -> str:
        return state["human_review"]["decision"]

    def finalize_approved(state: AgentState) -> dict:
        return {
            "final_result": {
                "status": "succeeded",
                "decision": "approve",
                "comment": state["human_review"]["comment"],
                "bill_review": state["review_result"],
                "fee_summary": state["fee_summary"],
            }
        }

    def finalize_rejected(state: AgentState) -> dict:
        return {
            "final_result": {
                "status": "rejected",
                "decision": "reject",
                "comment": state["human_review"]["comment"],
                "bill_review": state["review_result"],
                "fee_summary": state["fee_summary"],
            }
        }

    builder = StateGraph(AgentState)
    builder.add_node("extract_bill", extract_bill)
    builder.add_node("review_bill", review_bill)
    builder.add_node("summarize_fees", summarize_fees)
    builder.add_node("await_human_review", await_human_review)
    builder.add_node("finalize_approved", finalize_approved)
    builder.add_node("finalize_rejected", finalize_rejected)

    builder.add_edge(START, "extract_bill")
    builder.add_edge("extract_bill", "review_bill")
    builder.add_edge("review_bill", "summarize_fees")
    builder.add_edge("summarize_fees", "await_human_review")
    builder.add_conditional_edges(
        "await_human_review",
        choose_final_node,
        {
            "approve": "finalize_approved",
            "reject": "finalize_rejected",
        },
    )
    builder.add_edge("finalize_approved", END)
    builder.add_edge("finalize_rejected", END)
    return builder.compile(checkpointer=checkpointer)
