# VANTAGE Setup Guide

## Prerequisites

- macOS (Darwin 25.5.0+)
- Python 3.x
- Git
- Notion account with API access
- [OPERATOR TO FILL]: Required Python packages (see requirements.txt)

## Repository Structure

```
04-Vantage_CV/
├── Layer_1/                    # Main pipeline layer
│   ├── scripts/               # Python pipeline scripts
│   ├── wrappers/              # Shell wrapper scripts
│   ├── config/                # Configuration files
│   ├── feeds/                 # Feed JSON files
│   ├── archive/               # Archived scripts and backups
│   ├── .venv/                 # Python virtual environment
│   ├── .env → config/layer_1.env  # Environment variables (symlink)
│   └── requirements.txt       # Python dependencies
├── Layer_2/                    # Mail processing layer (placeholder)
├── Layer_3/                    # LinkedIn/mail integration layer
│   ├── scripts/               # Layer 3 scripts
│   ├── LAYER3.app             # Automator application
│   └── config/                # Configuration files
├── Layer_4/                    # Git sync layer
│   ├── scripts/               # Git sync scripts
│   ├── wrappers/              # Shell wrapper scripts
│   └── com.vantage.gitsync.plist  # LaunchAgent configuration
├── Dashboard/                  # Web dashboard
│   ├── scripts/               # Dashboard server and routes
│   ├── wrappers/              # Shell wrapper scripts
│   ├── dashboard.html         # Dashboard UI
│   └── config/                # Configuration files
├── Archive/                    # Repository archives
└── - Documentación/           # Documentation folders
```

## Environment Variables

### Layer 1 Configuration
Location: `Layer_1/config/layer_1.env`

Required environment variables:
- [OPERATOR TO FILL]: NOTION_API_KEY
- [OPERATOR TO FILL]: NOTION_DATABASE_ID
- [OPERATOR TO FILL]: Additional API keys or configuration

### Dashboard Configuration
Location: `Dashboard/config/` (if separate config exists)

## Python Environment

### Layer 1 Virtual Environment
Location: `Layer_1/.venv/`

Dependencies (Layer_1/requirements.txt):
```
python-dotenv>=1.0.0
requests>=2.31.0
notion-client>=2.2.0
pyyaml>=6.0
```

### Dashboard Dependencies
Location: `Dashboard/scripts/requirements_dashboard.txt`

Dependencies:
```
flask>=3.0.0
flask-cors>=4.0.0
notion-client==3.1.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### Setup Instructions
```bash
cd Layer_1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## First Run

### Layer 1 Pipeline
```bash
cd Layer_1
source .venv/bin/activate
python3 scripts/layer_1_run.py
```

Or use the wrapper:
```bash
./wrappers/layer_1_wrapper.sh
```

### Dashboard
```bash
cd Dashboard
source ../Layer_1/.venv/bin/activate
python3 scripts/dashboard_server.py
```

Or use the wrapper:
```bash
./wrappers/dashboard_start.sh
```

## LaunchAgent

### Git Sync Automation
Location: `Layer_4/com.vantage.gitsync.plist`

Schedule: Every 6 hours (09:00, 15:00, 21:00)

### Installation
```bash
# Load the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.vantage.gitsync.plist

# Or copy and load from repository
cp Layer_4/com.vantage.gitsync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.vantage.gitsync.plist
```

### Manual Git Sync
```bash
cd Layer_4
source ../Layer_1/.venv/bin/activate
python3 scripts/git_sync.py
```

Or use the wrapper:
```bash
./wrappers/git_sync_wrapper.sh
```

## Notion IDs

### Required Notion Database IDs
- [OPERATOR TO FILL]: Main tracker database ID
- [OPERATOR TO FILL]: Additional database IDs if applicable

### Notion Page IDs (for documentation sync)
- Aliases: 37c938be-fc42-80d4-b9ae-f5969830331b
- Change Log: 390938be-fc42-80e7-b429-d7d730339353

## Dashboard

### Access
- Local URL: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/health

### Features
- Pipeline visualization
- Status tracking
- Database management
- [OPERATOR TO FILL]: Additional features

### Dashboard Database
Location: `Dashboard/dashboard.db` and `Dashboard/dashboard_instances.db`

## Known Dependencies

### External Services
- Notion API
- [OPERATOR TO FILL]: Perplexity API (for discovery)
- [OPERATOR TO FILL]: Additional external services

### Internal Dependencies
- Layer 1 pipeline scripts
- Layer 3 mail processing
- Layer 4 git sync
- Dashboard server

### Shell Wrappers
- Layer_1/wrappers/layer_1_wrapper.sh
- Dashboard/wrappers/dashboard_start.sh
- Layer_4/wrappers/git_sync_wrapper.sh

### Automator Applications
- Layer_1/LAYER1.app
- Layer_3/LAYER3.app (renamed from LAYER2.app)
- Dashboard/Dashboard_.app

## Troubleshooting

### Common Issues
- [OPERATOR TO FILL]: Virtual environment not activating
- [OPERATOR TO FILL]: Notion API connection failures
- [OPERATOR TO FILL]: Git sync issues

### Log Files
- Git sync: /tmp/vantage_l4_gitsync.log
- Git sync errors: /tmp/vantage_l4_gitsync_err.log

## Additional Documentation

- Layer_1/VANTAGE_ARCHITECTURE.md - Detailed architecture documentation
- Layer_1/layer_1_routine.md - Operational routine guide
- [OPERATOR TO FILL]: Additional documentation references

## Repository Root Variable

All shell scripts use the standardized root variable:
```bash
VANTAGE_ROOT="$HOME/Documents/04-Vantage_CV"
```

This ensures consistent path references across all layers and wrappers.
