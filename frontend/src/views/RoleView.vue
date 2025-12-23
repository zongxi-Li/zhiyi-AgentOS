<template>
  <div class="role-view">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <h2>角色管理</h2>
          <el-button type="primary" @click="handleCreateRole" :icon="Plus">
            创建自定义角色
          </el-button>
        </div>
      </el-header>

      <el-main>
        <!-- 内置角色 -->
        <div class="role-section">
          <h3>内置角色</h3>
          <el-row :gutter="20" v-loading="roleStore.loading">
            <el-col
              v-for="role in roleStore.builtinRoles"
              :key="role.id"
              :xs="24" :sm="12" :md="8" :lg="6"
            >
              <RoleCard
                :role="role"
                :selected="roleStore.currentRole?.id === role.id"
                @select="handleSelectRole"
              />
            </el-col>
          </el-row>
        </div>

        <!-- 自定义角色 -->
        <div class="role-section" v-if="roleStore.customRoles.length > 0">
          <h3>自定义角色</h3>
          <el-row :gutter="20" v-loading="roleStore.loading">
            <el-col
              v-for="role in roleStore.customRoles"
              :key="role.id"
              :xs="24" :sm="12" :md="8" :lg="6"
            >
              <RoleCard
                :role="role"
                :selected="roleStore.currentRole?.id === role.id"
                @select="handleSelectRole"
                @edit="handleEditRole"
                @delete="handleDeleteRole"
              />
            </el-col>
          </el-row>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-if="!roleStore.loading && roleStore.builtinRoles.length === 0"
          description="暂无角色数据"
        />
      </el-main>
    </el-container>

    <!-- 编辑角色对话框 -->
    <EditRoleDialog
      v-model="showEditDialog"
      :role="editingRole"
      @updated="handleRoleUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'
import RoleCard from '@/components/RoleCard.vue'
import EditRoleDialog from '@/components/EditRoleDialog.vue'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const roleStore = useRoleStore()
const chatStore = useChatStore()

const handleSelectRole = (role: any) => {
  roleStore.selectRole(role)
  chatStore.setRole(role.id)
  ElMessage.success(`已切换到角色: ${role.name}`)
}

const handleCreateRole = () => {
  router.push('/create-role')
}

const showEditDialog = ref(false)
const editingRole = ref<any>(null)

const handleEditRole = (role: any) => {
  editingRole.value = role
  showEditDialog.value = true
}

const handleRoleUpdated = () => {
  roleStore.loadCustomRoles()
}

const handleDeleteRole = async (role: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色"${role.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await roleStore.deleteRole(role.id)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

onMounted(async () => {
  await roleStore.loadBuiltinRoles()
  await roleStore.loadCustomRoles()
})
</script>

<style scoped lang="scss">
.role-view {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background: var(--bg-color-page);
}

.header {
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color-base);
  padding: 0 var(--spacing-xl);
  box-shadow: var(--box-shadow-base);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  
  h2 {
    margin: 0;
    font-size: var(--font-size-2xl);
    font-weight: 700;
    color: var(--text-color-primary);
    letter-spacing: -0.01em;
  }
}

:deep(.el-main) {
  padding: var(--spacing-xl);
  overflow-y: auto;
}

.role-section {
  margin-bottom: var(--spacing-2xl);
  
  h3 {
    margin-bottom: var(--spacing-lg);
    color: var(--text-color-primary);
    font-size: var(--font-size-xl);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    letter-spacing: -0.01em;
    
    &::before {
      content: '';
      width: 4px;
      height: 20px;
      background: var(--primary-color);
      border-radius: 2px;
    }
  }
}
</style>

