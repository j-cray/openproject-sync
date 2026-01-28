# OpenProject Sync

A Python-based tool to synchronize a CSV roadmap to an OpenProject instance.

## Features
- **CSV Import**: Reads task data from a CSV file.
- **Hierarchy Support**: Automatically structures tasks under "Phases".
- **Deduplication**: Checks if tasks already exist to avoid duplicates.
- **Nix Support**: reproducible development environment via Flakes.

## Installation

### 1. Environment
This project uses **Nix** for dependency management.
```bash
nix develop
# or with direnv
direnv allow
```

### 2. Configuration
Create a `.env` file (copied from `.env` template):
```bash
OPENPROJECT_API_KEY=your_api_key
OPENPROJECT_URL=https://openproject.example.com
OPENPROJECT_PROJECT=project-identifier
```

## Usage

### Standalone
Run the script to sync the local `roadmap.csv`:
```bash
python sync.py
```

Run a dry run to see what would happen:
```bash
python sync.py --dry-run
```

### CSV Format
The script expects a CSV file with the following headers:
- `Type`: Must be "Phase" for parent containers, "Task" for children, or "Milestone".
- `Subject`: The title of the work package.
- `Description`: Detaied description (Markdown supported).
- `Priority`: (Optional) Priority level (e.g., High, Normal).
- `EstHours`: Estimated time in hours.

See `template.csv` for an example.

**Note:** The script relies on row order. A "Task" is assigned to the most recently encountered "Phase".

### As a Submodule
You can include this repository as a submodule to sync roadmaps from other projects.

1. Add the submodule:
   ```bash
   git submodule add <repo-url> openproject-sync
   ```

2. Run the sync script, pointing to your project's roadmap:
   ```bash
   python openproject-sync/sync.py path/to/your/roadmap.csv
   ```
