package com.kinlin.ai.controller;

import com.kinlin.ai.entity.User;
import com.kinlin.ai.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * 用户控制器
 */
@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * 获取当前用户信息
     */
    @GetMapping("/me")
    public ResponseEntity<User> getCurrentUser(
            @RequestHeader(value = "X-User-Id", required = false) UUID userId
    ) {
        if (userId == null) {
            return ResponseEntity.badRequest().build();
        }
        return userService.getUserById(userId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * 获取用户信息
     */
    @GetMapping("/{userId}")
    public ResponseEntity<User> getUser(@PathVariable UUID userId) {
        return userService.getUserById(userId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}

