import json
from pathlib import Path
import socket
import sqlite3
from uuid import uuid4
import httpx
import pytest
from backend.tools import local_ops as ops


@pytest.mark.parametrize('port',[-1,1,65536,'public'])
def test_unsafe_ports_rejected(port):
    with pytest.raises(ops.OpsError):ops.preflight(port)


def test_occupied_port_is_not_killed():
    with socket.socket() as owner:
        owner.bind(('127.0.0.1',0));owner.listen()
        port=owner.getsockname()[1]
        with pytest.raises(ops.OpsError,match='PORT_IN_USE'):ops.preflight(port)
        assert owner.getsockname()[1]==port


def test_child_environment_excludes_keys_and_proxies(monkeypatch):
    for key in ['GEMINI_API_KEY','GOOGLE_APPLICATION_CREDENTIALS','HTTPS_PROXY','SENTINEL_ALLOW_BILLABLE']:
        monkeypatch.setenv(key,'DO_NOT_INHERIT')
    env=ops.child_environment()
    assert 'GEMINI_API_KEY' not in env and 'GOOGLE_APPLICATION_CREDENTIALS' not in env and 'HTTPS_PROXY' not in env
    assert env['SENTINEL_ALLOW_BILLABLE']=='false' and env['SENTINEL_PROVIDER_MODE']=='DISABLED'


def test_rejects_normal_data_roots_and_unacknowledged_fixtures():
    with pytest.raises(ops.OpsError):ops.owned_root(ops.ROOT/'backend/private_media')
    with pytest.raises(ops.OpsError,match='ACKNOWLEDGEMENT'):ops.start(port=0,fixture='unsafe-then-valid')


def test_path_that_cannot_be_directory_fails_without_touching_contents(tmp_path):
    target=tmp_path/'private';target.write_text('preserve')
    with pytest.raises(FileExistsError):ops.private_directory(target)
    assert target.read_text()=='preserve'


def test_missing_backup_database_is_not_created():
    root=ops.BASE/('phase06-demo-missing-backup-'+uuid4().hex)
    ops.private_directory(root)
    ops.atomic_json(root/'runtime.local.json',dict(owner='SENTINEL_PHASE06',root=str(root),port=12345,status='STOPPED'))
    with pytest.raises(ops.OpsError,match='BACKUP_SOURCE_REQUIRED'):ops.backup(root)
    assert not (root/'data/demo.sqlite').exists()


@pytest.fixture(scope='module')
def running():
    result=ops.start(port=0,fixture='unsafe-then-valid',acknowledge=True)
    root=Path(result['run_root'])
    try:yield root,result
    finally:ops.stop(root)


def test_real_process_private_control_and_missing_auth(running):
    root,result=running
    with httpx.Client(base_url=result['url'],trust_env=False) as c:
        assert c.get('/readyz').json()=={'status':'ready'}
        assert c.get('/_local/control').status_code==403
        assert c.post('/_local/control',headers={'X-Operator-Token':'wrong'}).status_code==403
        assert c.get('/v1/jobs').status_code==401
    assert ops.control(root)['status']=='READY'
    with pytest.raises((ops.OpsError,FileExistsError)):ops.start(root,port=0)
    with pytest.raises(ops.OpsError):ops.backup(root)


def test_instance_mismatch_never_stops_a_server(running):
    root,_=running
    saved=ops.record(root)
    try:
        ops.atomic_json(root/'runtime.local.json',saved|{'instance_id':'wrong-instance'})
        with pytest.raises(ops.OpsError,match='IDENTITY_MISMATCH'):ops.stop(root)
    finally:ops.atomic_json(root/'runtime.local.json',saved)
    assert ops.control(root)['status']=='READY'


def test_normal_restart_preserves_identity_case_and_audit_and_backup(running):
    root,initial=running
    credentials=json.loads((root/'data/credentials.local.json').read_text(encoding='utf-8'))
    manager=credentials['manager']
    with httpx.Client(base_url=initial['url'],trust_env=False) as c:
        token=c.post('/v1/auth/login',json={'tenant_id':manager['tenant_id'],'username':'manager','password':manager['password']}).json()['access_token']
        headers={'Authorization':'Bearer '+token}
        job=c.post('/v1/jobs',headers=headers,json={'asset_id':'PERSIST-006','contractor_id':credentials['contractor']['id'],'engineer_id':credentials['engineer']['id'],'service_agent_id':credentials['agent']['id']}).json()
        case=c.post('/v1/cases',headers=headers,json={'job_id':job['id']}).json()
    assert ops.stop(root)['status']=='STOPPED'
    with pytest.raises(httpx.TransportError):httpx.get(initial['url']+'/readyz',trust_env=False,timeout=1)
    resumed=ops.start(root,port=0,fixture='unsafe-then-valid',acknowledge=True,resume=True)
    with httpx.Client(base_url=resumed['url'],trust_env=False) as c:
        found=c.get('/v1/cases/'+case['id'],headers=headers)
        assert found.status_code==200 and found.json()['version']==case['version'] and found.json()['max_permission']==0
        audit=c.get('/v1/cases/'+case['id']+'/audit',headers=headers).json()
        assert any(e['event_type']=='CASE_CREATED' for e in audit)
    assert ops.stop(root)['status']=='STOPPED'
    backup=ops.backup(root)
    with sqlite3.connect(Path(backup['backup_root'])/'demo.sqlite') as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert db.execute('SELECT id FROM cases WHERE id=?',(case['id'],)).fetchone()[0]==case['id']


def test_expired_demo_cannot_resume(running):
    root,_=running
    saved=ops.record(root)
    try:
        ops.atomic_json(root/'runtime.local.json',saved|{'expires_at':0})
        with pytest.raises(ops.OpsError,match='EXPIRED'):ops.start(root,port=0,fixture='unsafe-then-valid',acknowledge=True,resume=True)
    finally:ops.atomic_json(root/'runtime.local.json',saved)
