# Expense Bot - Development Guide

## Quick Start

For new developers, run the complete setup:
```bash
./scripts/dev-setup.sh
```

For daily development:
```bash
make dev
```

## Available Commands

Run `make help` to see all available commands:

- `make dev` - Start all services (frontend, backend, emulators)
- `make frontend` - Start only frontend
- `make backend` - Start only backend  
- `make emulators` - Start only Firebase emulators
- `make install` - Install all dependencies
- `make build` - Build for production
- `make test` - Run all tests
- `make lint` - Run all linting
- `make clean` - Clean build artifacts

## Architecture

```
expense-bot/
├── frontend/          # Next.js 15 frontend
├── backend/           # Python Flask backend  
├── infra/            # Infrastructure (Docker, Terraform)
├── notebooks/        # Jupyter notebooks for ML
├── scripts/          # Development scripts
├── Makefile         # Development commands
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Fill in your API keys and configuration
3. Run `./scripts/setup-env.sh` to generate frontend/backend env files

## Firebase Emulator Issues

If you're having connection issues:

1. **Chrome users**: Try Safari or Firefox first
2. **Clear cache**: Hard refresh (Cmd+Shift+R) 
3. **Restart emulators**: `make emulators-stop && make emulators`
4. **Check health**: `make health-check`

See `BROWSER_COMPATIBILITY.md` for detailed browser-specific guidance.

## Service URLs

When running `make dev`:

- Frontend: http://localhost:3000
- Backend API: http://localhost:9004  
- Firebase UI: http://localhost:4000
- Firestore Emulator: http://localhost:8080
- Auth Emulator: http://localhost:9099

## Troubleshooting

### Common Issues

1. **Port conflicts**: Stop services with `make emulators-stop`
2. **Environment issues**: Re-run `./scripts/setup-env.sh`
3. **Dependencies**: Re-run `make install`
4. **Chrome issues**: Use Safari or incognito mode

### Health Check

Run system health check:
```bash
make health-check
# or
./scripts/health-check.sh
```

### Clean Start

For a completely clean restart:
```bash
make clean
make emulators-stop
make install
make dev
```

## Development Workflow

1. Make code changes
2. Check health: `make health-check`
3. Run tests: `make test`  
4. Lint code: `make lint`
5. Commit changes

## Tips

- Use `make quick-start` for frontend-only development
- Chrome can be problematic - Safari works best with emulators
- Keep Firebase emulators running in a separate terminal
- Use `./start-dev.sh` for a simpler all-in-one startup

## Getting Help

- Run `make help` for all commands
- Look at `scripts/` directory for utilities