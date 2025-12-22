package com.kinlin.ai.dto;

import lombok.Data;

/**
 * 对话响应DTO
 */
@Data
public class ChatResponse {

    private String text;

    private String contextId;

    private Double confidence;

    private Integer tokensUsed;

    private Object animation; // 数字人动画数据
    
    private String recognizedText; // 语音识别结果（仅用于语音对话）
}

