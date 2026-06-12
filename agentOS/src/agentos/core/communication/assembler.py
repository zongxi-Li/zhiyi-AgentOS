"""上下文装配器：低熵通信的运行时核心。

对应设计书 §2.3「输入消息装配」与 §3.3「低熵实现」。引擎作为唯一通信中介，
为下游 Step 装配 ContextPack：

1. 按需索取的精准投递——按下游 input_spec 的字段清单，从上游输出中
   只提取所列字段，不把上游完整输出“全盘倾倒”给下游。
2. 证据链聚合——自动汇聚上游 evidence_refs，形成贯穿的证据链。
3. 低熵度量——量化“可获取 token 总量 vs 实际投递 token 量”的节省率。
4. 数据血缘——记录消费事件，回答“下游消费了上游哪些字段”。

input_spec 的约定（向下兼容）：
- 含 "fields": [..] 时，按字段名精准提取；
- 含 "from": {stepId: [field,..]} 时，按来源 Step 定向提取；
- 两者都没有时，回退为“全部上游输出”（等价旧行为），但仍记账。
"""

from __future__ import annotations

from typing import Any, Dict, List

from agentos.core.acg import ACGBlueprint, EdgeType, StepNode
from agentos.core.communication.audit import ProvenanceLedger
from agentos.core.communication.contract import ContextPack, estimate_tokens


class ContextAssembler:
    """按依赖边与 input_spec 装配下游执行上下文。"""

    def __init__(self, ledger: ProvenanceLedger | None = None):
        self.ledger = ledger or ProvenanceLedger()

    def assemble(
        self,
        *,
        run_id: str,
        blueprint: ACGBlueprint,
        step_node: StepNode,
        objective: str,
        upstream_outputs: Dict[str, Dict[str, Any]],
    ) -> ContextPack:
        """为 step_node 装配 ContextPack。

        upstream_outputs: {step_id -> 该上游 Step 的完整输出}，由执行器提供。
        """
        # 1) 确定数据来源：优先依赖边上游，回退到全部已知上游
        dep_sources = blueprint.dependency_sources(step_node.node_id)
        source_ids = [sid for sid in dep_sources if sid in upstream_outputs] or list(upstream_outputs.keys())

        # 可获取的 token 总量（若全盘倾倒）
        tokens_available = sum(estimate_tokens(upstream_outputs[sid]) for sid in source_ids)

        # 2) 按 input_spec 精准提取
        spec = step_node.input_spec or {}
        delivered: Dict[str, Any] = {}
        consumed_fields: List[str] = []

        from_map = spec.get("from") if isinstance(spec.get("from"), dict) else None
        field_list = spec.get("fields") if isinstance(spec.get("fields"), list) else None

        if from_map:
            for src_id, fields in from_map.items():
                src_out = upstream_outputs.get(src_id, {})
                for field in fields or []:
                    if field in src_out:
                        delivered[field] = src_out[field]
                        consumed_fields.append(field)
        elif field_list:
            for sid in source_ids:
                src_out = upstream_outputs.get(sid, {})
                for field in field_list:
                    if field in src_out and field not in delivered:
                        delivered[field] = src_out[field]
                        consumed_fields.append(field)
        else:
            # 回退：无清单则透传上游输出（兼容旧行为），仍记账
            for sid in source_ids:
                src_out = upstream_outputs.get(sid, {})
                for field, value in src_out.items():
                    if field not in delivered:
                        delivered[field] = value
                        consumed_fields.append(field)

        # 3) 聚合证据链
        evidence_refs = self._collect_evidence(source_ids, upstream_outputs)

        # 4) 低熵度量
        tokens_delivered = estimate_tokens(delivered)
        saving_ratio = 0.0
        if tokens_available > 0:
            saving_ratio = round(max(0.0, 1.0 - tokens_delivered / tokens_available), 4)

        # 5) 血缘记账
        self.ledger.record_consumption(
            step_id=step_node.node_id,
            producer_step_ids=source_ids,
            consumed_fields=consumed_fields,
        )

        return ContextPack(
            runId=run_id,
            stepId=step_node.node_id,
            objective=objective,
            stepGoal=step_node.goal or step_node.name,
            data=delivered,
            evidenceRefs=evidence_refs,
            tokensDelivered=tokens_delivered,
            tokensAvailable=tokens_available,
            savingRatio=saving_ratio,
            sourceStepIds=source_ids,
        )

    def record_production(self, step_id: str, output: Dict[str, Any]) -> None:
        """Step 完成后登记数据生产事件（供前向追溯与节省率统计）。"""
        self.ledger.record_production(step_id, output, estimate_tokens(output))

    @staticmethod
    def _collect_evidence(source_ids: List[str], upstream_outputs: Dict[str, Dict[str, Any]]) -> List[str]:
        refs: List[str] = []
        for sid in source_ids:
            out = upstream_outputs.get(sid, {})
            raw = out.get("evidence_refs") or out.get("evidenceRefs") or out.get("evidenceIds")
            if isinstance(raw, list):
                for item in raw:
                    ref = item if isinstance(item, str) else (item.get("id") if isinstance(item, dict) else None)
                    if ref and ref not in refs:
                        refs.append(ref)
        return refs


__all__ = ["ContextAssembler"]
