"""Practice services — create, resume, autosave, submit, and review sheets."""
from __future__ import annotations

import random
from datetime import UTC, datetime

from app.infra.audit import log as audit_log
from app.infra.scoring import POINTS_PER_CORRECT, SHEET_SIZE, is_correct
from app.infra.settings import get_setting, set_setting
from app.practice.dto import AnswerItem
from app.practice.models import (
    Practice,
    PracticeAnswer,
    PracticeAnswerTemp,
    PracticeBeforeShuffle,
    PracticeQuestion,
)
from app.practice.presenters import PracticeAdminOut, PracticeOut
from app.practice.repositories import PracticeRepository
from app.question.presenters import QuestionOut
from app.question.repositories import QuestionRepository
from app.student.presenters import StudentOut
from app.student.repositories import StudentRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, Forbidden, NotFound, ValidationFailed

MIN_QUESTIONS_KEY = "practiceMinQuestions"
DEFAULT_MIN_QUESTIONS = SHEET_SIZE


def _min_questions() -> int:
    raw = get_setting(MIN_QUESTIONS_KEY)
    if raw is None:
        return DEFAULT_MIN_QUESTIONS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MIN_QUESTIONS
    return value if value >= 1 else DEFAULT_MIN_QUESTIONS


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class PracticeService(ServiceBase[PracticeRepository]):
    """Business logic for practice sheets."""

    repository_class = PracticeRepository

    def __init__(
        self,
        repo: PracticeRepository | None = None,
        questions: QuestionRepository | None = None,
        students: StudentRepository | None = None,
    ):
        super().__init__(repo)
        self._questions = questions or QuestionRepository()
        self._students = students or StudentRepository()

    def min_questions(self) -> int:
        return _min_questions()

    def update_min_questions(self, value: int, *, changed_by: str) -> int:
        if _min_questions() == value:
            return value
        set_setting(MIN_QUESTIONS_KEY, str(value))
        audit_log(
            "practice_settings_updated",
            user_id=changed_by,
            resource="practice/settings",
            details={"minQuestions": value},
        )
        self._commit()
        return value

    def create(
        self,
        student_id: str,
        *,
        test: bool = False,
        category: str | None = None,
        app_role: str = "user",
    ) -> dict:
        student = self._students.find_by_user_id(student_id)
        if test:
            if app_role != "admin" and student is not None:
                raise Forbidden("test_requires_staff")
        elif student is None:
            raise Conflict("student_not_found")

        picked = student.category if student is not None else category
        if picked is None:
            raise ValidationFailed("category_required")

        min_questions = _min_questions()
        pool = self._questions.list_pool(category=picked, status="Active", limit=500)
        if len(pool) < min_questions:
            raise Conflict(
                f"insufficient_question_in_category: "
                f"have {len(pool)}, need {min_questions}"
            )

        picks = random.sample(pool, min_questions)
        now = datetime.now(UTC)
        if test:
            self._repo.delete_test_practices(student_id)
        name = f"{'test' if test else 'student'}-{student_id}-{int(now.timestamp())}"
        practice = Practice(
            name=name, student_id=student_id, category=picked, started_at=now
        )
        self._repo.add(practice)
        self._flush()

        pick_names = {q.name for q in picks}
        original = [q for q in pool if q.name in pick_names]
        shuffled = list(picks)
        random.shuffle(shuffled)
        for idx, q in enumerate(original):
            self._repo.add(
                PracticeBeforeShuffle(practice_id=name, question_id=q.name, original_idx=idx)
            )
        for idx, q in enumerate(shuffled):
            self._repo.add(
                PracticeQuestion(practice_id=name, question_id=q.name, shuffled_idx=idx)
            )

        audit_log(
            "practice_created",
            user_id=student_id,
            resource=f"practice/{name}",
            details={"category": picked},
        )
        self._commit()
        return PracticeOut.from_practice(practice).to_dict()

    def start(self, student_id: str) -> dict | None:
        practice = self._repo.active_for_student(student_id)
        if practice is None:
            return None

        questions = []
        for row in self._repo.get_questions(practice.name):
            q = self._questions.find_by_name(row.question_id)
            questions.append(
                {
                    "questionId": row.question_id,
                    "question": QuestionOut.from_question(q).to_dict() if q else None,
                }
            )
        saved = [
            {"questionId": t.question_id, "answer": t.answer}
            for t in self._repo.get_temps(practice.name)
        ]
        return {
            "practice": PracticeOut.from_practice(practice).to_dict(),
            "questions": questions,
            "savedAnswers": saved,
        }

    def save_temp(
        self, student_id: str, practice_name: str, question_id: str, answer: str | None
    ) -> dict:
        practice = self._repo.find_by_name(practice_name)
        if practice is None or practice.student_id != student_id:
            raise NotFound("practice_not_found")
        if practice.finished_at is not None:
            raise NotFound("practice_already_submitted")

        temp = self._repo.find_temp(practice_name, question_id)
        if temp is not None:
            temp.answer = answer or ""
        else:
            self._repo.add(
                PracticeAnswerTemp(
                    practice_id=practice_name, question_id=question_id, answer=answer or ""
                )
            )
        self._commit()
        return {"notEmpty": bool(answer and answer.strip())}

    def submit(
        self, student_id: str, practice_name: str, answers: list[AnswerItem]
    ) -> dict:
        practice = self._repo.find_by_name(practice_name)
        if practice is None or practice.student_id != student_id:
            raise Conflict("practice_not_found")
        if practice.finished_at is not None:
            raise Conflict("practice_already_submitted")

        answer_map = {a.question_id: a.answer for a in answers}
        score = 0
        for row in self._repo.get_questions(practice.name):
            q = self._questions.find_by_name(row.question_id)
            if q is None:
                continue
            response = answer_map.get(row.question_id)
            correct = is_correct(q, response)
            self._repo.add(
                PracticeAnswer(
                    practice_id=practice_name,
                    question_id=row.question_id,
                    answer=response or "",
                    is_correct=correct,
                )
            )
            if correct:
                score += POINTS_PER_CORRECT

        now = datetime.now(UTC)
        practice.score = score
        practice.finished_at = now
        started = _as_utc(practice.started_at)
        if started is not None:
            practice.time_limit = int((now - started).total_seconds())

        audit_log(
            "practice_submitted",
            user_id=student_id,
            resource=f"practice/{practice_name}",
            details={"score": score},
        )
        self._commit()
        return PracticeOut.from_practice(practice).to_dict()

    def detail(self, student_id: str, name: str) -> dict:
        practice = self._repo.find_by_name(name)
        if practice is None or practice.student_id != student_id:
            raise NotFound("practice_not_found")

        answer_map = {a.question_id: a for a in self._repo.get_answers(name)}
        questions = [
            self._question_payload(row.question_id) for row in self._repo.get_questions(name)
        ]
        answers = [
            {
                "questionId": row.question_id,
                "answer": row.answer,
                "isCorrect": row.is_correct,
            }
            for row in answer_map.values()
        ]
        before = [
            {
                "questionId": row.question_id,
                "question": self._question_payload(row.question_id)["question"],
                "originalIdx": row.original_idx,
            }
            for row in self._repo.get_before_shuffle(name)
        ]
        return {
            "practice": PracticeOut.from_practice(practice).to_dict(),
            "questions": questions,
            "answers": answers,
            "beforeShuffle": before,
        }

    def admin_detail(self, name: str) -> dict:
        practice = self._repo.find_by_name(name)
        if practice is None:
            raise NotFound("practice_not_found")

        answer_map = {a.question_id: a for a in self._repo.get_answers(name)}
        student = self._students.find_by_user_id(practice.student_id)
        before = [
            {
                "questionId": row.question_id,
                "question": self._question_payload(row.question_id)["question"],
                "originalIdx": row.original_idx,
            }
            for row in self._repo.get_before_shuffle(name)
        ]
        after = [
            {
                "questionId": row.question_id,
                "question": self._question_payload(row.question_id)["question"],
                "shuffledIdx": row.shuffled_idx,
            }
            for row in self._repo.get_questions(name)
        ]
        answers = [
            {
                "questionId": row.question_id,
                "answer": row.answer,
                "isCorrect": row.is_correct,
            }
            for row in answer_map.values()
        ]
        return {
            "practice": PracticeOut.from_practice(practice).to_dict(),
            "student": (
                StudentOut.from_student(student, student.user).to_dict()
                if student and student.user
                else None
            ),
            "beforeShuffle": before,
            "afterShuffle": after,
            "answers": answers,
        }

    def mine(self, student_id: str) -> list[dict]:
        return [
            PracticeOut.from_practice(p).to_dict()
            for p in self._repo.list_for_student(student_id, limit=100)
        ]

    def list_admin(self, **filters) -> tuple[list[dict], int]:
        items, total = self._repo.list_all(**filters)
        students = {
            s.user_id: s
            for s in self._students.find_by_user_ids([p.student_id for p in items])
        }
        rows = []
        for p in items:
            student = students.get(p.student_id)
            name = None
            email = None
            school = None
            if student is not None and student.user is not None:
                name = (
                    f"{student.user.first_name} {student.user.last_name}".strip() or None
                )
                email = student.user.email or None
                school = student.school or None
            rows.append(
                PracticeAdminOut.from_practice(
                    p, student_name=name, student_email=email, student_school=school
                ).to_dict()
            )
        return rows, total

    def _question_payload(self, question_id: str) -> dict:
        q = self._questions.find_by_name(question_id)
        return {
            "questionId": question_id,
            "question": QuestionOut.from_question(q).to_dict() if q else None,
        }


__all__ = ["PracticeService"]
