package com.kinlin.ai.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;
import java.util.UUID;

/** 认证用户工具类 — 从 Spring Security SecurityContextHolder 中提取当前已认证用户 ID */
public final class AuthenticatedUser {

    private AuthenticatedUser() {
    }

    public static Optional<UUID> currentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || authentication.getPrincipal() == null) {
            return Optional.empty();
        }

        Object principal = authentication.getPrincipal();
        if (principal instanceof UUID uuid) {
            return Optional.of(uuid);
        }

        if (principal instanceof String text && !"anonymousUser".equals(text)) {
            try {
                return Optional.of(UUID.fromString(text));
            } catch (IllegalArgumentException ignored) {
                return Optional.empty();
            }
        }

        return Optional.empty();
    }
}
