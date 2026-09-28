if (!(Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}
& ".venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
python -m uvicorn app.main:app --reload
