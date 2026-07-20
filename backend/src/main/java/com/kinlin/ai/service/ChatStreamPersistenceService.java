package com.kinlin.ai.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.kinlin.ai.entity.Conversation;
import com.kinlin.ai.entity.Message;
import com.kinlin.ai.repository.ConversationRepository;
import com.kinlin.ai.repository.MessageRepository;
import com.kinlin.ai.security.AuthenticatedUser;
import lombok.RequiredArgsConstructor;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Persists stream results while explicitly excluding raw reasoning deltas. */
@Service
@RequiredArgsConstructor
public class ChatStreamPersistenceService {

    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    private final ObjectMapper objectMapper;

    @Transactional
    public PreparedStream prepare(Map<String, Object> requestBody) {
        UUID userId = AuthenticatedUser.currentUserId()
                .orElseThrow(() -> new IllegalStateException("Authenticated user is required for chat streaming"));
        Map<String, Object> body = new LinkedHashMap<>(requestBody == null ? Map.of() : requestBody);
        String text = stringValue(body.get("text"));
        String contextId = stringValue(body.get("context_id"));
        UUID roleId = uuidValue(body.get("role_id"));

        Conversation conversation = contextId.isBlank()
                ? createConversation(userId, roleId, text)
                : conversationRepository.findByContextId(contextId)
                        .orElseGet(() -> createConversation(userId, roleId, text, contextId));

        Message userMessage = new Message();
        userMessage.setConversationId(conversation.getId());
        userMessage.setRole(Message.MessageRole.USER);
        userMessage.setContent(text);
        userMessage.setMessageType(Message.MessageType.TEXT);
        messageRepository.save(userMessage);

        body.put("context_id", conversation.getContextId());
        if (!(body.get("context") instanceof List<?>)) {
            body.put("context", buildContext(conversation.getId()));
        }
        return new PreparedStream(conversation.getId(), conversation.getContextId(), body);
    }

    public StreamCapture capture() {
        return new StreamCapture(objectMapper);
    }

    @Transactional
    public void complete(PreparedStream prepared, StreamCapture capture) {
        if (!capture.completed || capture.content.isEmpty()) {
            return;
        }
        Message assistantMessage = new Message();
        assistantMessage.setConversationId(prepared.conversationId());
        assistantMessage.setRole(Message.MessageRole.ASSISTANT);
        assistantMessage.setContent(capture.content.toString());
        assistantMessage.setMessageType(Message.MessageType.TEXT);
        assistantMessage.setMetadata(capture.metadata());
        messageRepository.save(assistantMessage);
    }

    private Conversation createConversation(UUID userId, UUID roleId, String text) {
        return createConversation(userId, roleId, text, "ctx_" + UUID.randomUUID());
    }

    private Conversation createConversation(UUID userId, UUID roleId, String text, String contextId) {
        Conversation conversation = new Conversation();
        conversation.setUserId(userId);
        conversation.setRoleId(roleId);
        conversation.setContextId(contextId);
        conversation.setTitle(text.length() > 50 ? text.substring(0, 50) + "..." : text);
        return conversationRepository.save(conversation);
    }

    private List<Map<String, String>> buildContext(UUID conversationId) {
        return messageRepository.findByConversationIdOrderByCreatedAtAsc(conversationId).stream()
                .filter(message -> message.getContent() != null && !message.getContent().isBlank())
                .map(message -> Map.of(
                        "role", message.getRole() == Message.MessageRole.USER ? "user" : "assistant",
                        "content", message.getContent()
                ))
                .toList();
    }

    private String stringValue(Object value) {
        return value == null ? "" : String.valueOf(value).trim();
    }

    private UUID uuidValue(Object value) {
        try {
            String text = stringValue(value);
            return text.isBlank() ? null : UUID.fromString(text);
        } catch (IllegalArgumentException ignored) {
            return null;
        }
    }

    public record PreparedStream(UUID conversationId, String contextId, Map<String, Object> body) { }

