# AgentOS Console and Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a usable AgentOS console that can inspect WorkflowRun details, review records, checkpoints, traces, and workflow metrics.

**Architecture:** Keep Python as the source of truth for WorkflowRun lifecycle, review records, checkpoints, and metrics. Expose those through `/ai/core/*`, then let the Java gateway and Vue console consume the same shapes. The frontend should render one working console first, then grow specialized panels on top of the same API layer.

**Tech Stack:** FastAPI, Pydantic, Python runtime/store classes, Spring Boot WebClient gateway, Vue 3, TypeScript, Pinia-compatible service layer, existing app router/component patterns.

---

### Task 1: Extend the Python governance model

**Files:**
- Modify: `agentOS/src/agentos/core/types.py`
- Modify: `agentOS/src/agentos/core/checkpoint.py`
- Modify: `agentOS/src/agentos/core/evaluation.py`
- Modify: `agent/app/api/agentos_core.py`
- Test: `agent/tests/test_agentos_core.py`
- Test: `agent/tests/test_sqlite_workflow_store.py`

- [ ] **Step 1: Write the failing test**

```python
def test_workflow_api_exports_checkpoints_reviews_and_metrics(client):
    checkpoints = client.get("/ai/core/workflows/runs/run_001/checkpoints")
    reviews = client.get("/ai/core/workflows/runs/run_001/reviews")
    metrics = client.get("/ai/core/workflows/metrics")
    assert checkpoints.status_code == 200
    assert reviews.status_code == 200
    assert metrics.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agentos_core.py -q`
Expected: fail because the new endpoints and response models do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class ReviewRequest(BaseModel):
    step_id: str
    decision: ReviewDecisionType
    reviewer: str = "system"
    comment: str = ""

