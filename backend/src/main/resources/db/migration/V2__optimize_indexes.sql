-- 数据库性能优化：添加更多索引
-- 执行时间：2024年

-- 用户表索引优化
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at);

-- 对话表索引优化
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_role ON conversations(role_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_role ON conversations(user_id, role_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at);

-- 消息表索引优化（已有部分索引，补充）
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at);

-- 角色表索引优化（已有部分索引，补充）
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_created ON roles(created_at);

-- 复合索引优化（用于常见查询场景）
-- 用户对话查询：按用户ID和更新时间排序
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);

-- 消息查询：按对话ID和创建时间排序（已有，但确保存在）
-- CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at);

-- 全文搜索索引（PostgreSQL）
-- 如果需要全文搜索功能，可以创建GIN索引
-- CREATE INDEX IF NOT EXISTS idx_messages_content_gin ON messages USING gin(to_tsvector('english', content));
-- CREATE INDEX IF NOT EXISTS idx_roles_description_gin ON roles USING gin(to_tsvector('english', description));

-- 分析表统计信息（优化查询计划）
ANALYZE users;
ANALYZE roles;
ANALYZE conversations;
ANALYZE messages;

