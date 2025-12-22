<template>
  <el-card 
    class="role-card" 
    :class="{ 'selected': isSelected }"
    @click="handleClick"
    shadow="hover"
  >
    <div class="role-header">
      <h3>{{ role.name }}</h3>
      <el-tag :type="role.roleType === 'BUILTIN' ? 'success' : 'info'" size="small">
        {{ role.roleType === 'BUILTIN' ? '内置' : '自定义' }}
      </el-tag>
    </div>
    <p class="role-description">{{ role.description }}</p>
    <div v-if="role.roleType === 'CUSTOM'" class="role-actions">
      <el-button 
        type="primary" 
        size="small" 
        @click.stop="handleEdit"
        :icon="Edit"
      >
        编辑
      </el-button>
      <el-button 
        type="danger" 
        size="small" 
        @click.stop="handleDelete"
        :icon="Delete"
      >
        删除
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Edit, Delete } from '@element-plus/icons-vue'
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

<style scoped>
.role-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.role-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.role-card.selected {
  border: 2px solid #409eff;
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.role-header h3 {
  margin: 0;
  font-size: 18px;
}

.role-description {
  color: #666;
  font-size: 14px;
  margin: 10px 0;
  min-height: 40px;
}

.role-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
</style>

