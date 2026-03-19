# Dev Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r gateway/requirements.txt
powershell -ExecutionPolicy Bypass -File ops/checks/check_import_app.ps1
```

Optional providers:
```powershell
py -m pip install -r gateway/requirements-optional.txt
```
