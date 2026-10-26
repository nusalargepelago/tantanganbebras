def test_seed_is_idempotent(app):
    from app.seed import seed

    with app.app_context():
        first = seed()
        second = seed()

    assert first == second
    assert first["users"] == 5
    assert first["students"] == 3
    assert first["questions"] == 36
    assert first["events"] == 5
    assert first["event_questions"] == 36
    assert first["event_attempt_questions"] == 20
    assert first["event_attempt_answers"] == 10
    assert first["practices"] == 2
    assert first["practice_questions"] == 20
    assert first["practice_answers"] == 10
    assert first["todos"] == 3


def test_seed_reaches_all_student_states(app):
    from app.event.models import EventAttempt
    from app.practice.models import Practice
    from app.seed import seed
    from framework.extensions import db

    with app.app_context():
        seed()
        attempts = {a.name: a for a in db.session.query(EventAttempt).all()}
        practices = {p.name: p for p in db.session.query(Practice).all()}

    # budi completed, siti in progress
    budi_attempt = attempts["seed-attempt-budi"]
    siti_attempt = attempts["seed-attempt-siti"]
    assert budi_attempt.score == 70
    assert budi_attempt.finished_at is not None
    assert siti_attempt.finished_at is None

    assert practices["seed-practice-budi"].score == 70
    assert practices["seed-practice-siti"].finished_at is None
