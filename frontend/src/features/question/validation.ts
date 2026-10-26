import { OPTION_LETTERS, optionKey } from '@/shared/questionOptions'
import { hasRichContent } from '@/shared/richText'

import type { QuestionPayload } from './store'

export interface QuestionErrors {
  question?: string
  optionA?: string
  optionB?: string
  optionC?: string
  optionD?: string
  correctAnswer?: string
  referenceAnswer?: string
}

export function validateQuestion(payload: Partial<QuestionPayload>): QuestionErrors {
  const errors: QuestionErrors = {}

  if (!hasRichContent(payload.question)) {
    errors.question = 'validation.questionRequired'
  }

  if (payload.questionType === 'Essay') {
    if (!hasRichContent(payload.referenceAnswer)) {
      errors.referenceAnswer = 'validation.referenceRequired'
    }
    return errors
  }

  for (const letter of OPTION_LETTERS) {
    const key = optionKey(letter)
    if (!hasRichContent(payload[key])) {
      errors[key] = 'validation.optionRequired'
    }
  }
  if (!payload.correctAnswer) {
    errors.correctAnswer = 'validation.correctAnswer'
  }
  return errors
}

export function hasErrors(errors: QuestionErrors): boolean {
  return Object.values(errors).some(Boolean)
}
