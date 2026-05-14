from bot.agents.router_ia import RouterIA


def test_parse_plan_valid_json():
    router = RouterIA()
    text = '{"pipeline": "detailed", "steps": ["image_description", "translation"], "detail_level": "alto"}'
    plan = router._parse_plan(text)
    assert plan["pipeline"] == "detailed"
    assert "image_description" in plan["steps"]
    assert "translation" in plan["steps"]
    assert plan["detail_level"] == "alto"


def test_parse_plan_with_junk():
    router = RouterIA()
    text = 'Here is your plan:\n\n{"pipeline": "simple", "steps": ["image_description"], "detail_level": "baixo"}\n\nEnd.'
    plan = router._parse_plan(text)
    assert plan["pipeline"] == "simple"
    assert "translation" in plan["steps"]
    assert plan["detail_level"] == "baixo"


def test_parse_plan_invalid_json_fallback():
    router = RouterIA()
    plan = router._parse_plan("not json at all")
    assert plan["pipeline"] == "simple"
    assert "image_description" in plan["steps"]
    assert "translation" in plan["steps"]


def test_parse_plan_adds_translation():
    router = RouterIA()
    text = '{"pipeline": "detailed", "steps": ["image_description"], "detail_level": "medio"}'
    plan = router._parse_plan(text)
    assert "translation" in plan["steps"]


def test_parse_plan_keeps_existing_translation():
    router = RouterIA()
    text = '{"pipeline": "simple", "steps": ["translation"], "detail_level": "baixo"}'
    plan = router._parse_plan(text)
    assert plan["steps"] == ["translation"]


def test_parse_plan_empty_dict():
    router = RouterIA()
    plan = router._parse_plan("{}")
    assert plan["pipeline"] == "simple"
    assert "translation" in plan["steps"]
