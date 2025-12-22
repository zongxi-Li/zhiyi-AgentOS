package com.kinlin.ai.service;

import com.kinlin.ai.dto.ChatResponse;
import com.kinlin.ai.dto.VoiceRecognitionResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AI服务调用类
 * 负责与Python AI服务通信
 */
@Service
public class AiService {

    private final WebClient webClient;

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    @Value("${ai.service.timeout}")
    private int timeout;

    public AiService(WebClient.Builder webClientBuilder, @Value("${ai.service.url}") String aiServiceUrl, @Value("${ai.service.timeout}") int timeout) {
        this.aiServiceUrl = aiServiceUrl;
        this.timeout = timeout;
        this.webClient = webClientBuilder
                .baseUrl(aiServiceUrl)
                .build();
    }

    /**
     * 发送文本消息到AI服务
     */
    public ChatResponse sendTextMessage(String text, String roleId, List<Map<String, String>> context) {
        return sendTextMessage(text, roleId, context, null);
    }

    /**
     * 发送文本消息到AI服务（带上下文ID）
     */
    public ChatResponse sendTextMessage(String text, String roleId, List<Map<String, String>> context, String contextId) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("text", text);
        if (roleId != null) {
            requestBody.put("role_id", roleId);
        }
        if (context != null) {
            requestBody.put("context", context);
        }
        if (contextId != null) {
            requestBody.put("context_id", contextId);
        }

        return webClient.post()
                .uri("/ai/chat/text")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(ChatResponse.class)
                .timeout(Duration.ofMillis(timeout))
                .block();
    }

    /**
     * 发送语音消息到AI服务
     * Python端会返回完整的对话响应，包含识别的文本和AI回复
     */
    public ChatResponse sendVoiceMessage(byte[] audioData, String roleId) {
        // 使用MultipartBodyBuilder构建multipart/form-data请求
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("audio", audioData)
               .filename("audio.wav")
               .contentType(MediaType.APPLICATION_OCTET_STREAM);
        
        if (roleId != null) {
            builder.part("role_id", roleId);
        }
        
        Map<String, Object> responseMap = webClient.post()
                .uri("/ai/chat/voice")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofMillis(timeout))
                .block();
        
        // 将响应Map转换为ChatResponse
        ChatResponse response = new ChatResponse();
        if (responseMap != null) {
            response.setText((String) responseMap.get("text"));
            Object confidenceObj = responseMap.get("confidence");
            if (confidenceObj != null) {
                if (confidenceObj instanceof Number) {
                    response.setConfidence(((Number) confidenceObj).doubleValue());
                } else if (confidenceObj instanceof Double) {
                    response.setConfidence((Double) confidenceObj);
                }
            } else {
                response.setConfidence(0.85);
            }
            response.setRecognizedText((String) responseMap.get("recognized_text"));
        }
        
        return response;
    }

    /**
     * 文本转语音
     */
    public byte[] textToSpeech(String text, String voice, Double speed, Double pitch) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("text", text);
        requestBody.put("voice", voice);
        if (speed != null) {
            requestBody.put("speed", speed);
        }
        if (pitch != null) {
            requestBody.put("pitch", pitch);
        }

        return webClient.post()
                .uri("/ai/tts")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(byte[].class)
                .timeout(Duration.ofMillis(timeout))
                .block();
    }
}

