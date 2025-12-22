package com.kinlin.ai.config;

import com.kinlin.ai.filter.RequestLoggingFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 过滤器配置类
 */
@Configuration
@RequiredArgsConstructor
public class FilterConfig {

    private final RequestLoggingFilter requestLoggingFilter;

    @Bean
    public FilterRegistrationBean<RequestLoggingFilter> loggingFilter() {
        FilterRegistrationBean<RequestLoggingFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(requestLoggingFilter);
        registration.addUrlPatterns("/*");
        registration.setOrder(1);
        return registration;
    }
}

