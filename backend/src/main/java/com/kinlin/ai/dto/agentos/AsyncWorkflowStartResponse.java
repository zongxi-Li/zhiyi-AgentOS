package com.kinlin.ai.dto.agentos;

import java.util.Objects;

/** Typed response for an accepted asynchronous workflow run. */
public record AsyncWorkflowStartResponse(
        boolean accepted,
        Task task,
        Run run
) {
    public AsyncWorkflowStartResponse {
        Objects.requireNonNull(task, "task");
        Objects.requireNonNull(run, "run");
        if (run.runId() == null || run.runId().isBlank()) {
            throw new IllegalArgumentException("run.runId is required");
        }
    }

    public record Task(String taskId, String status) {
    }

    public record Run(
            String runId,
            String status,
            String lifecyclePhase,
            String lifecycleMessage
    ) {
    }
}
