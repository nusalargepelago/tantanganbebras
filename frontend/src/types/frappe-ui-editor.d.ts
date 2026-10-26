/**
 * Type surface for `frappe-ui/editor` (molecules/editor).
 *
 * frappe-ui publishes this entry as raw TypeScript sources; checking them in
 * this project surfaces frappe-internal diagnostics we cannot fix (e.g.
 * `this.parent` inside `Placeholder.extend` in their `extensions.ts`). This
 * declaration mirrors the public API this app uses; runtime still resolves the
 * real package (Vite does not consult tsconfig `paths`).
 */
declare module 'frappe-ui/editor' {
  import type { Extension, Extensions, JSONContent } from '@tiptap/core'
  import type { DefineComponent } from 'vue'

  export interface MediaUploadProgress {
    loaded: number
    total: number
    percent: number
  }

  export interface MediaUploadRequestOptions {
    signal?: AbortSignal
    onProgress?: (progress: MediaUploadProgress) => void
  }

  export interface UploadedMedia {
    file_url: string
    width?: number | null
    height?: number | null
    [key: string]: unknown
  }

  export type UploadFunction = (
    file: File,
    options?: MediaUploadRequestOptions,
  ) => Promise<UploadedMedia>

  export interface MenuItem {
    [key: string]: unknown
  }

  export interface EditorProps {
    modelValue?: string | JSONContent | null
    extensions?: Extensions
    format?: 'html' | 'json' | 'markdown'
    placeholder?: string
    editable?: boolean
    autofocus?: boolean
    uploadFunction?: UploadFunction
  }

  export const Editor: DefineComponent<EditorProps, {}, any>
  export const EditorContent: DefineComponent<Record<string, never>, {}, any>
  export const EditorFixedMenu: DefineComponent<
    { items: MenuItem[]; size?: 'xs' | 'sm'; editor?: unknown },
    {},
    any
  >
  export const RichTextKit: Extension
  export const articleToolbar: MenuItem[]
  export const minimalToolbar: MenuItem[]
  export const commentToolbar: MenuItem[]
  export const Bold: MenuItem
  export const Italic: MenuItem
  export const Separator: MenuItem
  export const InsertLink: MenuItem
  export const InsertImage: MenuItem
}