class ReviewLog(CoreModel):
    run_id: str = Field(alias="runId")
    step_id: str = Field(alias="stepId")
    decision: ReviewDecisionType
    reviewer: str
    comment: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agentos_core.py tests/test_sqlite_workflow_store.py -q`
Expected: pass with checkpoint/review/metrics payloads returning JSON.

- [ ] **Step 5: Commit**

```bash
git add agentOS/src/agentos/core/types.py agentOS/src/agentos/core/checkpoint.py agentOS/src/agentos/core/evaluation.py agent/app/api/agentos_core.py agent/tests/test_agentos_core.py agent/tests/test_sqlite_workflow_store.py
git commit -m "feat: add AgentOS governance APIs"
```

### Task 2: Expand the Python API surface for console consumption

**Files:**
- Modify: `agent/app/api/agentos_core.py`
- Modify: `agentOS/src/agentos/core/workflow_runtime.py`
- Modify: `agentOS/src/agentos/core/trace.py`
- Test: `agent/tests/test_agentos_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_workflow_run_detail_includes_checkpoints_and_trace_export(client):
    detail = client.get("/ai/core/workflows/runs/run_001")
    trace = client.get("/ai/core/workflows/runs/run_001/trace")
    checkpoints = client.get("/ai/core/workflows/runs/run_001/checkpoints")
    assert "trace" in detail.json()
    assert trace.json()["eventCount"] >= 1
    assert checkpoints.json()["items"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agentos_core.py -q`
Expected: fail until the console payloads are added.

- [ ] **Step 3: Write minimal implementation**

```python
@router.get("/core/workflows/runs/{run_id}/checkpoints")
async def list_checkpoints(run_id: str):
    run = runtime.get_status(run_id)
    return {
        "items": [checkpoint.model_dump(by_alias=True, mode="json") for checkpoint in run.checkpoints],
        "total": len(run.checkpoints),
        "runId": run_id,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agentos_core.py -q`
Expected: pass with the detail, trace, and checkpoints endpoints aligned.

- [ ] **Step 5: Commit**

```bash
git add agent/app/api/agentos_core.py agentOS/src/agentos/core/workflow_runtime.py agentOS/src/agentos/core/trace.py agent/tests/test_agentos_core.py
git commit -m "feat: extend AgentOS console payloads"
```

### Task 3: Build the Vue AgentOS console shell

**Files:**
- Create: `frontend/src/views/AgentOsConsoleView.vue`
- Create: `frontend/src/components/agentos/WorkflowRunPanel.vue`
- Create: `frontend/src/components/agentos/WorkflowStepList.vue`
- Create: `frontend/src/components/agentos/CheckpointPanel.vue`
- Create: `frontend/src/components/agentos/TraceEventTimeline.vue`
- Create: `frontend/src/components/agentos/HumanReviewPanel.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/services/api/agentos.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from '@vue/test-utils'
import AgentOsConsoleView from '@/views/AgentOsConsoleView.vue'

test('renders the AgentOS console shell', () => {
  const wrapper = mount(AgentOsConsoleView)
  expect(wrapper.text()).toContain('AgentOS')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- AgentOsConsoleView`
Expected: fail because the view and components do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```vue
<template>
  <div class="agentos-console">
    <WorkflowRunPanel />
    <WorkflowStepList />
    <CheckpointPanel />
    <TraceEventTimeline />
    <HumanReviewPanel />
  </div>
</template>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run build`
Expected: build succeeds and the console route resolves.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/AgentOsConsoleView.vue frontend/src/components/agentos frontend/src/router/index.ts frontend/src/services/api/agentos.ts
git commit -m "feat: add AgentOS console shell"
```

### Task 4: Add checkpoint and review interaction wiring

**Files:**
- Modify: `frontend/src/components/agentos/HumanReviewPanel.vue`
- Modify: `frontend/src/components/agentos/CheckpointPanel.vue`
- Modify: `frontend/src/components/agentos/WorkflowRunPanel.vue`
- Modify: `frontend/src/services/api/agentos.ts`

- [ ] **Step 1: Write the failing test**

```ts
test('review panel submits a decision and refreshes the run', async () => {
  // mount panel, stub review API, assert submit handler calls refresh
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test`
Expected: fail until the panel and refresh contract are implemented.

- [ ] **Step 3: Write minimal implementation**

```ts
await agentosApi.applyWorkflowReview(runId, {
  stepId,
  decision,
  reviewer,
  comment
})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run build`
Expected: compile passes and the review action is wired.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/agentos/HumanReviewPanel.vue frontend/src/components/agentos/CheckpointPanel.vue frontend/src/components/agentos/WorkflowRunPanel.vue frontend/src/services/api/agentos.ts
git commit -m "feat: wire AgentOS review and checkpoint actions"
```

### Task 5: Turn evaluation into a first-class console metric

**Files:**
- Modify: `agentOS/src/agentos/core/evaluation.py`
- Modify: `agent/app/api/agentos_core.py`
- Modify: `frontend/src/services/api/agentos.ts`
- Modify: `frontend/src/views/AgentOsConsoleView.vue`

- [ ] **Step 1: Write the failing test**

```python
def test_workflow_metrics_include_failure_and_recovery_rates(client):
    metrics = client.get("/ai/core/workflows/metrics")
    payload = metrics.json()
    assert "failureRate" in payload
    assert "recoverySuccessRate" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agentos_core.py -q`
Expected: fail until the metrics endpoint and payload are implemented.

- [ ] **Step 3: Write minimal implementation**

```python
class WorkflowMetric(BaseModel):
    total_runs: int = Field(alias="totalRuns")
    completion_rate: float = Field(alias="completionRate")
    failure_rate: float = Field(alias="failureRate")
    recovery_success_rate: float = Field(alias="recoverySuccessRate")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_agentos_core.py -q`
Expected: pass and return the metric summary from workflow runs.

- [ ] **Step 5: Commit**

```bash
git add agentOS/src/agentos/core/evaluation.py agent/app/api/agentos_core.py frontend/src/services/api/agentos.ts frontend/src/views/AgentOsConsoleView.vue
git commit -m "feat: add AgentOS governance metrics"
```

### Task 6: Sync docs and validate the full stack

**Files:**
- Modify: `docs/design/core-todo.md`
- Modify: `README.md`
- Modify: `agent/README.md`
- Modify: `docs/design/agent-architecture-reorganization.md`

- [ ] **Step 1: Write the failing check**

```bash
rg -n "checkpoints|reviews|metrics|AgentOsConsoleView" docs/design README.md agent/README.md
```

- [ ] **Step 2: Run the check**

Run: `rg -n "checkpoints|reviews|metrics|AgentOsConsoleView" docs/design README.md agent/README.md`
Expected: every public API and console surface appears in the docs.

- [ ] **Step 3: Write minimal documentation updates**

```md
- `GET /ai/core/workflows/runs/{runId}/checkpoints`：查询恢复点列表。
- `GET /ai/core/workflows/metrics`：查询工作流治理指标。
- `POST /ai/core/workflows/runs/{runId}/reviews`：提交人工审核结果。
```

- [ ] **Step 4: Run the full verification**

Run: `python -m pytest tests/test_agentos_core.py tests/test_sqlite_workflow_store.py -q`
Run: `mvn clean compile`
Run: `git diff --check`

- [ ] **Step 5: Commit**

```bash
git add docs/design/core-todo.md README.md agent/README.md docs/design/agent-architecture-reorganization.md
git commit -m "docs: sync AgentOS console and governance work"
```

