<template>
  <div 
    class="role-card" 
    :class="{ 'selected': isSelected }"
    @click="handleClick"
  >
    <div class="card-bg"></div>
    <div class="card-content">
      <div class="card-header">
        <div class="avatar-wrapper" :style="{ background: roleGradient }">
          <span class="avatar-text">{{ role.name.charAt(0) }}</span>
        </div>
        <div class="role-meta">
          <div class="name-row">
            <h3>{{ role.name }}</h3>
            <el-tag 
              :type="role.roleType === 'BUILTIN' ? 'primary' : 'success'" 
              size="small"
              effect="dark"
              class="role-tag"
            >
              {{ role.roleType === 'BUILTIN' ? '内置' : '自定义' }}
            </el-tag>
          </div>
          <span class="role-id">ID: {{ role.id.substring(0, 8) }}</span>
        </div>
      </div>
      
      <div class="card-body">
        <p class="description">{{ role.description || '暂无描述' }}</p>
      </div>

      <div class="card-footer">
        <div class="status-indicator" :class="{ active: isSelected }">
          <span class="dot"></span>
          {{ isSelected ? '当前使用' : '点击切换' }}
        </div>
        
        <div v-if="role.roleType === 'CUSTOM'" class="actions">
          <el-tooltip content="编辑角色" placement="top" :show-after="500">
            <button class="icon-btn edit" @click.stop="handleEdit">
              <el-icon><EditPen /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="删除角色" placement="top" :show-after="500">
            <button class="icon-btn delete" @click.stop="handleDelete">
              <el-icon><Delete /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { EditPen, Delete } from '@element-plus/icons-vue'
import type { Role } from '@/services/api/role'

interface Props {
  role: Role
  selected?: boolean
}

interface Emits {
  (e: 'select', role: Role): void
  (e: 'edit', role: Role): void
  (e: 'delete', role: Role): void
}

const props = withDefaults(defineProps<Props>(), {
  selected: false
})

const emit = defineEmits<Emits>()

const isSelected = computed(() => props.selected)

// Generate gradient based on role ID/Type
const roleGradient = computed(() => {
  if (props.role.roleType === 'BUILTIN') {
    const gradients = [
      'linear-gradient(135deg, #6366f1, #8b5cf6)',
      'linear-gradient(135deg, #3b82f6, #06b6d4)',
      'linear-gradient(135deg, #f59e0b, #d97706)',
      'linear-gradient(135deg, #10b981, #3b82f6)'
    ]
    const index = props.role.name.length % gradients.length
    return gradients[index]
  } else {
    return 'linear-gradient(135deg, #ec4899, #8b5cf6)'
  }
})

const handleClick = () => {
  emit('select', props.role)
}

const handleEdit = () => {
  emit('edit', props.role)
}

const handleDelete = () => {
  emit('delete', props.role)
}
</script>

<style scoped lang="scss">
.role-card {
  position: relative;
  height: 200px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(31, 38, 135, 0.1);
    background: rgba(255, 255, 255, 0.8);
    border-color: rgba(255, 255, 255, 0.8);
    
    .card-footer {
      background: rgba(255, 255, 255, 0.5);
    }
  }
  
  &.selected {
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2), 0 8px 24px rgba(99, 102, 241, 0.15);
    background: rgba(255, 255, 255, 0.9);
    
    .status-indicator {
      color: #6366f1;
      
      .dot {
        background: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
      }
    }
  }
}

.card-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.card-header {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  
  .avatar-wrapper {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 20px;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .role-meta {
    flex: 1;
    min-width: 0;
    
    .name-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
      
      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 700;
        color: #303133;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .role-tag {
        border: none;
        height: 20px;
        padding: 0 8px;
      }
    }
    
    .role-id {
      font-size: 12px;
      color: #909399;
      font-family: monospace;
    }
  }
}

.card-body {
  flex: 1;
  
  .description {
    margin: 0;
    font-size: 14px;
    line-height: 1.6;
    color: #606266;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.card-footer {
  margin: 0 -20px -20px -20px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.3);
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.3s;
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 500;
    color: #909399;
    
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #dcdfe6;
      transition: all 0.3s;
    }
  }
  
  .actions {
    display: flex;
    gap: 8px;
    
    .icon-btn {
      width: 28px;
      height: 28px;
      border-radius: 8px;
      border: none;
      background: transparent;
      color: #909399;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      
      &:hover {
        background: rgba(0, 0, 0, 0.05);
        
        &.edit { color: #409eff; }
        &.delete { color: #f56c6c; }
      }
    }
  }
}
</style>
