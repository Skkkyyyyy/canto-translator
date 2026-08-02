.PHONY: logs

logs:
	cd backend && . .venv/bin/activate && datasette data/contributions.db -p 8001 --open
