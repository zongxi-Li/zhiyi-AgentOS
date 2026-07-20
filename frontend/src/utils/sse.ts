/** Extract an SSE data field while accepting the optional space allowed after `data:`. */
export function parseSseDataLine(line: string): string | null {
  const normalized = line.endsWith('\r') ? line.slice(0, -1) : line
  if (!normalized.startsWith('data:')) return null

  const value = normalized.slice('data:'.length)
  return value.startsWith(' ') ? value.slice(1) : value
}
