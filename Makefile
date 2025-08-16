style_wps:
	uv run flake8 . --select=WPS

style_ruff:
	uv run ruff check .

format_ruff:
	uv run ruff format .

style:
	make format_ruff style_ruff

runapp:
	uv run streamlit run src/app.py