    public static final class StreamCapture {
        private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() { };
        private final ObjectMapper objectMapper;
        private final StringBuilder content = new StringBuilder();
        private final Map<String, Object> usage = new LinkedHashMap<>();
        private boolean reasoningStarted;
        private boolean reasoningCompleted;
        private boolean contentStarted;
        private boolean completed;

        private StreamCapture(ObjectMapper objectMapper) {
            this.objectMapper = objectMapper;
        }

        @SuppressWarnings("unchecked")
        public void accept(ServerSentEvent<String> event) {
            if (event == null || event.data() == null || event.data().isBlank()) {
                return;
            }
            try {
                Map<String, Object> envelope = objectMapper.readValue(event.data(), MAP_TYPE);
                String type = String.valueOf(envelope.getOrDefault("event", event.event()));
                Object rawData = envelope.get("data");
                Map<String, Object> data = rawData instanceof Map<?, ?>
                        ? (Map<String, Object>) rawData
                        : Map.of();
                switch (type) {
                    case "reasoning_start" -> {
                        reasoningStarted = true;
                        copy(data, "requestedThinkingMode", "effectiveThinkingMode", "effectiveReasoningEffort");
                    }
                    case "reasoning_end" -> {
                        reasoningCompleted = true;
                        copy(data, "reasoningPhaseMs");
                    }
                    case "content_delta" -> {
                        Object delta = data.get("delta");
                        if (delta != null) {
                            contentStarted = true;
                            content.append(delta);
                        }
                    }
                    case "usage" -> copy(data,
                            "inputTokens", "input_tokens",
                            "reasoningTokens", "reasoning_tokens",
                            "outputTokens", "output_tokens",
                            "totalTokens", "total_tokens",
                            "latencyMs", "requestedModel", "effectiveModel",
                            "requestedThinkingMode", "effectiveThinkingMode",
                            "effectiveReasoningEffort", "resolutionReasons");
                    case "done" -> completed = "completed".equals(String.valueOf(data.get("status")));
                    default -> {
                        // reasoning_delta and error are intentionally not persisted as message metadata.
                    }
                }
            } catch (Exception ignored) {
                // Malformed stream events remain visible to the client but never enter persistence.
            }
        }

        public Map<String, Object> metadata() {
            Map<String, Object> metadata = new LinkedHashMap<>();
            metadata.putAll(usage);
            normalizeTokenName(metadata, "input_tokens", "inputTokens");
            normalizeTokenName(metadata, "reasoning_tokens", "reasoningTokens");
            normalizeTokenName(metadata, "output_tokens", "outputTokens");
            normalizeTokenName(metadata, "total_tokens", "totalTokens");
            metadata.put("thinkingEnabled", reasoningStarted);
            metadata.putIfAbsent("fallbackUsed", false);
            List<Map<String, String>> summary = new ArrayList<>();
            if (reasoningStarted) {
                summary.add(Map.of(
                        "stage", "reasoning",
                        "status", reasoningCompleted ? "completed" : "interrupted",
                        "description", reasoningCompleted ? "模型完成思考阶段" : "模型思考阶段未完整结束"
                ));
            }
            if (contentStarted) {
                summary.add(Map.of(
                        "stage", "answer_generation",
                        "status", completed ? "completed" : "interrupted",
                        "description", completed ? "模型完成最终回答生成" : "最终回答生成未完整结束"
                ));
            }
            metadata.put("executionSummary", summary);
            return metadata;
        }

        private void copy(Map<String, Object> data, String... keys) {
            for (String key : keys) {
                if (data.containsKey(key) && data.get(key) != null) {
                    usage.put(key, data.get(key));
                }
            }
        }

        private void normalizeTokenName(Map<String, Object> metadata, String oldName, String newName) {
            if (!metadata.containsKey(newName) && metadata.containsKey(oldName)) {
                metadata.put(newName, metadata.remove(oldName));
            } else {
                metadata.remove(oldName);
            }
        }
    }
}
