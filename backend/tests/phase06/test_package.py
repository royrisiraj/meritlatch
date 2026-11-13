from pathlib import Path
import hashlib,json,shutil,zipfile
import pytest
from backend.tools.release_package import ROOT,STATIC,build,verify,extract
from backend.app.hosting import bundle_files


@pytest.fixture(scope='module')
def package(tmp_path_factory):
    folder=tmp_path_factory.mktemp('phase06-package')
    result=build(folder/'one.zip')
    second=build(folder/'two.zip')
    assert result['sha256']==second['sha256']
    return folder/'one.zip'


def test_package_is_deterministic_and_has_no_runtime_state(package):
    result=verify(package)
    assert result['remote_deployment']=='NOT_ATTEMPTED'
    with zipfile.ZipFile(package) as archive:
        names=archive.namelist()
        assert not any(part in name for name in names for part in ['.env','credentials','sqlite','private_media','live_inputs','local.json','node_modules','.venv','screenshots'])
        assert 'frontend/dist/index.html' in names and 'backend/app/policy.py' in names


def test_explicit_secret_canaries_outside_allowlist_are_excluded(tmp_path):
    source=tmp_path/'source'
    names=STATIC|{'frontend/dist/'+name for name in bundle_files(ROOT/'frontend/dist')}
    for name in names:
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    canary=b'PHASE06_PRIVATE_CANARY_NOT_A_REAL_CREDENTIAL'
    for name in ['.env','backend/private_media/private.bin','fixtures/live_inputs/old_marker.local.json','screenshots/private.png','backend/app/private.local.py']:
        p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canary)
    build(tmp_path/'canary.zip',source)
    with zipfile.ZipFile(tmp_path/'canary.zip') as archive:
        assert all(canary not in archive.read(name) for name in archive.namelist())


@pytest.mark.parametrize('entry',['../escape','.env','backend/local.sqlite','C:/private'])
def test_archive_additions_and_traversal_rejected(package,tmp_path,entry):
    bad=tmp_path/'bad.zip';shutil.copyfile(package,bad)
    with zipfile.ZipFile(bad,'a') as archive:archive.writestr(entry,b'no')
    with pytest.raises(ValueError):verify(bad)
    with pytest.raises(ValueError):extract(bad,tmp_path/'extracted')
    assert not (tmp_path/'extracted').exists()


def test_payload_tampering_rejected(package,tmp_path):
    bad=tmp_path/'tampered.zip'
    with zipfile.ZipFile(package) as src,zipfile.ZipFile(bad,'w') as dest:
        for entry in src.infolist():dest.writestr(entry,b'tampered' if entry.filename=='backend/app/policy.py' else src.read(entry))
    with pytest.raises(ValueError,match='DIGEST'):verify(bad)


def test_safe_extraction_and_no_overwrite(package,tmp_path):
    dest=tmp_path/'extracted'
    result=extract(package,dest)
    assert result['status']=='PACKAGE_VERIFIED'
    assert (dest/'backend/app/hosting.py').is_file()
    with pytest.raises(FileExistsError):extract(package,dest)
    with pytest.raises(FileExistsError):build(package)


def test_unbuilt_frontend_fails_closed(tmp_path):
    with pytest.raises(ValueError,match='FRONTEND_BUILD_REQUIRED'):build(tmp_path/'missing.zip',tmp_path)
