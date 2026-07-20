"""ACG 构建器（设计书 §2.1「ACG构建器」）。

把意图画像 + 认知路由的协作网络物化为可执行的 ACGBlueprint：
1. 任务目标分解 → 步骤序列（按能力顺序，复杂度控制粒度）
2. 实例化 StepNode，绑定 assigned_agent
3. 赋能节点注入：阶段性结论后注入 Memory 节点；需外部依据的步骤注入
   Evidence 节点
4. 建立依赖主干 + write/read/support 边
5. 图级验证：环检测 + 悬空依赖检查

这是“动态补位”一侧：无模板命中时由本构建器动态生成 ACG。
"""

from __future__ import annotations

from typing import List

from agentos.core.acg import (
    ACGBlueprint,
    ACGEdge,
    AgentNode,
    ControlNode,
    ControlType,
    EdgeType,
    EvidenceNode,
    MemoryNode,
    StepNode,
    validate_blueprint,
)
from agentos.core.acg.nodes import _node_id
from agentos.core.planning.cognitive_router import CollaborationNetwork
from agentos.core.planning.profile import TaskSemanticProfile

# 需要证据支撑的能力（产出结论性内容，须可审计）
_EVIDENCE_CAPABILITIES = {"风险识别", "证据检索", "报告生成", "需求分析"}
# 产生阶段性结论、值得写入记忆的能力
_MEMORY_CAPABILITIES = {"风险识别", "需求分析", "报告生成"}

_ROLE_ALIASES = {
    "parse": {"文本解析", "合同解析", "contract_parse", "parse_contract", "case_intake", "需求分析"},
    "classify": {"条款分类", "clause_classify", "clause_classifier"},
    "risk": {"风险识别", "风险评估", "risk_detect", "risk_detection", "risk_assessment"},
    "evidence": {"证据检索", "依据匹配", "legal_evidence_match", "legal_evidence_search", "evidence_analysis"},
    "suggest": {"修改建议", "修订建议", "revision_suggest", "revision_suggestion", "suggestion_generate"},
    "review": {"人工审核", "复核", "human_review", "human_review_gate", "review"},
    "report": {"报告生成", "文书生成", "report_generate", "report_generation", "draft"},
}

_ROLE_ORDER = {
    "parse": 10,
    "classify": 20,
    "risk": 30,
    "evidence": 31,
    "suggest": 40,
    "review": 50,
    "report": 60,
}

_ROLE_SOURCE_FIELDS = {
    "classify": {"parse": ["contract_type", "scope", "payment_terms", "acceptance_terms", "ip_terms", "dispute_resolution"]},
    "risk": {"parse": ["contract_summary", "payment_terms", "acceptance_terms", "ip_terms"], "classify": ["clauses"]},
    "evidence": {"parse": ["contract_type"], "risk": ["risks", "risk_level", "risk_score"]},
    "suggest": {"risk": ["risks", "risk_summary"], "evidence": ["evidences", "citations"]},
    "review": {"risk": ["risks", "risk_summary"], "suggest": ["revision_suggestions", "manual_review_focus"]},
    "report": {
        "parse": ["contract_type", "parties", "scope"],
        "risk": ["risks", "risk_summary"],
        "evidence": ["evidences"],
        "suggest": ["revision_suggestions", "manual_review_focus"],
        "review": ["review_status", "review_focus"],
    },
}

_ROLE_REQUIRED_FIELDS = {
    "classify": ["contract_type"],
    "risk": ["clauses"],
    "evidence": ["risks"],
    "suggest": ["risks", "evidences"],
    "review": ["risks", "manual_review_focus"],
    "report": ["contract_type", "risks", "evidences", "revision_suggestions"],
}

_ROLE_OUTPUT_REQUIRED = {
    "parse": ["contract_summary", "contract_type", "parties"],
    "classify": ["clauses"],
    "risk": ["risks", "risk_level", "risk_score"],
    "evidence": ["evidences", "citations"],
    "suggest": ["revision_suggestions", "manual_review_focus"],
    "review": ["review_status", "review_focus"],
    "report": ["report_markdown"],
}


