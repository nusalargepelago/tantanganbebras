import DOMPurify from 'dompurify'

const ALLOWED_TAGS = [
  'p',
  'div',
  'span',
  'br',
  'strong',
  'b',
  'em',
  'i',
  'u',
  's',
  'strike',
  'del',
  'ins',
  'sub',
  'sup',
  'mark',
  'ul',
  'ol',
  'li',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'blockquote',
  'code',
  'pre',
  'hr',
  'a',
  'img',
  'table',
  'caption',
  'thead',
  'tbody',
  'tfoot',
  'tr',
  'th',
  'td',
  'colgroup',
  'col',
]

const ALLOWED_ATTR = [
  'href',
  'title',
  'target',
  'rel',
  'src',
  'alt',
  'width',
  'height',
  'style',
  'dir',
  'lang',
  'colspan',
  'rowspan',
  'span',
  'align',
]

// Google Docs (data:image) and uploaded files (relative) must keep rendering.
const ALLOWED_URI =
  /^(?:(?:https?|mailto|tel):|data:image\/(?:png|jpe?g|gif|webp|avif|bmp);base64,|\/(?!\/)|#)/i

// DOMPurify runs every non-URI attribute through ALLOWED_URI; size/layout attrs
// are not URLs and would be dropped by the strict regexp above.
const URI_SAFE_ATTR = [
  'width',
  'height',
  'align',
  'colspan',
  'rowspan',
  'span',
  'dir',
  'lang',
  'rel',
  'target',
]

const STYLE_PROPS = new Set([
  'text-align',
  'vertical-align',
  'font-size',
  'font-family',
  'font-weight',
  'font-style',
  'font-variant-numeric',
  'font-variant-east-asian',
  'font-variant-alternates',
  'font-variant-position',
  'font-kerning',
  'font-optical-sizing',
  'font-feature-settings',
  'font-variation-settings',
  'font-stretch',
  'line-height',
  'letter-spacing',
  'color',
  'background-color',
  'white-space',
  'white-space-collapse',
  'margin',
  'margin-top',
  'margin-right',
  'margin-bottom',
  'margin-left',
  'padding',
  'padding-top',
  'padding-right',
  'padding-bottom',
  'padding-left',
  'text-decoration',
  'text-indent',
  'text-transform',
  'width',
  'height',
  'max-width',
  'max-height',
  'border',
  'border-collapse',
  'border-width',
  'border-style',
  'border-color',
  'list-style-type',
  'direction',
])

function safeStyle(value: string): string {
  return value
    .split(';')
    .map((decl) => decl.trim())
    .filter((decl) => {
      const idx = decl.indexOf(':')
      if (idx === -1) return false
      const prop = decl.slice(0, idx).trim().toLowerCase()
      const val = decl.slice(idx + 1)
      if (!STYLE_PROPS.has(prop)) return false
      return !/url\s*\(|expression|javascript:/i.test(val)
    })
    .join('; ')
}

DOMPurify.addHook('uponSanitizeAttribute', (_node, data) => {
  if (data.attrName !== 'style') return
  const clean = safeStyle(data.attrValue)
  if (clean) data.attrValue = clean
  else data.keepAttr = false
})

DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.getAttribute('target') === '_blank') {
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

const cache = new Map<string, string>()
const CACHE_LIMIT = 200

export function sanitizeHtml(value: string | null | undefined): string {
  if (!value) return ''
  const cached = cache.get(value)
  if (cached !== undefined) return cached
  const clean = DOMPurify.sanitize(value, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOWED_URI_REGEXP: ALLOWED_URI,
    ADD_URI_SAFE_ATTR: URI_SAFE_ATTR,
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'svg', 'math'],
  })
  if (cache.size >= CACHE_LIMIT) cache.clear()
  cache.set(value, clean)
  return clean
}
