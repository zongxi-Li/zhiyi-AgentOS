package com.kinlin.ai.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class RecommendationContextRequest {

    private String roleName;

    private String scope;

    private String scene;

    private String currentInput;

    private String currentOutput;

    private List<String> conversationHistory;
}
