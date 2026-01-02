package com.kinlin.ai.controller;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * AI服务代理控制器
 * 用于代理Python AI服务的请求（如联邦模型管理等）
 */
@Slf4j
@RestController
@RequestMapping("/ai")
@RequiredArgsConstructor
public class AiServiceProxyController {

    private final WebClient.Builder webClientBuilder;

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    @Value("${ai.service.timeout}")
    private int timeout;

    private WebClient getWebClient() {
        return webClientBuilder
                .baseUrl(aiServiceUrl)
                .build();
    }

    /**
     * 代理GET请求到Python AI服务
     */
    @GetMapping("/**")
    public ResponseEntity<?> proxyGet(HttpServletRequest request) {
        try {
            String requestURI = request.getRequestURI();
            String path = extractPath(request);
            log.info("代理GET请求: requestURI={}, extractedPath={}", requestURI, path);
            
            // 检查是否是图像文件请求
            boolean isImageRequest = path.contains("/digital-human/image/") || 
                                    path.endsWith(".png") || 
                                    path.endsWith(".jpg") || 
                                    path.endsWith(".jpeg") || 
                                    path.endsWith(".gif") || 
                                    path.endsWith(".webp");
            
            if (isImageRequest) {
                // 对于图像文件，返回二进制数据
                byte[] imageData = getWebClient().get()
                        .uri(path)
                        .retrieve()
                        .bodyToMono(byte[].class)
                        .timeout(Duration.ofMillis(timeout))
                        .onErrorResume(e -> {
                            log.warn("代理图像请求到Python服务失败: {} - {}", path, e.getMessage());
                            return Mono.empty();
                        })
                        .block();
                
                if (imageData != null && imageData.length > 0) {
                    // 根据文件扩展名确定Content-Type
                    String contentType = "image/png";
                    if (path.endsWith(".jpg") || path.endsWith(".jpeg")) {
                        contentType = "image/jpeg";
                    } else if (path.endsWith(".gif")) {
                        contentType = "image/gif";
                    } else if (path.endsWith(".webp")) {
                        contentType = "image/webp";
                    }
                    
                    return ResponseEntity.ok()
                            .header("Content-Type", contentType)
                            .header("Cache-Control", "public, max-age=31536000")
                            .header("Access-Control-Allow-Origin", "*")
                            .body(imageData);
                } else {
                    return ResponseEntity.status(404).body(createErrorResponse(
                            new RuntimeException("图像文件不存在或无法访问"), path));
                }
            } else {
                // 对于JSON响应，使用Object类型
                Object response = getWebClient().get()
                        .uri(path)
                        .retrieve()
                        .bodyToMono(Object.class)
                        .timeout(Duration.ofMillis(timeout))
                        .onErrorResume(e -> {
                            log.warn("代理请求到Python服务失败: {} - {}", path, e.getMessage());
                            Exception ex = e instanceof Exception ? (Exception) e : new Exception(e.getMessage(), e);
                            return Mono.just(createErrorResponse(ex, path));
                        })
                        .block();

                return ResponseEntity.ok(response);
            }
        } catch (Exception e) {
            log.error("代理GET请求失败", e);
            return ResponseEntity.status(500).body(createErrorResponse(e, ""));
        }
    }

    /**
     * 代理POST请求到Python AI服务
     */
    @PostMapping("/**")
    public ResponseEntity<Object> proxyPost(
            @RequestBody(required = false) Object body,
            HttpServletRequest request
    ) {
        try {
            String path = extractPath(request);
            log.debug("代理POST请求到Python服务: {}", path);
            
            Object response = getWebClient().post()
                    .uri(path)
                    .bodyValue(body != null ? body : new HashMap<>())
                    .retrieve()
                    .bodyToMono(Object.class)
                    .timeout(Duration.ofMillis(timeout))
                    .onErrorResume(e -> {
                        log.warn("代理请求到Python服务失败: {} - {}", path, e.getMessage());
                        Exception ex = e instanceof Exception ? (Exception) e : new Exception(e.getMessage(), e);
                        return Mono.just(createErrorResponse(ex, path));
                    })
                    .block();

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("代理POST请求失败", e);
            return ResponseEntity.status(500).body(createErrorResponse(e, ""));
        }
    }

    /**
     * 提取请求路径（保留 /ai 前缀，因为Python服务的路由以 /ai 开头）
     */
    private String extractPath(HttpServletRequest request) {
        String requestURI = request.getRequestURI();
        String contextPath = request.getContextPath();
        
        log.debug("提取路径: requestURI={}, contextPath={}", requestURI, contextPath);
        
        // 去掉 context path（如果有）
        String path = requestURI;
        if (contextPath != null && !contextPath.isEmpty()) {
            path = path.substring(contextPath.length());
        }
        
        // 保留 /ai 前缀，因为Python服务的路由都是以 /ai 开头的
        // 例如：/ai/digital-human/image/{filename}
        // 不需要去掉 /ai 前缀
        
        // 添加查询参数
        String queryString = request.getQueryString();
        if (queryString != null && !queryString.isEmpty()) {
            path += "?" + queryString;
        }
        
        log.debug("提取后的路径（发送到Python服务）: {}", path);
        return path;
    }

    /**
     * 创建错误响应
     */
    private Map<String, Object> createErrorResponse(Exception e, String path) {
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        
        String errorMessage = e.getMessage();
        if (errorMessage == null || errorMessage.isEmpty()) {
            errorMessage = "Python AI服务不可用";
        }
        
        // 如果是连接错误，提供更友好的提示
        if (errorMessage.contains("Connection refused") || errorMessage.contains("timeout")) {
            response.put("message", "Python AI服务未启动，请确保服务运行在 " + aiServiceUrl);
        } else {
            response.put("message", "请求失败: " + errorMessage);
        }
        
        response.put("error", e.getClass().getSimpleName());
        response.put("path", path);
        
        return response;
    }
}

