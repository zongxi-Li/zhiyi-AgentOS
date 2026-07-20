# 领域模型实施计划

> **针对智能体工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实施本计划。步骤使用复选框（`- [ ]`）语法进行跟踪。

**目标：** 实现 `agentos.domain` 模块作为规范的领域模型核心层。

**架构：** 保持 `agentos.domain` 仅关注纯领域对象和不变量。`agentos.core.models.types` 继续为当前运行时提供服务，但领域测试将锁定新层的行为，使其日后能够在不改变系统其他部分的情况下成为 truth 来源。

**技术栈：** Python、pytest、现有的 AgentOS Pydantic 模型或轻量级数据类。

---

### 任务 1：领域 Agent 模型

**文件：**
- 创建：`agentOS/src/agentos/domain/agent.py`
- 创建：`agentOS/tests/test_domain_models.py`

- [ ] **步骤 1：编写会失败的测试**

```python
from agentos.domain.agent import AgentProfile


def test_agent_profile_normalizes_name_and_supports_capabilities():
    profile = AgentProfile(agent_name="risk", domain="legal", capabilities=["risk", "review"])
    assert profile.supports("risk") is True
    assert profile.supports("draft") is False
```

- [ ] **步骤 2：运行测试确认其失败**

运行：`pytest agentOS/tests/test_domain_models.py::test_agent_profile_normalizes_name_and_supports_capabilities -q`
预期：失败，出现 `ModuleNotFoundError` 或缺失属性。

- [ ] **步骤 3：编写最小实现**

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

- [ ] **步骤 4：运行测试确认其通过**

运行：`pytest agentOS/tests/test_domain_models.py::test_agent_profile_normalizes_name_and_supports_capabilities -q`
预期：通过

- [ ] **步骤 5：提交**

```bash
git add agentOS/src/agentos/domain/agent.py agentOS/tests/test_domain_models.py
git commit -m "feat: add domain agent model"
```

### 任务 2：步骤和工作流模型

**文件：**
- 创建：`agentOS/src/agentos/domain/step.py`
- 创建：`agentOS/src/agentos/domain/workflow.py`
- 修改：`agentOS/tests/test_domain_models.py`

- [ ] **步骤 1：编写会失败的测试**

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

- [ ] **步骤 2：运行测试确认其失败**

运行：`pytest agentOS/tests/test_domain_models.py::test_workflow_definition_exposes_first_and_next_step_ids -q`
预期：失败，缺少模块/类。

- [ ] **步骤 3：编写最小实现**

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

- [ ] **步骤 4：运行测试确认其通过**

运行：`pytest agentOS/tests/test_domain_models.py::test_workflow_definition_exposes_first_and_next_step_ids -q`
预期：通过

- [ ] **步骤 5：提交**

```bash
git add agentOS/src/agentos/domain/step.py agentOS/src/agentos/domain/workflow.py agentOS/tests/test_domain_models.py
git commit -m "feat: add domain workflow and step models"
```

### 任务 3：任务模型和导出

**文件：**
- 创建：`agentOS/src/agentos/domain/task.py`
- 更新：`agentOS/src/agentos/domain/__init__.py`
- 更新：`agentOS/tests/test_domain_models.py`

- [ ] **步骤 1：编写会失败的测试**

```python
from agentos.domain.task import Task


def test_task_uses_role_and_task_aliases_without_blank_override():
    task = Task(title="合同审查", domain="legal", intent="contract_review", role_type=" ", task_type="")
    assert task.domain == "legal"
    assert task.intent == "contract_review"
```

- [ ] **步骤 2：运行测试确认其失败**

运行：`pytest agentOS/tests/test_domain_models.py::test_task_uses_role_and_task_aliases_without_blank_override -q`
预期：失败，缺少模块/类。

- [ ] **步骤 3：编写最小实现**

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

- [ ] **步骤 4：运行测试确认其通过**

运行：`pytest agentOS/tests/test_domain_models.py -q`
预期：通过

- [ ] **步骤 5：提交**

```bash
git add agentOS/src/agentos/domain/task.py agentOS/src/agentos/domain/__init__.py agentOS/tests/test_domain_models.py
git commit -m "feat: add domain task model"
```
