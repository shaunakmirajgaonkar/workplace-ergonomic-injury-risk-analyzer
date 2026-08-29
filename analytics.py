
import numpy as np
import pandas as pd

def normalize(df):
    x = df.copy()
    x.columns = [str(c).strip().lower().replace("-", "_").replace(" ", "_") for c in x.columns]
    return x

def num(s, default=0.0):
    return pd.to_numeric(s, errors="coerce").fillna(default)

def score_worker_records(workers, workstations):
    w = workers.copy()
    s = workstations.copy()

    s = s.drop_duplicates(subset=["worker_id"], keep="last")
    w = w.drop_duplicates(subset=["worker_id"], keep="last")

    x = w.merge(s, on="worker_id", how="left", validate="one_to_one")

    # Convert all component gaps to [0,1].
    shift = ((num(x["shift_hours"]) - 7.0) / 5.0).clip(0, 1)
    repeat = num(x["repetitive_index"]).clip(0,1)
    manual = num(x["manual_handling_index"]).clip(0,1)
    posture = num(x["posture_exposure_index"]).clip(0,1)
    force = num(x["force_index"]).clip(0,1)
    vibration = num(x["vibration_index"]).clip(0,1)
    pace = num(x["task_pacing_index"]).clip(0,1)
    discomfort = (num(x["discomfort_reports_90d"]) / 7.0).clip(0,1)
    prior = (num(x["prior_injury_reports"]) / 5.0).clip(0,1)
    missed = (num(x["breaks_missed_per_shift"]) / 5.0).clip(0,1)

    ws_cols = [
        "monitor_fit_gap","chair_support_gap","keyboard_mouse_gap",
        "reach_distance_gap","lighting_glare_gap","space_constraint_gap",
        "adjustability_gap","workstation_age_index"
    ]
    ws_gap = x[ws_cols].apply(pd.to_numeric, errors="coerce").fillna(0).mean(axis=1).clip(0,1)

    x["ergonomic_risk_score"] = (
        100 * (
            .09*shift + .14*repeat + .09*manual + .14*posture +
            .08*force + .06*vibration + .07*pace + .13*discomfort +
            .08*prior + .05*missed + .07*ws_gap
        )
    ).clip(0,100).round(1)

    x["risk_band"] = pd.cut(
        x["ergonomic_risk_score"],
        [-0.1,24.9,49.9,74.9,100.1],
        labels=["Low","Moderate","High","Critical"]
    )

    x["primary_driver"] = np.select(
        [
            discomfort >= .60,
            posture >= .65,
            repeat >= .70,
            shift >= .60,
            manual >= .68,
            force >= .62,
            pace >= .68,
            ws_gap >= .60,
            vibration >= .60,
            missed >= .60
        ],
        [
            "Reported discomfort",
            "Posture exposure",
            "Repetitive task exposure",
            "Extended shift duration",
            "Manual-handling load",
            "Force demand",
            "High task pacing",
            "Workstation fit gaps",
            "Vibration exposure",
            "Missed breaks"
        ],
        default="Mixed ergonomic conditions"
    )

    return x
