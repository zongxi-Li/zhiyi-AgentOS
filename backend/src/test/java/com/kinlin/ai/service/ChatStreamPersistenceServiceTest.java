package com.kinlin.ai.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kinlin.ai.entity.Message;
import com.kinlin.ai.repository.ConversationRepository;
import com.kinlin.ai.repository.MessageRepository;
import org.junit.jupiter.api.Test;
import org.springframework.http.codec.ServerSentEvent;

import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class ChatStreamPersistenceServiceTest {

    @Test
    void persistsFinalContentAndMetricsWithoutRawReasoning() {
        ConversationRepository conversations = mock(ConversationRepository.class);
        MessageRepository messages = mock(MessageRepository.class);
        ChatStreamPersistenceService service = new ChatStreamPersistenceService(
                conversations, messages, new ObjectMapper());
        ChatStreamPersistenceService.StreamCapture capture = service.capture();

        capture.accept(event("reasoning_start", Map.of(
                "requestedThinkingMode", "deep",
                "effectiveThinkingMode", "deep",
                "effectiveReasoningEffort", "max"
        )));
        capture.accept(event("reasoning_delta", Map.of("delta", "raw private reasoning")));
        capture.accept(event("reasoning_end", Map.of("reasoningPhaseMs", 1200)));
        capture.accept(event("content_delta", Map.of("delta", "final ")));
        capture.accept(event("content_delta", Map.of("delta", "answer")));
        capture.accept(event("usage", Map.of(
                "reasoning_tokens", 320,
                "total_tokens", 500,
                "effectiveModel", "deepseek-v4-pro"
        )));
        capture.accept(event("done", Map.of("status", "completed")));

        ChatStreamPersistenceService.PreparedStream prepared =
                new ChatStreamPersistenceService.PreparedStream(UUID.randomUUID(), "ctx-test", Map.of());
        service.complete(prepared, capture);

        var captor = org.mockito.ArgumentCaptor.forClass(Message.class);
        verify(messages).save(captor.capture());
        Message saved = captor.getValue();
        assertEquals("final answer", saved.getContent());
        assertEquals(320, saved.getMetadata().get("reasoningTokens"));
        assertEquals(500, saved.getMetadata().get("totalTokens"));
        assertTrue((Boolean) saved.getMetadata().get("thinkingEnabled"));
        assertFalse(saved.getMetadata().toString().contains("raw private reasoning"));
        assertFalse(saved.getMetadata().containsKey("reasoning_content"));
    }

    private ServerSentEvent<String> event(String type, Map<String, Object> data) {
        try {
            String json = new ObjectMapper().writeValueAsString(Map.of(
                    "event", type,
                    "requestId", "request-1",
                    "sequence", 1,
                    "data", data
            ));
            return ServerSentEvent.builder(json).event(type).build();
        } catch (Exception error) {
            throw new AssertionError(error);
        }
    }
}
