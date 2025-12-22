package com.kinlin.ai.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RAG服务类
 * 调用Python AI服务的RAG功能
 */
@Slf4j
@Service
public class RagService {

    private final WebClient webClient;
    
    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceUrl;

    public RagService(WebClient.Builder webClientBuilder, @Value("${ai.service.url:http://localhost:8000}") String aiServiceUrl) {
        this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
        this.aiServiceUrl = aiServiceUrl;
    }

    /**
     * RAG查询
     */
    public RagResponse query(String query, Integer topK, String contextId) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("query", query);
        requestBody.put("top_k", topK != null ? topK : 5);
        if (contextId != null) {
            requestBody.put("context_id", contextId);
        }

        try {
            return webClient.post()
                    .uri(aiServiceUrl + "/rag/query")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(RagResponse.class)
                    .block();
        } catch (Exception e) {
            log.error("RAG查询失败", e);
            throw new RuntimeException("RAG查询失败: " + e.getMessage());
        }
    }

    /**
     * 上传文档
     */
    public String uploadDocument(byte[] fileData, String filename) {
        try {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.part("file", fileData)
                   .filename(filename)
                   .contentType(MediaType.APPLICATION_OCTET_STREAM);
            
            return webClient.post()
                    .uri(aiServiceUrl + "/rag/documents")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(builder.build()))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .map(response -> (String) response.get("document_id"))
                    .block();
        } catch (Exception e) {
            log.error("文档上传失败", e);
            throw new RuntimeException("文档上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 上传文档（使用MultipartFile）
     */
    public String uploadDocument(org.springframework.web.multipart.MultipartFile file) {
        try {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.part("file", file.getResource())
                   .filename(file.getOriginalFilename())
                   .contentType(MediaType.parseMediaType(
                           file.getContentType() != null ? file.getContentType() : "application/octet-stream"));
            
            return webClient.post()
                    .uri(aiServiceUrl + "/rag/documents")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(builder.build()))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .map(response -> (String) response.get("document_id"))
                    .block();
        } catch (Exception e) {
            log.error("文档上传失败", e);
            throw new RuntimeException("文档上传失败: " + e.getMessage());
        }
    }

    /**
     * RAG响应
     */
    public record RagResponse(
            String answer,
            List<Map<String, Object>> sources,
            Double confidence
    ) {
    }
    
    /**
     * 获取文档列表
     */
    public Map<String, Object> listDocuments() {
        try {
            return webClient.get()
                    .uri(aiServiceUrl + "/rag/documents")
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
        } catch (Exception e) {
            log.error("获取文档列表失败", e);
            throw new RuntimeException("获取文档列表失败: " + e.getMessage());
        }
    }
    
    /**
     * 删除文档
     */
    public void deleteDocument(String docId) {
        try {
            webClient.delete()
                    .uri(aiServiceUrl + "/rag/documents/" + docId)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();
        } catch (Exception e) {
            log.error("删除文档失败", e);
            throw new RuntimeException("删除文档失败: " + e.getMessage());
        }
    }
}

