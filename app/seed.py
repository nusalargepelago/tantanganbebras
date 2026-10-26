"""Default seeder — idempotent, deterministic demo data for Tantangan Bebras.

Run: ``uv run python -m app.seed`` (after migrations). Safe to re-run; a second
run inserts 0 rows. All content is deterministic (seeded RNG) and deadlines are
relative to now so the pack stays valid forever.
"""
from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from app.auth.models import User
from app.event.models import (
    Event,
    EventAttempt,
    EventAttemptAnswer,
    EventAttemptAnswerTemp,
    EventAttemptQuestion,
    EventQuestion,
)
from app.infra.naming import slugify
from app.infra.passwords import hash_password
from app.practice.models import (
    Practice,
    PracticeAnswer,
    PracticeAnswerTemp,
    PracticeBeforeShuffle,
    PracticeQuestion,
)
from app.question.models import Question
from app.student.models import Student
from app.todos.models import Todo
from app.topic.models import Topic
from framework.extensions import db

STAFF_PASSWORDS = {"admin": "Admin123!", "editor": "Editor123!"}
STUDENT_PASSWORD = "Siswa1234"
CORRECT_CYCLE = ["a", "b", "c", "d"]

TOPIC_TITLES = {
    "cub": ["Pola dan Urutan", "Berpikir Terstruktur"],
    "scout": ["Dekomposisi Masalah", "Pengenalan Pola"],
    "rover": ["Algoritma dan Efisiensi", "Representasi Data"],
}
CODE_PREFIX = {"cub": "SGA", "scout": "PGN", "rover": "PNK"}
CATEGORIES = ("cub", "scout", "rover")
PUBLISHED_EVENTS = {
    "cub": "event-cub-2026",
    "scout": "event-scout-2026",
    "rover": "event-rover-2026",
}
MC_COUNT = 10
TOTAL_PER_CATEGORY = 12


def _user(username: str) -> User | None:
    return db.session.query(User).filter_by(username=username).first()


def _exists(model, **filters) -> bool:
    return db.session.query(model).filter_by(**filters).first() is not None


def _answer_for(question_id: str, correct: bool) -> tuple[str, bool]:
    """Return an answer consistent with the question's ``correct_answer``."""
    question = db.session.query(Question).filter_by(name=question_id).first()
    actual = (question.correct_answer if question else None) or "a"
    if correct:
        return actual, True
    wrong = next(letter for letter in CORRECT_CYCLE if letter != actual)
    return wrong, False


def _ensure_staff(username: str, full_name: str, app_role: str) -> User:
    password = STAFF_PASSWORDS[username]
    user = _user(username)
    if user is not None:
        return user
    first, _, last = full_name.partition(" ")
    user = User(
        username=username,
        email=f"{username}@example.test",
        first_name=first,
        last_name=last.strip(),
        full_name=full_name,
        password=hash_password(password),
        active=True,
        app_role=app_role,
    )
    db.session.add(user)
    db.session.flush()
    return user


def _ensure_student(
    username: str, first: str, last: str, category: str, school: str
) -> tuple[User, Student]:
    user = _user(username)
    if user is None:
        user = User(
            username=username,
            email=f"{username}@example.test",
            first_name=first,
            last_name=last,
            full_name=f"{first} {last}",
            password=hash_password(STUDENT_PASSWORD),
            active=True,
            app_role="user",
        )
        db.session.add(user)
        db.session.flush()
    student = db.session.query(Student).filter_by(user_id=user.id).first()
    if student is None:
        student = Student(
            user_id=user.id,
            category=category,
            school=school,
            city="Bandung",
            country="Indonesia",
            status="Active",
        )
        db.session.add(student)
    return user, student


def _ensure_topic(title: str, category: str, idx: int) -> str:
    name = slugify(title, fallback="topic")
    if _exists(Topic, name=name):
        return name
    db.session.add(Topic(name=name, title=title, category=category, idx=idx))
    return name


def _ensure_question(
    code: str, category: str, topic_id: str, is_essay: bool, correct: str
) -> str:
    name = slugify(code, fallback="q")
    if _exists(Question, name=name):
        return name
    common = dict(
        name=name,
        question_code=code,
        category=category,
        difficulty_level="Easy" if not is_essay else "Medium",
        status="Active",
        topic_id=topic_id,
    )
    if is_essay:
        question = Question(
            question=f"Explain your reasoning for {code}.",
            question_type="Essay",
            reference_answer="A clear, justified explanation.",
            **common,
        )
    else:
        question = Question(
            question=f"Which option matches the pattern in {code}?",
            question_type="Multiple Choice",
            option_a="Alpha",
            option_b="Beta",
            option_c="Gamma",
            option_d="Delta",
            correct_answer=correct,
            **common,
        )
    db.session.add(question)
    return name


