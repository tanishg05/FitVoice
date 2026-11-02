"""Seed deterministic benchmark records for FitVoice demonstration & testing."""

from datetime import datetime, timedelta, timezone
from fitvoice.db.database import init_db
from fitvoice.db.repository import FitnessRepository


def seed_benchmark_data(db_path: str = None) -> None:
    """Populate database with reproducible 4-week benchmark data for testing."""
    init_db(db_path)
    repo = FitnessRepository(db_path)

    # Base reference date: 28 days ago up to today
    today = datetime.now(timezone.utc).date()

    # User 1: 'alex_lifter' - Bench Press Plateau & Recovery Deficit
    # Clear existing records for alex_lifter to make it strictly reproducible
    conn = repo._get_conn()
    conn.execute("DELETE FROM workout_sets WHERE user_id = 'alex_lifter'")
    conn.execute("DELETE FROM workout_sessions WHERE user_id = 'alex_lifter'")
    conn.execute("DELETE FROM recovery_logs WHERE user_id = 'alex_lifter'")
    conn.execute("DELETE FROM nutrition_logs WHERE user_id = 'alex_lifter'")
    conn.commit()
    conn.close()

    # 4 Weeks of Workout Sessions & Recovery Logs
    # Week 1: Great sleep (7.8h), low soreness (2-3), solid progression
    # Week 2: Good sleep (7.4h), moderate soreness (3-4), hitting 95kg
    # Week 3: Poor sleep (5.6h), elevated soreness (6-7), plateauing at 95kg
    # Week 4: Low sleep (5.3h), high soreness (7-8), stalled volume & fatigue

    schedule = [
        # (day_offset, session_name, bench_weight, bench_reps, bench_sets, other_ex, sleep, soreness, energy, readiness)
        # Week 1
        (27, "Upper Body Push", 85.0, 8, 3, ("Overhead Press", 50.0, 8, 3), 8.0, 2, 8, 8),
        (25, "Lower Body", None, 0, 0, ("Squat", 110.0, 5, 4), 7.8, 3, 7, 8),
        (24, "Upper Body Push", 87.5, 8, 3, ("Incline Dumbbell Press", 28.0, 10, 3), 7.6, 3, 8, 8),
        (22, "Pull & Core", None, 0, 0, ("Barbell Row", 80.0, 8, 4), 7.9, 2, 8, 8),
        # Week 2
        (20, "Upper Body Push", 90.0, 6, 3, ("Overhead Press", 52.5, 6, 3), 7.5, 3, 7, 7),
        (18, "Lower Body", None, 0, 0, ("Squat", 115.0, 5, 4), 7.4, 4, 7, 7),
        (16, "Upper Body Push", 92.5, 6, 3, ("Incline Dumbbell Press", 30.0, 8, 3), 7.2, 4, 7, 7),
        (15, "Pull & Core", None, 0, 0, ("Barbell Row", 82.5, 8, 4), 7.3, 3, 7, 7),
        # Week 3 (Sleep drops, soreness rises, plateau begins)
        (13, "Upper Body Push", 95.0, 5, 4, ("Overhead Press", 55.0, 5, 3), 5.7, 6, 5, 5),
        (11, "Lower Body", None, 0, 0, ("Squat", 117.5, 5, 4), 5.5, 7, 5, 4),
        (9,  "Upper Body Push", 95.0, 5, 4, ("Incline Dumbbell Press", 30.0, 7, 3), 5.8, 6, 5, 5),
        (8,  "Pull & Core", None, 0, 0, ("Barbell Row", 82.5, 6, 4), 5.4, 7, 4, 4),
        # Week 4 (Stall confirmed, high fatigue)
        (6,  "Upper Body Push", 95.0, 5, 4, ("Overhead Press", 55.0, 4, 3), 5.2, 7, 4, 4),
        (4,  "Lower Body", None, 0, 0, ("Squat", 120.0, 3, 4), 5.5, 8, 4, 3),
        (2,  "Upper Body Push", 95.0, 4, 4, ("Incline Dumbbell Press", 30.0, 6, 3), 5.1, 8, 4, 3),
        (1,  "Pull & Core", None, 0, 0, ("Barbell Row", 80.0, 6, 3), 5.3, 7, 4, 4),
    ]

    for item in schedule:
        day_offset, s_name, bw, br, bs, other_ex, sleep, sore, energy, read = item
        session_date = (today - timedelta(days=day_offset)).isoformat()

        sets = []
        if bw is not None:
            for set_num in range(bs):
                sets.append({
                    "exercise": "Bench Press",
                    "weight_kg": bw,
                    "reps": br,
                    "rpe": 8.0 if day_offset > 14 else 9.5,
                    "notes": f"Set {set_num + 1}"
                })

        if other_ex:
            ex_name, ex_weight, ex_reps, ex_sets = other_ex
            for set_num in range(ex_sets):
                sets.append({
                    "exercise": ex_name,
                    "weight_kg": ex_weight,
                    "reps": ex_reps,
                    "rpe": 8.0,
                    "notes": f"Set {set_num + 1}"
                })

        repo.save_workout_session(
            user_id="alex_lifter",
            session_name=s_name,
            date=session_date,
            sets=sets,
            duration_minutes=65,
            status="CONFIRMED",
        )

        repo.save_recovery_log(
            user_id="alex_lifter",
            date=session_date,
            sleep_hours=sleep,
            soreness_score=sore,
            energy_score=energy,
            readiness_score=read,
            notes=f"Auto-logged recovery day -{day_offset}"
        )

    # Also log sleep for off-days to have full recovery timeline
    for d in range(1, 28):
        dt = (today - timedelta(days=d)).isoformat()
        # check if already logged
        existing = repo.get_recovery_logs(user_id="alex_lifter", start_date=dt, end_date=dt)
        if not existing:
            # First 14 days: ~7.6 hrs, last 14 days: ~5.4 hrs
            sl = 7.7 if d > 14 else 5.4
            sr = 3 if d > 14 else 6
            repo.save_recovery_log(
                user_id="alex_lifter",
                date=dt,
                sleep_hours=sl,
                soreness_score=sr,
                energy_score=7 if d > 14 else 4,
                readiness_score=7 if d > 14 else 4,
                notes="Rest day recovery"
            )

    # Seed User 2: 'newbie_sam' - Insufficient Data Scenario (1 workout, 0 recovery)
    conn = repo._get_conn()
    conn.execute("DELETE FROM workout_sets WHERE user_id = 'newbie_sam'")
    conn.execute("DELETE FROM workout_sessions WHERE user_id = 'newbie_sam'")
    conn.execute("DELETE FROM recovery_logs WHERE user_id = 'newbie_sam'")
    conn.commit()
    conn.close()

    repo.save_workout_session(
        user_id="newbie_sam",
        session_name="Intro Gym Workout",
        date=(today - timedelta(days=2)).isoformat(),
        sets=[
            {"exercise": "Bench Press", "weight_kg": 50.0, "reps": 10, "rpe": 7.0},
        ],
        duration_minutes=30,
        status="CONFIRMED"
    )


if __name__ == "__main__":
    seed_benchmark_data()
    print("Benchmark data seeded successfully.")