def _object_schema(required: List[str]) -> dict:
    return {"type": "object", "required": list(required)}


class ACGBuilder:
    """动态 ACG 蓝图构建器。"""

    def build(
        self,
        *,
        task_id: str,
        profile: TaskSemanticProfile,
        network: CollaborationNetwork,
    ) -> ACGBlueprint:
        blueprint = ACGBlueprint(
            taskId=task_id,
            objective=profile.primary_goal,
            complexityLevel=profile.estimated_complexity,
            metadata={
                "generatedBy": "acg_builder",
                "domainHint": profile.domain_hint,
                "entropyBudget": profile.entropy_budget,
                "estimatedEntropy": network.estimated_entropy,
            },
        )

        # 1) 按能力语义归类并实例化 StepNode。节点 id 优先复用真实 agentName，
        #    让动态图可以被现有 Pack Agent 直接执行。
        step_nodes = self._build_step_nodes(blueprint, network)

        # 把抽象角色依赖解析成实际 Step id，形成可执行的字段级通信契约。
        self._configure_step_contracts(step_nodes)

        # 2) 依赖图生成：解析 → 并行分析 → 汇聚 → 建议/审核/报告。
        self._wire_task_graph(blueprint, step_nodes)

        # 3) 赋能节点注入
        for step in step_nodes:
            cap = step.capability or ""
            role = str(step.metadata.get("role") or "")
            if role == "evidence" or cap == "证据检索":
                ev = EvidenceNode(
                    nodeId=_node_id("ev"),
                    name=f"证据:{cap}",
                    evidenceType="retrieved",
                    metadata={"producerStepId": step.node_id},
                )
                blueprint.nodes.append(ev)
                step.evidence_ids.append(ev.node_id)
            if cap in _MEMORY_CAPABILITIES or role in {"risk", "suggest", "report"}:
                mem = MemoryNode(nodeId=_node_id("mem"), name=f"记忆:{cap}", memoryType="episodic")
                blueprint.nodes.append(mem)
                blueprint.edges.append(
                    ACGEdge(sourceId=step.node_id, targetId=mem.node_id, edgeType=EdgeType.WRITE)
                )
                step.memory_ids.append(mem.node_id)

        memory_by_source = {
            edge.source_id: edge.target_id
            for edge in blueprint.edges_of_type(EdgeType.WRITE)
        }
        evidence_by_source = {
            str(node.metadata.get("producerStepId")): node.node_id
            for node in blueprint.nodes
            if isinstance(node, EvidenceNode) and node.metadata.get("producerStepId")
        }
        for target in step_nodes:
            from_map = target.input_spec.get("from") if isinstance(target.input_spec, dict) else None
            if not isinstance(from_map, dict):
                continue
            for source_id in from_map:
                if source_id in memory_by_source:
                    blueprint.edges.append(
                        ACGEdge(
                            sourceId=memory_by_source[source_id],
                            targetId=target.node_id,
                            edgeType=EdgeType.READ,
                        )
                    )
                if source_id in evidence_by_source:
                    blueprint.edges.append(
                        ACGEdge(
                            sourceId=evidence_by_source[source_id],
                            targetId=target.node_id,
                            edgeType=EdgeType.SUPPORT,
                        )
                    )

        blueprint.touch()
        # 5) 图级验证（环检测 + 悬空依赖）
        validate_blueprint(blueprint)
        return blueprint

    def _build_step_nodes(self, blueprint: ACGBlueprint, network: CollaborationNetwork) -> List[StepNode]:
        used_ids: set[str] = set()
        agent_nodes: dict[str, str] = {}
        step_nodes: List[StepNode] = []
        sorted_bindings = sorted(
            enumerate(network.bindings),
            key=lambda item: (_ROLE_ORDER.get(_role_for(item[1].capability, item[1].agent_name), 90), item[0]),
        )

        for original_index, binding in sorted_bindings:
            role = _role_for(binding.capability, binding.agent_name)
            node_id = _step_id(binding, role, original_index, used_ids)
            used_ids.add(node_id)
            display = _display_name(binding.capability, role)
            step = StepNode(
                nodeId=node_id,
                name=display,
                goal=f"完成能力：{display}",
                agentName=binding.agent_name,
                capability=binding.capability,
                inputSpec={},
                outputSpec=_object_schema(_ROLE_OUTPUT_REQUIRED.get(role, [])) if role in _ROLE_OUTPUT_REQUIRED else {},
                reviewRequired=False,
                metadata={
                    "ephemeralAgent": binding.ephemeral,
                    "role": role,
                    "routerScore": binding.score,
                    "dynamicOrder": original_index,
                },
            )
            blueprint.nodes.append(step)
            step_nodes.append(step)

            if binding.agent_name not in agent_nodes:
                agent_node_id = f"agent::{binding.agent_name}"
                agent_nodes[binding.agent_name] = agent_node_id
                blueprint.nodes.append(
                    AgentNode(
                        nodeId=agent_node_id,
                        name=binding.agent_name,
                        role=display,
                        capabilityTags=[binding.capability],
                        ephemeral=binding.ephemeral,
                    )
                )
            blueprint.edges.append(
                ACGEdge(sourceId=agent_nodes[binding.agent_name], targetId=step.node_id, edgeType=EdgeType.EXECUTION)
            )

        return step_nodes

    def _configure_step_contracts(self, step_nodes: List[StepNode]) -> None:
        by_role: dict[str, List[StepNode]] = {}
        for step in step_nodes:
            by_role.setdefault(str(step.metadata.get("role") or "other"), []).append(step)

        for target_role, source_roles in _ROLE_SOURCE_FIELDS.items():
            for target in by_role.get(target_role, []):
                from_map: dict[str, List[str]] = {}
                for source_role, fields in source_roles.items():
                    for source in by_role.get(source_role, []):
                        from_map[source.node_id] = list(fields)
                if not from_map:
                    continue
                required = _ROLE_REQUIRED_FIELDS.get(target_role, [])
                target.input_spec = {
                    "from": from_map,
                    "schema": _object_schema(required),
                }

    def _wire_task_graph(self, blueprint: ACGBlueprint, step_nodes: List[StepNode]) -> None:
        if not step_nodes:
            return

        by_role: dict[str, List[StepNode]] = {}
        for step in step_nodes:
            by_role.setdefault(str(step.metadata.get("role") or "other"), []).append(step)

        start = ControlNode(nodeId="ctrl_start", name="START", controlType=ControlType.START)
        end = ControlNode(nodeId="ctrl_end", name="END", controlType=ControlType.END)
        blueprint.nodes.extend([start, end])

        parse_nodes = by_role.get("parse") or [step_nodes[0]]
        first = parse_nodes[0]
        _add_dep(blueprint, start.node_id, first.node_id)

        analysis_nodes = _unique_steps(
            by_role.get("classify", [])
            + by_role.get("risk", [])
            + [
                s
                for s in step_nodes
                if str(s.metadata.get("role"))
                not in {"parse", "classify", "risk", "evidence", "suggest", "review", "report"}
            ]
        )
        evidence_nodes = _unique_steps(by_role.get("evidence", []))
        post_analysis = _unique_steps(by_role.get("suggest", []) + by_role.get("review", []) + by_role.get("report", []))

        if len(analysis_nodes) >= 2:
            parallel = ControlNode(nodeId="ctrl_parallel_analysis", name="PARALLEL_ANALYSIS", controlType=ControlType.PARALLEL)
            consensus = ControlNode(nodeId="ctrl_consensus_analysis", name="CONSENSUS_ANALYSIS", controlType=ControlType.CONSENSUS)
            blueprint.nodes.extend([parallel, consensus])
            _add_dep(blueprint, first.node_id, parallel.node_id)
            for node in analysis_nodes:
                _add_dep(blueprint, parallel.node_id, node.node_id)
                _add_dep(blueprint, node.node_id, consensus.node_id)
            tail_source = consensus.node_id
        elif analysis_nodes:
            _add_dep(blueprint, first.node_id, analysis_nodes[0].node_id)
            tail_source = analysis_nodes[0].node_id
        else:
            tail_source = first.node_id

        previous = tail_source
        for node in evidence_nodes:
            _add_dep(blueprint, previous, node.node_id)
            previous = node.node_id

        for node in post_analysis:
            _add_dep(blueprint, previous, node.node_id)
            previous = node.node_id
        _add_dep(blueprint, previous, end.node_id)

        self._wire_low_entropy_channels(blueprint, by_role, step_nodes)

    def _wire_low_entropy_channels(
        self,
        blueprint: ACGBlueprint,
        by_role: dict[str, List[StepNode]],
        step_nodes: List[StepNode],
    ) -> None:
        del by_role  # contracts already contain concrete source Step ids
        by_id = {step.node_id: step for step in step_nodes}
        for target in step_nodes:
            from_map = target.input_spec.get("from") if isinstance(target.input_spec, dict) else None
            if not isinstance(from_map, dict):
                continue
            for source_id, fields in from_map.items():
                source = by_id.get(str(source_id))
                if source is not None:
                    _add_comm(
                        blueprint,
                        source,
                        target,
                        fields=[str(field) for field in fields] if isinstance(fields, list) else [],
                    )


