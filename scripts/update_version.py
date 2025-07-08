import json
import os
import subprocess
from pathlib import Path


def get_latest_tag() -> str:
    try:
        tags = subprocess.check_output(['git', 'tag', '--list', 'v*', '--sort=-v:refname'], text=True).split()
        return tags[0] if tags else 'v0.0.0'
    except Exception:
        return 'v0.0.0'


def get_short_commit() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except Exception:
        return 'unknown'


def build_run_url() -> str:
    run_id = os.environ.get('GITHUB_RUN_ID')
    if not run_id:
        return ''
    server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com')
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    if not repo:
        return ''
    return f"{server}/{repo}/actions/runs/{run_id}"


def main() -> None:
    tag = get_latest_tag()
    commit = get_short_commit()
    run = build_run_url()
    data = {'tag': tag, 'commit': commit, 'run': run}
    Path('version.json').write_text(json.dumps(data))
    print('version.json updated:', data)


if __name__ == '__main__':
    main()
