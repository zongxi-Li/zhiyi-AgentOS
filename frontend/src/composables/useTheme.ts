import { ref } from 'vue'
import { getColorScheme, type ColorSchemeId } from '@/themes/presets'

const currentScheme = ref<ColorSchemeId>('codex-dark')
const CODEX_DARK_MIGRATION_KEY = 'theme.codex_dark_v1'

function applySchemeVariables(schemeId: ColorSchemeId): void {
  const scheme = getColorScheme(schemeId)
  const root = document.documentElement
  for (const [key, value] of Object.entries(scheme.variables)) {
    root.style.setProperty(key, value)
  }
  root.dataset.colorScheme = scheme.id
  root.style.colorScheme = scheme.id === 'codex-dark' ? 'dark' : 'light'
  document.body.style.backgroundImage = scheme.bodyBackground
  currentScheme.value = scheme.id
}

export function useTheme() {
  function applyColorScheme(schemeId: ColorSchemeId): void {
    applySchemeVariables(schemeId)
  }

  return { currentScheme, applyColorScheme }
}

export function initTheme(): void {
  const saved = localStorage.getItem('appSettings')
  if (!saved) {
    localStorage.setItem(CODEX_DARK_MIGRATION_KEY, '1')
    applySchemeVariables('codex-dark')
    return
  }
  try {
    const parsed = JSON.parse(saved)
    if (!localStorage.getItem(CODEX_DARK_MIGRATION_KEY)) {
      parsed.colorScheme = 'codex-dark'
      localStorage.setItem('appSettings', JSON.stringify(parsed))
      localStorage.setItem(CODEX_DARK_MIGRATION_KEY, '1')
    }
    const schemeId: ColorSchemeId = parsed.colorScheme || 'codex-dark'
    applySchemeVariables(schemeId)
  } catch {
    applySchemeVariables('codex-dark')
  }
}

export { type ColorSchemeId }
