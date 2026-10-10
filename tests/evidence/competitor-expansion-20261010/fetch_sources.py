"""Fetch public original rule text for research; never execute retrieved material."""
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, sys, datetime

OUT = Path(__file__).parent / 'sources'
OUT.mkdir(exist_ok=True)
opener = build_opener(ProxyHandler({}))

def get(url):
    with opener.open(Request(url, headers={'User-Agent': 'Academic-Skill-Source-Research'}), timeout=35) as r:
        return r.read()

def fetch(row):
    repo, path = row['repo'], row['path']
    record = dict(row)
    try:
        meta = json.loads(get('https://api.github.com/repos/' + repo))
        branch = meta['default_branch']
        commit = json.loads(get('https://api.github.com/repos/' + repo + '/commits/' + branch))['sha']
        record.update(default_branch=branch, commit=commit, license=meta.get('license'),
                      canonical_repo=meta.get('full_name'), is_fork=meta.get('fork'),
                      parent_repo=(meta.get('parent') or {}).get('full_name'))
        url = 'https://raw.githubusercontent.com/' + repo + '/' + commit + '/' + path
        content = get(url)
        name = row['id'] + '.txt'
        (OUT / name).write_bytes(content)
        record.update(url=url, blob_url='https://github.com/' + repo + '/blob/' + commit + '/' + path,
                      sha256=hashlib.sha256(content).hexdigest(), bytes=len(content), local_file=name,
                      fetched_at_beijing=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
                      fetch_completed=True, rule_reading_completed=False)
    except Exception as error:
        record.update(fetch_completed=False, error=str(error), rule_reading_completed=False)
    (OUT / (row['id'] + '.receipt.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return {k: record.get(k) for k in ['id', 'fetch_completed', 'commit', 'bytes', 'license', 'error']}

if __name__ == '__main__':
    rows = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(fetch, rows):
            print(json.dumps(result, ensure_ascii=False), flush=True)
