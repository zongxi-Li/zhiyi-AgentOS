<template>
  <div class="role-view">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <h2>角色管理</h2>
          <el-button type="primary" @click="showCreateDialog = true" :icon="Plus">
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

    <!-- 创建角色对话框 -->
    <CreateRoleDialog
      v-model="showCreateDialog"
      @created="handleRoleCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useRoleStore } from '@/stores/role'
import RoleCard from '@/components/RoleCard.vue'
import CreateRoleDialog from '@/components/CreateRoleDialog.vue'
import { useChatStore } from '@/stores/chat'

const roleStore = useRoleStore()
const chatStore = useChatStore()
const showCreateDialog = ref(false)

const handleSelectRole = (role: any) => {
  roleStore.selectRole(role)
  chatStore.setRole(role.id)
  ElMessage.success(`已切换到角色: ${role.name}`)
}

const handleEditRole = (role: any) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中')
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

const handleRoleCreated = () => {
  roleStore.loadCustomRoles()
}

onMounted(async () => {
  await roleStore.loadBuiltinRoles()
  await roleStore.loadCustomRoles()
})
</script>

<style scoped>
.role-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h2 {
  margin: 0;
}

.role-section {
  margin-bottom: 40px;
}

.role-section h3 {
  margin-bottom: 20px;
  color: #303133;
  font-size: 18px;
}
</style>

