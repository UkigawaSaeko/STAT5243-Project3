# Mighty Patch A/B test page (STAT5243 Project 3)

Single-page **Shiny for Python** app: human advisor (A) vs private AI (B) assignment, survey, and GA4 events. Intended deployment target is **shinyapps.io**.

## Repository layout

| Path | Purpose |
|------|---------|
| `app.py` | Application entry; exports `app` |
| `www/` | Front-end assets: `styles.css`, `ab.js`; add **`product.png`** and **`advisor.png`** yourself or images will not load |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` / `.python-version` | Prefer Python 3.10–3.12 (matches rsconnect / shinyapps) |
| `rsconnect-python/` | Account/app metadata after rsconnect deploy (safe to keep for redeploys) |

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Or:

```bash
shiny run app.py --host 0.0.0.0 --port 3838
```

Optional environment variables: `GA_MEASUREMENT_ID`, `PORT`.

## Deploy to shinyapps.io

Cloud builds **do not support Python 3.14**. Use **`rsconnect` from Python 3.12 or 3.11** (the interpreter that runs `rsconnect` determines what gets uploaded).

```powershell
py -3.12 -m pip install -r requirements.txt rsconnect-python
py -3.12 -m rsconnect add --server shinyapps.io --account <account> --name <local-alias>
cd "path\to\your\project"
py -3.12 -m rsconnect deploy shiny . --name <local-alias> --title <app-title>
```

If your default `rsconnect` on PATH comes from Python 3.14, call the 3.12 executable explicitly (e.g. Anaconda `Scripts\rsconnect.exe`). Check with `where.exe rsconnect`.

App URL shape: `https://<account>.shinyapps.io/<app-name>/`

### Environment variables (shinyapps dashboard → app → Vars)

| Variable | Description |
|----------|-------------|
| `GA_MEASUREMENT_ID` | Web stream ID (`G-…`). If unset, `app.py`’s default is used; set empty to disable GA |
| `GA_DEBUG` | Set to `1` for GA4 DebugView; remove when finished |

After changing Vars, **redeploy or restart** the app.

## Google Analytics 4

- `app.py` injects gtag with **`send_page_view: false`** so there is no automatic `page_view` without A/B; the tagged `page_view` with experiment params is sent from `www/ab.js` after the session is ready.
- **Sanity check:** browser F12 → Network → request to `googletagmanager.com/gtag/js`; `collect` requests with status **204**; events appear in GA4 **Realtime** or DebugView.

### Custom dimensions ↔ event parameters (must match Admin registration)

`ab_group` appears **only** in server log JSON and is **not** sent to GA; bind dimensions to the parameter names below.

| Use | Parameter | Notes |
|-----|-----------|--------|
| A/B arm | `stat5243_ab` | Values `ab_A` / `ab_B`; in-app and CSV still use `A` / `B` |
| Experiment name | `experiment_name` | e.g. `sensitive_purchase_assistant_ab` |
| Variant | `variant` | `human_advisor` / `private_ai` |
| Embarrassment item | `embarrassment` | Mostly on `survey_submit` |
| Help willingness | `help_willingness` | Mostly on `survey_submit`; CSV column is still **`trust`** |

On first load, one of **`stat5243_ab_A`** or **`stat5243_ab_B`** is also sent as a dedicated event name for easy per-arm counts in the Events report.

## Behavior and storage

- **A/B assignment, session id, survey submitted flag:** `sessionStorage`. **Refresh** in the same tab keeps them; **close the tab and open the site again** re-randomizes the arm and allows a new survey submission.
- **Client events:** `Shiny.setInputValue("client_event", …)` → server appends rows to CSV.
- **Local CSV:** `logs/events.csv` (created on first write; `logs/*.csv` is gitignored).
- **Production shinyapps:** instance disk is often ephemeral—**do not rely** on server-side CSV; use **GA4** for analysis.

## Troubleshooting

- No realtime hits: verify property / `G-` ID, data filters, ad blockers.
- Deploy fails: ensure `rsconnect` is from Python 3.12/3.11, not 3.14.
