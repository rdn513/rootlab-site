from app.data import site, rub, product_price
from app.funnels import FUNNELS, TAG_FUNNEL, TAG_PLACE, TAG_PREFILL, next_step, resolve
from app.cards import bot_card, form_card, answer_lines
from app.web import validate


def test_every_site_tag_has_funnel_and_place():
    keys = set(site()["botTags"])
    assert keys - set(TAG_FUNNEL) == set(), "есть кнопки сайта без воронки"
    assert keys - set(TAG_PLACE) == set(), "есть кнопки без подписи места"
    assert set(TAG_FUNNEL) - keys == set(), "в боте метки, которых нет на сайте"


def test_prefill_keys_are_known():
    for tag, pre in TAG_PREFILL.items():
        assert tag in TAG_FUNNEL


def test_resolve_and_prefill_skips_question():
    f, key, pre = resolve("site_migration")
    assert f.id == "project" and pre == {"need": "migration"}
    assert next_step(f, pre).key == "site"
    assert resolve("unknown_tag") == (None, None, {})
    assert resolve(None)[0] is None


def test_prices_come_from_site_data():
    assert rub(30000) == "30 000 ₽"
    assert product_price("order").startswith("от 90 000")
    assert "30 000" in FUNNELS["audit"].intro()


def test_every_funnel_ends_with_contact_and_renders():
    for f in FUNNELS.values():
        assert f.steps[-1].kind == "contact"
        answers = {s.key: (s.options[0][0] if s.options else "текст") for s in f.steps}
        answers["contact_way"] = "phone:+79120000000"
        card = bot_card(1, f.id, "site_hero", 42, "Иван", "ivan", answers)
        assert "заявка #1" in card and "позвонить: +79120000000" in card
        assert f.done(answers)


def test_answer_lines_use_button_labels():
    lines = dict(answer_lines("audit", {"who": "studio", "servers": "8+"}))
    assert lines["Кто"] == "Веб-студия / агентство" and lines["Серверов"] == "Больше 8"


def test_form_validation():
    ok, err = validate({"name": "А", "contact": "@a", "consent": "on"})
    assert err is None and ok["name"] == "А"
    assert validate({"name": "А", "contact": "@a"})[1] == "consent"
    assert validate({"name": "", "contact": "@a", "consent": "on"})[1] == "required"
    assert validate({"name": "А", "contact": "@a", "consent": "on", "company_website": "x"})[1] == "spam"
    assert "Согласие" in form_card(3, ok)
