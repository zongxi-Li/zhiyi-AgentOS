package com.kinlin.ai.config;

import com.kinlin.ai.gateway.PythonServiceAuthentication;
import com.kinlin.ai.gateway.TrustedUserContextForwarder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.ClientRequest;
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
    public WebClient.Builder webClientBuilder(
            PythonServiceAuthentication authentication,
            TrustedUserContextForwarder userContextForwarder
    ) {
        return WebClient.builder()
                .baseUrl(aiServiceUrl)
                .codecs(configurer -> configurer
                        .defaultCodecs()
                        .maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .defaultHeader("Content-Type", "application/json")
                .filter((request, next) -> {
                    ClientRequest authenticated = ClientRequest.from(request)
                            .headers(headers -> {
                                authentication.apply(headers);
                                if (!request.url().getPath().startsWith("/health")) {
                                    userContextForwarder.apply(headers);
                                }
                            })
                            .build();
                    return next.exchange(authenticated);
                });
    }

    @Bean
    public RestTemplateCustomizer pythonAuthenticationRestTemplateCustomizer(
            PythonServiceAuthentication authentication,
            TrustedUserContextForwarder userContextForwarder
    ) {
        return restTemplate -> restTemplate.getInterceptors().add((request, body, execution) -> {
            authentication.apply(request.getHeaders());
            userContextForwarder.apply(request.getHeaders());
            return execution.execute(request, body);
        });
    }

    @Bean
    public WebClient webClient(WebClient.Builder builder) {
        return builder.build();
    }
}
