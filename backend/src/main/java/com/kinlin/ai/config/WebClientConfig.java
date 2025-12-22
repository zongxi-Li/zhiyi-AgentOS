package com.kinlin.ai.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;

/**
 * WebClient配置类
 * 用于调用Python AI服务
 */
@Configuration
public class WebClientConfig {

    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceUrl;

    @Bean
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder()
                .baseUrl(aiServiceUrl)
                .codecs(configurer -> configurer
                        .defaultCodecs()
                        .maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .defaultHeader("Content-Type", "application/json");
    }

    @Bean
    public WebClient webClient(WebClient.Builder builder) {
        return builder.build();
    }
}
