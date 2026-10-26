export type TourRole = 'student' | 'staff'

export type TourPlacement = 'top' | 'bottom' | 'left' | 'right' | 'center'

export interface TourRoute {
  name: string
  params?: Record<string, string>
  query?: Record<string, string>
}

export interface TourStep {
  /** Stable id; the i18n key suffix under `tour.<tourId>.steps`. */
  id: string
  /** Fixed route opened when the step starts. */
  route?: TourRoute
  /** Route name(s) that count as being on this step. Defaults to `route.name`. */
  match?: string | string[]
  /** Value of the `data-tour` attribute to highlight. Omit for a centered card. */
  target?: string
  placement?: Exclude<TourPlacement, 'center'>
  /** Advance when the user's own click navigates to the next step's route. */
  advanceOnRoute?: boolean
}

export interface TourDefinition {
  id: string
  roles: TourRole[]
  starter?: boolean
  icon?: string
  steps: TourStep[]
}

export interface TourRect {
  top: number
  left: number
  width: number
  height: number
}
