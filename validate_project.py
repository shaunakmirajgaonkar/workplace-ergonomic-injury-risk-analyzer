
from pathlib import Path
import pandas as pd
from analytics import score_worker_records

ROOT = Path(__file__).resolve().parent
workers = pd.read_csv(ROOT / "data/sample_worker_task_records.csv")
workstations = pd.read_csv(ROOT / "data/sample_workstation_assessments.csv")

out = score_worker_records(workers, workstations)

assert len(out) == 30
assert out.ergonomic_risk_score.between(0,100).all()
assert out.risk_band.notna().all()
assert len(set(out.columns)) == len(out.columns)

print("PASS: workplace ergonomic scoring")
print("Rows:", len(out))
print("Risk range:", out.ergonomic_risk_score.min(), "-", out.ergonomic_risk_score.max())
