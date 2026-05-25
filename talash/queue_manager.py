"""
queue_manager.py — Global asyncio queue, single background worker, live status.

Rules:
- One queue shared across ALL uploads (no per-upload tasks racing each other).
- Worker started ONCE at app startup, processes CVs one at a time.
- Status dict updated at every stage so GET /live-updates always reflects reality.
- If one CV fails, the error is logged and the worker moves to the next item.
"""

import asyncio
import traceback
from typing import Optional
from datetime import datetime

# ── Global queue ────────────────────────────────────────────────────────────
# Each item is a dict:
#   { "cv_label": str, "cv_text": str, "upload_id": str, "cv_num": int, "cv_total": int }
cv_queue: asyncio.Queue = asyncio.Queue()

# ── Live status (read by GET /live-updates) ─────────────────────────────────
processing_status: dict = {
    "status": "idle",           # idle | processing | completed | error
    "upload_id": None,
    "current_cv": 0,
    "total_cvs": 0,
    "current_candidate_name": None,
    "current_cv_label": None,
    "queue_depth": 0,
    "completed_count": 0,
    "failed_count": 0,
    "last_error": None,
    "last_updated": None,
}

# ── Per-upload tracking ─────────────────────────────────────────────────────
# upload_id → { total, done, failed, results[] }
upload_registry: dict[str, dict] = {}

_worker_task: Optional[asyncio.Task] = None


def _update_status(**kwargs):
    processing_status.update(kwargs)
    processing_status["queue_depth"] = cv_queue.qsize()
    processing_status["last_updated"] = datetime.utcnow().isoformat() + "Z"


async def _worker():
    """
    Single long-running coroutine.  Waits for items on cv_queue and processes
    them one at a time.  Never exits (runs until the process dies).
    """
    # Import here to avoid circular imports at module load time
    from .runner import app as langgraph_app, CVState

    print("[worker] CV queue worker started")

    while True:
        try:
            item = await cv_queue.get()
        except asyncio.CancelledError:
            print("[worker] Worker cancelled — shutting down")
            return

        cv_label  = item["cv_label"]
        cv_text   = item["cv_text"]
        upload_id = item["upload_id"]
        cv_num    = item["cv_num"]
        cv_total  = item["cv_total"]

        _update_status(
            status="processing",
            upload_id=upload_id,
            current_cv=cv_num,
            total_cvs=cv_total,
            current_candidate_name=None,       # filled in after extraction
            current_cv_label=cv_label,
        )

        print(f"\n[worker] Processing CV [{cv_num}/{cv_total}]  {cv_label}")

        try:
            state = CVState(
                pdf_path="",
                raw_texts=[(cv_label, cv_text)],
                all_results=[],
                error=None,
            )

            final_state = await langgraph_app.ainvoke(state)
            results     = final_state.get("all_results", [])
            result      = results[0] if results else {}

            # Extract name for live status
            info = result.get("personal_info") or {}
            name = info.get("name") or cv_label
            _update_status(current_candidate_name=name)

            summ   = result.get("summary") or {}
            score  = summ.get("overall_score", "—")
            grade  = summ.get("overall_grade", "—")
            status = summ.get("overall_status", "—")

            if "error" not in result:
                print(f"[worker] ✅ CV [{cv_num}/{cv_total}] DONE — {name} | {score}/100 [{grade}] {status}")
                _update_status(completed_count=processing_status["completed_count"] + 1)

                # Register result
                if upload_id in upload_registry:
                    upload_registry[upload_id]["results"].append(result)
                    upload_registry[upload_id]["done"] += 1
            else:
                raise RuntimeError(result.get("error", "Unknown pipeline error"))

        except Exception as exc:
            err_msg = str(exc)
            print(f"[worker] ❌ CV [{cv_num}/{cv_total}] FAILED — {cv_label}: {err_msg}")
            traceback.print_exc()
            _update_status(
                failed_count=processing_status["failed_count"] + 1,
                last_error=err_msg,
            )
            if upload_id in upload_registry:
                upload_registry[upload_id]["failed"] += 1

        finally:
            cv_queue.task_done()

            # If queue is now empty mark as idle
            if cv_queue.empty():
                _update_status(
                    status="idle",
                    current_cv=0,
                    total_cvs=0,
                    current_candidate_name=None,
                    current_cv_label=None,
                )


def start_worker():
    """
    Called once at FastAPI startup.  Creates the background worker task
    attached to the running event loop.
    """
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker())
        print("[worker] Background worker task created")


async def enqueue_cv(
    cv_label: str,
    cv_text:  str,
    upload_id: str,
    cv_num:   int,
    cv_total: int,
):
    """Put one CV on the queue.  Returns immediately."""
    await cv_queue.put({
        "cv_label":  cv_label,
        "cv_text":   cv_text,
        "upload_id": upload_id,
        "cv_num":    cv_num,
        "cv_total":  cv_total,
    })
    _update_status()   # refreshes queue_depth


def register_upload(upload_id: str, total: int):
    """Create a tracking entry for a new upload."""
    upload_registry[upload_id] = {
        "total":   total,
        "done":    0,
        "failed":  0,
        "results": [],
    }
