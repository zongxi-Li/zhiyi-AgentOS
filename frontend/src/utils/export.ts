/**
 * 导出工具
 */
export interface ConversationExport {
  messages: Array<{
    role: string
    content: string
    time: string
  }>
  role?: string
  createdAt: string
}

/**
 * 导出对话为JSON
 */
export function exportConversationToJson(data: ConversationExport): string {
  return JSON.stringify(data, null, 2)
}

/**
 * 导出对话为TXT
 */
export function exportConversationToTxt(data: ConversationExport): string {
  let content = `对话导出\n`
  content += `角色: ${data.role || '默认'}\n`
  content += `创建时间: ${data.createdAt}\n`
  content += `\n${'='.repeat(50)}\n\n`

  data.messages.forEach((msg, index) => {
    content += `[${msg.role.toUpperCase()}] ${msg.time}\n`
    content += `${msg.content}\n\n`
  })

  return content
}

/**
 * 下载文件
 */
export function downloadFile(content: string, filename: string, mimeType: string = 'text/plain') {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

