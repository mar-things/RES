# PostgreSQL Migration

1. Create a PostgreSQL database and user.
2. Set `DATABASE_URL` in `.env`:

   ```text
   DATABASE_URL=postgresql+psycopg2://res_user:strong_password@db-host:5432/res_db
   APP_ENV=production
   SECRET_KEY=<strong random value>
   ```

3. Install dependencies:

   ```powershell
   uv sync
   ```

4. Initialize schema and seed required data:

   ```powershell
   uv run python -c "from core.database import init_db; from core.seeds import seed_all; init_db(); seed_all()"
   ```

5. Start the desktop app:

   ```powershell
   uv run python main.py
   ```

The application uses SQLAlchemy models only, so the SQLite-to-PostgreSQL switch is
configuration-driven for the current schema.
