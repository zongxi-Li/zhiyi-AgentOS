package com.kinlin.ai.dto.agentos;

import java.util.Map;

/** Request accepted by the asynchronous workflow preparation endpoint. */
public record AsyncWorkflowStartRequest(
        String title,
        String domain,
        String intent,
        String roleType,
        String taskType,
        Map<String, Object> input,
        String securityLevel,
        String priority,
        String workflowId,
        String reviewMode,
        String clientRequestId
) {
}
