from backend.tests.phase01.conftest import account_template, Clock, World
from backend.app.api import create_app
from backend.app.settings import Settings
from fastapi.testclient import TestClient
import shutil
import pytest


@pytest.fixture
def world(tmp_path, account_template):
    template, ids, passwords, tokens = account_template
    database = tmp_path / "portal.sqlite"
    shutil.copy2(template, database)
    clock = Clock()
    app = create_app(Settings(database_path=database, environment="test", allow_synthetic=True,
                              media_root=tmp_path / "media"), clock=clock)
    with TestClient(app) as client:
        yield World(app, client, ids, passwords, tokens, clock)


@pytest.mark.parametrize('path', ['/v1/assignees', '/v1/jobs/absent/cases', '/v1/redteam/candidates/absent/history'])
def test_new_reads_require_auth(world, path):
    assert world.client.get(path).status_code == 401


@pytest.mark.parametrize('role', ['a_contractor', 'a_engineer', 'a_agent'])
def test_assignees_manager_only(world, role):
    assert world.request('GET', '/v1/assignees', role).status_code == 403


def test_assignees_scope_projection_and_pagination(world):
    response = world.request('GET', '/v1/assignees?limit=1').json()
    assert len(response['items']) == 1 and response['next_cursor']
    assert set(response['items'][0]) == {'id', 'username', 'role'}
    assert response['items'][0]['id'] in {world.ids['a_contractor'], world.ids['a_other_contractor']}
    next_page = world.request('GET', '/v1/assignees?limit=1&after=' + response['next_cursor']).json()
    assert len(next_page['items']) == 1 and next_page['items'][0]['id'] != response['items'][0]['id']
    assert world.request('GET', '/v1/assignees?after=' + world.ids['b_contractor']).status_code == 404
    assert world.request('GET', '/v1/assignees?limit=101').status_code == 422


def test_job_cases_scope_paging_and_no_media(world):
    job, case = world.new()
    world.request('POST', '/v1/cases', data={'job_id':job['id']})
    path = f"/v1/jobs/{job['id']}/cases?limit=1"
    result = world.request('GET', path, 'a_contractor').json()
    assert len(result['items']) == 1 and result['next_cursor']
    assert 'observation' not in result['items'][0] and 'approval_id' not in result['items'][0]
    assert result['items'][0]['max_permission'] == 0
    second = world.request('GET', path + '&after=' + result['next_cursor'], 'a_contractor').json()
    assert second['items'][0]['id'] != result['items'][0]['id']
    for key in ['a_other_contractor', 'b_manager', 'b_contractor']:
        assert world.request('GET', path, key).status_code == 404
    assert world.request('GET', path, 'a_agent').status_code == 403


def test_cursor_cannot_reference_another_job(world):
    job, _ = world.new()
    _, other = world.new()
    assert world.request('GET', f"/v1/jobs/{job['id']}/cases?after={other['id']}").status_code == 404


def test_candidate_history_scoped_and_no_authority(world):
    from backend.app.assurance_service import AssuranceService
    service = AssuranceService(world.service)
    candidate = service.create_candidate(world.tokens['a_engineer'], 'SAFE_BASELINE')
    path = f"/v1/redteam/candidates/{candidate['id']}/history"
    assert world.request('GET', path, 'a_engineer').json() == {'proposals':[], 'reviews':[], 'gates':[], 'proposals_truncated':False, 'reviews_truncated':False, 'gates_truncated':False}
    assert world.request('GET', path, 'b_engineer').status_code == 404
    assert world.request('GET', path).status_code == 403
    assert world.request('GET', path, 'a_contractor').status_code == 403
