package com.kinlin.ai.service;

import com.kinlin.ai.config.AgentProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class AgentOsGatewayService {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_BODY =
            new ParameterizedTypeReference<>() {
            };

    private final WebClient webClient;
    private final AgentProperties agentProperties;
    private final int timeoutMs;

    public AgentOsGatewayService(WebClient.Builder webClientBuilder, AgentProperties agentProperties,
                                 @Value("${ai.service.url:http://localhost:8000}") String aiServiceUrl) {
        this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
        this.agentProperties = agentProperties;
        this.timeoutMs = agentProperties.getTimeoutMs();
    }

    public Map<String, Object> get(String path) {
        if (!agentProperties.isEnabled()) {
            return disabledResponse(path);
        }
        try {
            return webClient.get()
                    .uri(path)
                    .retrieve()
                    .bodyToMono(MAP_BODY)
                    .timeout(Duration.ofMillis(timeoutMs))
                    .onErrorResume(e -> toErrorResponse(e, path))
                    .block();
        } catch (Exception e) {
            return errorResponse(e, path);
        }
    }

    public Map<String, Object> post(String path, Object body) {
        if (!agentProperties.isEnabled()) {
            return disabledResponse(path);
        }
        try {
            return webClient.post()
                    .uri(path)
                    .bodyValue(body != null ? body : new HashMap<>())
                    .retrieve()
                    .bodyToMono(MAP_BODY)
                    .timeout(Duration.ofMillis(timeoutMs))
                    .onErrorResume(e -> toErrorResponse(e, path))
                    .block();
        } catch (Exception e) {
            return errorResponse(e, path);
        }
    }

    public String getText(String path) {
        if (!agentProperties.isEnabled()) {
            return "AgentOS gateway is disabled by configuration. path=" + path;
        }
        try {
            return webClient.get()
                    .uri(path)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeoutMs))
                    .onErrorResume(e -> Mono.just(errorText(e, path)))
                    .block();
        } catch (Exception e) {
            return errorText(e, path);
        }
    }

    private Mono<Map<String, Object>> toErrorResponse(Throwable throwable, String path) {
        Exception ex = throwable instanceof Exception ? (Exception) throwable : new Exception(throwable.getMessage(), throwable);
        return Mono.just(errorResponse(ex, path));
    }

    private Map<String, Object> disabledResponse(String path) {
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("message", "AgentOS gateway is disabled by configuration.");
        response.put("error", "agent.disabled");
        response.put("path", path);
        return response;
    }

    private Map<String, Object> errorResponse(Exception e, String path) {
        log.error("AgentOS gateway request failed. path={}", path, e);
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("message", e.getMessage() == null ? "AgentOS gateway unavailable." : e.getMessage());
        response.put("error", e.getClass().getSimpleName());
        response.put("path", path);
        return response;
    }

    private String errorText(Throwable e, String path) {
        log.error("AgentOS gateway text request failed. path={}", path, e);
        String message = e.getMessage() == null ? "AgentOS gateway unavailable." : e.getMessage();
        return "AgentOS gateway request failed: " + message + "\npath=" + path + "\n";
    }
}
