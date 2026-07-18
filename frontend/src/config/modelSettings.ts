export type ModelProviderId = 'system' | 'qwen' | 'deepseek' | 'openai' | 'custom'
export type ReasoningEffort = 'off' | 'low' | 'medium' | 'high'

export interface ModelProviderPreset {
  id: ModelProviderId
  name: string
  description: string
  baseUrl: string
  models: string[]
}

export interface ModelSettings {
  provider: ModelProviderId
  apiKey: string
  baseUrl: string
  models: string[]
  selectedModel: string
  reasoningEffort: ReasoningEffort
}

export const MODEL_SETTINGS_KEY = 'kinlin.model_settings'
export const MODEL_SETTINGS_EVENT = 'kinlin-model-settings-change'
export const SYSTEM_FALLBACK_MODELS = ['deepseek-chat', 'deepseek-v4-flash', 'deepseek-v4-pro']

export const modelProviderPresets: ModelProviderPreset[] = [
  {
    id: 'system',
    name: '系统默认',
    description: '使用服务端环境变量中已配置的模型',
    baseUrl: '',
    models: [...SYSTEM_FALLBACK_MODELS]
  },
  {
    id: 'qwen',
    name: '通义千问',
    description: '阿里云百炼 OpenAI 兼容接口',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen3.7-plus', 'qwen3.7-max', 'qwen3.6-flash']
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek 官方 OpenAI 兼容接口',
    baseUrl: 'https://api.deepseek.com/v1',
    models: ['deepseek-v4-pro', 'deepseek-v4-flash']
  },
  {
    id: 'openai',
    name: 'OpenAI 兼容',
    description: 'OpenAI 官方或兼容 Chat Completions 的服务',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-5.2', 'gpt-5-mini']
  },
  {
    id: 'custom',
    name: '自定义',
    description: '连接自托管或其他 OpenAI 兼容服务',
    baseUrl: '',
    models: []
  }
]

export const reasoningOptions: Array<{ value: ReasoningEffort; label: string; shortLabel: string }> = [
  { value: 'off', label: '关闭思考', shortLabel: '关' },
  { value: 'low', label: '低度思考', shortLabel: '低' },
  { value: 'medium', label: '中度思考', shortLabel: '中' },
  { value: 'high', label: '高度思考', shortLabel: '高' }
]

export function getDefaultModelSettings(): ModelSettings {
  return {
    provider: 'system',
    apiKey: '',
    baseUrl: '',
    models: [...SYSTEM_FALLBACK_MODELS],
    selectedModel: SYSTEM_FALLBACK_MODELS[0],
    reasoningEffort: 'off'
  }
}

export function loadModelSettings(): ModelSettings {
  const fallback = getDefaultModelSettings()
  try {
    const raw = localStorage.getItem(MODEL_SETTINGS_KEY)
    if (!raw) return fallback
    const parsed = JSON.parse(raw) as Partial<ModelSettings>
    const provider = modelProviderPresets.some(item => item.id === parsed.provider)
      ? parsed.provider as ModelProviderId
      : fallback.provider
    const storedModels = Array.isArray(parsed.models)
      ? parsed.models.filter(model => typeof model === 'string' && model.trim()).map(model => model.trim())
      : fallback.models
    const models = provider === 'system' && (
      storedModels.length === 0 || storedModels.includes('系统默认')
    )
      ? [...SYSTEM_FALLBACK_MODELS]
      : [...new Set(storedModels)]
    const storedSelectedModel = parsed.selectedModel?.trim() || ''
    const selectedModel = models.includes(storedSelectedModel)
      ? storedSelectedModel
      : models[0] || fallback.selectedModel

    return {
      ...fallback,
      ...parsed,
      provider,
      models: models.length ? models : fallback.models,
      selectedModel,
      reasoningEffort: reasoningOptions.some(item => item.value === parsed.reasoningEffort)
        ? parsed.reasoningEffort as ReasoningEffort
        : fallback.reasoningEffort
    }
  } catch {
    return fallback
  }
}

export function saveModelSettings(settings: ModelSettings): void {
  const selectedModel = settings.selectedModel.trim()
  const models = [...new Set([
    ...settings.models.map(model => model.trim()).filter(Boolean),
    ...(selectedModel ? [selectedModel] : [])
  ])]
  const normalized: ModelSettings = {
    ...settings,
    apiKey: settings.apiKey.trim(),
    baseUrl: settings.baseUrl.trim().replace(/\/$/, ''),
    models,
    selectedModel
  }
  localStorage.setItem(MODEL_SETTINGS_KEY, JSON.stringify(normalized))
  window.dispatchEvent(new CustomEvent(MODEL_SETTINGS_EVENT, { detail: normalized }))
}

export function applyProviderPreset(settings: ModelSettings, provider: ModelProviderId): ModelSettings {
  const preset = modelProviderPresets.find(item => item.id === provider) || modelProviderPresets[0]
  return {
    ...settings,
    provider,
    baseUrl: preset.baseUrl,
    models: [...preset.models],
    selectedModel: preset.models[0] || '',
    apiKey: provider === 'system' ? '' : settings.apiKey
  }
}

export function toModelRequestSettings(settings: ModelSettings) {
  if (settings.provider === 'system') {
    return {
      model: settings.selectedModel === '系统默认' ? undefined : settings.selectedModel,
      reasoningEffort: settings.reasoningEffort
    }
  }
  return {
    model: settings.selectedModel,
    baseUrl: settings.baseUrl,
    apiKey: settings.apiKey,
    reasoningEffort: settings.reasoningEffort
  }
}
