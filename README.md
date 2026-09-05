# Customer Support Resolution Assistant

A Flask-based customer support workspace with grounded knowledge-base responses, ticket handling, diagnostics, escalation summaries, and customer and agent views.

## Run locally

From the project directory:

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in a browser. If port 5000 is already in use, start the app on another port with:

```powershell
python -c "import app; app.app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False, threaded=True)"
```

The health endpoint is available at `/health`.

## Test

Run the test suite with:

```powershell
python -m unittest -v
```

## Main API areas

- `/api/customers` for customer records
- `/api/tickets` for ticket creation and retrieval
- `/api/kb` for knowledge-base articles
- `/api/diagnostics/run` for line diagnostics
- `/api/analytics` for desk metrics