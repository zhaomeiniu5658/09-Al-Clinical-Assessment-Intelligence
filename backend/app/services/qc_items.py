import re
from typing import Any

from app.services.doctor_test import HAMD17_ITEMS


def merge_item_results(
    doctor_items: list[dict[str, Any]],
    ai_items: list[dict[str, Any]],
    *,
    assume_missing_ai_matches: bool = False,
    existing_items: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Merge Dify rows into the complete doctor score sheet by item number."""
    by_number = {
        item_number: row
        for row in ai_items
        if (item_number := _item_number(row.get("hamd_item"))) is not None
    }
    if len(by_number) < len(ai_items):
        by_number.update(
            {
                index + 1: row
                for index, row in enumerate(ai_items)
                if index + 1 not in by_number
            }
        )
    existing_by_number = {
        item_number: row
        for row in existing_items or []
        if (item_number := _item_number(row.get("hamd_item"))) is not None
    }
    merged: list[dict[str, Any]] = []

    for index, doctor_row in enumerate(doctor_items):
        item_number = index + 1
        ai_row = by_number.get(item_number) or {}
        existing_row = existing_by_number.get(item_number) or {}
        doctor_score = doctor_row.get("doctor_score")
        ai_score = ai_row.get("ai_score")
        if ai_score is None and assume_missing_ai_matches and ai_items:
            ai_score = doctor_score

        row = {
            "hamd_item": doctor_row.get("hamd_item") or HAMD17_ITEMS[index],
            "doctor_score": doctor_score,
            "ai_score": ai_score,
            "ai_scoring_basis": ai_row.get("ai_scoring_basis"),
            "difference": _difference(doctor_score, ai_score),
        }
        review_score = _first_present(doctor_row, ai_row, existing_row, key="review_score")
        review_opinion = _first_present(doctor_row, ai_row, existing_row, key="review_opinion")
        if review_score is not None:
            row["review_score"] = review_score
        if review_opinion is not None:
            row["review_opinion"] = review_opinion
        merged.append(row)

    return merged


def _item_number(value: Any) -> int | None:
    if value is None:
        return None
    match = re.match(r"^\s*(\d{1,2})\s*[.、)|\s]", str(value))
    return int(match.group(1)) if match else None


def _difference(doctor_score: Any, ai_score: Any) -> float | int | None:
    if not isinstance(doctor_score, int | float) or not isinstance(ai_score, int | float):
        return None
    difference = abs(float(ai_score) - float(doctor_score))
    return int(difference) if difference.is_integer() else difference


def _first_present(*rows: dict[str, Any], key: str) -> Any:
    for row in rows:
        value = row.get(key)
        if value is not None:
            return value
    return None
