-- Fase 1: Modelo de dados (a base de tudo)
-- PostgreSQL como fila via LISTEN/NOTIFY

CREATE TYPE job_status AS ENUM (
  'pending', 'running', 'done', 'failed', 'dead'
);

CREATE TABLE jobs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  queue         TEXT NOT NULL DEFAULT 'default',
  payload       JSONB NOT NULL,
  status        job_status NOT NULL DEFAULT 'pending',
  priority      INT NOT NULL DEFAULT 0,        -- maior = mais urgente
  attempts      INT NOT NULL DEFAULT 0,
  max_attempts  INT NOT NULL DEFAULT 3,
  run_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at    TIMESTAMPTZ,
  finished_at   TIMESTAMPTZ,
  lease_expires_at TIMESTAMPTZ,                -- Expiração do lease para evitar job "zumbi"
  last_error    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice parcial: não cresce com o histórico de concluídos
CREATE INDEX idx_jobs_pending ON jobs (queue, status, priority DESC, run_at)
  WHERE status = 'pending';

-- Trigger que notifica workers via LISTEN/NOTIFY
CREATE OR REPLACE FUNCTION notify_job() RETURNS trigger AS $$
BEGIN
  -- NEW.queue é passado no payload para o worker saber qual fila processar
  PERFORM pg_notify('job_available', NEW.queue);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_job_insert
  AFTER INSERT ON jobs
  FOR EACH ROW EXECUTE FUNCTION notify_job();

-- Trigger para notificações em updates (ex: quando um job volta para pending em retry)
CREATE OR REPLACE FUNCTION notify_job_update() RETURNS trigger AS $$
BEGIN
  IF NEW.status = 'pending' AND (OLD.status != 'pending' OR NEW.run_at <= now()) THEN
    PERFORM pg_notify('job_available', NEW.queue);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_job_update
  AFTER UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION notify_job_update();
