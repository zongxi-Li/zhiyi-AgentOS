package com.kinlin.ai.controller;

import com.kinlin.ai.entity.Conversation;
import com.kinlin.ai.service.ConversationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/**
 * 对话会话控制器
 */
@RestController
@RequestMapping("/conversations")
@RequiredArgsConstructor
public class ConversationController {

    private final ConversationService conversationService;

    /**
     * 获取用户的对话列表
     */
    @GetMapping
    public ResponseEntity<List<Conversation>> getUserConversations(
            @RequestHeader(value = "X-User-Id", required = false) UUID userId
    ) {
        if (userId == null) {
            return ResponseEntity.badRequest().build();
        }
        List<Conversation> conversations = conversationService.getUserConversations(userId);
        return ResponseEntity.ok(conversations);
    }

    /**
     * 获取对话详情
     */
    @GetMapping("/{contextId}")
    public ResponseEntity<Conversation> getConversation(@PathVariable String contextId) {
        return conversationService.getConversationByContextId(contextId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * 删除对话
     */
    @DeleteMapping("/{conversationId}")
    public ResponseEntity<Void> deleteConversation(@PathVariable UUID conversationId) {
        conversationService.deleteConversation(conversationId);
        return ResponseEntity.ok().build();
    }
}

