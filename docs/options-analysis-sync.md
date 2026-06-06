# Options Analysis Sync

The usmonitor.app options page is behaviorally paired with the local desktop/single-machine project:

```text
C:\Users\user\Documents\Option Analysis
```

When the local Option Analysis terminal changes, review this web implementation for the same behavior:

- UI, language switching, watchlists, autocomplete, filters, sorting, and table/detail columns.
- Massive API host, auth behavior, REST assumptions, timeout/retry behavior, and quote mode handling.
- Quick refresh versus full chain scan behavior.
- PER, PER rank, Black-Scholes value, premium versus model, stress tests, and edge flags.
- Options navigation and `/options` entry points.

Current Serenity files:

- `static\options.html`
- `static\options.js`
- `static\styles.css`
- `app\main.py`
- `app\services\options_analysis.py`
- `app\config.py`
- `.env.example`, `.env.deploy.example`, and `render.yaml`

The local project contains the machine-readable mapping and check script:

```powershell
cd "C:\Users\user\Documents\Option Analysis"
.\scripts\check_usmonitor_sync.cmd
```

Do not blindly copy files from the local app. The local app and Serenity use different front-end/runtime structures, so changes should be ported deliberately and tested in both places.
