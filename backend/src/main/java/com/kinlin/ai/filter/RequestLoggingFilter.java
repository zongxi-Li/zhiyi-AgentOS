package com.kinlin.ai.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 请求日志过滤器
 * 记录所有HTTP请求
 */
@Slf4j
@Component
public class RequestLoggingFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        long startTime = System.currentTimeMillis();
        
        filterChain.doFilter(request, response);
        
        long duration = System.currentTimeMillis() - startTime;
        log.info("{} {} - {}ms - Status: {}", 
            request.getMethod(), 
            request.getRequestURI(),
            duration,
            response.getStatus());
    }
}

