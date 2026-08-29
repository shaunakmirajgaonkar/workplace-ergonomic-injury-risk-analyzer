
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics import normalize, score_worker_records

def test_normalize():
    x = normalize(pd.DataFrame({"Worker ID":[1], "Task-Type":[2]}))
    assert list(x.columns) == ["worker_id", "task_type"]

def test_score_bounds_and_unique_columns():
    workers = pd.DataFrame({
        "worker_id":["W1","W2"],
        "worker_name":["A","B"],
        "department":["Assembly","Support"],
        "zone":["North","South"],
        "task_type":["Repetitive Assembly","Keyboard Intensive"],
        "shift_hours":[8,12],
        "repetitive_index":[.2,.9],
        "manual_handling_index":[.1,.7],
        "posture_exposure_index":[.2,.9],
        "force_index":[.1,.7],
        "vibration_index":[.1,.5],
        "task_pacing_index":[.2,.9],
        "discomfort_reports_90d":[0,6],
        "prior_injury_reports":[0,3],
        "breaks_missed_per_shift":[0,4],
    })
    ws = pd.DataFrame({
        "worker_id":["W1","W2"],
        "monitor_fit_gap":[.1,.8],
        "chair_support_gap":[.1,.8],
        "keyboard_mouse_gap":[.1,.8],
        "reach_distance_gap":[.1,.8],
        "lighting_glare_gap":[.1,.7],
        "space_constraint_gap":[.1,.7],
        "adjustability_gap":[.1,.9],
        "workstation_age_index":[.1,.8],
    })
    out = score_worker_records(workers, ws)
    assert out.ergonomic_risk_score.between(0,100).all()
    assert out.risk_band.notna().all()
    assert out.primary_driver.notna().all()
    assert len(set(out.columns)) == len(out.columns)
