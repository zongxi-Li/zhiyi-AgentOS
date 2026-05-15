package com.kinlin.ai.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kinlin.ai.service.AgentOsGatewayService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.LinkedHashMap;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AgentOsGatewayController.class)
class AgentOsGatewayControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private AgentOsGatewayService agentOsGatewayService;

    @Test
    void startWorkflow_forwardsToAgentOsCore() throws Exception {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("run", Map.of("runId", "run_001", "status", "waiting_review"));

        when(agentOsGatewayService.post(eq("/ai/core/workflows/start"), any(Map.class)))
                .thenReturn(response);

        Map<String, Object> request = Map.of(
                "title", "合同审查",
                "domain", "legal",
                "intent", "contract_review"
        );

        mockMvc.perform(post("/api/agentos/core/workflows/start")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.run.runId").value("run_001"))
                .andExpect(jsonPath("$.run.status").value("waiting_review"));
    }

    @Test
    void listWorkflowRuns_forwardsFiltersToAgentOsCore() throws Exception {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("total", 1);
        response.put("items", java.util.List.of(Map.of("runId", "run_001")));

        when(agentOsGatewayService.get("/ai/core/workflows/runs?status=waiting_review&source=workbench&page=1&pageSize=10"))
                .thenReturn(response);

        mockMvc.perform(get("/api/agentos/core/workflows/runs")
                        .param("status", "waiting_review")
                        .param("source", "workbench")
                        .param("page", "1")
                        .param("pageSize", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(1))
                .andExpect(jsonPath("$.items[0].runId").value("run_001"));
    }

    @Test
    void upgradeChat_forwardsToAgentOsChatUpgrade() throws Exception {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("source", "chat");
        response.put("run", Map.of("status", "waiting_review"));

        when(agentOsGatewayService.post(eq("/ai/chat/workflows/upgrade"), any(Map.class)))
                .thenReturn(response);

        mockMvc.perform(post("/api/agentos/chat/workflows/upgrade")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of("text", "聊天升级案件分析"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.source").value("chat"))
                .andExpect(jsonPath("$.run.status").value("waiting_review"));
    }
}
