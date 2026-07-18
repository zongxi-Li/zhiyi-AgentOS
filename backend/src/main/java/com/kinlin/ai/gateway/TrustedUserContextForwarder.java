package com.kinlin.ai.gateway;

import com.kinlin.ai.security.AuthenticatedUser;
import com.kinlin.ai.security.AuthenticatedUserContext;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;

/** Rebuilds trusted identity headers from Spring Security, never from client input. */
@Component
public class TrustedUserContextForwarder {

    public void apply(HttpHeaders headers) {
        AuthenticatedUserContext context = AuthenticatedUser.currentContext()
                .orElseThrow(() -> new IllegalStateException("authenticated user context is required"));
        headers.set(AiGatewayHeaders.AUTHENTICATED_USER_ID, context.userId().toString());
        headers.set(AiGatewayHeaders.AUTHENTICATED_USER_SUBJECT, context.subject());
        headers.set(AiGatewayHeaders.AUTHENTICATED_USER_ROLE, context.role());
        if (context.tenantId() != null && !context.tenantId().isBlank()) {
            headers.set(AiGatewayHeaders.AUTHENTICATED_TENANT_ID, context.tenantId());
        } else {
            headers.remove(AiGatewayHeaders.AUTHENTICATED_TENANT_ID);
        }
    }
}
