# Domain Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `agentos.domain` modules as the canonical core domain model layer.

**Architecture:** Keep `agentos.domain` focused on pure domain objects and invariants only. `agentos.core.models.types` continues to serve the runtime today, but domain tests will lock the new layer's behavior so it can become the source of truth later without changing the rest of the system.

**Tech Stack:** Python, pytest, existing AgentOS pydantic models or lightweight dataclasses.

---

### Task 1: Domain Agent Model

**Files:**
- Create: `agentOS/src/agentos/domain/agent.py`
- Create: `agentOS/tests/test_domain_models.py`

- [ ] **Step 1: Write the failing test**

```python
from agentos.domain.agent import AgentProfile


def test_agent_profile_normalizes_name_and_supports_capabilities():
    profile = AgentProfile(agent_name="risk", domain="legal", capabilities=["risk", "review"])
    assert profile.supports("risk") is True
    assert profile.supports("draft") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agentOS/tests/test_domain_models.py::test_agent_profile_normalizes_name_and_supports_capabilities -q`
Expected: FAIL with `ModuleNotFoundError` or missing attribute.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentProfile:
    agent_name: str
    domain: str
    capabilities: list[str] = field(default_factory=list)

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agentOS/tests/test_domain_models.py::test_agent_profile_normalizes_name_and_supports_capabilities -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agentOS/src/agentos/domain/agent.py agentOS/tests/test_domain_models.py
git commit -m "feat: add domain agent model"
```

### Task 2: Step and Workflow Models

**Files:**
- Create: `agentOS/src/agentos/domain/step.py`
- Create: `agentOS/src/agentos/domain/workflow.py`
- Modify: `agentOS/tests/test_domain_models.py`

- [ ] **Step 1: Write the failing test**

```python
from agentos.domain.step import StepDefinition
from agentos.domain.workflow import WorkflowDefinition


def test_workflow_definition_exposes_first_and_next_step_ids():
    workflow = WorkflowDefinition(
        workflow_id="legal_contract_review_v1",
        name="Legal Contract Review",
        domain="legal",
        intent="contract_review",
        steps=[
            StepDefinition(step_id="risk", name="Risk", agent_name="risk"),
            StepDefinition(step_id="draft", name="Draft", agent_name="draft"),
        ],
    )
    assert workflow.first_step_id() == "risk"
    assert workflow.next_step_id("risk") == "draft"
    assert workflow.next_step_id("draft") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agentOS/tests/test_domain_models.py::test_workflow_definition_exposes_first_and_next_step_ids -q`
Expected: FAIL with missing module/class.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StepDefinition:
    step_id: str
    name: str
    agent_name: str
    capability: str | None = None
    input: dict = field(default_factory=dict)
    review_required: bool = False
    next_step_id: str | None = None
    max_retries: int = 0
```

```python
@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    domain: str
    intent: str = "general"
    version: str = "1.0.0"
    description: str = ""
    steps: list[StepDefinition] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agentOS/tests/test_domain_models.py::test_workflow_definition_exposes_first_and_next_step_ids -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agentOS/src/agentos/domain/step.py agentOS/src/agentos/domain/workflow.py agentOS/tests/test_domain_models.py
git commit -m "feat: add domain workflow and step models"
```

### Task 3: Task Model and Exports

**Files:**
- Create: `agentOS/src/agentos/domain/task.py`
- Update: `agentOS/src/agentos/domain/__init__.py`
- Update: `agentOS/tests/test_domain_models.py`

- [ ] **Step 1: Write the failing test**

```python
from agentos.domain.task import Task


def test_task_uses_role_and_task_aliases_without_blank_override():
    task = Task(title="合同审查", domain="legal", intent="contract_review", role_type=" ", task_type="")
    assert task.domain == "legal"
    assert task.intent == "contract_review"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest agentOS/tests/test_domain_models.py::test_task_uses_role_and_task_aliases_without_blank_override -q`
Expected: FAIL with missing module/class.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    domain: str = "general"
    intent: str = "general"
    input: dict = field(default_factory=dict)
    role_type: str | None = None
    task_type: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest agentOS/tests/test_domain_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agentOS/src/agentos/domain/task.py agentOS/src/agentos/domain/__init__.py agentOS/tests/test_domain_models.py
git commit -m "feat: add domain task model"
```
