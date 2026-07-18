import { ref } from 'vue'
import { getColorScheme, type ColorSchemeId } from '@/themes/presets'

const currentScheme = ref<ColorSchemeId>('blue-purple')

function applySchemeVariables(schemeId: ColorSchemeId): void {
  const scheme = getColorScheme(schemeId)
  const root = document.documentElement
  for (const [key, value] of Object.entries(scheme.variables)) {
    root.style.setProperty(key, value)
  }
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
    applySchemeVariables('blue-purple')
    return
  }
  try {
    const parsed = JSON.parse(saved)
    const schemeId: ColorSchemeId = parsed.colorScheme || 'blue-purple'
    applySchemeVariables(schemeId)
  } catch {
    applySchemeVariables('blue-purple')
  }
}

export { type ColorSchemeId }
