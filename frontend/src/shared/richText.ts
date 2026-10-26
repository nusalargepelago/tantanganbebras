const BLANK_HTML = /&nbsp;|&#160;|&#xa0;/gi

function plainText(value: string): string {
  return value
    .replace(/<[^>]*>/g, '')
    .replace(BLANK_HTML, ' ')
    .replace(/\u00a0/g, ' ')
    .trim()
}

export function hasTextContent(value: string | null | undefined): boolean {
  if (!value) return false
  return plainText(value).length > 0
}

export function hasRichContent(value: string | null | undefined): boolean {
  if (!value) return false
  return /<img\b/i.test(value) || hasTextContent(value)
}

export function stripTags(value: string | null | undefined): string {
  return plainText(value ?? '')
}