def _ensure_event(
    name: str, event_name: str, category: str, deadline: datetime, published: bool,
    question_names: list[str], description: str,
) -> None:
    if not _exists(Event, name=name):
        db.session.add(
            Event(
                name=name,
                event_name=event_name,
                category=category,
                time_limit=60,
                event_deadline=deadline,
                published=published,
                description=description,
            )
        )
    for idx, question_id in enumerate(question_names):
        if not _exists(EventQuestion, event_id=name, question_id=question_id):
            db.session.add(EventQuestion(event_id=name, question_id=question_id, idx=idx))


def _seeded_practice(
    name: str, user_id: str, category: str, question_names: list[str],
    *, score: int | None, time_limit: int | None, started: datetime,
    finished: datetime | None, rng: random.Random,
) -> None:
    if not _exists(Practice, name=name):
        db.session.add(
            Practice(
                name=name,
                student_id=user_id,
                category=category,
                score=score,
                time_limit=time_limit,
                started_at=started,
                finished_at=finished,
            )
        )
    for idx, question_id in enumerate(question_names):
        if not _exists(PracticeBeforeShuffle, practice_id=name, question_id=question_id):
            db.session.add(
                PracticeBeforeShuffle(practice_id=name, question_id=question_id, original_idx=idx)
            )
    shuffled = list(question_names)
    rng.shuffle(shuffled)
    for idx, question_id in enumerate(shuffled):
        if not _exists(PracticeQuestion, practice_id=name, question_id=question_id):
            db.session.add(
                PracticeQuestion(practice_id=name, question_id=question_id, shuffled_idx=idx)
            )
    if finished is not None:
        for idx, question_id in enumerate(question_names):
            if _exists(PracticeAnswer, practice_id=name, question_id=question_id):
                continue
            answer, is_correct = _answer_for(question_id, correct=idx < 7)
            db.session.add(
                PracticeAnswer(
                    practice_id=name,
                    question_id=question_id,
                    answer=answer,
                    is_correct=is_correct,
                )
            )


def _seed_attempt(
    name: str, user_id: str, event_name: str, question_names: list[str],
    *, score: int | None, time_limit: int | None, started: datetime,
    finished: datetime | None,
) -> None:
    if not _exists(EventAttempt, name=name):
        db.session.add(
            EventAttempt(
                name=name,
                student_id=user_id,
                event_id=event_name,
                score=score,
                time_limit=time_limit,
                started_at=started,
                finished_at=finished,
            )
        )
    pivot_ids: dict[str, str] = {}
    for idx, question_id in enumerate(question_names):
        existing = db.session.query(EventAttemptQuestion).filter_by(
            event_attempt_id=name, question_id=question_id
        ).first()
        if existing is None:
            row = EventAttemptQuestion(event_attempt_id=name, question_id=question_id, idx=idx)
            db.session.add(row)
            db.session.flush()
            pivot_ids[question_id] = row.id
        else:
            pivot_ids[question_id] = existing.id
    if finished is not None:
        for idx, question_id in enumerate(question_names):
            if _exists(EventAttemptAnswer, event_attempt_question_id=pivot_ids[question_id]):
                continue
            answer, is_correct = _answer_for(question_id, correct=idx < 7)
            db.session.add(
                EventAttemptAnswer(
                    event_attempt_question_id=pivot_ids[question_id],
                    answer=answer,
                    is_correct=is_correct,
                )
            )


def _seed_todos(admin: User) -> None:
    specs = [
        ("Review question bank this week", False),
        ("Publish the Cub Event 2026", True),
        ("Update the Rover category guide", False),
    ]
    for title, completed in specs:
        if _exists(Todo, title=title, creator_id=admin.id):
            continue
        db.session.add(Todo(title=title, completed=completed, creator_id=admin.id))


