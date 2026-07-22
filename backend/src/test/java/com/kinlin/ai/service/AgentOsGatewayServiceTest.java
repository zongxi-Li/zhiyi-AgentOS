package com.kinlin.ai.service;

import com.kinlin.ai.config.AgentProperties;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class AgentOsGatewayServiceTest {

    @Test
    void asyncStartPreservesAcceptedStatusWithoutUsingSynchronousTimeoutSemantics() {
        AgentProperties properties = new AgentProperties();
        properties.setTimeoutMs(240000);
        properties.setAsyncStartTimeoutMs(15000);
        WebClient.Builder builder = WebClient.builder().exchangeFunction(request -> Mono.just(
                jsonResponse(HttpStatus.ACCEPTED,
                        "{\"accepted\":true,\"task\":{\"taskId\":\"task_1\",\"status\":\"pending\"},"
                                + "\"run\":{\"runId\":\"run_1\",\"status\":\"pending\"}}")
        ));
        AgentOsGatewayService service = new AgentOsGatewayService(builder, properties, "http://agentos");

        Map<String, Object> response = service.postAsyncStart(
                "/ai/core/workflows/start-async",
                Map.of("clientRequestId", "request_1")
        );

        assertEquals(202, response.get(AgentOsGatewayService.INTERNAL_HTTP_STATUS_KEY));
        assertEquals("run_1", ((Map<?, ?>) response.get("run")).get("runId"));
    }

    @Test
    void asyncStartPreservesUpstream503InsteadOfConvertingItTo404() {
        AgentProperties properties = new AgentProperties();
        WebClient.Builder builder = WebClient.builder().exchangeFunction(request -> Mono.just(
                jsonResponse(HttpStatus.SERVICE_UNAVAILABLE,
                        "{\"detail\":\"workflow execution could not be submitted\"}")
        ));
        AgentOsGatewayService service = new AgentOsGatewayService(builder, properties, "http://agentos");

        Map<String, Object> response = service.postAsyncStart(
                "/ai/core/workflows/start-async",
                Map.of("clientRequestId", "request_1")
        );

        assertEquals(503, response.get(AgentOsGatewayService.INTERNAL_HTTP_STATUS_KEY));
        assertEquals("workflow execution could not be submitted", response.get("detail"));
    }

    private ClientResponse jsonResponse(HttpStatus status, String body) {
        return ClientResponse.create(status)
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(body)
                .build();
    }
}
