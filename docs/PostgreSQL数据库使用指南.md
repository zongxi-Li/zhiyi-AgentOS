# Kinlin AI - PostgreSQL数据库使用指南

## 📚 目录

1. [数据库概述](#数据库概述)
2. [安装和配置](#安装和配置)
3. [数据库表结构](#数据库表结构)
4. [如何使用数据库](#如何使用数据库)
5. [常用操作示例](#常用操作示例)
6. [数据库迁移](#数据库迁移)
7. [连接测试](#连接测试)
8. [常见问题](#常见问题)

---

## 一、数据库概述

### 为什么使用PostgreSQL？

- ✅ **可靠性高**: 企业级数据库，数据安全可靠
- ✅ **功能强大**: 支持JSONB、全文搜索等高级功能
- ✅ **性能优秀**: 适合高并发场景
- ✅ **开源免费**: 无需授权费用
- ✅ **与Spring Boot集成好**: JPA/Hibernate完美支持

### 数据库用途

PostgreSQL存储系统的**核心业务数据**：

| 数据类型 | 表名 | 用途 |
|---------|------|------|
| 用户数据 | `users` | 用户账号、密码、邮箱 |
| 角色数据 | `roles` | 内置角色、自定义角色 |
| 对话数据 | `conversations` | 对话会话信息 |
| 消息数据 | `messages` | 对话消息内容 |
| 反馈数据 | `user_feedback` | 用户反馈和评价 |

---

## 二、安装和配置

### 方式1：使用Docker（推荐）✅

**最简单的方式**，一键启动：

```bash
# 使用docker-compose启动（包含PostgreSQL）
cd docker
docker-compose up -d postgres

# 查看日志
docker-compose logs postgres

# 停止
docker-compose stop postgres
```

**Docker配置**（`docker/docker-compose.yml`）:
```yaml
postgres:
  image: postgres:15
  container_name: kinlin-postgres
  environment:
    POSTGRES_DB: kinlin_ai
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### 方式2：本地安装

#### Windows安装

1. **下载PostgreSQL**
   - 访问 https://www.postgresql.org/download/windows/
   - 下载安装包（推荐15版本）

2. **安装**
   - 运行安装程序
   - 设置密码（记住这个密码）
   - 端口默认5432

3. **创建数据库**
   ```sql
   -- 使用psql命令行工具
   psql -U postgres
   
   -- 创建数据库
   CREATE DATABASE kinlin_ai;
   
   -- 创建用户（可选）
   CREATE USER kinlin_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE kinlin_ai TO kinlin_user;
   ```

#### Linux安装（银河麒麟系统）

```bash
# 安装PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到postgres用户
sudo -u postgres psql

# 创建数据库
CREATE DATABASE kinlin_ai;
CREATE USER kinlin_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE kinlin_ai TO kinlin_user;
\q
```

### 配置数据库连接

**配置文件**: `backend/src/main/resources/application.yml`

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/kinlin_ai
    username: postgres          # 数据库用户名
    password: 367343            # 数据库密码（请修改）
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 20     # 最大连接数
      minimum-idle: 5           # 最小空闲连接
      connection-timeout: 30000 # 连接超时（毫秒）
```

**修改密码**:
```yaml
# 将 password 改为你的PostgreSQL密码
password: your_password_here
```

---

## 三、数据库表结构

### 1. 用户表 (users)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,    -- 用户名（唯一）
    email VARCHAR(100) UNIQUE,                -- 邮箱（唯一，可选）
    password_hash VARCHAR(255),              -- 密码哈希（BCrypt加密）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created ON users(created_at);
```

**字段说明**:
- `id`: 主键，UUID类型
- `username`: 用户名，必填，唯一
- `email`: 邮箱，可选，唯一
- `password_hash`: 加密后的密码
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 2. 角色表 (roles)

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,              -- 角色名称
    description TEXT,                       -- 角色描述
    role_type VARCHAR(20) NOT NULL,         -- 角色类型：BUILTIN/CUSTOM
    user_id UUID,                           -- 创建者ID（自定义角色）
    system_prompt TEXT,                     -- 系统提示词
    dialogue_style JSONB,                   -- 对话风格（JSON格式）
    personality JSONB,                      -- 性格特点（JSON格式）
    avatar_config JSONB,                    -- 数字人配置（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**字段说明**:
- `role_type`: `BUILTIN`（内置角色）或 `CUSTOM`（自定义角色）
- `dialogue_style`: JSON格式，如 `{"formality": 0.8, "warmth": 0.6}`
- `personality`: JSON格式，如 `["严谨", "专业", "耐心"]`
- `avatar_config`: JSON格式，数字人配置

### 3. 对话表 (conversations)

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,                           -- 用户ID
    role_id UUID,                           -- 角色ID
    context_id VARCHAR(100) UNIQUE,         -- 上下文ID（用于多轮对话）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. 消息表 (messages)

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,          -- 对话ID
    role VARCHAR(20) NOT NULL,              -- 角色：USER/ASSISTANT
    content TEXT NOT NULL,                  -- 消息内容
    message_type VARCHAR(20) DEFAULT 'TEXT', -- 消息类型：TEXT/VOICE/IMAGE/FILE
    file_url VARCHAR(500),                   -- 文件URL（如果是文件消息）
    metadata JSONB,                         -- 元数据（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. 用户反馈表 (user_feedback)

```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,                           -- 用户ID
    conversation_id UUID,                   -- 对话ID
    message_id UUID,                        -- 消息ID
    role_id UUID,                           -- 角色ID
    feedback_type VARCHAR(50),              -- 反馈类型：quality/relevance/helpfulness
    rating INTEGER,                          -- 评分（1-5）
    content TEXT,                           -- 反馈内容
    sentiment VARCHAR(20),                  -- 情感标签：positive/negative/neutral
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 四、如何使用数据库

### 1. 通过JPA Repository（推荐）✅

系统使用Spring Data JPA，通过Repository接口操作数据库。

#### 基本操作

```java
// 1. 注入Repository
@Autowired
private UserRepository userRepository;

// 2. 保存数据
User user = new User();
user.setUsername("test_user");
user.setEmail("test@example.com");
userRepository.save(user);

// 3. 查询数据
Optional<User> user = userRepository.findByUsername("test_user");
if (user.isPresent()) {
    System.out.println("找到用户: " + user.get().getUsername());
}

// 4. 更新数据
User user = userRepository.findById(userId).orElseThrow();
user.setEmail("new_email@example.com");
userRepository.save(user);  // 自动更新

// 5. 删除数据
userRepository.deleteById(userId);

// 6. 查询所有
List<User> allUsers = userRepository.findAll();
```

#### 自定义查询方法

Repository接口支持方法名自动生成查询：

```java
// UserRepository.java
public interface UserRepository extends JpaRepository<User, UUID> {
    // 根据用户名查找
    Optional<User> findByUsername(String username);
    
    // 根据邮箱查找
    Optional<User> findByEmail(String email);
    
    // 检查是否存在
    boolean existsByUsername(String username);
    
    // 复杂查询（使用@Query注解）
    @Query("SELECT u FROM User u WHERE u.createdAt > :date")
    List<User> findRecentUsers(@Param("date") LocalDateTime date);
}
```

### 2. 在Service中使用

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    /**
     * 创建用户
     */
    public User createUser(String username, String email, String password) {
        // 检查用户名是否已存在
        if (userRepository.existsByUsername(username)) {
            throw new BusinessException("用户名已存在");
        }
        
        // 创建用户
        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setPasswordHash(PasswordUtil.hash(password));
        
        return userRepository.save(user);
    }
    
    /**
     * 根据用户名查找用户
     */
    public User getUserByUsername(String username) {
        return userRepository.findByUsername(username)
            .orElseThrow(() -> new ResourceNotFoundException("用户不存在"));
    }
    
    /**
     * 更新用户信息
     */
    @Transactional
    public User updateUser(UUID userId, String email) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("用户不存在"));
        
        user.setEmail(email);
        return userRepository.save(user);
    }
}
```

### 3. 在Controller中使用

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody CreateUserRequest request) {
        User user = userService.createUser(
            request.getUsername(),
            request.getEmail(),
            request.getPassword()
        );
        return ResponseEntity.ok(user);
    }
    
    @GetMapping("/{username}")
    public ResponseEntity<User> getUser(@PathVariable String username) {
        User user = userService.getUserByUsername(username);
        return ResponseEntity.ok(user);
    }
}
```

---

## 五、常用操作示例

### 1. 用户操作

```java
// 创建用户
User user = new User();
user.setUsername("alice");
user.setEmail("alice@example.com");
user.setPasswordHash(PasswordUtil.hash("password123"));
userRepository.save(user);

// 查找用户
Optional<User> user = userRepository.findByUsername("alice");

// 检查用户是否存在
boolean exists = userRepository.existsByUsername("alice");

// 更新用户
User user = userRepository.findByUsername("alice").orElseThrow();
user.setEmail("new_email@example.com");
userRepository.save(user);

// 删除用户
userRepository.deleteByUsername("alice");
```

### 2. 角色操作

```java
// 查找所有内置角色
List<Role> builtinRoles = roleRepository.findByRoleType(Role.RoleType.BUILTIN);

// 查找用户的自定义角色
List<Role> customRoles = roleRepository.findByUserId(userId);

// 创建自定义角色
Role role = new Role();
role.setName("心理咨询师");
role.setRoleType(Role.RoleType.CUSTOM);
role.setUserId(userId);
role.setSystemPrompt("你是一位专业的心理咨询师...");
roleRepository.save(role);
```

### 3. 对话操作

```java
// 创建对话
Conversation conversation = new Conversation();
conversation.setUserId(userId);
conversation.setRoleId(roleId);
conversation.setContextId(UUID.randomUUID().toString());
conversationRepository.save(conversation);

// 查找用户的对话
List<Conversation> conversations = conversationRepository.findByUserId(userId);

// 查找对话（根据上下文ID）
Optional<Conversation> conv = conversationRepository.findByContextId(contextId);
```

### 4. 消息操作

```java
// 保存消息
Message message = new Message();
message.setConversationId(conversationId);
message.setRole(Message.MessageRole.USER);
message.setContent("你好");
message.setMessageType(Message.MessageType.TEXT);
messageRepository.save(message);

// 获取对话的所有消息（按时间排序）
List<Message> messages = messageRepository
    .findByConversationIdOrderByCreatedAtAsc(conversationId);

// 获取最近的消息
List<Message> recentMessages = messageRepository
    .findRecentMessages(conversationId);
```

### 5. 复杂查询示例

```java
// 使用@Query注解自定义查询
@Query("SELECT m FROM Message m WHERE m.conversationId = :convId " +
       "AND m.createdAt > :since ORDER BY m.createdAt DESC")
List<Message> findRecentMessagesSince(
    @Param("convId") UUID conversationId,
    @Param("since") LocalDateTime since
);

// 统计查询
@Query("SELECT COUNT(m) FROM Message m WHERE m.conversationId = :convId")
long countMessages(@Param("convId") UUID conversationId);

// 分组统计
@Query("SELECT m.role, COUNT(m) FROM Message m " +
       "WHERE m.conversationId = :convId GROUP BY m.role")
List<Object[]> countMessagesByRole(@Param("convId") UUID conversationId);
```

---

## 六、数据库迁移

### Flyway数据库迁移

系统使用Flyway管理数据库版本，迁移脚本在：
`backend/src/main/resources/db/migration/`

**迁移文件命名规则**:
- `V1__init_schema.sql` - 版本1，初始化表结构
- `V2__optimize_indexes.sql` - 版本2，优化索引
- `V3__add_password_hash.sql` - 版本3，添加密码字段
- `V4__create_user_feedback_table.sql` - 版本4，创建反馈表

**自动执行**:
- 启动Spring Boot应用时，Flyway会自动执行未执行的迁移脚本
- 按版本号顺序执行
- 已执行的脚本不会重复执行

**手动执行迁移**:
```bash
# 查看迁移状态
mvn flyway:info

# 执行迁移
mvn flyway:migrate

# 回滚（需要Pro版本）
mvn flyway:undo
```

---

## 七、连接测试

### 1. 使用psql命令行

```bash
# 连接数据库
psql -U postgres -d kinlin_ai

# 或者指定主机和端口
psql -h localhost -p 5432 -U postgres -d kinlin_ai

# 查看所有表
\dt

# 查看表结构
\d users

# 查询数据
SELECT * FROM users;

# 退出
\q
```

### 2. 使用pgAdmin（图形界面）

1. **下载安装pgAdmin**
   - 访问 https://www.pgadmin.org/download/
   - 下载并安装

2. **连接数据库**
   - 打开pgAdmin
   - 右键 "Servers" → "Create" → "Server"
   - 填写连接信息：
     - Name: Kinlin AI
     - Host: localhost
     - Port: 5432
     - Database: kinlin_ai
     - Username: postgres
     - Password: your_password

3. **查看数据**
   - 展开数据库 → Schemas → public → Tables
   - 右键表 → "View/Edit Data" → "All Rows"

### 3. 测试连接（Java代码）

```java
@SpringBootTest
class DatabaseConnectionTest {
    
    @Autowired
    private DataSource dataSource;
    
    @Test
    void testConnection() throws SQLException {
        try (Connection conn = dataSource.getConnection()) {
            assertNotNull(conn);
            assertTrue(conn.isValid(5));
            System.out.println("数据库连接成功！");
        }
    }
}
```

### 4. 测试Repository

```java
@SpringBootTest
class UserRepositoryTest {
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void testSaveUser() {
        User user = new User();
        user.setUsername("test_user");
        user.setEmail("test@example.com");
        
        User saved = userRepository.save(user);
        assertNotNull(saved.getId());
        System.out.println("用户保存成功，ID: " + saved.getId());
    }
    
    @Test
    void testFindUser() {
        Optional<User> user = userRepository.findByUsername("test_user");
        assertTrue(user.isPresent());
        System.out.println("找到用户: " + user.get().getUsername());
    }
}
```

---

## 八、常见问题

### Q1: 连接数据库失败？

**错误**: `Connection refused` 或 `Connection timeout`

**解决方案**:
1. 检查PostgreSQL是否启动
   ```bash
   # Windows
   services.msc  # 查看PostgreSQL服务
   
   # Linux
   sudo systemctl status postgresql
   ```

2. 检查端口是否正确（默认5432）
   ```bash
   # 检查端口是否被占用
   netstat -an | grep 5432
   ```

3. 检查防火墙设置
   ```bash
   # Linux
   sudo ufw allow 5432
   ```

4. 检查配置文件中的连接信息
   ```yaml
   url: jdbc:postgresql://localhost:5432/kinlin_ai
   username: postgres
   password: your_password  # 确认密码正确
   ```

### Q2: 表不存在？

**错误**: `relation "users" does not exist`

**解决方案**:
1. 检查JPA配置
   ```yaml
   jpa:
     hibernate:
       ddl-auto: update  # 自动创建/更新表
   ```

2. 手动执行迁移脚本
   ```bash
   psql -U postgres -d kinlin_ai -f backend/src/main/resources/db/migration/V1__init_schema.sql
   ```

3. 检查数据库名称是否正确

### Q3: 密码错误？

**错误**: `password authentication failed`

**解决方案**:
1. 确认密码是否正确
2. 重置密码
   ```sql
   -- 使用psql连接
   psql -U postgres
   
   -- 修改密码
   ALTER USER postgres WITH PASSWORD 'new_password';
   ```

3. 更新配置文件中的密码

### Q4: 如何备份数据库？

```bash
# 备份整个数据库
pg_dump -U postgres -d kinlin_ai > backup.sql

# 备份特定表
pg_dump -U postgres -d kinlin_ai -t users > users_backup.sql

# 恢复数据库
psql -U postgres -d kinlin_ai < backup.sql
```

### Q5: 如何查看数据库大小？

```sql
-- 查看数据库大小
SELECT pg_size_pretty(pg_database_size('kinlin_ai'));

-- 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Q6: 如何优化数据库性能？

1. **添加索引**（已完成）
   - 查看 `V2__optimize_indexes.sql`

2. **连接池配置**
   ```yaml
   hikari:
     maximum-pool-size: 20  # 根据服务器配置调整
     minimum-idle: 5
   ```

3. **查询优化**
   - 使用索引字段查询
   - 避免全表扫描
   - 使用分页查询

---

## 九、最佳实践

### 1. 事务管理

```java
@Service
@Transactional  // 类级别事务
public class UserService {
    
    @Transactional(readOnly = true)  // 只读事务
    public User getUser(UUID id) {
        return userRepository.findById(id).orElseThrow();
    }
    
    @Transactional  // 写事务
    public User createUser(User user) {
        return userRepository.save(user);
    }
}
```

### 2. 异常处理

```java
public User getUserById(UUID id) {
    return userRepository.findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("用户不存在: " + id));
}
```

### 3. 分页查询

```java
// 使用Pageable
Pageable pageable = PageRequest.of(0, 10);  // 第0页，每页10条
Page<User> users = userRepository.findAll(pageable);

// 自定义分页
@Query("SELECT u FROM User u WHERE u.createdAt > :date")
Page<User> findRecentUsers(@Param("date") LocalDateTime date, Pageable pageable);
```

### 4. 批量操作

```java
// 批量保存
List<User> users = Arrays.asList(user1, user2, user3);
userRepository.saveAll(users);

// 批量删除
userRepository.deleteAllById(userIds);
```

---

## 十、快速参考

### 常用SQL命令

```sql
-- 连接数据库
\c kinlin_ai

-- 查看所有表
\dt

-- 查看表结构
\d users

-- 查看所有用户
SELECT * FROM users;

-- 统计用户数量
SELECT COUNT(*) FROM users;

-- 查看最近的对话
SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;

-- 查看对话的消息数
SELECT c.id, COUNT(m.id) as message_count
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id;
```

### 常用Repository方法

```java
// 基本CRUD
save(entity)              // 保存
findById(id)             // 根据ID查找
findAll()                // 查找所有
deleteById(id)           // 删除
count()                  // 统计数量

// 自定义查询
findByUsername(name)     // 根据用户名查找
existsByUsername(name)   // 检查是否存在
findByUserIdAndRoleId()  // 多条件查询
```

---

## 十一、总结

### 数据库使用流程

1. **安装PostgreSQL** ✅
   - 使用Docker（推荐）或本地安装

2. **配置连接** ✅
   - 修改 `application.yml` 中的数据库连接信息

3. **启动应用** ✅
   - Spring Boot会自动创建表（如果不存在）

4. **使用Repository** ✅
   - 在Service中注入Repository
   - 调用Repository方法操作数据

5. **测试验证** ✅
   - 使用单元测试或直接查询数据库

### 关键点

- ✅ **数据库是必须的** - 系统核心功能依赖数据库
- ✅ **JPA自动管理** - 表结构自动创建和更新
- ✅ **Repository模式** - 通过接口操作数据库，无需写SQL
- ✅ **事务管理** - 使用`@Transactional`注解

---

**最后更新**: 2024年


