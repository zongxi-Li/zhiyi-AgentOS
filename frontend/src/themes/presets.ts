export type ColorSchemeId = 'claude-warm' | 'tea-green' | 'blue-purple'

export interface ColorScheme {
  id: ColorSchemeId
  name: string
  nameEn: string
  previewColor: string
  variables: Record<string, string>
  bodyBackground: string
}

const claudeWarm: ColorScheme = {
  id: 'claude-warm',
  name: 'Claude 暖橙',
  nameEn: 'Claude Warm',
  previewColor: '#D97757',
  bodyBackground:
    'linear-gradient(180deg, rgba(255, 255, 255, 0.5), rgba(250, 249, 245, 0.9)), ' +
    'radial-gradient(at 14% 0%, rgba(217, 119, 87, 0.06) 0px, transparent 40%), ' +
    'radial-gradient(at 90% 12%, rgba(191, 141, 92, 0.05) 0px, transparent 38%)',
  variables: {
    '--primary-color': '#D97757',
    '--primary-hover': '#C15F3C',
    '--primary-active': '#A84B2F',
    '--primary-fade': 'rgba(217, 119, 87, 0.1)',
    '--primary-line': 'rgba(217, 119, 87, 0.24)',

    '--accent-color': '#B07B4F',
    '--accent-fade': 'rgba(176, 123, 79, 0.1)',

    '--bg-app': '#FAF9F5',
    '--bg-sidebar': '#F5F3EC',
    '--bg-card': '#FFFFFF',
    '--bg-panel': '#F5F4EE',
    '--bg-input': '#F0EEE6',
    '--bg-glass': 'rgba(255, 255, 255, 0.7)',
    '--app-layout-bg':
      'linear-gradient(180deg, rgba(255, 255, 255, 0.55), rgba(250, 249, 245, 0.98)), var(--bg-app)',
    '--sidebar-bg': 'rgba(245, 243, 236, 0.94)',
    '--drawer-bg': 'rgba(250, 249, 245, 0.97)',
    '--sidebar-border': 'rgba(228, 223, 210, 0.7)',
    '--scrollbar-thumb': 'rgba(217, 119, 87, 0.18)',
    '--scrollbar-thumb-hover': 'rgba(217, 119, 87, 0.28)',

    '--text-primary': '#1F1E1D',
    '--text-regular': '#3D3A34',
    '--text-secondary': '#73706B',
    '--text-disabled': '#ABA79E',

    '--border-light': '#E9E4D8',
    '--border-hover': '#D9D2C2',
    '--border-focus': 'rgba(217, 119, 87, 0.42)',

    '--success': '#4A7C59',
    '--warning': '#B5852F',
    '--danger': '#C0533F',
    '--info': '#7A6E5D',

    '--shadow-sm': '0 1px 2px rgba(31, 30, 29, 0.04)',
    '--shadow-md': '0 8px 24px rgba(31, 30, 29, 0.06)',
    '--shadow-lg': '0 18px 48px rgba(31, 30, 29, 0.08)',
    '--shadow-glow': '0 12px 28px rgba(217, 119, 87, 0.16)',

    '--el-color-primary': '#D97757',
    '--el-color-primary-light-3': '#E39F87',
    '--el-color-primary-light-5': '#ECBBA9',
    '--el-color-primary-light-7': '#F4D7CB',
    '--el-color-primary-light-8': '#F8E5DC',
    '--el-color-primary-light-9': '#FCF2ED',
    '--el-color-primary-dark-2': '#C15F3C',
  },
}

