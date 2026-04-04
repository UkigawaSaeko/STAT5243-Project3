"""
STAT5243 — Shiny for Python. A/B test page; events → logs/events.csv.
Uses ui.tags + include_css/include_js so www/ assets resolve on shinyapps.io.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
from typing import Optional
import json
import os
import posixpath
import tempfile
from datetime import datetime, timezone

from htmltools import HTMLDependency

from shiny import App, reactive, ui

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_IMG_DEP_VERSION = "0.0"

# GA4：若在 shinyapps「Vars」里设置了 GA_MEASUREMENT_ID，则优先用环境变量；否则用下方默认值（页面才会加载 gtag，GA 才有数据）。
_GA4_MEASUREMENT_ID_DEFAULT = "G-NG3HRLC1YV"


def _www_full(rel: str) -> str:
    """Path under project dir (use forward slashes in rel)."""
    rel = rel.replace("/", os.sep)
    return os.path.join(BASE_DIR, rel)


def _include_css(path: str):
    """Prefer shiny include_css; fallback link so missing files do not crash import (shinyapps)."""
    full = _www_full(path)
    fn = getattr(ui, "include_css", None)
    if callable(fn) and os.path.isfile(full):
        try:
            return fn(path)
        except (OSError, RuntimeError, ValueError):
            pass
    href = path[4:] if path.startswith("www/") else path
    return ui.tags.link(rel="stylesheet", href=href, type="text/css")


def _include_js(path: str):
    full = _www_full(path)
    fn = getattr(ui, "include_js", None)
    if callable(fn) and os.path.isfile(full):
        try:
            return fn(path)
        except (OSError, RuntimeError, ValueError):
            pass
    src = path[4:] if path.startswith("www/") else path
    return ui.tags.script(src=src)


def _include_img(path: str, **attrs) -> ui.Tag:
    """Like include_css: register file via HTMLDependency so shinyapps serves a valid URL."""
    full = _www_full(path)
    href = path[4:] if path.startswith("www/") else path
    if not os.path.isfile(full):
        return ui.tags.img(src=href, **attrs)
    try:
        with open(full, "rb") as f:
            key = hashlib.sha1(f.read()).hexdigest()
        basename = os.path.basename(full)
        tmpdir = os.path.join(tempfile.gettempdir(), f"stat5243_img_{key}")
        path_dest = os.path.join(tmpdir, basename)
        if not os.path.isfile(path_dest):
            os.makedirs(tmpdir, exist_ok=True)
            shutil.copy2(full, path_dest)
        dep = HTMLDependency(
            "include-img-" + key,
            _IMG_DEP_VERSION,
            source={"subdir": tmpdir},
            all_files=False,
        )
        src = posixpath.join(
            dep.source_path_map()["href"].replace("\\", "/"),
            basename.replace("\\", "/"),
        )
        return ui.tags.img(dep, src=src, **attrs)
    except (OSError, RuntimeError, ValueError):
        return ui.tags.img(src=href, **attrs)


LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "events.csv")


def _ensure_log_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def _log_file_for_write() -> Optional[str]:
    """Prefer logs/ under app; fall back to temp dir if disk is read-only (common on shinyapps.io)."""
    try:
        _ensure_log_dir()
        p = os.path.join(LOG_DIR, ".write_check")
        with open(p, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(p)
        return LOG_FILE
    except OSError:
        try:
            return os.path.join(tempfile.gettempdir(), "stat5243_events.csv")
        except OSError:
            return None


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"


def _append_event(event_name: str, session_id: str, ab_group: str, detail: dict) -> None:
    log_path = _log_file_for_write()
    if log_path is None:
        return
    try:
        detail = dict(detail)
        detail["server_ts"] = _now_ts()
        new_file = not os.path.isfile(log_path)
        row = {
            "ts": _now_ts(),
            "session_id": session_id,
            "ab_group": ab_group,
            "event_name": event_name,
            "detail_json": json.dumps(detail, ensure_ascii=False),
        }
        fieldnames = ["ts", "session_id", "ab_group", "event_name", "detail_json"]
        with open(log_path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            if new_file:
                w.writeheader()
            w.writerow(row)
    except OSError:
        pass


def _ga_head(ga: str) -> list:
    if not ga:
        return []
    # 设为 1 时 gtag 带 debug_mode，便于 GA4「管理 → DebugView」看到事件（排查完请关掉）
    _dbg = os.environ.get("GA_DEBUG", "").strip().lower() in ("1", "true", "yes")
    # 关闭 config 自带的 page_view，避免「无 A/B 参数」的命中；由 ab.js 在分组确定后发唯一一次 page_view
    if _dbg:
        config_extra = ", { debug_mode: true, send_page_view: false }"
    else:
        config_extra = ", { send_page_view: false }"
    return [
        ui.tags.script(
            src=f"https://www.googletagmanager.com/gtag/js?id={ga}",
            **{"async": True},
        ),
        ui.tags.script(
            ui.HTML(
                f"""
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{ga}'{config_extra});
"""
            )
        ),
    ]


def _product_card() -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            _include_img(
                "www/product.png",
                alt="Hero Mighty Patch The Original 72-count jumbo pack",
            ),
            class_="product-img-wrap",
        ),
        ui.tags.div(
            ui.tags.h1(
                "Hero Mighty Patch™ The Original — Hydrocolloid Acne Patches (72 Count, Jumbo Pack)"
            ),
            ui.tags.p(
                ui.tags.em("Your Blemish Hero"),
                style="margin:0 0 10px;font-size:0.95rem;color:#565959;",
            ),
            ui.tags.div("$21.97", class_="price-line"),
            ui.tags.div("($0.31 / count)", class_="unit-price"),
            ui.tags.ul(
                ui.tags.li("Absorbs pimple gunk in 6 hours"),
                ui.tags.li("Works overnight while you sleep"),
                ui.tags.li("Suitable for sensitive skin"),
                ui.tags.li("Helps shrink zits and whiteheads in one use"),
                ui.tags.li("The Original — trusted hydrocolloid spot care"),
                class_="bullets",
            ),
            ui.tags.div(
                ui.tags.button(
                    "Add to Cart",
                    type="button",
                    class_="btn-cart",
                    onclick="ABTracker.addToCart();",
                ),
                ui.tags.button(
                    "Claim sample offer",
                    type="button",
                    class_="btn-sample",
                    onclick="ABTracker.claimSample();",
                ),
                class_="btn-row",
            ),
            ui.tags.div(
                "Added to cart successfully.",
                id="cart-success",
                class_="toast-success",
                style="display:none;",
                role="status",
                **{"aria-live": "polite"},
            ),
            ui.tags.div(
                "Demo store — no real purchase.",
                style="font-size:0.85rem;color:#565959;",
            ),
            class_="product-meta",
        ),
        class_="product-card",
    )


def _help_block() -> ui.Tag:
    return ui.tags.div(
        ui.tags.h2("Questions? We're here to help.", id="help-headline"),
        ui.tags.div("Loading…", id="ab-badge", class_="ab-badge"),
        ui.tags.div(
            ui.tags.div(
                _include_img(
                    "www/advisor.png",
                    alt="Skin care specialist",
                    class_="advisor-avatar",
                    width="72",
                    height="72",
                ),
                id="advisor-avatar-wrap",
                class_="advisor-avatar-wrap",
                style="display:none;",
                **{"aria-hidden": "true"},
            ),
            ui.tags.div(
                ui.tags.p("Loading…", id="help-hint", class_="hint"),
                class_="help-panel-main",
            ),
            class_="help-panel-row",
        ),
        ui.tags.button("Loading…", id="btn-help", class_="btn-help", type="button"),
        id="help-block",
        class_="help-block",
    )


def _survey_block() -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            ui.tags.h3("Short survey (optional)"),
            ui.tags.div(
                "1. If you were buying a product like this, how much would you worry about embarrassment or being judged by others?",
                class_="q",
            ),
            ui.tags.div(
                _radio_row("survey_emb", "1", "1 — Not at all"),
                _radio_row("survey_emb", "2", "2"),
                _radio_row("survey_emb", "3", "3"),
                _radio_row("survey_emb", "4", "4"),
                _radio_row("survey_emb", "5", "5 — Very much"),
            ),
            ui.tags.div(
                "2. How willing would you be to use the Help button on this page to get advice?",
                class_="q",
                style="margin-top:12px;",
            ),
            ui.tags.div(
                _radio_row("survey_trust", "1", "1 — Very unwilling"),
                _radio_row("survey_trust", "2", "2"),
                _radio_row("survey_trust", "3", "3"),
                _radio_row("survey_trust", "4", "4"),
                _radio_row("survey_trust", "5", "5 — Very willing"),
            ),
            ui.tags.button(
                "Submit survey",
                type="button",
                class_="btn-survey",
                onclick="ABTracker.surveySubmit();",
            ),
            id="survey-fields",
        ),
        ui.tags.div(
            "Thank you — your responses were submitted successfully.",
            id="survey-success",
            class_="survey-success",
            style="display:none;",
            role="status",
            **{"aria-live": "polite"},
        ),
        id="survey-section",
        class_="survey-block",
    )


def _radio_row(name: str, value: str, label: str) -> ui.Tag:
    return ui.tags.label(
        ui.tags.input(type="radio", name=name, value=value),
        f" {label}",
    )


def _modal() -> ui.Tag:
    return ui.tags.div(
        ui.tags.div(
            ui.tags.button("×", id="help-close", class_="modal-close", type="button", **{"aria-label": "Close"}),
            ui.tags.div(
                ui.tags.div("Message a specialist", class_="modal-title"),
                ui.tags.div(
                    ui.tags.button(
                        "What is the best way to use it?",
                        type="button",
                        onclick=(
                            "ABTracker.showHelpReply('reply-a', "
                            "'Thanks for asking. For patches like this, cleanse at night, dry the skin, "
                            "then apply; change after about 6–8 hours. If irritation worsens, see a dermatologist.');"
                        ),
                    ),
                    ui.tags.button(
                        "I feel a bit embarrassed buying this…",
                        type="button",
                        onclick=(
                            "ABTracker.showHelpReply('reply-a', "
                            "'That is completely normal — many people feel that way. You can start with a small pack "
                            "and check ingredients for your skin type.');"
                        ),
                    ),
                    ui.tags.button(
                        "How should I store it after opening?",
                        type="button",
                        onclick=(
                            "ABTracker.showHelpReply('reply-a', "
                            "'After opening, store in a clean, dry place and follow the box directions. "
                            "Want help comparing sizes?');"
                        ),
                    ),
                    class_="chat-options",
                ),
                ui.tags.div(id="reply-a", class_="reply-box"),
                id="help-flow-a",
                style="display:none;",
            ),
            ui.tags.div(
                ui.tags.div("Private AI assistant", class_="modal-title"),
                ui.tags.p(
                    "AI-generated answers for product questions. This chat stays private in your browser session "
                    "and is not shared with other customers or sold to third parties.",
                    class_="modal-privacy-note",
                ),
                ui.tags.div(
                    ui.tags.button(
                        "Which kinds of breakouts is it for?",
                        type="button",
                        onclick=(
                            "ABTracker.showHelpReply('reply-b', "
                            "'Hydrocolloid patches are commonly used on surfaced blemishes to help absorb fluid. "
                            "Apply to clean, dry skin and leave on overnight. General information only — not medical advice.');"
                        ),
                    ),
                    ui.tags.button(
                        "Is my chat kept private?",
                        type="button",
                        onclick=(
                            "ABTracker.showHelpReply('reply-b', "
                            "'We do not share your chat with other shoppers or use it for advertising. "
                            "For full details, see our Privacy Policy.');"
                        ),
                    ),
                    ui.tags.button(
                        "Help me compare value",
                        type="button",
                        onclick=(
                            "ABTracker.showHelpReply('reply-b', "
                            "'Compare price per patch and how often you plan to use them — the 72-count pack often "
                            "lowers the per-patch cost if you use patches regularly.');"
                        ),
                    ),
                    class_="chat-options",
                ),
                ui.tags.div(id="reply-b", class_="reply-box"),
                id="help-flow-b",
                style="display:none;",
            ),
            class_="modal-box",
        ),
        id="help-modal",
        class_="modal-overlay",
        **{"aria-hidden": "true"},
    )


def _build_ui():
    if "GA_MEASUREMENT_ID" in os.environ:
        ga = os.environ["GA_MEASUREMENT_ID"].strip()
    else:
        ga = _GA4_MEASUREMENT_ID_DEFAULT
    head = _ga_head(ga)
    head.append(_include_css("www/styles.css"))
    head.append(ui.tags.title("Mighty Patch — Shop"))

    return ui.page_fluid(
        ui.head_content(*head),
        ui.tags.div(ui.input_text("client_event", ""), style="display: none;"),
        ui.tags.div(
            _product_card(),
            _help_block(),
            _survey_block(),
            ui.tags.div(
                "Product information and pricing are for demonstration only. No real purchase or checkout.",
                class_="footer-note",
            ),
            class_="app-wrap",
        ),
        _modal(),
        _include_js("www/ab.js"),
    )


app_ui = _build_ui()


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.client_event)
    def _log_client_event():
        try:
            raw = input.client_event()
            if raw is None:
                return
            s = str(raw).strip()
            if not s:
                return
            try:
                data = json.loads(s)
            except json.JSONDecodeError:
                return
            event_name = data.get("event") or ""
            payload = data.get("payload")
            if not isinstance(payload, dict):
                payload = {}
            client_ts = data.get("client_ts")
            detail = dict(payload)
            if client_ts is not None:
                detail["client_ts"] = client_ts
            session_id = str(payload.get("session_id") or "")
            ab_group = str(payload.get("ab_group") or "")
            _append_event(event_name, session_id, ab_group, detail)
        except Exception:
            # Never take down the session if logging fails
            pass


app = App(app_ui, server)


if __name__ == "__main__":
    from shiny import run_app

    run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", "3838")))
