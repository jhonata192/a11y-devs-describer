from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from pipeline.sanitizer import sanitize_block_text


def parse_text_to_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            blocks.append(
                {
                    "type": "heading",
                    "level": len(heading_match.group(1)),
                    "text": sanitize_block_text(
                        heading_match.group(2).strip()
                    ),
                }
            )
            i += 1
            continue
        plain_heading = _extract_plain_heading(stripped, len(blocks))
        if plain_heading is not None:
            blocks.append(plain_heading)
            i += 1
            continue
        # Listas não ordenadas (- ou * ou +)
        if re.match(r"^(?:[-*+]\s+)", stripped):
            items, end_index = _parse_list_items(lines, i, r"^(?:[-*+]\s+)")
            blocks.append({
                "type": "list",
                "ordered": False,
                "items": items
            })
            i = end_index + 1
            continue

        # Listas ordenadas (1. ou 1) ou (1))
        if re.match(r"^(?:\(?\d+[\.\)]\s+)", stripped):
            items, end_index = _parse_list_items(lines, i, r"^(?:\(?\d+[\.\)]\s+)")
            blocks.append({
                "type": "list",
                "ordered": True,
                "items": items
            })
            i = end_index + 1
            continue
        if stripped.startswith("```"):
            blocks.append({"type": "code", "text": stripped})
            i += 1
            continue
        
        # Suporte para blocos de matemática LaTeX ($$ formula $$)
        if stripped.startswith("$$"):
            math_content, end_index = _parse_math_block(lines, i)
            if math_content:
                blocks.append({
                    "type": "math",
                    "text": math_content,
                    "display": True
                })
                i = end_index + 1
                continue

        if _looks_like_table_row(stripped):
            rows, end_index = _parse_table_rows(lines, i)
            if rows:
                blocks.append({"type": "table", "rows": rows})
                i = end_index + 1
                continue
        blocks.append(
            {
                "type": "paragraph",
                "text": sanitize_block_text(stripped),
            }
        )
        i += 1
    return _attach_ids(blocks)


def _attach_ids(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for index, block in enumerate(blocks, start=1):
        block.setdefault("id", f"blk-{uuid4().hex[:10]}-{index}")
    return blocks


def _looks_like_table_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|")


def _extract_plain_heading(
    line: str,
    current_blocks: int,
) -> dict[str, Any] | None:
    prefixed = re.match(
        (
            r"^(?:titulo|t[ií]tulo|secao|se[cç][aã]o|"
            r"capitulo|cap[ií]tulo)\s*:\s*(.+)$"
        ),
        line,
        re.IGNORECASE,
    )
    if prefixed:
        keyword = line.split(":", 1)[0].strip().lower()
        level = 1 if "titulo" in keyword or "título" in keyword else 2
        return {
            "type": "heading",
            "level": level,
            "text": sanitize_block_text(prefixed.group(1).strip()),
        }

    if _looks_like_upper_heading(line):
        level = 1 if current_blocks == 0 else 2
        return {
            "type": "heading",
            "level": level,
            "text": sanitize_block_text(line),
        }
    return None


def _looks_like_upper_heading(line: str) -> bool:
    has_letter = any(ch.isalpha() for ch in line)
    if not has_letter:
        return False
    if len(line) > 90:
        return False
    if line.endswith((".", ";", "!", "?")):
        return False
    if ":" in line:
        return False
    return line == line.upper()


def _parse_table_rows(
    lines: list[str],
    start_index: int,
) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    i = start_index

    while i < len(lines):
        stripped = lines[i].strip()
        if not _looks_like_table_row(stripped):
            break
        cells = [
            sanitize_block_text(cell.strip())
            for cell in stripped.strip("|").split("|")
        ]
        if cells and all(set(cell) <= {"-", ":"} for cell in cells):
            i += 1
            continue
        rows.append(cells)
        i += 1

    return rows, i - 1


def _parse_math_block(
    lines: list[str],
    start_index: int,
) -> tuple[str, int]:
    """Extrai o conteúdo de um bloco de matemática delimitado por $$."""
    first_line = lines[start_index].strip()
    
    # Caso simplificado: $$formula$$ na mesma linha
    if first_line.startswith("$$") and first_line.endswith("$$") and len(first_line) > 4:
        return first_line[2:-2].strip(), start_index

    # Caso multi-linha
    content = []
    if len(first_line) > 2:
        content.append(first_line[2:])
    
    i = start_index + 1
    while i < len(lines):
        line = lines[i]
        if "$$" in line:
            end_pos = line.find("$$")
            content.append(line[:end_pos])
            break
        content.append(line)
        i += 1
    
    return "\n".join(content).strip(), i


def _parse_list_items(
    lines: list[str],
    start_index: int,
    pattern: str,
) -> tuple[list[str], int]:
    """Agrupa itens de lista consecutivos que correspondem ao padrão."""
    items = []
    i = start_index
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            # Permite uma linha vazia entre itens se o próximo for um item de lista
            if i + 1 < len(lines) and re.match(pattern, lines[i+1].strip()):
                i += 1
                continue
            break
            
        match = re.match(pattern, line)
        if not match:
            break
            
        # Remove o marcador (ex: "1. " ou "- ")
        content = re.sub(pattern, "", line).strip()
        items.append(sanitize_block_text(content))
        i += 1
        
    return items, i - 1
