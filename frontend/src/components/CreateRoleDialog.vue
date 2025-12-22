<template>
  <el-dialog
    v-model="visible"
    title="创建自定义角色"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="角色名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入角色名称" />
      </el-form-item>

      <el-form-item label="角色描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入角色描述"
        />
      </el-form-item>

      <el-form-item label="系统提示词" prop="systemPrompt">
        <el-input
          v-model="form.systemPrompt"
          type="textarea"
          :rows="5"
          placeholder="请输入系统提示词，用于定义角色的对话风格和专业知识"
        />
      </el-form-item>

      <el-form-item label="对话风格">
        <el-input
          v-model="form.dialogueStyleText"
          type="textarea"
          :rows="3"
          placeholder="例如：正式度、温度、技术水平等（JSON格式）"
        />
      </el-form-item>

      <el-form-item label="性格特点">
        <el-input
          v-model="form.personalityText"
          type="textarea"
          :rows="3"
          placeholder="例如：耐心、专业、富有创意等（JSON格式）"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        创建
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useRoleStore } from '@/stores/role'
import type { RoleCreateRequest } from '@/services/api/role'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'created', role: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const roleStore = useRoleStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const form = reactive({
  name: '',
  description: '',
  systemPrompt: '',
  dialogueStyleText: '',
  personalityText: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' }
  ],
  systemPrompt: [
    { required: true, message: '请输入系统提示词', trigger: 'blur' }
  ]
}

const handleClose = () => {
  formRef.value?.resetFields()
  visible.value = false
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const request: RoleCreateRequest = {
          name: form.name,
          description: form.description,
          systemPrompt: form.systemPrompt,
          dialogueStyle: parseJson(form.dialogueStyleText),
          personality: parseJson(form.personalityText)
        }

        const role = await roleStore.createRole(request)
        ElMessage.success('角色创建成功')
        emit('created', role)
        handleClose()
      } catch (error: any) {
        ElMessage.error(error.message || '创建角色失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const parseJson = (text: string): any => {
  if (!text || !text.trim()) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return undefined
  }
}

watch(() => props.modelValue, (val) => {
  if (val) {
    // 重置表单
    form.name = ''
    form.description = ''
    form.systemPrompt = ''
    form.dialogueStyleText = ''
    form.personalityText = ''
  }
})
</script>