def _slug(text: str) -> str:
    return "".join(c for c in (text or "") if c.isalnum())[:12] or "cap"


def _role_for(capability: str, agent_name: str = "") -> str:
    terms = {capability, agent_name}
    lowered = {t.strip().lower() for t in terms if t}
    for role, aliases in _ROLE_ALIASES.items():
        alias_lower = {a.lower() for a in aliases}
        if lowered & alias_lower:
            return role
    for role, aliases in _ROLE_ALIASES.items():
        alias_lower = {a.lower() for a in aliases}
        if any(term and any(term in alias or alias in term for alias in alias_lower) for term in lowered):
            return role
    return "other"


def _step_id(binding, role: str, index: int, used_ids: set[str]) -> str:
    base = binding.agent_name if binding.agent_name and not binding.agent_name.startswith("ephemeral::") else ""
    if not base:
        base = f"{role}_{_slug(binding.capability)}"
    node_id = base
    suffix = 2
    while node_id in used_ids:
        node_id = f"{base}_{suffix}"
        suffix += 1
    return node_id or f"step_{index}_{_slug(binding.capability)}"


def _display_name(capability: str, role: str) -> str:
    defaults = {
        "parse": "合同文本解析",
        "classify": "条款分类",
        "risk": "风险识别",
        "evidence": "Evidence 依据匹配",
        "suggest": "修改建议生成",
        "review": "人工审核门",
        "report": "审查报告生成",
    }
    return defaults.get(role, capability or "动态任务步骤")