def seed() -> dict[str, int]:
    """Seed demo data inside an app context. Idempotent. Returns table counts."""
    now = datetime.now(UTC)

    admin = _ensure_staff("admin", "Admin User", "admin")
    _ensure_staff("editor", "Editor User", "user")
    budi, _ = _ensure_student("budi", "Budi", "Santoso", "cub", "SMP Negeri 1 Bandung")
    siti, _ = _ensure_student("siti", "Siti", "Rani", "scout", "SMP Negeri 2 Yogyakarta")
    rani, _ = _ensure_student("rani", "Rani", "Putri", "rover", "SMA Negeri 1 Surabaya")
    db.session.flush()

    topic_names: dict[str, list[str]] = {}
    mc_slugs: dict[str, list[str]] = {}
    for category in CATEGORIES:
        topic_names[category] = [
            _ensure_topic(title, category, idx)
            for idx, title in enumerate(TOPIC_TITLES[category])
        ]
        mc_slugs[category] = []
        for i in range(1, TOTAL_PER_CATEGORY + 1):
            code = f"TB-{CODE_PREFIX[category]}-{i:03d}"
            is_essay = i > MC_COUNT
            topic_idx = 0 if i <= 6 else 1
            correct = CORRECT_CYCLE[(i - 1) % len(CORRECT_CYCLE)]
            name = _ensure_question(
                code, category, topic_names[category][topic_idx], is_essay, correct
            )
            if not is_essay:
                mc_slugs[category].append(name)
    db.session.flush()

    for category in CATEGORIES:
        _ensure_event(
            PUBLISHED_EVENTS[category],
            f"Bebras {category.title()} 2026",
            category,
            now + timedelta(days=30),
            True,
            mc_slugs[category],
            "Published challenge for the 2026 season.",
        )
    _ensure_event(
        "event-draft", "Bebras Draft", "cub", now + timedelta(days=14), False,
        mc_slugs["cub"][:3], "Draft not yet published.",
    )
    _ensure_event(
        "event-expired", "Bebras Expired", "cub", now - timedelta(days=1), True,
        mc_slugs["cub"][:3], "Already past its deadline.",
    )
    db.session.flush()

    _seeded_practice(
        "seed-practice-budi", budi.id, "cub", mc_slugs["cub"],
        score=70, time_limit=600, started=now - timedelta(minutes=10),
        finished=now, rng=random.Random(42),
    )
    _seeded_practice(
        "seed-practice-siti", siti.id, "scout", mc_slugs["scout"],
        score=None, time_limit=None, started=now - timedelta(minutes=20),
        finished=None, rng=random.Random(7),
    )
    for idx, question_id in enumerate(mc_slugs["scout"][:3]):
        if not _exists(
            PracticeAnswerTemp, practice_id="seed-practice-siti", question_id=question_id
        ):
            db.session.add(
                PracticeAnswerTemp(
                    practice_id="seed-practice-siti",
                    question_id=question_id,
                    answer=CORRECT_CYCLE[idx % len(CORRECT_CYCLE)],
                )
            )
    db.session.flush()

    _seed_attempt(
        "seed-attempt-budi", budi.id, PUBLISHED_EVENTS["cub"], mc_slugs["cub"],
        score=70, time_limit=900, started=now - timedelta(minutes=15), finished=now,
    )
    _seed_attempt(
        "seed-attempt-siti", siti.id, PUBLISHED_EVENTS["scout"], mc_slugs["scout"],
        score=None, time_limit=None, started=now - timedelta(minutes=30), finished=None,
    )
    db.session.flush()
    for idx, question_id in enumerate(mc_slugs["scout"][:2]):
        existing = db.session.query(EventAttemptQuestion).filter_by(
            event_attempt_id="seed-attempt-siti", question_id=question_id
        ).first()
        if existing is None:
            continue
        if not _exists(
            EventAttemptAnswerTemp,
            event_attempt_id="seed-attempt-siti",
            event_attempt_question_id=existing.id,
        ):
            db.session.add(
                EventAttemptAnswerTemp(
                    event_attempt_id="seed-attempt-siti",
                    event_attempt_question_id=existing.id,
                    answer=CORRECT_CYCLE[idx % len(CORRECT_CYCLE)],
                )
            )

    _seed_todos(admin)
    db.session.commit()
    return _counts()


def _counts() -> dict[str, int]:
    models = [
        User, Student, Topic, Question, Event, EventQuestion, EventAttempt,
        EventAttemptQuestion, EventAttemptAnswer, EventAttemptAnswerTemp,
        Practice, PracticeBeforeShuffle, PracticeQuestion, PracticeAnswer,
        PracticeAnswerTemp, Todo,
    ]
    return {model.__tablename__: db.session.query(model).count() for model in models}


def main() -> None:
    from app.create_app import create_app

    app = create_app()
    with app.app_context():
        counts = seed()
    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
