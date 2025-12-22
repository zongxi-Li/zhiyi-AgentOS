package com.kinlin.ai.dto;

import lombok.Data;

import java.util.UUID;

/**
 * 对话请求DTO
 */
@Data
public class ChatRequest {

    private String text;

    private UUID roleId;

    private String contextId;

    private String fileUrl; // 文件URL（图片、文档等）
    
    private Boolean useRag; // 是否使用RAG增强
}
