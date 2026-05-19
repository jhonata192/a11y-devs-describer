import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from bot.utils.logger import logger
from config.settings import settings

DB_PATH = settings.db_path


def _criar_tabelas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ocr_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            text TEXT NOT NULL,
            fonte TEXT DEFAULT 'tesseract',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ocr_revised (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            text TEXT NOT NULL,
            modelo TEXT DEFAULT 'qwen2.5:3b',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ocr_translated (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            text TEXT NOT NULL,
            modelo TEXT DEFAULT 'qwen2.5:1.5b',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_raw_task ON ocr_raw(task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_revised_task ON ocr_revised(task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_translated_task ON ocr_translated(task_id)")
    conn.commit()


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _criar_tabelas(conn)
    return conn


def init_db():
    conn = get_connection()
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


def salvar_ocr_raw(task_id: str, page_number: int, text: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO ocr_raw (task_id, page_number, text) VALUES (?, ?, ?)",
            (task_id, page_number, text),
        )
        conn.commit()
    finally:
        conn.close()


def listar_ocr_raw(task_id: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM ocr_raw WHERE task_id = ? ORDER BY page_number", (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def salvar_ocr_revised(task_id: str, page_number: int, text: str, modelo: str = "qwen2.5:3b"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO ocr_revised (task_id, page_number, text, modelo) VALUES (?, ?, ?, ?)",
            (task_id, page_number, text, modelo),
        )
        conn.commit()
    finally:
        conn.close()


def listar_ocr_revised(task_id: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM ocr_revised WHERE task_id = ? ORDER BY page_number", (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def salvar_ocr_translated(task_id: str, page_number: int, text: str, modelo: str = "qwen2.5:1.5b"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO ocr_translated (task_id, page_number, text, modelo) VALUES (?, ?, ?, ?)",
            (task_id, page_number, text, modelo),
        )
        conn.commit()
    finally:
        conn.close()


def listar_ocr_translated(task_id: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM ocr_translated WHERE task_id = ? ORDER BY page_number", (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def limpar_ocr_data(task_id: str):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM ocr_raw WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM ocr_revised WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM ocr_translated WHERE task_id = ?", (task_id,))
        conn.commit()
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
