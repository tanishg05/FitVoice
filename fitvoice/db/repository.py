"""Parameterized SQL repository for FitVoice."""

import sqlite3
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fitvoice.db.database import get_db_connection


class FitnessRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        return get_db_connection(self.db_path)

    # ---------------------------------------------------------
    # Workouts
    # ---------------------------------------------------------
    def save_workout_session(
        self,
        user_id: str,
        session_name: str,
        date: str,
        sets: List[Dict[str, Any]],
        duration_minutes: Optional[int] = None,
        status: str = "CONFIRMED",
    ) -> str:
        """Save a workout session and its sets atomically using parameterized SQL."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO workout_sessions (id, user_id, date, session_name, duration_minutes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_id, date, session_name, duration_minutes, status, now)
            )

            for s in sets:
                set_id = f"set_{uuid.uuid4().hex[:12]}"
                cursor.execute(
                    """
                    INSERT INTO workout_sets (id, session_id, user_id, exercise, weight_kg, reps, rpe, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        set_id,
                        session_id,
                        user_id,
                        s.get("exercise", "").strip().title(),
                        float(s.get("weight_kg", 0.0)),
                        int(s.get("reps", 0)),
                        float(s["rpe"]) if s.get("rpe") is not None else None,
                        s.get("notes"),
                    )
                )
            conn.commit()
            return session_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_workout_sessions(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: str = "CONFIRMED",
    ) -> List[Dict[str, Any]]:
        """Retrieve confirmed workout sessions within an optional date range."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM workout_sessions WHERE user_id = ? AND status = ?"
        params: List[Any] = [user_id, status]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_workout_sets(
        self,
        user_id: str,
        exercise: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: str = "CONFIRMED",
    ) -> List[Dict[str, Any]]:
        """Retrieve exercise sets with session context."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT ws.id as set_id, ws.session_id, ws.user_id, ws.exercise, ws.weight_kg,
                   ws.reps, ws.rpe, ws.notes, s.date, s.session_name, s.status
            FROM workout_sets ws
            JOIN workout_sessions s ON ws.session_id = s.id
            WHERE ws.user_id = ? AND s.status = ?
        """
        params: List[Any] = [user_id, status]

        if exercise:
            query += " AND LOWER(ws.exercise) = LOWER(?)"
            params.append(exercise.strip())
        if start_date:
            query += " AND s.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND s.date <= ?"
            params.append(end_date)

        query += " ORDER BY s.date ASC, ws.id ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # Recovery Logs
    # ---------------------------------------------------------
    def save_recovery_log(
        self,
        user_id: str,
        date: str,
        sleep_hours: float,
        soreness_score: Optional[int] = None,
        energy_score: Optional[int] = None,
        readiness_score: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Save a daily recovery record."""
        log_id = f"rec_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO recovery_logs (id, user_id, date, sleep_hours, soreness_score, energy_score, readiness_score, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (log_id, user_id, date, sleep_hours, soreness_score, energy_score, readiness_score, notes, now)
        )
        conn.commit()
        conn.close()
        return log_id

    def get_recovery_logs(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recovery logs for a user in an optional date window."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM recovery_logs WHERE user_id = ?"
        params: List[Any] = [user_id]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ---------------------------------------------------------
    # Nutrition Logs
    # ---------------------------------------------------------
    def save_nutrition_log(
        self,
        user_id: str,
        date: str,
        item: str,
        calories: Optional[float] = None,
        protein_g: Optional[float] = None,
        carbs_g: Optional[float] = None,
        fat_g: Optional[float] = None,
        status: str = "CONFIRMED",
    ) -> str:
        log_id = f"nut_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO nutrition_logs (id, user_id, date, item, calories, protein_g, carbs_g, fat_g, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (log_id, user_id, date, item, calories, protein_g, carbs_g, fat_g, status, now)
        )
        conn.commit()
        conn.close()
        return log_id

    def get_nutrition_logs(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: str = "CONFIRMED",
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM nutrition_logs WHERE user_id = ? AND status = ?"
        params: List[Any] = [user_id, status]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def confirm_candidate_record(self, table_name: str, record_id: str) -> bool:
        """Confirm a candidate record into persistent verified storage."""
        if table_name not in ("workout_sessions", "nutrition_logs"):
            raise ValueError(f"Invalid table name for confirmation: {table_name}")

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {table_name} SET status = 'CONFIRMED' WHERE id = ?",
            (record_id,)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
