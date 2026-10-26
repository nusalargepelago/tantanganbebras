"""Dashboard services — assemble admin and student dashboard payloads."""
from __future__ import annotations

from app.dashboard.repositories import DashboardRepository
from app.event.presenters import EventAttemptOut, EventOut
from app.practice.presenters import PracticeOut
from app.student.presenters import StudentOut
from app.student.repositories import StudentRepository
from framework.base import ServiceBase
from framework.exceptions import NotFound

_CATEGORY_ORDER = ("cub", "scout", "rover")


class DashboardService(ServiceBase[DashboardRepository]):
    """Cross-domain dashboard read model."""

    repository_class = DashboardRepository

    def __init__(
        self,
        repo: DashboardRepository | None = None,
        students: StudentRepository | None = None,
    ):
        super().__init__(repo)
        self._students = students or StudentRepository()

    def admin_payload(self) -> dict:
        by_category = self._repo.question_counts_by_category()
        status_counts = self._repo.student_status_counts()
        event_counts = self._repo.event_question_counts()

        counts = {
            "questionCub": by_category.get("cub", 0),
            "questionScout": by_category.get("scout", 0),
            "questionRover": by_category.get("rover", 0),
            "eventActive": self._repo.active_event_count(),
            "studentActive": status_counts.get("Active", 0),
            "studentInactive": status_counts.get("Inactive", 0),
            "eventStudentToday": self._repo.attempts_last_24h(),
        }
        recent_events = [
            EventOut.from_event(e, question_count=event_counts.get(e.name, 0)).to_dict()
            for e in self._repo.recent_events(limit=5)
        ]
        recent_students = [
            StudentOut.from_student(s, s.user).to_dict()
            for s in self._repo.recent_students(limit=5)
            if s.user
        ]
        return {
            "counts": counts,
            "recentEvents": recent_events,
            "recentStudents": recent_students,
        }

    def stats_payload(self) -> dict:
        total_students, total_schools = self._repo.student_totals()
        category_counts = self._repo.student_category_counts()
        order = {c: i for i, c in enumerate(_CATEGORY_ORDER)}
        return {
            "totals": {"students": total_students, "schools": total_schools},
            "schools": [
                {"school": school, "count": count}
                for school, count in self._repo.students_by_school()
            ],
            "registrations": [
                {"year": year, "count": count}
                for year, count in self._repo.students_by_year()
            ],
            "categories": [
                {"category": category, "count": count}
                for category, count in sorted(
                    category_counts.items(), key=lambda item: (order.get(item[0], len(order)), item[0])
                )
            ],
        }

    def student_payload(self, student_id: str) -> dict:
        student = self._students.find_by_user_id(student_id)
        if student is None:
            raise NotFound("student_not_found")

        last_practice = self._repo.last_practice(student_id)
        last_attempt = self._repo.last_attempt(student_id)
        return {
            "category": student.category,
            "totalPractice": self._repo.practice_count(student_id),
            "totalChallenge": self._repo.attempt_count(student_id),
            "lastPractice": (
                PracticeOut.from_practice(last_practice).to_dict() if last_practice else None
            ),
            "lastEvent": (
                EventAttemptOut.from_attempt(last_attempt).to_dict() if last_attempt else None
            ),
        }


__all__ = ["DashboardService"]
