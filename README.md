# CarStats

A personal car logging app: fuel fill-ups, maintenance/service history (with
invoice/photo attachments), due-date/due-mileage reminders, and a cost
dashboard. Backend is FastAPI + SQLModel + SQLite; frontend is React + Vite +
TypeScript. Access is gated behind Google OAuth, restricted to a single
allowed email.

## Local development

### Backend

```bash
cd backend
uv sync
cp .env.example .env   # fill in ALLOWED_EMAIL at minimum; Google OAuth creds
                        # aren't needed to exercise most of the API locally
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. Interactive API docs at `/docs`.

Run tests: `uv run pytest`. Lint: `uv run ruff check .`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` and proxies `/api` and `/auth` to the backend
on port 8000 (see `frontend/vite.config.ts`).

Since real Google sign-in requires registered OAuth credentials and a
reachable redirect URL, local development against `/api/*` without signing
in will get a 401 — testing the authenticated app end-to-end happens after
the production deploy below, or by registering an OAuth client with
`http://localhost:8000/auth/callback` as an additional redirect URI.

## Production deployment (Oracle Cloud free VM + Cloudflare Tunnel)

This runs the whole app as one Docker container, always-on, at zero cost:
an Oracle Cloud "Always Free" VM for compute + persistent disk, and a
Cloudflare Tunnel for public HTTPS access without opening any ports.

### One-time setup

1. **Create the VM**: Oracle Cloud Console → Compute → Instances → Create
   Instance. Pick an "Always Free" eligible shape (an Ampere A1 or VM.Standard.E2.1.Micro).
   Ubuntu or Oracle Linux both work fine, since the app runs entirely inside
   Docker; make sure a public IP is assigned.

   If you're on E2.1.Micro (1 GB RAM), add swap before installing anything —
   `dnf`/`apt` dependency resolution across several repos can otherwise choke
   the machine into unresponsive swap-thrashing:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
2. **Install Docker** on the VM:

   On Ubuntu:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

   On Oracle Linux (the convenience script above doesn't support it):
   ```bash
   sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
   sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   ```

   (log out/in for the group change to apply)
3. **Clone this repo** onto the VM.
4. **Create a Google OAuth client**: Google Cloud Console → APIs & Services →
   Credentials → Create OAuth client ID (Web application). Add
   `https://<your-tunnel-hostname>/auth/callback` as an authorized redirect
   URI once you know it from step 5.
5. **Create a Cloudflare Tunnel**: Cloudflare Zero Trust dashboard → Networks
   → Tunnels → Create a tunnel. Point its public hostname at
   `http://app:8000` (the `app` service name from `docker-compose.yml`).
   Copy the tunnel token.
6. **Configure secrets**: on the VM, `cp .env.example .env` and fill in
   `CARSTATS_GOOGLE_CLIENT_ID`, `CARSTATS_GOOGLE_CLIENT_SECRET`,
   `CARSTATS_OAUTH_REDIRECT_URL` (the tunnel hostname from step 5),
   `CARSTATS_ALLOWED_EMAIL` (your Google account email), and
   `CLOUDFLARE_TUNNEL_TOKEN` from step 5. Generate `CARSTATS_SESSION_SECRET`
   with e.g. `openssl rand -hex 32`.
7. **Deploy**: `./deploy.sh`

### Subsequent deploys

After pushing changes, on the VM: `./deploy.sh` — pulls the latest commit,
rebuilds the image, and restarts the containers. The SQLite database and
uploaded files live in the `carstats_data` Docker volume and survive
redeploys.
