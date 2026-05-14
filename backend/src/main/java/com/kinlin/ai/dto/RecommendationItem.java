package com.kinlin.ai.dto;

import lombok.Data;

@Data
public class RecommendationItem {

    private String text;

    private String reason;

    private String targetAction;

    private double confidence;

    private String scope;
}
