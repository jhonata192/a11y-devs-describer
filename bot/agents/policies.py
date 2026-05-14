from config.settings import settings


def aplicar_politicas(plan: dict, metadata: dict) -> dict:
    steps = plan.get("steps", [])
    detail = plan.get("detail_level", "medio")
    pipeline = plan.get("pipeline", "simple")

    steps_to_add = []
    tipo = metadata.get("tipo")

    if tipo == "pdf":
        texto_embutido = metadata.get("texto_embutido", False)
        if not texto_embutido and "image_description" not in steps:
            steps_to_add.append("image_description")
            if detail == "baixo":
                detail = "medio"

    if tipo == "imagem":
        if "image_description" not in steps:
            steps_to_add.append("image_description")

    if tipo in ("pdf", "imagem"):
        if "text_extraction" not in steps:
            steps_to_add.append("text_extraction")

    if "translation" not in steps:
        steps_to_add.append("translation")

    if steps_to_add:
        steps = steps_to_add + steps
        if pipeline == "simple":
            pipeline = "detailed"

    detail_levels = ["baixo", "medio", "alto"]
    if detail not in detail_levels:
        detail = "medio"

    return {
        "pipeline": pipeline,
        "steps": steps,
        "detail_level": detail,
        "priority": plan.get("priority", "speed"),
    }
