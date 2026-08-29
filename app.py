
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from analytics import normalize, score_worker_records

st.set_page_config(
    page_title="Workplace Ergonomic Injury Risk Analyzer",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.markdown("""
<style>
.stApp{
    background:linear-gradient(180deg,#fbfefd 0%,#f3f7fb 55%,#fff7f2 100%);
    color:#233447;
}
.block-container{max-width:1550px;padding-top:1rem;padding-bottom:2rem}
[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #dfe8ef}
[data-testid="stSidebar"] *{color:#233447!important}
.hero{
    background:linear-gradient(135deg,#effcf8 0%,#edf6ff 55%,#fff4e8 100%);
    border:1px solid #dce8e7;border-radius:28px;padding:29px 31px;
    margin-bottom:20px;box-shadow:0 14px 34px rgba(38,60,78,.06)
}
.eyebrow{font-size:.73rem;font-weight:900;letter-spacing:.15em;color:#2a7f68;text-transform:uppercase}
.hero h1{font-size:2.35rem;line-height:1.08;margin:.4rem 0 .55rem;color:#223447!important}
.hero p{color:#607286;max-width:1180px;margin:0;font-size:1rem}
.pill{
 display:inline-block;background:#fff;border:1px solid #dbe5ec;border-radius:999px;
 padding:7px 12px;margin:12px 6px 0 0;font-size:.82rem;font-weight:780;color:#41576c
}
.card{
 background:#fff;border:1px solid #dfe7ec;border-radius:18px;padding:16px;
 box-shadow:0 9px 25px rgba(32,55,73,.045)
}
.label{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;font-weight:850;color:#758698}
.value{font-size:1.9rem;font-weight:880;color:#203447;margin-top:4px}
.sub{font-size:.77rem;color:#7c8d9d}
.section{font-size:1.18rem;font-weight:880;color:#24374a;margin:24px 0 11px}
.note{
 background:#fff8ec;border:1px solid #eddcba;border-radius:15px;
 padding:14px 16px;color:#6b5328
}
.footer{text-align:center;color:#82909d;font-size:.75rem;margin-top:20px}
</style>
""", unsafe_allow_html=True)

def counts(s, name):
    return s.astype(str).value_counts(dropna=False).rename_axis(name).reset_index(name="count")

st.sidebar.markdown("## 🧘 ErgoGuard Local")
st.sidebar.caption("Screen • Understand • Review")
page = st.sidebar.radio(
    "Workspace",
    [
        "Dashboard","Worker Register","Ergonomic Risk","Workstation Fit",
        "Discomfort Analytics","Shift & Workload","Department Comparison",
        "Zone Comparison","Priority Review Queue","Scenario Lab","Reports & Export"
    ],
    label_visibility="collapsed"
)
st.sidebar.divider()

u1 = st.sidebar.file_uploader("Upload authorized worker-task CSV", type=["csv"])
u2 = st.sidebar.file_uploader("Upload workstation-assessment CSV", type=["csv"])
u3 = st.sidebar.file_uploader("Upload discomfort-report CSV", type=["csv"])
u4 = st.sidebar.file_uploader("Upload shift/environment CSV", type=["csv"])

workers = normalize(pd.read_csv(u1) if u1 else pd.read_csv(DATA/"sample_worker_task_records.csv"))
workstations = normalize(pd.read_csv(u2) if u2 else pd.read_csv(DATA/"sample_workstation_assessments.csv"))
discomfort = normalize(pd.read_csv(u3) if u3 else pd.read_csv(DATA/"sample_discomfort_reports.csv"))
context = normalize(pd.read_csv(u4) if u4 else pd.read_csv(DATA/"sample_shift_environment_context.csv"))

required = [
    "worker_id","worker_name","department","zone","task_type","shift_hours",
    "repetitive_index","manual_handling_index","posture_exposure_index",
    "force_index","vibration_index","task_pacing_index",
    "discomfort_reports_90d","prior_injury_reports","breaks_missed_per_shift"
]
missing = [c for c in required if c not in workers.columns]
if missing:
    st.error("Missing worker-task columns: " + ", ".join(missing))
    st.stop()

ws_required = [
    "worker_id","monitor_fit_gap","chair_support_gap","keyboard_mouse_gap",
    "reach_distance_gap","lighting_glare_gap","space_constraint_gap",
    "adjustability_gap","workstation_age_index"
]
missing_ws = [c for c in ws_required if c not in workstations.columns]
if missing_ws:
    st.error("Missing workstation columns: " + ", ".join(missing_ws))
    st.stop()

scored = score_worker_records(workers, workstations)

zones = ["All"] + sorted(scored.zone.astype(str).unique())
bands = ["All","Low","Moderate","High","Critical"]
sel_zone = st.sidebar.selectbox("Zone", zones)
sel_band = st.sidebar.selectbox("Risk band", bands)
threshold = st.sidebar.slider("Minimum risk score", 0, 100, 0)

view = scored.copy()
if sel_zone != "All":
    view = view[view.zone.astype(str) == sel_zone]
if sel_band != "All":
    view = view[view.risk_band.astype(str) == sel_band]
view = view[view.ergonomic_risk_score >= threshold]

if view.empty:
    st.warning("No records match the current filters.")
    st.stop()

st.markdown("""
<div class="hero">
<div class="eyebrow">WORKPLACE ERGONOMICS • LOCAL-FIRST • EXPLAINABLE SCREENING</div>
<h1>Identify ergonomic conditions that may merit earlier workplace-safety review.</h1>
<p>Combine task repetition, posture exposure, manual handling, force, vibration, shift duration, task pacing, workstation fit, reported discomfort, prior injury records and missed breaks to support transparent ergonomic-review planning.</p>
<span class="pill">🔁 Repetition</span><span class="pill">🪑 Workstation Fit</span><span class="pill">🧍 Posture</span><span class="pill">🧰 Manual Handling</span><span class="pill">⏱️ Shift Duration</span><span class="pill">💬 Discomfort</span><span class="pill">🔒 Local Processing</span>
</div>
""", unsafe_allow_html=True)

kpis = [
    ("Workers", view.worker_id.nunique(), "Workers in filter"),
    ("High / Critical", int((view.ergonomic_risk_score >= 50).sum()), "Review-priority signals"),
    ("Critical", int((view.ergonomic_risk_score >= 75).sum()), "Highest screening band"),
    ("Discomfort reports", int(view.discomfort_reports_90d.sum()), "Reported in 90 days"),
    ("Avg risk", f"{view.ergonomic_risk_score.mean():.1f}", "Average screening score"),
]
cards = st.columns(5)
for c,(a,b,d) in zip(cards,kpis):
    c.markdown(
        f'<div class="card"><div class="label">{a}</div><div class="value">{b}</div><div class="sub">{d}</div></div>',
        unsafe_allow_html=True
    )

if page == "Dashboard":
    st.markdown('<div class="section">Ergonomic command view</div>', unsafe_allow_html=True)
    a,b,c = st.columns([1,1.25,1])
    with a:
        mix = counts(view.risk_band,"band")
        order = pd.CategoricalDtype(["Low","Moderate","High","Critical"], ordered=True)
        mix["band"] = mix["band"].astype(order)
        mix = mix.sort_values("band")
        fig = px.pie(mix, names="band", values="count", hole=.62, title="Risk distribution", template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    with b:
        fig = px.scatter(
            view, x="repetitive_index", y="ergonomic_risk_score",
            size="discomfort_reports_90d", color="posture_exposure_index",
            hover_name="worker_name",
            hover_data=["task_type","shift_hours","manual_handling_index","primary_driver"],
            range_x=[0,1], range_y=[0,100],
            title="Repetition × ergonomic-risk signal", template="plotly_white"
        )
        st.plotly_chart(fig, width="stretch")
    with c:
        top = view.sort_values("ergonomic_risk_score", ascending=False).head(8)
        fig = px.bar(
            top.sort_values("ergonomic_risk_score"),
            x="ergonomic_risk_score", y="worker_name", orientation="h",
            text_auto=".0f", range_x=[0,100],
            title="Priority workers", template="plotly_white"
        )
        st.plotly_chart(fig, width="stretch")

    d,e = st.columns(2)
    with d:
        z = view.groupby("zone", as_index=False).agg(
            avg_risk=("ergonomic_risk_score","mean"),
            workers=("worker_id","nunique")
        )
        fig = px.bar(z, x="zone", y="avg_risk", text_auto=".0f", range_y=[0,100],
                     title="Zone risk comparison", template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    with e:
        drv = counts(view.primary_driver,"driver")
        fig = px.bar(drv.sort_values("count"), x="count", y="driver",
                     orientation="h", text_auto=True,
                     title="Primary ergonomic drivers", template="plotly_white")
        st.plotly_chart(fig, width="stretch")

    st.markdown('<div class="section">Current worker register</div>', unsafe_allow_html=True)
    st.dataframe(
        view.sort_values("ergonomic_risk_score", ascending=False),
        width="stretch", hide_index=True
    )
    visual = ROOT/"assets/workplace_ergonomic_dashboard_visual.svg"
    if visual.exists():
        with st.expander("Dashboard visual"):
            st.image(str(visual), width="stretch")

elif page == "Worker Register":
    st.markdown('<div class="section">Worker and task register</div>', unsafe_allow_html=True)
    q = st.text_input("Search worker, department, zone or task type")
    v = view.copy()
    if q:
        s = q.lower()
        v = v[
            v.worker_name.str.lower().str.contains(s,na=False) |
            v.department.str.lower().str.contains(s,na=False) |
            v.zone.str.lower().str.contains(s,na=False) |
            v.task_type.str.lower().str.contains(s,na=False)
        ]
    st.dataframe(v.sort_values("ergonomic_risk_score", ascending=False),
                 width="stretch", hide_index=True)

elif page == "Ergonomic Risk":
    st.markdown('<div class="section">Ergonomic risk analytics</div>', unsafe_allow_html=True)
    a,b = st.columns(2)
    with a:
        fig = px.scatter(
            view, x="posture_exposure_index", y="ergonomic_risk_score",
            size="shift_hours", color="task_type", hover_name="worker_name",
            range_x=[0,1], range_y=[0,100],
            title="Posture exposure × risk", template="plotly_white"
        )
        st.plotly_chart(fig, width="stretch")
    with b:
        fig = px.scatter(
            view, x="manual_handling_index", y="ergonomic_risk_score",
            size="force_index", color="zone", hover_name="worker_name",
            range_x=[0,1], range_y=[0,100],
            title="Manual handling × risk", template="plotly_white"
        )
        st.plotly_chart(fig, width="stretch")
    st.dataframe(
        view[[
            "worker_id","worker_name","department","zone","task_type",
            "ergonomic_risk_score","risk_band","primary_driver",
            "shift_hours","repetitive_index","posture_exposure_index",
            "manual_handling_index","force_index","discomfort_reports_90d"
        ]].sort_values("ergonomic_risk_score", ascending=False),
        width="stretch", hide_index=True
    )

elif page == "Workstation Fit":
    st.markdown('<div class="section">Workstation fit analytics</div>', unsafe_allow_html=True)
    ws_view = view[["worker_id","worker_name","department","zone","ergonomic_risk_score",
                    "monitor_fit_gap","chair_support_gap","keyboard_mouse_gap",
                    "reach_distance_gap","lighting_glare_gap","space_constraint_gap",
                    "adjustability_gap","workstation_age_index"]].copy()
    ws_view["fit_gap_score"] = ws_view[
        ["monitor_fit_gap","chair_support_gap","keyboard_mouse_gap","reach_distance_gap",
         "lighting_glare_gap","space_constraint_gap","adjustability_gap","workstation_age_index"]
    ].mean(axis=1).round(3)
    a,b = st.columns(2)
    with a:
        fig = px.scatter(ws_view, x="fit_gap_score", y="ergonomic_risk_score",
                         size="workstation_age_index", color="zone",
                         hover_name="worker_name", range_x=[0,1], range_y=[0,100],
                         title="Workstation fit gap × risk", template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    with b:
        melted = ws_view.melt(
            id_vars=["worker_name"],
            value_vars=["monitor_fit_gap","chair_support_gap","keyboard_mouse_gap",
                        "reach_distance_gap","lighting_glare_gap","space_constraint_gap","adjustability_gap"],
            var_name="domain", value_name="gap"
        )
        avg = melted.groupby("domain", as_index=False)["gap"].mean().sort_values("gap")
        fig = px.bar(avg, x="gap", y="domain", orientation="h", text_auto=".2f",
                     title="Workstation gap domains", range_x=[0,1], template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    st.dataframe(ws_view.sort_values("ergonomic_risk_score", ascending=False),
                 width="stretch", hide_index=True)

elif page == "Discomfort Analytics":
    st.markdown('<div class="section">Reported discomfort analytics</div>', unsafe_allow_html=True)
    discomfort["report_date"] = pd.to_datetime(discomfort["report_date"], errors="coerce")
    dv = discomfort[discomfort.worker_id.isin(view.worker_id)].copy()
    a,b = st.columns(2)
    with a:
        body = counts(dv.body_region,"body_region")
        fig = px.bar(body.sort_values("count"), x="count", y="body_region",
                     orientation="h", text_auto=True, title="Reported body regions",
                     template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    with b:
        sev = counts(dv.severity,"severity")
        fig = px.bar(sev, x="severity", y="count", text_auto=True,
                     title="Reported discomfort severity", template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    trend = dv.assign(month=dv.report_date.dt.to_period("M").astype(str)).groupby(
        "month", as_index=False
    ).agg(reports=("report_id","count"))
    fig = px.line(trend, x="month", y="reports", markers=True,
                  title="Monthly discomfort-report trend", template="plotly_white")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(dv.sort_values("report_date", ascending=False),
                 width="stretch", hide_index=True)

elif page == "Shift & Workload":
    st.markdown('<div class="section">Shift and workload context</div>', unsafe_allow_html=True)
    a,b = st.columns(2)
    with a:
        fig = px.scatter(view, x="shift_hours", y="ergonomic_risk_score",
                         size="breaks_missed_per_shift", color="department",
                         hover_name="worker_name", range_y=[0,100],
                         title="Shift duration × risk", template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    with b:
        cv = context[context.zone.isin(view.zone)].copy()
        cv["month"] = pd.to_datetime(cv["month"], errors="coerce")
        t = cv.groupby("month", as_index=False).agg(
            overtime=("overtime_pressure_index","mean"),
            staffing=("staffing_pressure_index","mean"),
            temp=("temperature_stress_index","mean"),
            pace=("pace_pressure_index","mean")
        )
        fig = px.line(t, x="month", y=["overtime","staffing","temp","pace"], markers=True,
                      title="Monthly workload/environment context", template="plotly_white")
        st.plotly_chart(fig, width="stretch")
    st.dataframe(view[[
        "worker_name","department","zone","shift_hours","breaks_missed_per_shift",
        "task_pacing_index","ergonomic_risk_score","risk_band","primary_driver"
    ]].sort_values("ergonomic_risk_score", ascending=False),
    width="stretch", hide_index=True)

elif page == "Department Comparison":
    st.markdown('<div class="section">Department comparison</div>', unsafe_allow_html=True)
    d = view.groupby("department", as_index=False).agg(
        avg_risk=("ergonomic_risk_score","mean"),
        max_risk=("ergonomic_risk_score","max"),
        workers=("worker_id","nunique"),
        discomfort=("discomfort_reports_90d","sum"),
        avg_shift=("shift_hours","mean")
    )
    fig = px.scatter(d, x="avg_shift", y="avg_risk", size="workers",
                     color="department", text="department", range_y=[0,100],
                     title="Department shift duration × average risk",
                     template="plotly_white")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(d.sort_values("avg_risk", ascending=False),
                 width="stretch", hide_index=True)

elif page == "Zone Comparison":
    st.markdown('<div class="section">Zone comparison</div>', unsafe_allow_html=True)
    z = view.groupby("zone", as_index=False).agg(
        avg_risk=("ergonomic_risk_score","mean"),
        workers=("worker_id","nunique"),
        discomfort=("discomfort_reports_90d","sum"),
        repetition=("repetitive_index","mean"),
        posture=("posture_exposure_index","mean"),
        workstation=("monitor_fit_gap","mean")
    )
    fig = px.scatter(z, x="repetition", y="avg_risk", size="workers",
                     color="zone", text="zone", range_x=[0,1], range_y=[0,100],
                     title="Zone repetition × average risk",
                     template="plotly_white")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(z.sort_values("avg_risk", ascending=False),
                 width="stretch", hide_index=True)

elif page == "Priority Review Queue":
    st.markdown('<div class="section">Ergonomic priority review queue</div>', unsafe_allow_html=True)
    q = view[[
        "worker_id","worker_name","department","zone","task_type",
        "ergonomic_risk_score","risk_band","primary_driver",
        "shift_hours","repetitive_index","posture_exposure_index",
        "manual_handling_index","discomfort_reports_90d",
        "breaks_missed_per_shift"
    ]].sort_values("ergonomic_risk_score", ascending=False)
    st.dataframe(q, width="stretch", hide_index=True)
    st.download_button(
        "⬇️ Download priority review queue",
        q.to_csv(index=False).encode(),
        file_name="ergonomic_priority_review_queue.csv",
        mime="text/csv"
    )

elif page == "Scenario Lab":
    st.markdown('<div class="section">Ergonomic Scenario Lab</div>', unsafe_allow_html=True)
    st.caption("Scenario controls modify screening emphasis only. They do not diagnose injury, determine medical fitness, or authorize workplace actions.")
    a,b,c,d,e = st.columns(5)
    with a: rw = st.slider("Repetition", 5, 30, 16, 1)
    with b: pw = st.slider("Posture", 5, 30, 16, 1)
    with c: dw = st.slider("Discomfort", 5, 25, 13, 1)
    with d: sw = st.slider("Shift duration", 5, 25, 9, 1)
    with e: ww = st.slider("Workstation gaps", 5, 25, 8, 1)

    weights = np.array([rw,pw,dw,sw,ww], dtype=float)
    weights = weights / weights.sum()
    sc = view.copy()
    sc["scenario_score"] = (
        100 * (
            weights[0]*sc.repetitive_index.clip(0,1) +
            weights[1]*sc.posture_exposure_index.clip(0,1) +
            weights[2]*(sc.discomfort_reports_90d/7).clip(0,1) +
            weights[3]*(((sc.shift_hours-7)/5).clip(0,1)) +
            weights[4]*sc[[
                "monitor_fit_gap","chair_support_gap","keyboard_mouse_gap",
                "reach_distance_gap","lighting_glare_gap","space_constraint_gap",
                "adjustability_gap","workstation_age_index"
            ]].mean(axis=1).clip(0,1)
        )
    ).clip(0,100).round(1)
    sc["scenario_change"] = (sc.scenario_score - sc.ergonomic_risk_score).round(1)

    st.dataframe(
        sc[["worker_id","worker_name","department","ergonomic_risk_score",
            "scenario_score","scenario_change","repetitive_index",
            "posture_exposure_index","discomfort_reports_90d","shift_hours"]]
        .sort_values("scenario_score", ascending=False),
        width="stretch", hide_index=True
    )
    st.download_button(
        "⬇️ Download scenario CSV",
        sc.to_csv(index=False).encode(),
        file_name="ergonomic_scenario.csv",
        mime="text/csv"
    )

else:
    st.markdown('<div class="section">Reports & export</div>', unsafe_allow_html=True)
    exports = [
        ("Scored worker records", view, "ergonomic_scored_workers.csv"),
        ("Workstation assessments", workstations, "workstation_assessments.csv"),
        ("Discomfort reports", discomfort, "discomfort_reports.csv"),
        ("Shift/environment context", context, "shift_environment_context.csv"),
    ]
    for label, df, fn in exports:
        st.download_button(
            "⬇️ Download " + label,
            df.to_csv(index=False).encode(),
            file_name=fn,
            mime="text/csv"
        )

st.markdown("""
<div class="note"><b>Important:</b> This analyzer is an ergonomic planning and review aid. A high score does not diagnose an injury, establish causation, determine an employee's medical condition or fitness for work, or replace qualified occupational-health, ergonomics, safety, engineering or clinical review.</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="footer">100% local CSV processing • No external APIs • Explainable heuristics • Human-in-the-loop review • Synthetic sample data</div>',
    unsafe_allow_html=True
)
