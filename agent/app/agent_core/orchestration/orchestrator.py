from time import perf_counter
from typing import Optional, Tuple

from app.agent_core.agents.base import AgentOutput, AgentRunContext
from app.agent_core.agents.registry import AgentRegistry
from app.agent_core.memory.workflow_memory import WorkflowMemory
from app.agent_core.orchestration.types import (
    AgentTask,
    StepStatus,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowStep,
)


class Orchestrator:
    """Core dispatcher that knows workflow structure, not industry details."""

    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry

    def select_next_step(self, run: WorkflowRun) -> Optional[WorkflowStep]:
        if run.current_step_id:
            step = run.get_step(run.current_step_id)
            if step.status in {StepStatus.PENDING, StepStatus.RETRYING}:
                return step

        for step in run.steps:
            if step.status in {StepStatus.PENDING, StepStatus.RETRYING}:
                return step
        return None

    async def dispatch_agent(
        self,
        task: AgentTask,
        run: WorkflowRun,
        workflow: WorkflowDefinition,
        step: WorkflowStep,
        memory: WorkflowMemory,
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
