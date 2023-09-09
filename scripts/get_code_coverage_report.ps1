activate

Remove-Item -LiteralPath "htmlcov" -Force -Recurse
pytest --cov api api/tests --cov-report html
start msedge /htmlcov/index.html