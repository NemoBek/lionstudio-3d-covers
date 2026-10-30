"""Publish only new, owner-authorized Telegram photos; no private source files."""
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'work'
sys.path.insert(0,str(SOURCE/'tools'))
from import_telegram_covers import run
from covers import validate_covers,canonical_post,cover_key
from io_utils import write_bundle


def main():
    manifest_path=HERE/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'version':1,'entries':{}}
    entries=manifest['entries']
    registry=json.loads((SOURCE/'covers.json').read_text(encoding='utf-8'))
    # Seed previously checked downloads, so a delayed GitVerse publication never
    # causes the same Telegram photo to be downloaded again.
    cached={}
    for key,entry in entries.items():
        post=canonical_post(entry['postUrl'])
        if cover_key(post)!=key or entry['path'] not in (f'public/covers/{key}.jpg',f'public/covers/{key}.png',f'public/covers/{key}.webp'):
            raise ValueError('Invalid cached photo mapping')
        body=(HERE/entry['path']).read_bytes()
        if hashlib.sha256(body).hexdigest()!=entry['sha256']:raise ValueError('Invalid cached photo checksum')
        if key not in registry:
            registry[key]=entry
            cached[entry['path']]=body
    validate_covers(registry,SOURCE,cached)
    writes={SOURCE/path:body for path,body in cached.items()}
    writes[SOURCE/'covers.json']=json.dumps(registry,ensure_ascii=False,indent=2)+'\n'
    writes[SOURCE/'covers.js']='window.LION_COVERS = '+json.dumps(registry,ensure_ascii=False)+';\n'
    write_bundle(writes)
    report=run(root=SOURCE,all_posts=True,max_downloads=20,report_dir='reports',
               permission='Channel owner permission confirmed by user 2026-10-26; automatic import authorized 2026-10-31')
    updated=json.loads((SOURCE/'covers.json').read_text(encoding='utf-8'))
    writes={}
    for row in report['entries']:
        if row['status']!='imported':continue
        key=row['messageId'];entry=dict(updated[key])
        entry['permissionReference']='owner-permission-confirmed-2026-10-26'
        entries[key]=entry
        writes[HERE/entry['path']]=(SOURCE/entry['path']).read_bytes()
    (HERE/'public/covers').mkdir(parents=True,exist_ok=True)
    summary={key:report[key] for key in ('checkedAt','selectedCount','counts')}
    summary['pending']=[{key:row.get(key) for key in ('messageId','title','stage','detail')}
                        for row in report['entries'] if row['status'] not in ('kept','imported')]
    manifest.update(version=1,checkedAt=report['checkedAt'],entries=entries)
    writes[manifest_path]=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    writes[HERE/'status.json']=json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
    write_bundle(writes)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
