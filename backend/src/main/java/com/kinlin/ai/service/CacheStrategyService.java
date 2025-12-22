package com.kinlin.ai.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

/**
 * 缓存策略服务
 * 实现对话缓存、角色缓存等
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CacheStrategyService {

    private final CacheService cacheService;

    /**
     * 缓存对话历史
     */
    @Cacheable(value = "conversationHistory", key = "#contextId")
    public List<?> cacheConversationHistory(String contextId, List<?> messages) {
        log.debug("Caching conversation history for contextId: {}", contextId);
        return messages;
    }

    /**
     * 缓存角色信息
     */
    @Cacheable(value = "roleInfo", key = "#roleId")
    public Object cacheRoleInfo(UUID roleId, Object role) {
        log.debug("Caching role info for roleId: {}", roleId);
        return role;
    }

    /**
     * 更新角色缓存
     */
    @CachePut(value = "roleInfo", key = "#roleId")
    public Object updateRoleCache(UUID roleId, Object role) {
        log.debug("Updating role cache for roleId: {}", roleId);
        return role;
    }

    /**
     * 清除角色缓存
     */
    @CacheEvict(value = "roleInfo", key = "#roleId")
    public void evictRoleCache(UUID roleId) {
        log.debug("Evicting role cache for roleId: {}", roleId);
    }

    /**
     * 清除对话缓存
     */
    @CacheEvict(value = "conversationHistory", key = "#contextId")
    public void evictConversationCache(String contextId) {
        log.debug("Evicting conversation cache for contextId: {}", contextId);
    }

    /**
     * 预热缓存
     */
    public void warmupCache() {
        log.info("Warming up cache...");
        // TODO: 实现缓存预热逻辑
    }
}

