export const OPTION_LETTERS = ['a', 'b', 'c', 'd'] as const

export type OptionKey = 'optionA' | 'optionB' | 'optionC' | 'optionD'

export function optionKey(letter: string): OptionKey {
  return `option${letter.toUpperCase()}` as OptionKey
}
