from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "docs" / "evidence" / "pilot-proof-metrics.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_utc(value: str) -> datetime:
    if not value.endswith("Z"):
        raise AssertionError(f"timestamp must be UTC/Z: {value}")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_ratio(actual: float, numerator: int, denominator: int) -> None:
    expected = numerator / denominator
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
        raise AssertionError(
            f"ratio mismatch: actual={actual} expected={expected} "
            f"for {numerator}/{denominator}"
        )


def verify_pilot(pilot: dict) -> tuple[int, int, int, int]:
    pilot_id = pilot["id"]
    manifest_path = ROOT / pilot["manifest_path"]
    if not manifest_path.is_file():
        raise AssertionError(f"{pilot_id}: missing manifest {manifest_path}")

    manifest = load_json(manifest_path)
    if manifest.get("blueprint") != pilot["expected_blueprint"]:
        raise AssertionError(f"{pilot_id}: blueprint mismatch")
    if manifest.get("modules") != pilot["expected_manifest_modules"]:
        raise AssertionError(f"{pilot_id}: manifest module list mismatch")

    expected_reused_modules = len(pilot["expected_manifest_modules"]) + len(
        pilot["additional_reused_runtime_modules"]
    )
    reuse = pilot["module_reuse"]
    if reuse["reused_modules"] != expected_reused_modules:
        raise AssertionError(f"{pilot_id}: reused module count mismatch")

    expected_building_blocks = expected_reused_modules + pilot["generated_product_shells"]
    if reuse["counted_runtime_building_blocks"] != expected_building_blocks:
        raise AssertionError(f"{pilot_id}: runtime building-block count mismatch")
    assert_ratio(reuse["ratio"], expected_reused_modules, expected_building_blocks)

    manual_edits = pilot["manual_post_generation_product_source_edits"]
    if manual_edits != 0:
        raise AssertionError(
            f"{pilot_id}: pilot proof must record any manual generated-product edits explicitly"
        )
    if pilot["manual_product_code_avoidance_ratio"] != 1.0:
        raise AssertionError(f"{pilot_id}: manual product-code avoidance ratio mismatch")

    created = parse_utc(pilot["pr_created_at"])
    first_working = pilot["first_working_runtime"]
    completed = parse_utc(first_working["completed_at"])
    measured_seconds = int((completed - created).total_seconds())
    if first_working["seconds_from_pr_open"] != measured_seconds:
        raise AssertionError(
            f"{pilot_id}: first-working duration mismatch: "
            f"recorded={first_working['seconds_from_pr_open']} calculated={measured_seconds}"
        )
    if measured_seconds < 0:
        raise AssertionError(f"{pilot_id}: negative first-working duration")

    for evidence_key in ("first_working_runtime", "final_exact_head"):
        evidence = pilot[evidence_key]
        if not SHA_RE.fullmatch(evidence["head_sha"]):
            raise AssertionError(f"{pilot_id}: invalid SHA in {evidence_key}")
        if not isinstance(evidence["workflow_run_id"], int) or evidence["workflow_run_id"] <= 0:
            raise AssertionError(f"{pilot_id}: invalid workflow run id in {evidence_key}")

    final_exact = pilot["final_exact_head"]
    if final_exact["conclusion"] != "success":
        raise AssertionError(f"{pilot_id}: final exact-head evidence is not successful")
    if parse_utc(final_exact["completed_at"]) < completed:
        raise AssertionError(f"{pilot_id}: final exact-head proof predates first working proof")

    unresolved = pilot["unresolved_exact_head_regressions"]
    if not isinstance(unresolved, int) or unresolved < 0:
        raise AssertionError(f"{pilot_id}: invalid unresolved regression count")

    defects = pilot["pilot_blocking_defects_found_and_fixed"]
    if not isinstance(defects, list) or any(not isinstance(item, str) or not item for item in defects):
        raise AssertionError(f"{pilot_id}: defect list must contain non-empty strings")

    production_candidate = pilot["production_candidate"]
    pc_status = production_candidate["status"]
    if pc_status == "open_not_reached":
        if production_candidate["completed_at"] is not None:
            raise AssertionError(f"{pilot_id}: open production candidate cannot have completed_at")
        if production_candidate["seconds_from_pr_open"] is not None:
            raise AssertionError(f"{pilot_id}: open production candidate cannot have duration")
    elif pc_status == "reached":
        pc_completed = parse_utc(production_candidate["completed_at"])
        pc_seconds = int((pc_completed - created).total_seconds())
        if production_candidate["seconds_from_pr_open"] != pc_seconds:
            raise AssertionError(f"{pilot_id}: production-candidate duration mismatch")
    else:
        raise AssertionError(f"{pilot_id}: unsupported production-candidate status {pc_status}")

    return expected_reused_modules, expected_building_blocks, manual_edits, len(defects)


def main() -> None:
    metrics = load_json(METRICS_PATH)
    if metrics.get("schema_version") != 1:
        raise AssertionError("unsupported pilot-proof metrics schema")
    if metrics.get("status") != "open":
        raise AssertionError("Phase 8 must remain open until production-candidate duration is reached")

    pilots = metrics.get("pilots")
    if not isinstance(pilots, list) or len(pilots) < 2:
        raise AssertionError("Phase 8 requires at least two pilots")

    ids = [pilot["id"] for pilot in pilots]
    platforms = [pilot["platform"] for pilot in pilots]
    if len(ids) != len(set(ids)):
        raise AssertionError("pilot ids must be unique")
    if len(set(platforms)) < 2:
        raise AssertionError("pilots must be materially different at the platform/boundary level")

    reused_total = 0
    building_blocks_total = 0
    manual_edits_total = 0
    defects_total = 0
    unresolved_total = 0
    pc_statuses: set[str] = set()

    for pilot in pilots:
        reused, building_blocks, manual_edits, defects = verify_pilot(pilot)
        reused_total += reused
        building_blocks_total += building_blocks
        manual_edits_total += manual_edits
        defects_total += defects
        unresolved_total += pilot["unresolved_exact_head_regressions"]
        pc_statuses.add(pilot["production_candidate"]["status"])

    combined = metrics["combined"]
    if combined["reused_modules"] != reused_total:
        raise AssertionError("combined reused module count mismatch")
    if combined["counted_runtime_building_blocks"] != building_blocks_total:
        raise AssertionError("combined runtime building-block count mismatch")
    assert_ratio(combined["module_reuse_ratio"], reused_total, building_blocks_total)
    if combined["manual_post_generation_product_source_edits"] != manual_edits_total:
        raise AssertionError("combined manual post-generation edit count mismatch")
    if combined["pilot_blocking_defects_found_and_fixed"] != defects_total:
        raise AssertionError("combined defect count mismatch")
    if combined["unresolved_exact_head_regressions"] != unresolved_total:
        raise AssertionError("combined unresolved regression count mismatch")

    expected_pc_status = "open_not_reached" if pc_statuses == {"open_not_reached"} else "mixed_or_reached"
    if combined["production_candidate_duration_status"] != expected_pc_status:
        raise AssertionError("combined production-candidate status mismatch")

    print(
        "Pilot proof metrics verified: "
        f"{len(pilots)} pilots, reuse={reused_total}/{building_blocks_total}, "
        f"manual_post_generation_edits={manual_edits_total}, "
        f"fixed_blockers={defects_total}, unresolved_regressions={unresolved_total}."
    )


if __name__ == "__main__":
    main()
