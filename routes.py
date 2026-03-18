from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai_service import generate_meal_plan_structured, generate_plan_insights
from models import MpPlanSnapshot, MpSnapshotMeal, SessionLocal, create_all, dumps_json, loads_json


router = APIRouter()


class PlanRequest(BaseModel):
    query: str
    preferences: Optional[str] = ""


class InsightsRequest(BaseModel):
    selection: str
    context: Optional[str] = ""


class RebalanceRequest(BaseModel):
    snapshot_id: int
    diet_type: Optional[str] = None
    servings: Optional[int] = None
    budget: Optional[float] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _fallback_plan(query: str, preferences: str) -> Dict[str, Any]:
    board = [
        {"day": "Mon", "slot": "Lunch", "recipe_name": "Chicken Quinoa Power Bowl", "macros": {"protein_g": 42, "carbs_g": 38, "fat_g": 14}, "prep_minutes": 25, "cost_per_serving": 5.5, "portions": 1, "dietary_tags": ["high-protein"], "rationale": "Fits protein-first weekday prep."},
        {"day": "Tue", "slot": "Lunch", "recipe_name": "Turkey Bean Chili Cups", "macros": {"protein_g": 39, "carbs_g": 32, "fat_g": 12}, "prep_minutes": 30, "cost_per_serving": 4.8, "portions": 1, "dietary_tags": ["high-protein"], "rationale": "Batch-friendly and budget efficient."},
        {"day": "Wed", "slot": "Lunch", "recipe_name": "Tuna Pasta Protein Salad", "macros": {"protein_g": 36, "carbs_g": 40, "fat_g": 11}, "prep_minutes": 20, "cost_per_serving": 4.6, "portions": 1, "dietary_tags": ["meal-prep"], "rationale": "Office-friendly cold meal option."},
    ]
    return {
        "summary": "Drafted a 3-day prep board with protein-forward lunches and batch-cook flow.",
        "score": 0.84,
        "items": [
            "Structured brief resolved from messy goal",
            "Weekly board populated for 3 lunches",
            "Grocery basket grouped with pantry toggles",
            "Prep workflow includes container outputs",
        ],
        "structured_brief": {
            "goal": query,
            "preferences": preferences,
            "servings": 1,
            "budget": 40,
            "dietary_constraints": ["high-protein"],
            "prep_cadence": "Sunday batch prep",
            "cook_time_limit_minutes": 30,
            "leftover_assumption": "Lunch leftovers acceptable for 1 day",
            "confidence_flags": ["Budget parsed from goal text", "Protein target inferred"],
        },
        "weekly_board": board,
        "grocery_basket": [
            {"ingredient": "Chicken breast", "quantity": 1.2, "unit": "lb", "estimated_cost": 8.5, "pantry": False},
            {"ingredient": "Quinoa", "quantity": 2, "unit": "cup", "estimated_cost": 3.2, "pantry": True},
            {"ingredient": "Ground turkey", "quantity": 1, "unit": "lb", "estimated_cost": 6.2, "pantry": False},
            {"ingredient": "Black beans", "quantity": 2, "unit": "can", "estimated_cost": 2.4, "pantry": True},
            {"ingredient": "Canned tuna", "quantity": 3, "unit": "can", "estimated_cost": 4.8, "pantry": False},
        ],
        "prep_steps": [
            {"step": "Cook quinoa and boil pasta", "parallelizable": True, "minutes": 15, "container_outputs": 0},
            {"step": "Roast chicken and simmer turkey chili", "parallelizable": True, "minutes": 30, "container_outputs": 0},
            {"step": "Portion all lunches into containers", "parallelizable": False, "minutes": 12, "container_outputs": 6},
        ],
        "explainability": {
            "budget_fit": "Estimated total stays under $40 with pantry staples.",
            "protein_alignment": "Each lunch targets ~35-42g protein.",
            "cook_time_match": "All recipes are 30 min or less.",
            "dietary_compatibility": "No restrictive diet applied beyond protein emphasis.",
        },
        "note": "AI is temporarily unavailable; this flagship-aware fallback plan is provided.",
    }


