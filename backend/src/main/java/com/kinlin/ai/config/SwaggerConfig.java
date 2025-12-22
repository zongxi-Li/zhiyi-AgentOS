package com.kinlin.ai.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Swagger API文档配置
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Kinlin AI API")
                        .version("1.0.0")
                        .description("Kinlin AI系统多功能交互助手API文档")
                        .contact(new Contact()
                                .name("Kinlin AI Team")
                                .email("support@kinlin.ai")));
    }
}

