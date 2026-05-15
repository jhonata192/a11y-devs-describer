import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from bot.utils.logger import logger
from config.settings import settings

DB_PATH = settings.temp_dir / "history.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                arquivo TEXT NOT NULL,
                extensao TEXT NOT NULL,
                tamanho_bytes INTEGER DEFAULT 0,
                modo TEXT DEFAULT 'normal',
                pipeline TEXT DEFAULT '',
                status TEXT DEFAULT 'processing',
                tempo_segundos REAL DEFAULT 0,
                erro TEXT DEFAULT '',
                resultado_resumo TEXT DEFAULT '',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                concluido_em TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def registrar_conversao(
    task_id: str,
    arquivo: str,
    extensao: str,
    tamanho_bytes: int = 0,
    modo: str = "normal",
):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO conversoes
               (task_id, arquivo, extensao, tamanho_bytes, modo)
               VALUES (?, ?, ?, ?, ?)""",
            (task_id, arquivo, extensao, tamanho_bytes, modo),
        )
        conn.commit()
    finally:
        conn.close()


def finalizar_conversao(
    task_id: str,
    status: str,
    pipeline: str = "",
    erro: str = "",
    resultado_resumo: str = "",
    tempo_segundos: float = 0,
):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE conversoes SET
               status = ?, pipeline = ?, erro = ?,
               resultado_resumo = ?, tempo_segundos = ?,
               concluido_em = CURRENT_TIMESTAMP
               WHERE task_id = ?""",
            (status, pipeline, erro, resultado_resumo, tempo_segundos, task_id),
        )
        conn.commit()
    finally:
        conn.close()


def listar_historico(limite: int = 10) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM conversoes
               ORDER BY criado_em DESC LIMIT ?""",
            (limite,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def estatisticas() -> dict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM conversoes").fetchone()[0]
        sucesso = conn.execute(
            "SELECT COUNT(*) FROM conversoes WHERE status='done'"
        ).fetchone()[0]
        erros = conn.execute(
            "SELECT COUNT(*) FROM conversoes WHERE status='error'"
        ).fetchone()[0]
        tempo_medio = conn.execute(
            "SELECT AVG(tempo_segundos) FROM conversoes WHERE status='done'"
        ).fetchone()[0] or 0
        return {
            "total": total,
            "sucesso": sucesso,
            "erros": erros,
            "tempo_medio_segundos": round(tempo_medio, 1),
        }
    finally:
        conn.close()
