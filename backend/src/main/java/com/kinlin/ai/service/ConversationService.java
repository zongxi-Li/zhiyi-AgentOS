package com.kinlin.ai.service;

import com.kinlin.ai.entity.Conversation;
import com.kinlin.ai.repository.ConversationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 对话服务类
 * 处理对话会话相关的业务逻辑
 */
@Service
@RequiredArgsConstructor
public class ConversationService {

    private final ConversationRepository conversationRepository;

    /**
     * 获取用户的对话列表
     */
    public List<Conversation> getUserConversations(UUID userId) {
        return conversationRepository.findByUserId(userId);
    }

    /**
     * 根据上下文ID获取对话
     */
    public Optional<Conversation> getConversationByContextId(String contextId) {
        return conversationRepository.findByContextId(contextId);
    }

    /**
     * 创建新对话
     */
    @Transactional
    public Conversation createConversation(UUID userId, UUID roleId) {
        Conversation conversation = new Conversation();
        conversation.setUserId(userId);
        conversation.setRoleId(roleId);
        conversation.setContextId(UUID.randomUUID().toString());
        return conversationRepository.save(conversation);
    }

    /**
     * 删除对话
     */
    @Transactional
    public void deleteConversation(UUID conversationId) {
        conversationRepository.deleteById(conversationId);
    }

    /**
     * 获取或创建对话
     */
    @Transactional
    public Conversation getOrCreateConversation(String contextId, UUID userId, UUID roleId) {
        if (contextId != null && !contextId.isEmpty()) {
            return conversationRepository.findByContextId(contextId)
                    .orElseGet(() -> createConversation(userId, roleId));
        }
        return createConversation(userId, roleId);
    }
}

