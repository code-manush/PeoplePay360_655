from fastapi import APIRouter, HTTPException
from app.repositories.postgres_repos import PostgresScheduleRepository
from app.core.response import success_response, error_response

router = APIRouter(prefix="/schedules", tags=["schedules"])
schedule_repo = PostgresScheduleRepository()


def _calc_weekly_hours(days: list) -> float:
    return sum(float(d.get("expected_hours", 0)) for d in days if d.get("is_working"))


def _enrich_schedule(s: dict) -> dict:
    days = schedule_repo.find_days(s["id"])
    return {
        **s,
        "days": sorted(days, key=lambda d: ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY","SUNDAY"].index(d.get("day_of_week","MONDAY"))),
        "weekly_hours": _calc_weekly_hours(days),
        "working_days_count": sum(1 for d in days if d.get("is_working")),
    }


@router.get("")
def list_schedules():
    schedules = schedule_repo.find_all()
    return success_response([_enrich_schedule(s) for s in schedules])


@router.get("/{schedule_id}")
def get_schedule(schedule_id: str):
    s = schedule_repo.find_by_id(schedule_id)
    if not s:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Schedule {schedule_id} not found"))
    return success_response(_enrich_schedule(s))


@router.post("")
def create_schedule(body: dict):
    if not body.get("name"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Name is required"))
    days = body.pop("days", [])
    schedule = schedule_repo.create({**body, "is_active": True})
    # Validate day times
    for d in days:
        if d.get("is_working") and d.get("start_time") and d.get("end_time"):
            if d["end_time"] <= d["start_time"]:
                raise HTTPException(status_code=422, detail=error_response(
                    "VALIDATION_ERROR", f"End time must be after start time for {d.get('day_of_week')}"))
    if days:
        schedule_repo.upsert_days(schedule["id"], days)
    return success_response(_enrich_schedule(schedule), "Schedule created")


@router.put("/{schedule_id}")
def update_schedule(schedule_id: str, body: dict):
    s = schedule_repo.find_by_id(schedule_id)
    if not s:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Schedule {schedule_id} not found"))
    days = body.pop("days", None)
    updated = schedule_repo.update(schedule_id, body)
    if days is not None:
        schedule_repo.upsert_days(schedule_id, days)
    return success_response(_enrich_schedule(updated))


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: str):
    if not schedule_repo.delete(schedule_id):
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Schedule {schedule_id} not found"))
    return success_response(None, "Schedule deleted")
