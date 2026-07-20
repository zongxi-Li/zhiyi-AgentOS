"""AgentOS Core 的 orchestrator 模块，提供运行时控制、状态、Trace、审核或治理能力。"""


from time import perf_counter
from typing import Tuple

from agentos.agents.base import AgentOutput, AgentRunContext
from agentos.agents import AgentRegistry
from agentos.memory.workflow_memory import WorkflowMemory
from agentos.core.models.types import (
    AgentTask,
    StepStatus,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStep,
)


class Orchestrator:
    """只理解工作流结构、不绑定行业细节的核心调度器。"""

    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry

    async def dispatch_agent(
        self,
        task: AgentTask,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
        step: WorkflowStep,
        memory: WorkflowMemory,
        context_pack=None,
    ) -> Tuple[AgentOutput, int]:
        agent = self.agent_registry.resolve(
            domain=run.domain,
            agent_name=step.agent_name,
            capability=step.capability,
        )
        context = AgentRunContext(
            task=task,
            run=run,
            workflow=workflow,
            step=step,
            memory=memory,
            contextPack=context_pack,
        )
        started = perf_counter()
        result = await agent.run(context)
        duration_ms = int((perf_counter() - started) * 1000)
        return result, duration_ms

    def compose_final_output(self, run: WorkflowRun) -> dict:
        artifacts = {step.step_id: step.output for step in run.steps if step.output}
        final_answer = ""
        for step in reversed(run.steps):
            if step.output.get("final_answer"):
                final_answer = str(step.output["final_answer"])
                break
            if step.output.get("draft"):
                final_answer = str(step.output["draft"])
                break

        if not final_answer:
            completed = [step.name for step in run.steps if step.status == StepStatus.COMPLETED]
            final_answer = f"Workflow completed: {', '.join(completed)}" if completed else "Workflow completed."

        return {
            "final_answer": final_answer,
            "artifacts": artifacts,
        }
