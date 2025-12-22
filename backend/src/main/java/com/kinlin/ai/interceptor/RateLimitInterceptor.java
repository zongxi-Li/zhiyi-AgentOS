package com.kinlin.ai.interceptor;

import com.google.common.cache.LoadingCache;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * API限流拦截器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class RateLimitInterceptor implements HandlerInterceptor {

    private static final int MAX_REQUESTS_PER_MINUTE = 60;
    private final LoadingCache<String, AtomicInteger> rateLimitCache;

    @Override
    public boolean preHandle(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler
    ) {
        String clientId = getClientId(request);
        
        try {
            AtomicInteger requestCount = rateLimitCache.get(clientId);
            int currentCount = requestCount.incrementAndGet();
            
            if (currentCount > MAX_REQUESTS_PER_MINUTE) {
                log.warn("Rate limit exceeded for client: {}", clientId);
                response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
                response.getWriter().write("{\"error\":\"请求过于频繁，请稍后再试\"}");
                return false;
            }
            
            // 设置响应头
            response.setHeader("X-RateLimit-Limit", String.valueOf(MAX_REQUESTS_PER_MINUTE));
            response.setHeader("X-RateLimit-Remaining", String.valueOf(MAX_REQUESTS_PER_MINUTE - currentCount));
            
            return true;
        } catch (Exception e) {
            log.error("Rate limit check failed", e);
            return true; // 出错时允许请求通过
        }
    }

    private String getClientId(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isEmpty()) {
            return forwarded.split(",")[0].trim();
        }
        String remoteAddr = request.getRemoteAddr();
        return remoteAddr != null ? remoteAddr : "unknown";
    }
}

