"""Request a Pages build by pushing only one JSON file; then verify the live date.

The optional deploy credential is confined to this GitVerse repository. Source code,
generated catalog files and the worker's dirty index are never included in the push.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
REMOTE='git@gitverse.ru:NemoBek/lionstudio-3d.git'
SITE='https://nemobek.gitverse.site/lionstudio-3d/'
REQUEST_FILE='.publish-request.json'


def git(source,*args,env=None,data=None):
    return subprocess.check_output(['git',*args],cwd=source,input=data,
        env=env,timeout=90).decode().strip()


def request_publish(source,remote=REMOTE,env=None,now=None):
    source=Path(source)
    request={'requestedAt':(now or datetime.now(timezone.utc)).isoformat(),
             'catalogSha256':hashlib.sha256((source/'data.js').read_bytes()).hexdigest()}
    # Separate index: only the latest remote source tree plus this one JSON blob.
    # Do not add the worker's modified catalog/photos, other staged files or secrets.
    with tempfile.TemporaryDirectory() as temp:
        git_env={**os.environ,**(env or {}),'GIT_INDEX_FILE':str(Path(temp)/'index'),
                 'GIT_TERMINAL_PROMPT':'0'}
        git_env.pop('GITVERSE_DEPLOY_KEY',None)
        git(source,'fetch','--depth=1',remote,'refs/heads/master',env=git_env)
        parent=git(source,'rev-parse','FETCH_HEAD',env=git_env)
        git(source,'read-tree',parent,env=git_env)
        body=(json.dumps(request,sort_keys=True)+'\n').encode()
        blob=git(source,'hash-object','-w','--stdin',env=git_env,data=body)
        git(source,'update-index','--add','--cacheinfo','100644',blob,REQUEST_FILE,env=git_env)
        tree=git(source,'write-tree',env=git_env)
        revision=git(source,'-c','user.name=Catalog-Publish','-c',
            'user.email=catalog-publish@users.noreply.github.com','commit-tree',tree,
            '-p',parent,'-m','Request validated catalog publication',env=git_env)
        # No force push. A simultaneous source edit makes this fail safely.
        git(source,'push',remote,revision+':refs/heads/master',env=git_env)
    request['requestCommit']=revision
    return request


def read(url):
    with urlopen(Request(url,headers={'User-Agent':'LionStudio-Publication-Check/1.0'}),timeout=20) as response:
        body=response.read(2_000_001)
        if len(body)>2_000_000:raise ValueError('Publication response exceeds limit')
        return body


def probe(request,reader=read):
    html=reader(SITE).decode('utf-8')
    match=re.search(r'<span id="catalogUpdated">Синхронизация: (\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}) \(UTC\+5\)</span>',html)
    if not match:return None
    published=datetime.strptime(match[1],'%d.%m.%Y, %H:%M').replace(tzinfo=timezone(timedelta(hours=5)))
    requested=datetime.fromisoformat(request['requestedAt']).replace(second=0,microsecond=0)
    if published<requested:return None
    scripts=re.findall(r'src="([a-z-]+\.([a-f0-9]{12})\.js)"',html)
    if len(scripts)!=5:return None
    for name,digest in scripts:
        if hashlib.sha256(reader(SITE+name)).hexdigest()[:12]!=digest:return None
    return {'status':'published','syncedAt':published.isoformat(),
            'requestCommit':request['requestCommit'],'runtimeFilesChecked':len(scripts)}


def wait_for_publication(request,max_wait=480,reader=read,sleep=time.sleep,clock=time.monotonic):
    deadline=clock()+max_wait
    while True:
        try:
            result=probe(request,reader)
            if result:return result
        except HTTPError as exc:
            if exc.code in (403,429):raise
            if exc.code not in (404,500,502,503,504):raise
        except (URLError,TimeoutError,ConnectionError,UnicodeDecodeError):pass
        if clock()>=deadline:raise TimeoutError('GitVerse did not publish a fresh catalog within the deadline')
        sleep(min(15,max(0,deadline-clock())))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE/'work')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    receipt=HERE/'publish-receipt.json'
    if args.check:
        print(json.dumps(wait_for_publication(json.loads(receipt.read_text()))))
        return
    key=os.environ.get('GITVERSE_DEPLOY_KEY','')
    if not key:raise SystemExit('Missing approved repository deploy key')
    with tempfile.TemporaryDirectory() as temp:
        private=Path(temp)/'deploy_key'
        private.write_text(key.rstrip()+'\n',encoding='utf-8');private.chmod(0o600)
        command='ssh -i '+shlex.quote(str(private))+' -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile='+shlex.quote(str(HERE/'gitverse_known_hosts'))
        request=request_publish(args.source,env={'GIT_SSH_COMMAND':command})
    receipt.write_text(json.dumps(request,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'requested',**request}))


if __name__=='__main__':main()
