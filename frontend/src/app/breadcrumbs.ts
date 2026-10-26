export interface BreadcrumbItem {
  label: string
  route?: { name: string; params?: Record<string, string> }
  href?: string
  onClick?: (event?: MouseEvent) => void
  [key: string]: unknown
}

export const HOME: BreadcrumbItem = {
  label: 'Dashboard',
  route: { name: 'Dashboard' },
}

interface Crumb {
  label: string
  parent?: BreadcrumbItem
}

export const breadcrumbMap: Record<string, Crumb> = {
  Dashboard: { label: 'crumb.dashboard' },
  QuestionList: { label: 'crumb.questionBank' },
  QuestionNew: {
    label: 'crumb.newQuestion',
    parent: { label: 'crumb.questionBank', route: { name: 'QuestionList' } },
  },
  QuestionDetail: {
    label: 'crumb.question',
    parent: { label: 'crumb.questionBank', route: { name: 'QuestionList' } },
  },
  QuestionEdit: {
    label: 'crumb.editQuestion',
    parent: { label: 'crumb.questionBank', route: { name: 'QuestionList' } },
  },
  QuestionEditor: {
    label: 'crumb.editor',
    parent: { label: 'crumb.questionBank', route: { name: 'QuestionList' } },
  },
  StudentList: { label: 'crumb.students' },
  StudentImport: {
    label: 'crumb.import',
    parent: { label: 'crumb.students', route: { name: 'StudentList' } },
  },
  StudentNew: {
    label: 'crumb.newStudent',
    parent: { label: 'crumb.students', route: { name: 'StudentList' } },
  },
  StudentDetail: {
    label: 'crumb.student',
    parent: { label: 'crumb.students', route: { name: 'StudentList' } },
  },
  StudentEdit: {
    label: 'crumb.editStudent',
    parent: { label: 'crumb.students', route: { name: 'StudentList' } },
  },
  UsersList: { label: 'crumb.users' },
  UserNew: {
    label: 'crumb.newUser',
    parent: { label: 'crumb.users', route: { name: 'UsersList' } },
  },
  UserDetail: {
    label: 'crumb.user',
    parent: { label: 'crumb.users', route: { name: 'UsersList' } },
  },
  UserEdit: {
    label: 'crumb.editUser',
    parent: { label: 'crumb.users', route: { name: 'UsersList' } },
  },
  PracticeList: { label: 'crumb.practice' },
  PracticeRunner: {
    label: 'crumb.practice',
    parent: { label: 'crumb.practice', route: { name: 'PracticeList' } },
  },
  PracticeResult: {
    label: 'crumb.result',
    parent: { label: 'crumb.practice', route: { name: 'PracticeList' } },
  },
  PracticeAdminList: { label: 'crumb.practiceReview' },
  PracticeAdminDetail: {
    label: 'crumb.practiceDetail',
    parent: { label: 'crumb.practiceReview', route: { name: 'PracticeAdminList' } },
  },
  EventList: { label: 'crumb.events' },
  EventNew: {
    label: 'crumb.newEvent',
    parent: { label: 'crumb.events', route: { name: 'EventList' } },
  },
  EventDetail: {
    label: 'crumb.event',
    parent: { label: 'crumb.events', route: { name: 'EventList' } },
  },
  EventEdit: {
    label: 'crumb.editEvent',
    parent: { label: 'crumb.events', route: { name: 'EventList' } },
  },
  EventResults: {
    label: 'crumb.eventResults',
    parent: { label: 'crumb.events', route: { name: 'EventList' } },
  },
  EventStudentList: { label: 'crumb.events' },
  EventStudentResult: {
    label: 'crumb.result',
    parent: { label: 'crumb.events', route: { name: 'EventStudentList' } },
  },
  AdminDashboard: { label: 'crumb.dashboard' },
  StudentDashboard: { label: 'crumb.dashboard' },
  TodosList: { label: 'crumb.todos' },
  Backup: { label: 'crumb.backup' },
}
