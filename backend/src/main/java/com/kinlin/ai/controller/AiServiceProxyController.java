package com.kinlin.ai.controller;

import com.kinlin.ai.gateway.AiProxyService;
import com.kinlin.ai.gateway.AiSseGatewayService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.http.codec.ServerSentEvent;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.io.IOException;

/** Java security boundary for every client-visible /ai route. */
@RestController
@RequestMapping("/ai")
@RequiredArgsConstructor
public class AiServiceProxyController {

    private final AiProxyService aiProxyService;
    private final AiSseGatewayService aiSseGatewayService;

    @RequestMapping(value = "/**", method = {
            RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT,
            RequestMethod.PATCH, RequestMethod.DELETE
    })
    public ResponseEntity<byte[]> proxy(HttpServletRequest request) {
        try {
            return aiProxyService.forward(request);
        } catch (IllegalArgumentException | IOException error) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body("{\"error\":\"AI_PROXY_INVALID_REQUEST\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
    }

    @PostMapping(value = "/chat/text/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Mono<ResponseEntity<Flux<ServerSentEvent<String>>>> proxyChatStream(
            @org.springframework.web.bind.annotation.RequestBody(required = false) Object body) {
        return aiSseGatewayService.openPost("/ai/chat/text/stream", body);
    }

    @PostMapping(value = "/test/sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Mono<ResponseEntity<Flux<ServerSentEvent<String>>>> proxyDeterministicTestStream(
            @org.springframework.web.bind.annotation.RequestBody(required = false) Object body) {
        return aiSseGatewayService.openPost("/ai/test/sse", body);
    }
}
