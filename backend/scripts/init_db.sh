#!/usr/bin/env bash
# =============================================================================
# init_db.sh — Database initialization script for academic-figure-generator
#
# Responsibilities:
#   1. Wait for PostgreSQL to be ready (health-check loop)
#   2. Run Alembic migrations to bring schema to HEAD
#   3. Run seed_color_schemes.py to populate preset data
#   4. (Optional) Create MinIO bucket if MINIO_* vars are set
#
# Usage:
#   ./scripts/init_db.sh
#
# Environment variables (read from environment or .env):
#   POSTGRES_HOST         (default: localhost)
#   POSTGRES_PORT         (default: 5432)
#   POSTGRES_USER         (default: afg_user)
#   POSTGRES_PASSWORD     (required)
#   POSTGRES_DB           (default: academic_figure_generator)
#   DATABASE_URL          (optional, overrides individual POSTGRES_* vars)
#   MINIO_ENDPOINT        (optional, enables bucket creation)
#   MINIO_ACCESS_KEY      (optional)
#   MINIO_SECRET_KEY      (optional)
#   MINIO_BUCKET_NAME     (default: academic-figures)
#   MAX_WAIT_SECONDS      (default: 60)
#   SKIP_SEED             (set to "true" to skip seeding)
#   SKIP_MINIO            (set to "true" to skip MinIO bucket creation)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-afg_user}"
POSTGRES_DB="${POSTGRES_DB:-academic_figure_generator}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-60}"
SKIP_SEED="${SKIP_SEED:-false}"
SKIP_MINIO="${SKIP_MINIO:-false}"

# Script is expected to run from the backend/ directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log_info()  { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [INFO]  $*"; }
log_ok()    { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [OK]    $*"; }
log_warn()  { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [WARN]  $*" >&2; }
log_error() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [ERROR] $*" >&2; }

# ---------------------------------------------------------------------------
# Step 1: Wait for PostgreSQL
# ---------------------------------------------------------------------------
wait_for_postgres() {
    log_info "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT} ..."
    local elapsed=0
    local interval=2

    until pg_isready \
        --host="${POSTGRES_HOST}" \
        --port="${POSTGRES_PORT}" \
        --username="${POSTGRES_USER}" \
        --dbname="${POSTGRES_DB}" \
        --quiet 2>/dev/null
    do
        if [[ ${elapsed} -ge ${MAX_WAIT_SECONDS} ]]; then
            log_error "PostgreSQL did not become ready within ${MAX_WAIT_SECONDS}s. Aborting."
            exit 1
        fi
        log_info "  PostgreSQL not ready yet (${elapsed}s elapsed). Retrying in ${interval}s ..."
        sleep "${interval}"
        elapsed=$(( elapsed + interval ))
    done

    log_ok "PostgreSQL is ready (${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB})."
}

# ---------------------------------------------------------------------------
# Step 2: Run Alembic migrations
# ---------------------------------------------------------------------------
run_migrations() {
    log_info "Running Alembic migrations ..."
    cd "${BACKEND_DIR}"

    if ! command -v alembic &>/dev/null; then
        log_error "'alembic' command not found. Ensure it is installed in the current Python environment."
        exit 1
    fi

    alembic upgrade head

    log_ok "Alembic migrations applied successfully."
}

# ---------------------------------------------------------------------------
# Step 3: Seed color schemes
# ---------------------------------------------------------------------------
seed_data() {
    if [[ "${SKIP_SEED}" == "true" ]]; then
        log_warn "SKIP_SEED=true — skipping seed_color_schemes.py."
        return
    fi

    log_info "Seeding preset color schemes ..."
    cd "${BACKEND_DIR}"

    if ! python scripts/seed_color_schemes.py; then
        log_error "seed_color_schemes.py failed."
        exit 1
    fi

    log_ok "Color schemes seeded."
}

# ---------------------------------------------------------------------------
# Step 4: Create MinIO bucket (optional)
# ---------------------------------------------------------------------------
create_minio_bucket() {
    if [[ "${SKIP_MINIO}" == "true" ]]; then
        log_warn "SKIP_MINIO=true — skipping MinIO bucket creation."
        return
    fi

    local endpoint="${MINIO_ENDPOINT:-}"
    if [[ -z "${endpoint}" ]]; then
        log_warn "MINIO_ENDPOINT not set — skipping MinIO bucket creation."
        return
    fi

    local access_key="${MINIO_ACCESS_KEY:-minioadmin}"
    local secret_key="${MINIO_SECRET_KEY:-minioadmin}"
    local bucket="${MINIO_BUCKET_NAME:-academic-figures}"
    local use_ssl="${MINIO_USE_SSL:-false}"

    # Determine scheme for mc alias
    local scheme="http"
    if [[ "${use_ssl}" == "true" ]]; then
        scheme="https"
    fi
    local mc_url="${scheme}://${endpoint}"

    # Wait for MinIO health endpoint before attempting bucket creation
    log_info "Waiting for MinIO at ${mc_url} ..."
    local elapsed=0
    local interval=3
    local minio_wait_max=60

    until curl --silent --fail "${mc_url}/minio/health/live" &>/dev/null; do
        if [[ ${elapsed} -ge ${minio_wait_max} ]]; then
            log_warn "MinIO did not become healthy within ${minio_wait_max}s. Skipping bucket creation."
            return
        fi
        log_info "  MinIO not ready (${elapsed}s). Retrying ..."
        sleep "${interval}"
        elapsed=$(( elapsed + interval ))
    done
    log_ok "MinIO is healthy."

    if command -v mc &>/dev/null; then
        # Use MinIO Client (mc) if available
        mc alias set init_alias "${mc_url}" "${access_key}" "${secret_key}" --quiet 2>/dev/null || true

        if mc ls "init_alias/${bucket}" &>/dev/null; then
            log_info "MinIO bucket '${bucket}' already exists — skipping creation."
        else
            mc mb "init_alias/${bucket}"
            log_ok "MinIO bucket '${bucket}' created."
        fi

        # Set bucket policy to private (download requires signed URLs)
        mc anonymous set none "init_alias/${bucket}" 2>/dev/null || true

    elif python -c "import minio" &>/dev/null 2>&1; then
        # Fall back to Python minio SDK
        python - <<EOF
import os
from minio import Minio

client = Minio(
    endpoint="${endpoint}",
    access_key="${access_key}",
    secret_key="${secret_key}",
    secure=${use_ssl^},  # Python True/False from bash true/false
)
bucket = "${bucket}"
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)
    print(f"[OK] MinIO bucket '{bucket}' created via Python SDK.")
else:
    print(f"[INFO] MinIO bucket '{bucket}' already exists.")
EOF
    else
        log_warn "Neither 'mc' nor 'minio' Python package found. Skipping bucket creation."
        log_warn "Create the bucket manually: mc mb myminio/${bucket}"
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    log_info "================================================================"
    log_info "  academic-figure-generator — database initialization"
    log_info "  Backend dir : ${BACKEND_DIR}"
    log_info "  PostgreSQL  : ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    log_info "================================================================"

    wait_for_postgres
    run_migrations
    seed_data
    create_minio_bucket

    log_info "================================================================"
    log_ok   "  Initialization complete. Service is ready to start."
    log_info "================================================================"
}

main "$@"
