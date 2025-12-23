package com.kinlin.ai.controller;

import com.kinlin.ai.dto.KnowledgeGraphRequest;
import com.kinlin.ai.service.KnowledgeGraphService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 知识图谱控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/knowledge-graph")
@RequiredArgsConstructor
public class KnowledgeGraphController {

    private final KnowledgeGraphService knowledgeGraphService;

    /**
     * 从文档构建知识图谱
     */
    @PostMapping("/build")
    public ResponseEntity<Map<String, Object>> buildKnowledgeGraph(
            @Valid @RequestBody KnowledgeGraphRequest request
    ) {
        Map<String, Object> result = knowledgeGraphService.buildKnowledgeGraph(request.getDocuments());
        return ResponseEntity.ok(result);
    }

    /**
     * 混合检索：知识图谱 + 向量数据库
     */
    @PostMapping("/search")
    public ResponseEntity<Map<String, Object>> hybridSearch(
            @RequestParam("question") String question,
            @RequestBody List<Map<String, Object>> vectorDbResults,
            @RequestParam(value = "topK", defaultValue = "5") Integer topK
    ) {
        Map<String, Object> result = knowledgeGraphService.hybridSearch(question, vectorDbResults, topK);
        return ResponseEntity.ok(result);
    }

    /**
     * 基于知识图谱进行推理
     */
    @PostMapping("/reason")
    public ResponseEntity<Map<String, Object>> reasonWithKnowledgeGraph(
            @RequestParam("question") String question
    ) {
        Map<String, Object> result = knowledgeGraphService.reasonWithKnowledgeGraph(question);
        return ResponseEntity.ok(result);
    }

    /**
     * 获取知识图谱统计信息
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getGraphStats() {
        Map<String, Object> result = knowledgeGraphService.getGraphStats();
        return ResponseEntity.ok(result);
    }

    /**
     * 查询实体相关信息
     */
    @GetMapping("/entity/{entityId}")
    public ResponseEntity<Map<String, Object>> getEntityInfo(
            @PathVariable String entityId,
            @RequestParam(value = "relation", required = false) String relation,
            @RequestParam(value = "limit", defaultValue = "10") Integer limit
    ) {
        Map<String, Object> result = knowledgeGraphService.getEntityInfo(entityId, relation, limit);
        return ResponseEntity.ok(result);
    }
}