const teaGreen: ColorScheme = {
  id: 'tea-green',
  name: '茶绿',
  nameEn: 'Tea Green',
  previewColor: '#3f6b63',
  bodyBackground:
    'linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(246, 247, 244, 0.96)), ' +
    'radial-gradient(at 12% 0%, rgba(63, 107, 99, 0.08) 0px, transparent 36%), ' +
    'radial-gradient(at 92% 16%, rgba(111, 102, 143, 0.08) 0px, transparent 34%)',
  variables: {
    '--primary-color': '#3f6b63',
    '--primary-hover': '#345b54',
    '--primary-active': '#294943',
    '--primary-fade': 'rgba(63, 107, 99, 0.1)',
    '--primary-line': 'rgba(63, 107, 99, 0.22)',

    '--accent-color': '#6f668f',
    '--accent-fade': 'rgba(111, 102, 143, 0.1)',

    '--bg-app': '#f6f7f4',
    '--bg-sidebar': '#fbfbf8',
    '--bg-card': '#ffffff',
    '--bg-panel': '#fbfcfa',
    '--bg-input': '#f1f3ef',
    '--bg-glass': 'rgba(255, 255, 255, 0.72)',
    '--app-layout-bg':
      'linear-gradient(180deg, rgba(255, 255, 255, 0.66), rgba(246, 247, 244, 0.98)), var(--bg-app)',
    '--sidebar-bg': 'rgba(251, 251, 248, 0.92)',
    '--drawer-bg': 'rgba(251, 251, 248, 0.96)',
    '--sidebar-border': 'rgba(227, 230, 223, 0.72)',
    '--scrollbar-thumb': 'rgba(63, 107, 99, 0.16)',
    '--scrollbar-thumb-hover': 'rgba(63, 107, 99, 0.24)',

    '--text-primary': '#1d2422',
    '--text-regular': '#3d4642',
    '--text-secondary': '#727c76',
    '--text-disabled': '#a6aca8',

    '--border-light': '#e3e6df',
    '--border-hover': '#cfd6cd',
    '--border-focus': 'rgba(63, 107, 99, 0.42)',

    '--success': '#3d7656',
    '--warning': '#9a7432',
    '--danger': '#b24a4a',
    '--info': '#496b8f',

    '--shadow-sm': '0 1px 2px rgba(29, 36, 34, 0.04)',
    '--shadow-md': '0 8px 24px rgba(29, 36, 34, 0.06)',
    '--shadow-lg': '0 18px 48px rgba(29, 36, 34, 0.08)',
    '--shadow-glow': '0 12px 28px rgba(63, 107, 99, 0.14)',

    '--el-color-primary': '#3f6b63',
    '--el-color-primary-light-3': '#79a098',
    '--el-color-primary-light-5': '#a5c2ba',
    '--el-color-primary-light-7': '#c9ddd5',
    '--el-color-primary-light-8': '#dbeae2',
    '--el-color-primary-light-9': '#edf5f1',
    '--el-color-primary-dark-2': '#345b54',
  },
}

const bluePurple: ColorScheme = {
  id: 'blue-purple',
  name: '蓝紫',
  nameEn: 'Blue Purple',
  previewColor: '#5B5FCF',
  bodyBackground:
    'linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(245, 244, 250, 0.96)), ' +
    'radial-gradient(at 12% 0%, rgba(91, 95, 207, 0.08) 0px, transparent 36%), ' +
    'radial-gradient(at 92% 16%, rgba(139, 92, 246, 0.08) 0px, transparent 34%)',
  variables: {
    '--primary-color': '#5B5FCF',
    '--primary-hover': '#4A4EB8',
    '--primary-active': '#3D41A3',
    '--primary-fade': 'rgba(91, 95, 207, 0.1)',
    '--primary-line': 'rgba(91, 95, 207, 0.22)',

    '--accent-color': '#8B5CF6',
    '--accent-fade': 'rgba(139, 92, 246, 0.1)',

    '--bg-app': '#f5f4fa',
    '--bg-sidebar': '#fafaff',
    '--bg-card': '#ffffff',
    '--bg-panel': '#fafafd',
    '--bg-input': '#f0f0f8',
    '--bg-glass': 'rgba(255, 255, 255, 0.72)',
    '--app-layout-bg':
      'linear-gradient(180deg, rgba(255, 255, 255, 0.66), rgba(245, 244, 250, 0.98)), var(--bg-app)',
    '--sidebar-bg': 'rgba(250, 250, 255, 0.92)',
    '--drawer-bg': 'rgba(250, 250, 255, 0.96)',
    '--sidebar-border': 'rgba(228, 227, 240, 0.72)',
    '--scrollbar-thumb': 'rgba(91, 95, 207, 0.16)',
    '--scrollbar-thumb-hover': 'rgba(91, 95, 207, 0.24)',

    '--text-primary': '#1c1c2e',
    '--text-regular': '#3c3c56',
    '--text-secondary': '#6f6f8a',
    '--text-disabled': '#a4a4b8',

    '--border-light': '#e4e3f0',
    '--border-hover': '#cecdd8',
    '--border-focus': 'rgba(91, 95, 207, 0.42)',

    '--success': '#3d7656',
    '--warning': '#9a7432',
    '--danger': '#b24a4a',
    '--info': '#5B7FCF',

    '--shadow-sm': '0 1px 2px rgba(28, 28, 46, 0.04)',
    '--shadow-md': '0 8px 24px rgba(28, 28, 46, 0.06)',
    '--shadow-lg': '0 18px 48px rgba(28, 28, 46, 0.08)',
    '--shadow-glow': '0 12px 28px rgba(91, 95, 207, 0.14)',

    '--el-color-primary': '#5B5FCF',
    '--el-color-primary-light-3': '#8C8FDD',
    '--el-color-primary-light-5': '#ADAFE7',
    '--el-color-primary-light-7': '#CECFF1',
    '--el-color-primary-light-8': '#DEDFF5',
    '--el-color-primary-light-9': '#EFEFFA',
    '--el-color-primary-dark-2': '#4A4EB8',
  },
}

export const colorSchemes: ColorScheme[] = [claudeWarm, bluePurple, teaGreen]

export function getColorScheme(id: ColorSchemeId): ColorScheme {
  return colorSchemes.find((s) => s.id === id) || claudeWarm
}
