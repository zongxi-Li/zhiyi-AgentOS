package com.kinlin.ai.service;

import com.kinlin.ai.entity.Role;
import com.kinlin.ai.repository.RoleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 个性化推荐服务
 * 基于用户画像推荐角色和内容
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RecommendationService {

    private final UserProfileService userProfileService;
    private final RoleRepository roleRepository;

    /**
     * 推荐角色
     *
     * @param userId 用户ID
     * @param limit  推荐数量
     * @return 推荐的角色列表
     */
    public List<RoleRecommendation> recommendRoles(UUID userId, int limit) {
        // 获取用户画像
        UserProfileService.UserProfile profile = userProfileService.buildUserProfile(userId);

        List<RoleRecommendation> recommendations = new ArrayList<>();

        // 1. 推荐常用角色（如果用户有使用历史）
        if (profile.getFavoriteRoleId() != null) {
            roleRepository.findById(profile.getFavoriteRoleId()).ifPresent(role -> {
                recommendations.add(new RoleRecommendation(
                        role,
                        "您经常使用的角色",
                        1.0
                ));
            });
        }

        // 2. 推荐相似角色（基于角色类型）
        if (profile.getRoleUsageCount() != null && !profile.getRoleUsageCount().isEmpty()) {
            Set<Role.RoleType> usedRoleTypes = profile.getRoleUsageCount().keySet().stream()
                    .map(roleIdStr -> {
                        try {
                            UUID roleId = UUID.fromString(roleIdStr);
                            return roleRepository.findById(roleId)
                                    .map(Role::getRoleType)
                                    .orElse(null);
                        } catch (IllegalArgumentException e) {
                            log.warn("Invalid UUID format: {}", roleIdStr);
                            return null;
                        }
                    })
                    .filter(type -> type != null)
                    .collect(Collectors.toSet());

            roleRepository.findAll().stream()
                    .filter(role -> usedRoleTypes.contains(role.getRoleType()))
                    .filter(role -> !role.getId().equals(profile.getFavoriteRoleId()))
                    .limit(limit - recommendations.size())
                    .forEach(role -> {
                        recommendations.add(new RoleRecommendation(
                                role,
                                "与您常用角色相似",
                                0.8
                        ));
                    });
        }

        // 3. 推荐热门角色（如果推荐不足）
        if (recommendations.size() < limit) {
            List<Role> popularRoles = roleRepository.findAll().stream()
                    .filter(role -> profile.getFavoriteRoleId() == null ||
                            !role.getId().equals(profile.getFavoriteRoleId()))
                    .limit(limit - recommendations.size())
                    .collect(Collectors.toList());

            popularRoles.forEach(role -> {
                recommendations.add(new RoleRecommendation(
                        role,
                        "热门角色",
                        0.6
                ));
            });
        }

        // 按推荐分数排序
        recommendations.sort((a, b) -> Double.compare(b.getScore(), a.getScore()));

        log.info("为用户 {} 推荐了 {} 个角色", userId, recommendations.size());
        return recommendations;
    }

    /**
     * 推荐对话主题（基于用户历史）
     *
     * @param userId 用户ID
     * @return 推荐的主题列表
     */
    public List<String> recommendTopics(UUID userId) {
        UserProfileService.UserProfile profile = userProfileService.buildUserProfile(userId);

        List<String> topics = new ArrayList<>();

        // 基于用户活跃度推荐
        if ("very_active".equals(profile.getActivityLevel())) {
            topics.add("深度技术讨论");
            topics.add("专业咨询");
        } else if ("active".equals(profile.getActivityLevel())) {
            topics.add("日常交流");
            topics.add("学习辅导");
        } else {
            topics.add("快速问答");
            topics.add("简单咨询");
        }

        // 基于常用角色推荐主题
        if (profile.getFavoriteRoleName() != null) {
            switch (profile.getFavoriteRoleName()) {
                case "律师":
                    topics.add("法律咨询");
                    topics.add("合同审查");
                    break;
                case "教师":
                    topics.add("知识讲解");
                    topics.add("学习辅导");
                    break;
                case "程序员":
                    topics.add("代码问题");
                    topics.add("技术讨论");
                    break;
                case "作家":
                    topics.add("创意写作");
                    topics.add("文章润色");
                    break;
            }
        }

        return topics;
    }

    /**
     * 角色推荐数据类
     */
    public static class RoleRecommendation {
        private Role role;
        private String reason;
        private double score;

        public RoleRecommendation(Role role, String reason, double score) {
            this.role = role;
            this.reason = reason;
            this.score = score;
        }

        public Role getRole() {
            return role;
        }

        public String getReason() {
            return reason;
        }

        public double getScore() {
            return score;
        }
    }
}

