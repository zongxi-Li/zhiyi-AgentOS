"""通信数据血缘审计。

对应设计书 §3.4《通信审计》：把每一次数据生产与消费事件原子化、关联化
记录，构建可双向追溯的数据血统图谱，使智能体协同的“黑箱”白盒化。

- DataProductionEvent：Step 输出被引擎持久化时生成（数据诞生 + checksum）。
- DataConsumptionEvent：引擎为下游装配输入时生成（谁消费了谁的哪些字段）。

前向追溯“这个结论从何而来”、后向影响分析“这个数据用在了何处”，
共同支撑根因分析、合规证明与低熵通信的可观测性。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from agentos.core.acg import ACGBlueprint, EdgeType


def _checksum(payload: Any) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        text = str(payload)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class DataProductionEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    event_id: str = Field(alias="eventId")
    producer_step_id: str = Field(alias="producerStepId")
    checksum: str = ""
    field_names: List[str] = Field(default_factory=list, alias="fieldNames")
    token_size: int = Field(default=0, alias="tokenSize")


class DataConsumptionEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    event_id: str = Field(alias="eventId")
    consumer_step_id: str = Field(alias="consumerStepId")
    producer_step_ids: List[str] = Field(default_factory=list, alias="producerStepIds")
    consumed_fields: List[str] = Field(default_factory=list, alias="consumedFields")


class ProvenanceLedger:
    """数据血缘账本：累积生产/消费事件，支持双向追溯。"""

    def __init__(self) -> None:
        self._seq = 0
        self.productions: Dict[str, DataProductionEvent] = {}
        self.consumptions: List[DataConsumptionEvent] = []

    def _next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}_{self._seq:06d}"

    def record_production(self, step_id: str, output: Dict[str, Any], token_size: int) -> DataProductionEvent:
        event = DataProductionEvent(
            eventId=self._next_id("prod"),
            producerStepId=step_id,
            checksum=_checksum(output),
            fieldNames=sorted(output.keys()) if isinstance(output, dict) else [],
            tokenSize=token_size,
        )
        self.productions[step_id] = event
        return event

    def record_consumption(
        self, step_id: str, producer_step_ids: List[str], consumed_fields: List[str]
    ) -> DataConsumptionEvent:
        event = DataConsumptionEvent(
            eventId=self._next_id("cons"),
            consumerStepId=step_id,
            producerStepIds=sorted(set(producer_step_ids)),
            consumedFields=sorted(set(consumed_fields)),
        )
        self.consumptions.append(event)
        return event

    # ---- 双向追溯 ----
    def trace_backward(self, step_id: str) -> List[str]:
        """前向追溯：返回该 Step 直接/间接消费过的上游 Step 集合。"""
        seen: set[str] = set()
        frontier = [step_id]
        while frontier:
            current = frontier.pop()
            for cons in self.consumptions:
                if cons.consumer_step_id == current:
                    for producer in cons.producer_step_ids:
                        if producer not in seen:
                            seen.add(producer)
                            frontier.append(producer)
        return sorted(seen)

    def trace_forward(self, step_id: str) -> List[str]:
        """后向影响分析：返回消费了该 Step 产物的所有下游 Step。"""
        impacted: set[str] = set()
        for cons in self.consumptions:
            if step_id in cons.producer_step_ids:
                impacted.add(cons.consumer_step_id)
        return sorted(impacted)

    def to_graph(self) -> Dict[str, Any]:
        """导出数据血统图（供前端血缘面板渲染）。"""
        return {
            "productions": [e.model_dump(by_alias=True) for e in self.productions.values()],
            "consumptions": [e.model_dump(by_alias=True) for e in self.consumptions],
        }


__all__ = [
    "DataProductionEvent",
    "DataConsumptionEvent",
    "ProvenanceLedger",
]
