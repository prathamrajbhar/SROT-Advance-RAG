module.exports = {
  apps: [
    {
      name: "srot-api",
      cwd: __dirname,
      script: ".venv/bin/uvicorn",
      args: "main:app --host 0.0.0.0 --port 8087 --workers 2",
      interpreter: "none",
      restart_delay: 2000,
      max_restarts: 10,
      env_file: "../../.env",
      env: {
        PORT: 8087,
        ENVIRONMENT: "production",
      },
    },
    {
      name: "srot-worker",
      cwd: __dirname,
      script: ".venv/bin/celery",
      args: "-A modules.ingestion.tasks worker --loglevel=info --concurrency=4",
      interpreter: "none",
      restart_delay: 2000,
      max_restarts: 10,
      env_file: "../../.env",
      env: {
        ENVIRONMENT: "production",
      },
    },
  ],
};
