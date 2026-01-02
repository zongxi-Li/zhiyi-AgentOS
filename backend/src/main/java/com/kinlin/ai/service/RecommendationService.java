package com.kinlin.ai.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 推荐服务
 * 基于对话上下文生成推荐问题
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RecommendationService {

    /**
     * 基于对话上下文生成推荐问题
     *
     * @param conversationHistory 对话历史（最近的几条消息）
     * @param roleName 当前角色名称（可选）
     * @return 推荐问题列表
     */
    public List<String> generateRecommendations(List<String> conversationHistory, String roleName) {
        List<String> recommendations = new ArrayList<>();

        if (conversationHistory == null || conversationHistory.isEmpty()) {
            // 如果没有对话历史，返回通用推荐
            return getDefaultRecommendations(roleName);
        }

        // 分析最近的消息，提取关键词
        String recentText = conversationHistory.stream()
                .limit(3) // 只分析最近3条消息
                .collect(Collectors.joining(" "));

        // 提取关键词（简单实现：提取常见问题词）
        List<String> keywords = extractKeywords(recentText);

        // 基于关键词生成推荐问题
        recommendations.addAll(generateQuestionsByKeywords(keywords, roleName));

        // 如果推荐问题不足，补充默认推荐
        if (recommendations.size() < 3) {
            recommendations.addAll(getDefaultRecommendations(roleName));
        }

        // 返回最多5个推荐问题
        return recommendations.stream()
                .distinct()
                .limit(5)
                .collect(Collectors.toList());
    }

    /**
     * 提取关键词
     */
    private List<String> extractKeywords(String text) {
        List<String> keywords = new ArrayList<>();
        
        // 常见问题关键词
        String[] questionWords = {"什么", "如何", "怎么", "为什么", "哪个", "哪些", "能否", "可以", "是否"};
        String[] topicWords = {"法律", "合同", "纠纷", "学习", "教育", "代码", "编程", "写作", "文章"};

        for (String word : questionWords) {
            if (text.contains(word)) {
                keywords.add(word);
            }
        }

        for (String word : topicWords) {
            if (text.contains(word)) {
                keywords.add(word);
            }
        }

        return keywords;
    }

    /**
     * 基于关键词生成推荐问题
     */
    private List<String> generateQuestionsByKeywords(List<String> keywords, String roleName) {
        List<String> questions = new ArrayList<>();

        if (keywords.isEmpty()) {
            return questions;
        }

        // 根据角色和关键词生成问题
        if (roleName != null) {
            if (roleName.contains("律师") || roleName.contains("法律")) {
                if (keywords.contains("合同")) {
                    questions.add("合同纠纷如何处理？");
                    questions.add("如何起草一份有效的合同？");
                }
                if (keywords.contains("纠纷")) {
                    questions.add("发生纠纷时应该采取什么措施？");
                }
                questions.add("常见的法律问题有哪些？");
            } else if (roleName.contains("教师") || roleName.contains("教育")) {
                if (keywords.contains("学习")) {
                    questions.add("如何提高学习效率？");
                    questions.add("有什么好的学习方法推荐？");
                }
                questions.add("如何制定学习计划？");
            } else if (roleName.contains("程序") || roleName.contains("代码")) {
                if (keywords.contains("代码") || keywords.contains("编程")) {
                    questions.add("如何优化代码性能？");
                    questions.add("常见的编程错误有哪些？");
                }
                questions.add("如何调试代码？");
            } else if (roleName.contains("作家") || roleName.contains("写作")) {
                if (keywords.contains("写作") || keywords.contains("文章")) {
                    questions.add("如何提高写作水平？");
                    questions.add("文章结构应该如何安排？");
                }
                questions.add("如何写出吸引人的开头？");
            }
        }

        // 通用问题
        if (keywords.contains("什么")) {
            questions.add("能详细解释一下吗？");
        }
        if (keywords.contains("如何") || keywords.contains("怎么")) {
            questions.add("具体步骤是什么？");
        }
        if (keywords.contains("为什么")) {
            questions.add("有什么原因吗？");
        }

        return questions;
    }

    /**
     * 获取默认推荐问题
     */
    private List<String> getDefaultRecommendations(String roleName) {
        List<String> recommendations = new ArrayList<>();

        if (roleName != null) {
            if (roleName.contains("律师") || roleName.contains("法律")) {
                recommendations.add("合同纠纷如何处理？");
                recommendations.add("如何保护自己的合法权益？");
                recommendations.add("常见的法律风险有哪些？");
            } else if (roleName.contains("教师") || roleName.contains("教育")) {
                recommendations.add("如何提高学习效率？");
                recommendations.add("有什么好的学习方法？");
                recommendations.add("如何制定学习计划？");
            } else if (roleName.contains("程序") || roleName.contains("代码")) {
                recommendations.add("如何优化代码性能？");
                recommendations.add("常见的编程错误有哪些？");
                recommendations.add("如何调试代码？");
            } else if (roleName.contains("作家") || roleName.contains("写作")) {
                recommendations.add("如何提高写作水平？");
                recommendations.add("文章结构应该如何安排？");
                recommendations.add("如何写出吸引人的开头？");
            } else {
                recommendations.add("能详细解释一下吗？");
                recommendations.add("有什么建议吗？");
                recommendations.add("还有其他相关问题吗？");
            }
        } else {
            recommendations.add("能详细解释一下吗？");
            recommendations.add("有什么建议吗？");
            recommendations.add("还有其他相关问题吗？");
        }

        return recommendations;
    }
}