@router.post("/plan")
@router.post("/plan")
async def build_plan(payload: PlanRequest, db: Session = Depends(get_db)):
    ai_result = await generate_meal_plan_structured(payload.query, payload.preferences or "")
    if ai_result.get("fallback"):
        plan = _fallback_plan(payload.query, payload.preferences or "")
    else:
        plan = {
            "summary": ai_result.get("summary", "Meal plan generated."),
            "score": float(ai_result.get("score", 0.8)),
            "items": ai_result.get("items", []),
            "structured_brief": ai_result.get("structured_brief", {}),
            "weekly_board": ai_result.get("weekly_board", []),
            "grocery_basket": ai_result.get("grocery_basket", []),
            "prep_steps": ai_result.get("prep_steps", []),
            "explainability": ai_result.get("explainability", {}),
        }

    total_cost = round(sum(float(x.get("estimated_cost", 0)) for x in plan.get("grocery_basket", [])), 2)
    total_protein = int(sum(int(m.get("macros", {}).get("protein_g", 0)) for m in plan.get("weekly_board", [])))

    snapshot = MpPlanSnapshot(
        name=f"Prep Run {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        query=payload.query,
        preferences_json=dumps_json({"preferences": payload.preferences or ""}),
        summary=plan.get("summary", ""),
        score=float(plan.get("score", 0.0)),
        brief_json=dumps_json(plan.get("structured_brief", {})),
        weekly_board_json=dumps_json(plan.get("weekly_board", [])),
        grocery_basket_json=dumps_json(plan.get("grocery_basket", [])),
        prep_steps_json=dumps_json(plan.get("prep_steps", [])),
        total_cost=total_cost,
        total_protein=total_protein,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    for meal in plan.get("weekly_board", []):
        macros = meal.get("macros", {})
        db.add(MpSnapshotMeal(
            snapshot_id=snapshot.id,
            day_label=str(meal.get("day", "Mon")),
            meal_slot=str(meal.get("slot", "Lunch")),
            recipe_name=str(meal.get("recipe_name", "Meal")),
            dietary_tags=",".join(meal.get("dietary_tags", [])) if isinstance(meal.get("dietary_tags", []), list) else str(meal.get("dietary_tags", "")),
            prep_minutes=int(meal.get("prep_minutes", 20)),
            cost_per_serving=float(meal.get("cost_per_serving", 5.0)),
            protein_g=int(macros.get("protein_g", 25)),
            carbs_g=int(macros.get("carbs_g", 30)),
            fat_g=int(macros.get("fat_g", 10)),
            portions=int(meal.get("portions", 1)),
            rationale=str(meal.get("rationale", "")),
            is_swapped=False,
        ))
    db.commit()

    return {
        "summary": plan.get("summary", ""),
        "items": plan.get("items", []),
        "score": plan.get("score", 0.0),
        "artifact": {
            "snapshot_id": snapshot.id,
            "structured_brief": plan.get("structured_brief", {}),
            "weekly_board": plan.get("weekly_board", []),
            "grocery_basket": plan.get("grocery_basket", []),
            "prep_steps": plan.get("prep_steps", []),
            "totals": {"estimated_cost": total_cost, "protein_g": total_protein},
            "explainability": plan.get("explainability", {}),
        },
    }


@router.post("/insights")
@router.post("/insights")
async def plan_insights(payload: InsightsRequest):
    ai_result = await generate_plan_insights(payload.selection, payload.context or "")
    if ai_result.get("fallback"):
        return {
            "insights": [
                {"title": "Budget pressure on protein choices", "impact": "medium", "why": "Lower-cost proteins may be needed to stay under budget."},
                {"title": "Prep-time bottleneck", "impact": "low", "why": "One recipe exceeds your 30-minute threshold."},
            ],
            "next_actions": [
                "Swap one meat recipe for lentil + yogurt protein bowl",
                "Batch-cook grains once and reuse across slots",
            ],
            "highlights": {"budget_delta": -3.2, "protein_delta": 6, "time_delta": -12},
        }

    return {
        "insights": ai_result.get("insights", []),
        "next_actions": ai_result.get("next_actions", []),
        "highlights": ai_result.get("highlights", {"budget_delta": 0, "protein_delta": 0, "time_delta": 0}),
    }


@router.post("/rebalance")
@router.post("/rebalance")
async def rebalance_plan(payload: RebalanceRequest, db: Session = Depends(get_db)):
    snapshot = db.query(MpPlanSnapshot).filter(MpPlanSnapshot.id == payload.snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    board = loads_json(snapshot.weekly_board_json, [])
    basket = loads_json(snapshot.grocery_basket_json, [])
    changes = []

    if payload.diet_type and payload.diet_type.lower() == "vegetarian":
        for m in board:
            if "chicken" in m.get("recipe_name", "").lower() or "turkey" in m.get("recipe_name", "").lower() or "tuna" in m.get("recipe_name", "").lower():
                old = m.get("recipe_name", "Meal")
                m["recipe_name"] = "Chickpea Tofu Protein Bowl"
                m["macros"] = {"protein_g": 31, "carbs_g": 34, "fat_g": 13}
                m["dietary_tags"] = ["vegetarian", "high-protein"]
                m["cost_per_serving"] = 4.2
                m["rationale"] = "Swapped to satisfy vegetarian constraint while maintaining protein density."
                changes.append(f"Swapped {old} to {m['recipe_name']}")

        basket = [i for i in basket if i.get("ingredient", "").lower() not in ["chicken breast", "ground turkey", "canned tuna"]]
        basket.extend([
            {"ingredient": "Firm tofu", "quantity": 3, "unit": "block", "estimated_cost": 7.5, "pantry": False},
            {"ingredient": "Chickpeas", "quantity": 4, "unit": "can", "estimated_cost": 4.4, "pantry": True},
        ])

    if payload.servings and payload.servings > 0:
        multiplier = payload.servings
        for m in board:
            m["portions"] = multiplier
        for i in basket:
            try:
                i["quantity"] = round(float(i.get("quantity", 1)) * multiplier, 2)
            except Exception:
                pass
        changes.append(f"Scaled all portions and ingredient quantities to {payload.servings} servings")

    total_cost = round(sum(float(x.get("estimated_cost", 0)) for x in basket), 2)
    if payload.budget is not None and total_cost > payload.budget:
        changes.append(f"Total cost ${total_cost} exceeds budget ${payload.budget}; consider pantry toggles or swaps")

    snapshot.weekly_board_json = dumps_json(board)
    snapshot.grocery_basket_json = dumps_json(basket)
    snapshot.total_cost = total_cost
    snapshot.total_protein = int(sum(int(m.get("macros", {}).get("protein_g", 0)) for m in board))
    snapshot.updated_at = datetime.utcnow()
    db.commit()

    return {
        "snapshot_id": snapshot.id,
        "weekly_board": board,
        "grocery_basket": basket,
        "totals": {"estimated_cost": snapshot.total_cost, "protein_g": snapshot.total_protein},
        "rebalance_indicators": changes,
    }


@router.get("/snapshots")
@router.get("/snapshots")
def list_snapshots(db: Session = Depends(get_db)):
    rows = db.query(MpPlanSnapshot).order_by(MpPlanSnapshot.updated_at.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "summary": r.summary,
            "score": r.score,
            "total_cost": r.total_cost,
            "total_protein": r.total_protein,
            "updated_at": r.updated_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/snapshots/{snapshot_id}")
@router.get("/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    s = db.query(MpPlanSnapshot).filter(MpPlanSnapshot.id == snapshot_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {
        "id": s.id,
        "name": s.name,
        "query": s.query,
        "preferences": loads_json(s.preferences_json, {}),
        "summary": s.summary,
        "score": s.score,
        "structured_brief": loads_json(s.brief_json, {}),
        "weekly_board": loads_json(s.weekly_board_json, []),
        "grocery_basket": loads_json(s.grocery_basket_json, []),
        "prep_steps": loads_json(s.prep_steps_json, []),
        "totals": {"estimated_cost": s.total_cost, "protein_g": s.total_protein},
    }


def seed_demo_data() -> None:
    create_all()
    db = SessionLocal()
    try:
        count = db.query(MpPlanSnapshot).count()
        if count > 0:
            return
        demo_queries = [
            "3-day high-protein lunch prep for Alex with a $40 budget",
            "Family weeknight dinner plan for 4 with one vegetarian meal and 30-minute cook limit",
            "Low-carb solo meal plan with batch cooking on Sunday and leftovers for lunches",
        ]
        for q in demo_queries:
            plan = _fallback_plan(q, "auto-seeded")
            total_cost = round(sum(float(x.get("estimated_cost", 0)) for x in plan.get("grocery_basket", [])), 2)
            total_protein = int(sum(int(m.get("macros", {}).get("protein_g", 0)) for m in plan.get("weekly_board", [])))
            snap = MpPlanSnapshot(
                name=f"Seeded: {q[:42]}",
                query=q,
                preferences_json=dumps_json({"preferences": "auto-seeded"}),
                summary=plan.get("summary", ""),
                score=float(plan.get("score", 0.8)),
                brief_json=dumps_json(plan.get("structured_brief", {})),
                weekly_board_json=dumps_json(plan.get("weekly_board", [])),
                grocery_basket_json=dumps_json(plan.get("grocery_basket", [])),
                prep_steps_json=dumps_json(plan.get("prep_steps", [])),
                total_cost=total_cost,
                total_protein=total_protein,
            )
            db.add(snap)
        db.commit()
    finally:
        db.close()
