package com.kinlin.ai.controller;

import com.kinlin.ai.gateway.AiProxyService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.springframework.beans.factory.annotation.Value;
import reactor.core.Disposable;

import java.io.IOException;
import java.util.HashMap;

/** Java security boundary for every client-visible /ai route. */
@RestController
@RequestMapping("/ai")
@RequiredArgsConstructor
public class AiServiceProxyController {

    private final AiProxyService aiProxyService;
    private final WebClient.Builder webClientBuilder;

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    @Value("${ai.service.timeout}")
    private int timeout;

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
    public SseEmitter proxyChatStream(@org.springframework.web.bind.annotation.RequestBody(required = false) Object body) {
        SseEmitter emitter = new SseEmitter((long) timeout);
        Disposable subscription = webClientBuilder.baseUrl(aiServiceUrl).build().post()
                .uri("/ai/chat/text/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(body != null ? body : new HashMap<>())
                .retrieve()
                .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})
                .subscribe(
                        event -> {
                            try {
                                if (event.data() != null) {
                                    emitter.send(SseEmitter.event().data(event.data()));
                                }
                            } catch (Exception sendError) {
                                emitter.completeWithError(sendError);
                            }
                        },
                        emitter::completeWithError,
                        emitter::complete
                );
        emitter.onCompletion(subscription::dispose);
        emitter.onTimeout(() -> {
            subscription.dispose();
            emitter.complete();
        });
        emitter.onError(error -> subscription.dispose());
        return emitter;
    }
}
