import shutil
from types import SimpleNamespace
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.tests.phase01.conftest import account_template, Clock
from backend.app.api import create_app
from backend.app.hosting import mount_hosting
from backend.app.settings import Settings
from backend.tools.local_ops import ROOT


@pytest.fixture
def hosted(tmp_path, account_template):
    template, ids, passwords, tokens = account_template
    database = tmp_path/'demo.sqlite'
    shutil.copyfile(template,database)
    bundle = tmp_path/'bundle'
    shutil.copytree(ROOT/'frontend/dist',bundle)
    app = create_app(Settings(database_path=database,environment='test',provider_mode='MOCK_AI',
                              media_root=tmp_path/'media'),clock=Clock())
    mount_hosting(app,bundle)
    with TestClient(app,base_url='http://127.0.0.1') as client:
        yield app,client,bundle,tokens


def test_liveness_readiness_are_safe_and_distinct(hosted):
    app,c,bundle,tokens=hosted
    assert c.get('/healthz').status_code==200
    assert c.get('/readyz').json()=={'status':'ready'}
    assert not list(app.state.settings.media_root.glob('.ready-*'))
    for response in [c.get('/readyz'),c.get('/healthz')]:
        assert str(app.state.settings.database_path) not in response.text
        assert 'token' not in response.text and 'user_count' not in response.text


@pytest.mark.parametrize('route',['/','/login','/contractor/jobs','/manager/queue','/engineer'])
def test_real_bundle_and_deep_links(hosted,route):
    _,c,_,_=hosted
    r=c.get(route)
    assert r.status_code==200 and '<div id="root">' in r.text
    assert "script-src 'self'" in r.headers['content-security-policy']
    assert r.headers['referrer-policy']=='no-referrer'
    assert r.headers['x-frame-options']=='DENY'


@pytest.mark.parametrize('route',['/.env','/.git/config','/backend/local.sqlite','/v1/missing','/docs','/_local/control','/assets/../../.env'])
def test_no_spa_fallback_for_private_or_unknown_paths(hosted,route):
    _,c,_,_=hosted
    r=c.get(route)
    assert r.status_code==404 and '<html' not in r.text


def test_host_origin_and_authorization_remain_enforced(hosted):
    _,c,_,tokens=hosted
    assert c.get('/readyz',headers={'Host':'evil.example'}).status_code==400
    assert c.get('/v1/jobs').status_code==401
    assert c.get('/v1/alerts',headers={'Authorization':'Bearer '+tokens['a_manager']}).status_code==403
    assert c.get('/v1/jobs',headers={'Authorization':'Bearer '+tokens['a_contractor']}).json()==[]
    assert 'access-control-allow-origin' not in c.options('/v1/jobs',headers={'Origin':'https://evil.example'}).headers


def test_removed_frontend_is_not_a_ready_backend(hosted):
    _,c,bundle,_=hosted
    (bundle/'index.html').unlink()
    assert c.get('/healthz').status_code==200
    assert c.get('/readyz').status_code==503
    assert c.get('/').status_code==503


def test_modified_asset_is_not_served(hosted):
    _,c,bundle,_=hosted
    asset=next((bundle/'assets').glob('*.js'))
    asset.write_bytes(b'untrusted changed bundle')
    assert c.get('/readyz').status_code==503
    assert c.get('/assets/'+asset.name).status_code==503


def test_unwritable_media_target_is_redacted(hosted):
    app,c,_,_=hosted
    target=app.state.settings.media_root
    target.write_bytes(b'file cannot be a media directory')
    response=c.get('/readyz')
    assert response.status_code==503 and response.json()=={'status':'not_ready'}
    assert str(target) not in response.text


def test_database_failure_injection_fails_readiness(hosted,monkeypatch):
    app,c,_,_=hosted
    def unavailable():raise OSError('private database error must stay private')
    monkeypatch.setattr(app.state.service.repository,'transaction',unavailable)
    assert c.get('/readyz').json()=={'status':'not_ready'}
    assert c.get('/healthz').status_code==200


@pytest.mark.parametrize('config',[
    dict(provider_mode='LIVE_GEMINI',allow_billable=True,gemini_api_key='dummy'),
    dict(provider_mode='MOCK_AI',allow_billable=True,gemini_api_key=None),
    dict(provider_mode='MOCK_AI',allow_billable=False,gemini_api_key='dummy')])
def test_hosting_refuses_any_live_or_secret_configuration(hosted,config):
    app,_,bundle,_=hosted
    app.state.settings=SimpleNamespace(**config)
    with pytest.raises(ValueError,match='OFFLINE_CONFIGURATION_REQUIRED'):mount_hosting(app,bundle)


def test_failed_security_execution_cannot_pass_hosted_gate(hosted):
    app,c,_,tokens=hosted
    headers={'Authorization':'Bearer '+tokens['a_engineer']}
    candidate=c.post('/v1/redteam/candidates',headers=headers,json={'profile':'SAFE_BASELINE'}).json()
    app.state.assurance.runner=lambda request:(None,'RUN_TIMEOUT',0.01)
    run=c.post('/v1/redteam/run',headers=headers,json={'candidate_id':candidate['id'],'expected_candidate_version':1,
        'idempotency_key':'phase06_failed_run_key_123'}).json()
    assert run['status']=='FAILED' and run['summary']['unevaluable']==38
    response=c.post(f"/v1/redteam/candidates/{candidate['id']}/release-gate",headers=headers,
        json={'expected_version':1,'run_id':run['id']})
    assert response.status_code==409 and response.json()['reason_codes']==['CURRENT_COMPLETE_RUN_REQUIRED']
