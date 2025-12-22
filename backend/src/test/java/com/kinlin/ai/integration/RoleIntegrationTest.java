package com.kinlin.ai.integration;

import com.kinlin.ai.dto.RoleCreateRequest;
import com.kinlin.ai.entity.Role;
import com.kinlin.ai.repository.RoleRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 角色管理集成测试
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class RoleIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private RoleRepository roleRepository;

    private String baseUrl;
    private UUID userId;

    @BeforeEach
    void setUp() {
        baseUrl = "http://localhost:" + port + "/api/roles";
        userId = UUID.randomUUID();
    }

    @Test
    void testGetBuiltinRoles() {
        ResponseEntity<Role[]> response = restTemplate.getForEntity(
                baseUrl + "/builtin",
                Role[].class
        );

        assertTrue(response.getStatusCode().is2xxSuccessful());
        assertNotNull(response.getBody());
    }

    @Test
    void testCreateCustomRole() {
        RoleCreateRequest request = new RoleCreateRequest();
        request.setName("自定义角色");
        request.setDescription("测试描述");
        request.setSystemPrompt("你是一个自定义角色");

        HttpHeaders headers = new HttpHeaders();
        headers.set("X-User-Id", userId.toString());
        HttpEntity<RoleCreateRequest> entity = new HttpEntity<>(request, headers);

        ResponseEntity<Role> response = restTemplate.exchange(
                baseUrl + "/custom",
                HttpMethod.POST,
                entity,
                Role.class
        );

        assertTrue(response.getStatusCode().is2xxSuccessful());
        assertNotNull(response.getBody());
        assertEquals("自定义角色", response.getBody().getName());
    }
}

