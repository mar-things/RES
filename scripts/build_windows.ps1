param(
    [string]$EntryPoint = "main.py"
)

$ErrorActionPreference = "Stop"

uv run pyinstaller --onefile --windowed --name RES $EntryPoint
