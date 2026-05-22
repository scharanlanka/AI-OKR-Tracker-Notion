from datetime import date, timedelta
from sqlalchemy.orm import Session

from models import KeyResult, Objective


def get_all_okrs(db: Session):
    return db.query(Objective).order_by(Objective.created_at.desc()).all()


def get_risks(db: Session):
    seven_days = date.today() + timedelta(days=7)

    rows = (
        db.query(KeyResult, Objective)
        .join(Objective, KeyResult.objective_id == Objective.id)
        .filter(
            (KeyResult.is_blocked.is_(True))
            | (KeyResult.progress < 0.5)
            | ((KeyResult.deadline.isnot(None)) & (KeyResult.deadline <= seven_days) & (KeyResult.progress < 0.8))
        )
        .order_by(KeyResult.deadline.asc().nulls_last())
        .all()
    )

    return [
        {
            "objective_title": obj.title,
            "key_result_title": kr.title,
            "owner": kr.owner,
            "progress": kr.progress,
            "status": kr.status,
            "deadline": kr.deadline,
            "is_blocked": kr.is_blocked,
        }
        for kr, obj in rows
    ]


def get_upcoming_deadlines(db: Session, days: int = 14):
    threshold = date.today() + timedelta(days=days)
    rows = (
        db.query(KeyResult, Objective)
        .join(Objective, KeyResult.objective_id == Objective.id)
        .filter(KeyResult.deadline.isnot(None), KeyResult.deadline <= threshold)
        .order_by(KeyResult.deadline.asc())
        .all()
    )

    return [
        {
            "objective_title": obj.title,
            "key_result_title": kr.title,
            "owner": kr.owner,
            "deadline": kr.deadline,
            "progress": kr.progress,
        }
        for kr, obj in rows
    ]