def _unique_steps(steps: List[StepNode]) -> List[StepNode]:
    seen: set[str] = set()
    unique: List[StepNode] = []
    for step in steps:
        if step.node_id in seen:
            continue
        seen.add(step.node_id)
        unique.append(step)
    return unique


def _add_dep(blueprint: ACGBlueprint, source_id: str, target_id: str) -> None:
    if source_id == target_id:
        return
    for edge in blueprint.edges_of_type(EdgeType.DEPENDENCY):
        if edge.source_id == source_id and edge.target_id == target_id:
            return
    blueprint.edges.append(ACGEdge(sourceId=source_id, targetId=target_id, edgeType=EdgeType.DEPENDENCY))


def _add_comm(
    blueprint: ACGBlueprint,
    source: StepNode,
    target: StepNode,
    *,
    fields: List[str] | None = None,
) -> None:
    if source.node_id == target.node_id:
        return
    for edge in blueprint.edges_of_type(EdgeType.COMMUNICATION):
        if edge.source_id == source.node_id and edge.target_id == target.node_id:
            return
    if fields is None:
        raw_fields = target.input_spec.get("fields")
        fields = list(raw_fields) if isinstance(raw_fields, list) else []
    blueprint.edges.append(
        ACGEdge(
            sourceId=source.node_id,
            targetId=target.node_id,
            edgeType=EdgeType.COMMUNICATION,
            dataFields=list(fields),
            metadata={"mode": "low_entropy", "contract": "input.fields"},
        )
    )
    _add_dep(blueprint, source.node_id, target.node_id)


__all__ = ["ACGBuilder"]
