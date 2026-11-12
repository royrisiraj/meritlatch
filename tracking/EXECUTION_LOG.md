# Phase 00 execution log — 12 November 2026

Windows PowerShell, workspace `D:\project\sentinel_ladder_v2`.
Product scope: Phase 00 only. Policy observations: **SYNTHETIC**.
No live/model, E2E, concurrency, cloud or customer benchmark result is claimed.
Commands below were actually executed. Reference-file contents are not duplicated;
test/setup/smoke output is recorded below. Edits used the apply_patch tool.
No commit, push, remote connection or deployment command was executed.

## Repository verification before writing code

```powershell
git status --short --branch
```

Exit 0, actual output:

```text
## No commits yet on master
?? 00_START_HERE.md
?? AGENTS.md
?? ANTIGRAVITY_WINDOWS_HANDOFF.md
?? CODEX_FIRST_MESSAGE.md
?? DEMO_AND_PITCH_GUARDRAILS.md
?? FILE_MANIFEST.json
?? IMPLEMENTATION_DECISIONS.md
?? MASTER_BOOK_ALIGNMENT_CHANGELOG.md
?? contracts/
?? prompts/
?? reference/
?? tracking/
```

`git remote -v` exited 0 with no output (no remote configured).

## Reference and environment inspection command register

Each Get-Content command exited 0 and returned the named file or page selection.
Some initial large tool output was truncated by the renderer; bounded subsequent
reads supplied the complete text. Initial default-encoding reads displayed
mojibake; UTF-8 reads and PDF inspection resolved it.

```powershell
rg --files --hidden -g '!.git/**'
Get-Content -Raw AGENTS.md
Get-Content -Raw 00_START_HERE.md
Get-Content -Raw contracts/DOMAIN_AND_API_CONTRACTS.md
Get-Content -Raw tracking/REQUIREMENT_MATRIX.md
Get-Content -Raw tracking/STATUS_LEDGER.md
Get-Content -Raw prompts/00_BOOTSTRAP.md
Get-Content -Raw reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt
Get-Content -Encoding UTF8 -Raw prompts/00_BOOTSTRAP.md
Get-Content -Encoding UTF8 -Raw tracking/STATUS_LEDGER.md
Get-Content -Encoding UTF8 -Raw tracking/REQUIREMENT_MATRIX.md
Get-Content -Encoding UTF8 -Raw IMPLEMENTATION_DECISIONS.md
Get-Content -Encoding UTF8 reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt -TotalCount 360
$pages = (Get-Content -Encoding UTF8 -Raw reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt) -split "`f"; $pages[6..12]
$pages = (Get-Content -Encoding UTF8 -Raw reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt) -split "`f"; $pages[13..19]
$pages = (Get-Content -Encoding UTF8 -Raw reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt) -split "`f"; $pages[20..28]
$pages = (Get-Content -Encoding UTF8 -Raw reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt) -split "`f"; $pages[29..34]
Get-Content -Encoding UTF8 -Raw tracking/PHASE_GATE_REPORT_TEMPLATE.md
Get-Content -Encoding UTF8 -Raw ANTIGRAVITY_WINDOWS_HANDOFF.md
Get-Content -Encoding UTF8 reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt | Select-Object -Skip 350 -First 30
```

`rg --files` exited 0 and listed the supplied reference/instruction kit only.
All chapters and appendices were read; no prior implementation was assumed.

```powershell
py -0p
```

Exit 0:

```text
 -V:3.14 *        C:\Python314\python.exe
```

```powershell
Get-Command python,python3,uv,pdftotext -ErrorAction SilentlyContinue | Select-Object Name,Source
```

Exit 1: python.exe at `C:\Python314\python.exe`, python3.exe WindowsApps
alias found; uv and pdftotext were not found. No installation claimed.

```powershell
py -3 -m pip --version
```

Exit 0:

```text
pip 26.2.1 from C:\Python314\Lib\site-packages\pip (python 3.14)
```

```powershell
py -3 -m pip list --format=columns
```

Exit 0:

```text
Package Version
------- -------
pip     26.2.1
```

## Environment creation and initial install

```powershell
py -3 -m venv .venv
```

Exit 0, no stdout/stderr.

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi pydantic uvicorn pytest httpx pypdf
```

First attempt exit 1. PyPI socket connection was blocked by the sandbox;
five retry warnings reported WinError 10013. Final stderr:

```text
ERROR: Could not find a version that satisfies the requirement fastapi (from versions: none)
ERROR: No matching distribution found for fastapi
```

The exact same command was rerun with tool-level network approval; installation
completed with exit 0. Actual completion output:

```text
Successfully installed annotated-doc-0.0.6 annotated-types-0.8.0 anyio-4.16.0 certifi-2026.10.23 click-8.5.1 colorama-0.4.6 fastapi-0.162.5 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 opentelemetry-api-1.45.2 packaging-26.3 pluggy-1.7.0 pydantic-2.14.3 pydantic-core-2.50.4 pygments-2.21.0 pypdf-7.0.1 pytest-9.2.0 starlette-1.10.0 typing-extensions-4.16.0 typing-inspection-0.4.5 uvicorn-0.54.0

[notice] A new release of pip is available: 26.2.1 -> 26.3
[notice] To update, run: D:\project\sentinel_ladder_v2\.venv\Scripts\python.exe -m pip install --upgrade pip
```

## First executed tests and dependency inspection

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 106 items

backend\tests\test_api.py ........                                       [  7%]
backend\tests\test_config.py .................                           [ 23%]
backend\tests\test_policy.py ........................................... [ 64%]
.....................................                                    [ 99%]
backend\tests\test_security.py .                                         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 106 passed, 1 warning in 1.73s ========================
```

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
No broken requirements found.
```

```powershell
.\.venv\Scripts\python.exe -m pip freeze
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
annotated-doc==0.0.6
annotated-types==0.8.0
anyio==4.16.0
certifi==2026.10.23
click==8.5.1
colorama==0.4.6
fastapi==0.162.5
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
opentelemetry-api==1.45.2
packaging==26.3
pluggy==1.7.0
pydantic==2.14.3
pydantic_core==2.50.4
Pygments==2.21.0
pypdf==7.0.1
pytest==9.2.0
starlette==1.10.0
typing-inspection==0.4.5
typing_extensions==4.16.0
uvicorn==0.54.0
```

The first run passed 106 tests. Added nonblank trusted-context validation and
tests for unsupported actions/configurable units, then reran all tests.

## Final test suite

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 113 items

backend\tests\test_api.py ........                                       [  7%]
backend\tests\test_config.py ...................                         [ 23%]
backend\tests\test_policy.py ........................................... [ 61%]
..........................................                               [ 99%]
backend\tests\test_security.py .                                         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 113 passed, 1 warning in 0.70s ========================
```

Counts from test source and executed collection: policy 85; config 19; API 8;
isolated-process policy 1. **113 passed, 0 failed, 0 skipped.** No coverage measured.
The single Starlette TestClient warning was not suppressed.

## Locked installation verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
Requirement already satisfied: annotated-doc==0.0.6 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 3)) (0.0.6)
Requirement already satisfied: annotated-types==0.8.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 4)) (0.8.0)
Requirement already satisfied: anyio==4.16.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 5)) (4.16.0)
Requirement already satisfied: certifi==2026.10.23 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 6)) (2026.10.23)
Requirement already satisfied: click==8.5.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 7)) (8.5.1)
Requirement already satisfied: colorama==0.4.6 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 8)) (0.4.6)
Requirement already satisfied: fastapi==0.162.5 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 9)) (0.162.5)
Requirement already satisfied: h11==0.16.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 10)) (0.16.0)
Requirement already satisfied: httpcore==1.0.9 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 11)) (1.0.9)
Requirement already satisfied: httpx==0.28.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 12)) (0.28.1)
Requirement already satisfied: idna==3.20 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 13)) (3.20)
Requirement already satisfied: iniconfig==2.3.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 14)) (2.3.1)
Requirement already satisfied: opentelemetry-api==1.45.2 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 15)) (1.45.2)
Requirement already satisfied: packaging==26.3 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 16)) (26.3)
Requirement already satisfied: pluggy==1.7.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 17)) (1.7.0)
Requirement already satisfied: pydantic==2.14.3 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 18)) (2.14.3)
Requirement already satisfied: pydantic_core==2.50.4 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 19)) (2.50.4)
Requirement already satisfied: Pygments==2.21.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 20)) (2.21.0)
Requirement already satisfied: pypdf==7.0.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 21)) (7.0.1)
Requirement already satisfied: pytest==9.2.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 22)) (9.2.0)
Requirement already satisfied: starlette==1.10.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 23)) (1.10.0)
Requirement already satisfied: typing-inspection==0.4.5 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 24)) (0.4.5)
Requirement already satisfied: typing_extensions==4.16.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 25)) (4.16.0)
Requirement already satisfied: uvicorn==0.54.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 26)) (0.54.0)

[notice] A new release of pip is available: 26.2.1 -> 26.3
[notice] To update, run: D:\project\sentinel_ladder_v2\.venv\Scripts\python.exe -m pip install --upgrade pip
```

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from importlib.metadata import distributions; print('\n'.join(sorted(d.metadata['Name']+': '+str(d.metadata.get('Requires-Python')) for d in distributions())))"
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
Pygments: >=3.9
annotated-doc: >=3.10
annotated-types: >=3.10
anyio: >=3.10
certifi: >=3.7
click: >=3.10
colorama: !=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*,!=3.5.*,!=3.6.*,>=2.7
fastapi: >=3.10
h11: >=3.8
httpcore: >=3.8
httpx: >=3.8
idna: >=3.9
iniconfig: >=3.10
opentelemetry-api: >=3.10
packaging: >=3.9
pip: >=3.10
pluggy: >=3.10
pydantic: >=3.10
pydantic_core: >=3.10
pypdf: >=3.10
pytest: >=3.10
starlette: >=3.11
typing-inspection: >=3.10
typing_extensions: >=3.9
uvicorn: >=3.10
```

Package metadata permits Python 3.11/3.12. Actual 3.11/3.12 tests and remote CI
were **NOT RUN**: those interpreters are absent and no push was authorized.
Every available Phase 00 test ran on Python 3.14.7.

## Original PDF cross-check

```powershell
.\.venv\Scripts\python.exe -c "from pypdf import PdfReader; from pathlib import Path; import re; r=PdfReader('reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf'); pages=[p.extract_text() for p in r.pages]; ref=Path('reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt').read_text(encoding='utf-8'); norm=lambda s: re.sub(r'\s+', '', s); a=norm(''.join(pages)); b=norm(ref); print('PDF pages:',len(pages)); print('All page text matches supplied reference ignoring whitespace:', a == b); print('\n'.join('Page '+str(i+1)+': '+str(len(p))+' extracted characters' for i,p in enumerate(pages)))"
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
PDF pages: 35
All page text matches supplied reference ignoring whitespace: False
Page 1: 888 extracted characters
Page 2: 2528 extracted characters
Page 3: 1518 extracted characters
Page 4: 1642 extracted characters
Page 5: 2104 extracted characters
Page 6: 2409 extracted characters
Page 7: 2344 extracted characters
Page 8: 1802 extracted characters
Page 9: 2524 extracted characters
Page 10: 824 extracted characters
Page 11: 2198 extracted characters
Page 12: 2228 extracted characters
Page 13: 1712 extracted characters
Page 14: 1960 extracted characters
Page 15: 2035 extracted characters
Page 16: 1813 extracted characters
Page 17: 1629 extracted characters
Page 18: 2537 extracted characters
Page 19: 2406 extracted characters
Page 20: 2018 extracted characters
Page 21: 1198 extracted characters
Page 22: 2197 extracted characters
Page 23: 1931 extracted characters
Page 24: 1449 extracted characters
Page 25: 1758 extracted characters
Page 26: 2388 extracted characters
Page 27: 2008 extracted characters
Page 28: 2386 extracted characters
Page 29: 2443 extracted characters
Page 30: 1118 extracted characters
Page 31: 1877 extracted characters
Page 32: 1914 extracted characters
Page 33: 2518 extracted characters
Page 34: 1668 extracted characters
Page 35: 1804 extracted characters
```

The equality check was false. Direct PDF text inspection and token diffs showed
headers/footers and table cells in different reading orders. No Phase 00 semantic
conflict was found in the inspected relevant sections. The source reference was
not modified.

These commands initially failed with exit 1 because Windows cp1252 could not
encode the PDF bullet character / arrow. They were rerun with `-X utf8`:

```powershell
.\.venv\Scripts\python.exe -c "from pypdf import PdfReader; r=PdfReader('reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf'); print('\n'.join('--- PDF PAGE '+str(i+1)+' ---\n'+r.pages[i].extract_text() for i in [6,7,17,25,27]))"
.\.venv\Scripts\python.exe -c "from pypdf import PdfReader; from pathlib import Path; import difflib; r=PdfReader('reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf'); ref=Path('reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt').read_text(encoding='utf-8').split('\f'); norm=lambda s: s.replace(chr(0xf0b7),'•').split(); print('\n'.join('Page '+str(i+1)+': '+str(list(difflib.unified_diff(norm(ref[i]), norm(p.extract_text()), n=1))[:30]) for i,p in enumerate(r.pages)))"
```

Actual final errors were respectively:

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\uf0b7' in position 3398: character maps to <undefined>
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 3654: character maps to <undefined>
```

Corrected commands, both exit 0:

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from pypdf import PdfReader; r=PdfReader('reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf'); print('\n'.join('--- PDF PAGE '+str(i+1)+' ---\n'+r.pages[i].extract_text() for i in [6,7,17,25,27]))"
.\.venv\Scripts\python.exe -X utf8 -c "from pypdf import PdfReader; from pathlib import Path; import difflib; r=PdfReader('reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf'); ref=Path('reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt').read_text(encoding='utf-8').split('\f'); norm=lambda s: s.replace(chr(0xf0b7),'•').split(); print('\n'.join('Page '+str(i+1)+': '+str(list(difflib.unified_diff(norm(ref[i]), norm(p.extract_text()), n=1))[:30]) for i,p in enumerate(r.pages)))"
```

The first returned the original PDF pages 7,8,18,26,28; the second returned
per-page reading-order diffs for all 35 pages (diagnostic, not a passing test).

## Running HTTP server smoke check

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Exit code: running (session 43657). Actual output (terminal control sequences removed):

```text
INFO:     Started server process [17864]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz | Select-Object StatusCode,Content
```

Exit code: 0. Actual output (terminal control sequences removed):

```text

StatusCode Content        
---------- -------        
       200 {"status":"ok"}
```

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/docs | Select-Object StatusCode
```

Exit code: 0. Actual output (terminal control sequences removed):

```text

StatusCode
----------
       200
```

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/openapi.json).paths.PSObject.Properties.Name
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
/healthz
```

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
No broken requirements found.
```

These four commands were each executed twice: the first tools completed, but a
JavaScript output-formatting error (`ReferenceError: cmd is not defined`) discarded
their return values. The second results above were captured correctly; both
HTTP request batches appeared as 200 in Uvicorn output. This was a tool
orchestration error, not an application test failure.

Ctrl+C was sent twice to exec session 43657; the tool did not terminate Uvicorn.
Its startup log identified the owned server as PID 17864. Process identity was
then verified before stopping only that temporary smoke process:

```powershell
Get-CimInstance Win32_Process -Filter 'ProcessId = 17864' | Select-Object ProcessId,ExecutablePath,CommandLine
```

Exit code: 1. Actual output (terminal control sequences removed):

```text
Get-CimInstance : Access denied 
At line:2 char:1
+ Get-CimInstance Win32_Process -Filter 'ProcessId = 17864' | Select-Ob ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (:) [Get-CimInstance], CimException
    + FullyQualifiedErrorId : HRESULT 0x80041003,Microsoft.Management.Infrastructure.CimCmdlets.GetCimInstanceCommand
```

The same inspection was rerun with tool-level approval after sandbox denial:

```powershell
Get-CimInstance Win32_Process -Filter 'ProcessId = 17864' | Select-Object ProcessId,ExecutablePath,CommandLine
```

Exit code: 0. Actual output (terminal control sequences removed):

```text

ProcessId ExecutablePath          CommandLine                                                                          
--------- --------------          -----------                                                                          
    17864 C:\Python314\python.exe "D:\project\sentinel_ladder_v2\.venv\Scripts\python.exe" -m uvicorn backend.app.ma...
```

```powershell
Stop-Process -Id 17864 -ErrorAction Stop
```

Exit code: 0. Actual output (terminal control sequences removed):

```text

```

Stop-Process exited 0 with no output. The owned Uvicorn exec session then exited
with code 1 due to termination; this was cleanup, not startup/health failure.
The server is not left running. No customer service was stopped.

## Ignore rules

```powershell
git check-ignore .venv/Scripts/python.exe .env backend/private_media/example.png backend/local.sqlite backend/__pycache__/models.pyc .pytest_cache/README.md
```

Exit code: 0. Actual output (terminal control sequences removed):

```text
.venv/Scripts/python.exe
.env
backend/private_media/example.png
backend/local.sqlite
backend/__pycache__/models.pyc
.pytest_cache/README.md
```

## Final Git status

Final status is recorded below after all report files have been created.
All original kit files were already untracked, and remain so. No staging or commit
occurred; modified original tracking files also appear untracked for that reason.

```powershell
git status --short --branch --untracked-files=all
```

Exit 0:

```text
## No commits yet on master
?? .env.example
?? .github/workflows/tests.yml
?? .gitignore
?? 00_START_HERE.md
?? AGENTS.md
?? ANTIGRAVITY_WINDOWS_HANDOFF.md
?? CODEX_FIRST_MESSAGE.md
?? DEMO_AND_PITCH_GUARDRAILS.md
?? FILE_MANIFEST.json
?? IMPLEMENTATION_DECISIONS.md
?? MASTER_BOOK_ALIGNMENT_CHANGELOG.md
?? README.md
?? backend/__init__.py
?? backend/app/__init__.py
?? backend/app/config.py
?? backend/app/main.py
?? backend/app/models.py
?? backend/app/policy.py
?? backend/requirements.txt
?? backend/tests/conftest.py
?? backend/tests/test_api.py
?? backend/tests/test_config.py
?? backend/tests/test_policy.py
?? backend/tests/test_security.py
?? contracts/DOMAIN_AND_API_CONTRACTS.md
?? docs/architecture.md
?? docs/decisions.md
?? docs/security.md
?? fixtures/synthetic_cases.json
?? frontend/README.md
?? policies/maintenance_v1.json
?? prompts/00_BOOTSTRAP.md
?? prompts/01_POLICY_AUTH_CASES.md
?? prompts/02_SAFE_MEDIA_AND_GEMINI.md
?? prompts/03_COMPLETE_CASE_WORKFLOW.md
?? prompts/04_REDTEAM_ALERTS.md
?? prompts/05_THREE_FUNCTIONAL_PORTALS.md
?? prompts/06_CLOUD_AND_THREE_MINUTE_DEMO.md
?? prompts/07_UI_POLISH_ONLY_AFTER_GATES.md
?? pyproject.toml
?? reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt
?? reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf
?? tracking/EXECUTION_LOG.md
?? tracking/PHASE_00_REPORT.md
?? tracking/PHASE_GATE_REPORT_TEMPLATE.md
?? tracking/REQUIREMENT_MATRIX.md
?? tracking/SECURITY_TEST_CATALOG.md
?? tracking/STATUS_LEDGER.md
```

```powershell
git status
```

Exit 0:

```text
On branch master

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.env.example
	.github/
	.gitignore
	00_START_HERE.md
	AGENTS.md
	ANTIGRAVITY_WINDOWS_HANDOFF.md
	CODEX_FIRST_MESSAGE.md
	DEMO_AND_PITCH_GUARDRAILS.md
	FILE_MANIFEST.json
	IMPLEMENTATION_DECISIONS.md
	MASTER_BOOK_ALIGNMENT_CHANGELOG.md
	README.md
	backend/
	contracts/
	docs/
	fixtures/
	frontend/
	policies/
	prompts/
	pyproject.toml
	reference/
	tracking/

nothing added to commit but untracked files present (use "git add" to track)
```


# Phase 01 execution — 12 November 2026

Windows PowerShell; workspace `D:\project\sentinel_ladder_v2`. Phase 00 was accepted by the user. No commit, push, remote configuration, cloud resource, live AI call, real payment or Phase 02 work occurred.

Required pre-change reads (all exited 0 and returned the named contents):

```powershell
Get-Content -Encoding UTF8 -Raw AGENTS.md
Get-Content -Encoding UTF8 -Raw prompts/01_POLICY_AUTH_CASES.md
Get-Content -Encoding UTF8 -Raw contracts/DOMAIN_AND_API_CONTRACTS.md
Get-Content -Encoding UTF8 -Raw tracking/PHASE_00_REPORT.md
Get-Content -Encoding UTF8 -Raw tracking/REQUIREMENT_MATRIX.md
Get-Content -Encoding UTF8 -Raw tracking/STATUS_LEDGER.md
Get-Content -Encoding UTF8 -Raw docs/architecture.md
Get-Content -Encoding UTF8 -Raw docs/security.md
```

Initial discovery commands (exit 0; Git showed no commits and only untracked files, remote output empty):

```powershell
git status --short --branch; git remote -v
rg --files backend policies fixtures .github; Get-Content -Raw backend/requirements.txt
```

The authoritative PDF was parsed directly and its relevant original pages read below. The complete book had also been read during Phase 00. Original tests were hashed before changes and later verified byte-for-byte unchanged. File edits used apply_patch; a sequential Python edit moved clock samples into transactions. A documentation patch initially failed because delete/add operations targeted the same files in one patch; no partial changes were applied. Documentation replacement then succeeded sequentially. No test was weakened.

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from pypdf import PdfReader; r=PdfReader('reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf'); print('PDF pages:',len(r.pages)); print('\n'.join('PDF PAGE '+str(i+1)+'\n'+r.pages[i].extract_text() for i in [6,7,9,10,12,13,16,17,18,19,27]))"
```

Exit code 0.

Output: `PDF pages: 35`, followed by extracted original pages 7,8,10,11,13,14,17,18,19,20,28. Source text is not duplicated here; the actual tool output was inspected. No specification conflict affecting this phase was found.

```powershell
Get-Content -Raw backend/app/models.py
```

Exit code 0.

Returned the named source file contents (not duplicated here).

```powershell
Get-Content -Raw backend/app/policy.py
```

Exit code 0.

Returned the named source file contents (not duplicated here).

```powershell
Get-Content -Raw backend/tests/test_api.py; Get-Content -Raw backend/app/main.py; Get-Content -Raw backend/tests/conftest.py
```

Exit code 0.

Returned the named source file contents (not duplicated here).

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from pathlib import Path; import hashlib,json; print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('backend/tests').glob('*.py')},indent=2))"
```

Exit code 0.

```text
{
  "backend\\tests\\conftest.py": "12f92fcb36e9703cb06eb18fa4b7f7e13282a2a53752220d236b0de4ea7fc37f",
  "backend\\tests\\test_api.py": "2e5f97e0e0616c4d1b1b8871c7176f86a96656c572f515dc4ab0a7d4fceb9024",
  "backend\\tests\\test_config.py": "cd2041071b7079c6bffe61e8381249399c88902c318a529c3c6f90cc1c492898",
  "backend\\tests\\test_policy.py": "10796d0cdf2acf72c043bef3547fd45215f36b5364571eb1bbf1ae8cf818b57c",
  "backend\\tests\\test_security.py": "ad99dcad0f0c23452e39bd4f43d5ac29f6882393908e3732f3de1b774426d55c"
}
```

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Exit code 0.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 113 items

backend\tests\test_api.py ........                                       [  7%]
backend\tests\test_config.py ...................                         [ 23%]
backend\tests\test_policy.py ........................................... [ 61%]
..........................................                               [ 99%]
backend\tests\test_security.py .                                         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 113 passed, 1 warning in 0.69s ========================
```

```powershell
.\.venv\Scripts\python.exe -m pip install SQLAlchemy
```

Exit code 1.

```text
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions")': /simple/sqlalchemy/
WARNING: Retrying (Retry(total=3, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions")': /simple/sqlalchemy/
WARNING: Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions")': /simple/sqlalchemy/
WARNING: Retrying (Retry(total=1, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions")': /simple/sqlalchemy/
WARNING: Retrying (Retry(total=0, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions")': /simple/sqlalchemy/
ERROR: Could not find a version that satisfies the requirement SQLAlchemy (from versions: none)

[notice] A new release of pip is available: 26.2.1 -> 26.3
[notice] To update, run: D:\project\sentinel_ladder_v2\.venv\Scripts\python.exe -m pip install --upgrade pip
ERROR: No matching distribution found for SQLAlchemy
```

```powershell
.\.venv\Scripts\python.exe -m pip install SQLAlchemy
```

Tool-level network retry approved. Exit code 0.

```text
Collecting SQLAlchemy
  Downloading sqlalchemy-2.1.8-cp314-cp314-win_amd64.whl.metadata (9.9 kB)
Requirement already satisfied: typing-extensions>=4.6.0 in .\.venv\Lib\site-packages (from SQLAlchemy) (4.16.0)
Downloading sqlalchemy-2.1.8-cp314-cp314-win_amd64.whl (2.4 MB)
   ---------------------------------------- 2.4/2.4 MB 31.2 MB/s  0:00:00
Installing collected packages: SQLAlchemy
Successfully installed SQLAlchemy-2.1.8

[notice] A new release of pip is available: 26.2.1 -> 26.3
[notice] To update, run: D:\project\sentinel_ladder_v2\.venv\Scripts\python.exe -m pip install --upgrade pip
```

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from pathlib import Path; from tempfile import TemporaryDirectory; from fastapi.testclient import TestClient; from backend.testing import create_test_app; from backend.app.provisioning import provision_user; from backend.app.api_models import Role; import secrets; t=TemporaryDirectory(); app=create_test_app(Path(t.name)/'test.sqlite'); password=secrets.token_urlsafe(20); user=provision_user(app.state.service.repository,'test-a','manager',Role.MANAGER,password); client=TestClient(app); r=client.post('/v1/auth/login',json={'tenant_id':'test-a','username':'manager','password':password}); print('Login status:',r.status_code); print('Schema operations:',len(client.get('/openapi.json').json()['paths'])); app.state.service.repository.close(); t.cleanup()"
```

Exit code 0.

```text
D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
Login status: 200
Schema operations: 16
```

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/phase01 -x
```

Command still running at this return (session 64229); continuation below.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
plugins: anyio-4.16.0
collected 108 items

backend\tests\phase01\test_challenges.py .............                   [ 12%]
backend\tests\phase01\test_identity.py ..............................    [ 39%]
backend\tests\phase01\test_scope.py ..............
```

```powershell
[poll pytest session 64229]
```

Exit code 0.

```text
......                 [ 58%]
backend\tests\phase01\test_workflow.py ................................. [ 88%]
............                                                             [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 108 passed, 1 warning in 15.05s =======================
```

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Command still running at this return (session 1631); continuation below.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 257 items

backend\tests\phase01\test_challenges.py .............                   [  5%]
backend\tests\phase01\test_http_boundary.py ..........                   [  8%]
backend\tests\phase01\test_identity.py ..............................    [ 20%]
backend\tests\phase01\test_persistence.py .
```

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Exit code 0.

```text
No broken requirements found.
```

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase01
```

Exit code 0.

```text
HTTP health/docs: 200 / 200
Authenticated four independent roles; anonymous jobs request: 401
Missing evidence: L0; prepare_invoice DENY
Internal SYNTHETIC observation: L2; unapproved completion DENY
Contractor self-approval / engineer approval: 403 / 403
Manager review: L3; repeated simulated completion: one receipt
Changed invoice: approval invalidated; completion DENY
Redacted audit verified; logout revocation: 401
PASS: actual localhost HTTP workflow, SYNTHETIC only; no Gemini, money movement or cloud
```

```powershell
[poll pytest session 1631]
```

Exit code 0.

```text
.................             [ 27%]
backend\tests\phase01\test_scope.py ....................                 [ 35%]
backend\tests\phase01\test_transactions.py ........                      [ 38%]
backend\tests\phase01\test_workflow.py ................................. [ 51%]
............                                                             [ 56%]
backend\tests\test_api.py ........                                       [ 59%]
backend\tests\test_config.py ...................                         [ 66%]
backend\tests\test_policy.py ........................................... [ 83%]
..........................................                               [ 99%]
backend\tests\test_security.py .                                         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 257 passed, 1 warning in 20.75s =======================
```

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from pathlib import Path; p=Path('backend/app/case_service.py'); s=p.read_text(encoding='utf-8'); old='        now = self._now()\n        with self.repository.transaction() as tx:\n'; new='        with self.repository.transaction() as tx:\n            now = self._now()\n'; n=s.count(old); s=s.replace(old,new); s=s.replace('        now = self._now()\n        bucket = digest([tenant_id, username])','        bucket = digest([tenant_id, username])'); s=s.replace('        result = None\n        with self.repository.transaction() as tx:\n            limit', '        result = None\n        with self.repository.transaction() as tx:\n            now = self._now()\n            limit'); p.write_text(s,encoding='utf-8'); print('Moved',n,'authorization clock samples inside locked transactions; login clock moved as well.')"
```

Exit code 0.

```text
Moved 10 authorization clock samples inside locked transactions; login clock moved as well.
```

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Command still running at this return (session 92143); continuation below.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 266 items

backend\tests\phase01\test_challenges.py .............                   [  4%]
backend\tests\phase01\test_http_boundary.py ..........                   [  8%]
backend\tests\phase01\test_identity.py .........................
```

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Exit code 0.

```text
Requirement already satisfied: annotated-doc==0.0.6 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 3)) (0.0.6)
Requirement already satisfied: annotated-types==0.8.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 4)) (0.8.0)
Requirement already satisfied: anyio==4.16.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 5)) (4.16.0)
Requirement already satisfied: certifi==2026.10.23 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 6)) (2026.10.23)
Requirement already satisfied: click==8.5.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 7)) (8.5.1)
Requirement already satisfied: colorama==0.4.6 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 8)) (0.4.6)
Requirement already satisfied: fastapi==0.162.5 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 9)) (0.162.5)
Requirement already satisfied: h11==0.16.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 10)) (0.16.0)
Requirement already satisfied: httpcore==1.0.9 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 11)) (1.0.9)
Requirement already satisfied: httpx==0.28.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 12)) (0.28.1)
Requirement already satisfied: idna==3.20 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 13)) (3.20)
Requirement already satisfied: iniconfig==2.3.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 14)) (2.3.1)
Requirement already satisfied: opentelemetry-api==1.45.2 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 15)) (1.45.2)
Requirement already satisfied: packaging==26.3 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 16)) (26.3)
Requirement already satisfied: pluggy==1.7.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 17)) (1.7.0)
Requirement already satisfied: pydantic==2.14.3 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 18)) (2.14.3)
Requirement already satisfied: pydantic_core==2.50.4 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 19)) (2.50.4)
Requirement already satisfied: Pygments==2.21.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 20)) (2.21.0)
Requirement already satisfied: pypdf==7.0.1 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 21)) (7.0.1)
Requirement already satisfied: pytest==9.2.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 22)) (9.2.0)
Requirement already satisfied: starlette==1.10.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 23)) (1.10.0)
Requirement already satisfied: typing-inspection==0.4.5 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 24)) (0.4.5)
Requirement already satisfied: typing_extensions==4.16.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 25)) (4.16.0)
Requirement already satisfied: uvicorn==0.54.0 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 26)) (0.54.0)
Requirement already satisfied: SQLAlchemy==2.1.8 in .\.venv\Lib\site-packages (from -r backend/requirements.txt (line 27)) (2.1.8)

[notice] A new release of pip is available: 26.2.1 -> 26.3
[notice] To update, run: D:\project\sentinel_ladder_v2\.venv\Scripts\python.exe -m pip install --upgrade pip
```

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from pathlib import Path; import hashlib,json; expected=json.loads(Path('tracking/PHASE_01_BASELINE_TEST_HASHES.json').read_text()); actual={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in expected}; assert actual == expected; print('All 5 original Phase 00 test/conftest files are byte-for-byte unchanged.')"
```

Exit code 0.

```text
All 5 original Phase 00 test/conftest files are byte-for-byte unchanged.
```

```powershell
[poll pytest session 92143]
```

Exit code 1.

```text
.....    [ 19%]
backend\tests\phase01\test_persistence.py ..................             [ 26%]
backend\tests\phase01\test_scope.py .........................            [ 36%]
backend\tests\phase01\test_transactions.py ........F                     [ 39%]
backend\tests\phase01\test_workflow.py ................................. [ 51%]
...............                                                          [ 57%]
backend\tests\test_api.py ........                                       [ 60%]
backend\tests\test_config.py ...................                         [ 67%]
backend\tests\test_policy.py ........................................... [ 83%]
..........................................                               [ 99%]
backend\tests\test_security.py .                                         [100%]

================================== FAILURES ===================================
_ test_authorization_samples_server_clock_after_waiting_for_transaction_lock __

world = <conftest.World object at 0x00000192CC891D50>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000192CC7DFD10>

    def test_authorization_samples_server_clock_after_waiting_for_transaction_lock(world, monkeypatch):
        job, case, ch = world.ready()
        approved = world.approve(case).json()
        original = world.service.repository.transaction
    
        @contextmanager
        def lock_wait():
            with original() as tx:
                world.clock.advance(300)  # Simulate expiry while waiting for the DB lock.
                yield tx
    
        monkeypatch.setattr(world.service.repository, "transaction", lock_wait)
        status, result = world.service.action(world.tokens["a_agent"], case["id"], approved["version"], Action.COMPLETE_SIMULATED_ACTION, True)
>       assert status == 409
E       assert 200 == 409

backend\tests\phase01\test_transactions.py:154: AssertionError
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED backend/tests/phase01/test_transactions.py::test_authorization_samples_server_clock_after_waiting_for_transaction_lock
================== 1 failed, 265 passed, 1 warning in 22.90s ==================
```

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Command still running at this return (session 39484); continuation below.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 266 items

backend\tests\phase01\test_challenges.py .............                   [  4%]
backend\tests\phase01\test_http_boundary.py ..........                   [  8%]
backend\tests\phase01\test_identity.py ..............................    [ 19%]
backend\tests\phase01\test_persistence.py
```

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase01
```

Exit code 0.

```text
HTTP health/docs: 200 / 200
Authenticated four independent roles; anonymous jobs request: 401
Missing evidence: L0; prepare_invoice DENY
Internal SYNTHETIC observation: L2; unapproved completion DENY
Contractor self-approval / engineer approval: 403 / 403
Manager review: L3; repeated simulated completion: one receipt
Changed invoice: approval invalidated; completion DENY
Redacted audit verified; logout revocation: 401
PASS: actual localhost HTTP workflow, SYNTHETIC only; no Gemini, money movement or cloud
```

```powershell
.\.venv\Scripts\python.exe -m backend.tools.manage --help
```

Exit code 0.

```text
usage: python.exe -m backend.tools.manage [-h]
                                          {create-user,init-demo,list-users,register-policy} ...

Offline local account/policy provisioning; no credentials on command line.

positional arguments:
  {create-user,init-demo,list-users,register-policy}
    init-demo           Prompt for independent passwords for four roles in
                        each of two fictional tenants
    register-policy     Offline reviewed version registration; never
                        automatically activates

options:
  -h, --help            show this help message and exit
```

```powershell
[poll pytest session 39484]
```

Exit code 0.

```text
..................             [ 26%]
backend\tests\phase01\test_scope.py .........................            [ 36%]
backend\tests\phase01\test_transactions.py .........                     [ 39%]
backend\tests\phase01\test_workflow.py ................................. [ 51%]
...............                                                          [ 57%]
backend\tests\test_api.py ........                                       [ 60%]
backend\tests\test_config.py ...................                         [ 67%]
backend\tests\test_policy.py ........................................... [ 83%]
..........................................                               [ 99%]
backend\tests\test_security.py .                                         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 266 passed, 1 warning in 22.59s =======================
```

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Exit code 0.

```text
No broken requirements found.
```

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Command still running at this return (session 71851); continuation below.

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\project\sentinel_ladder_v2
configfile: pyproject.toml
testpaths: backend/tests
plugins: anyio-4.16.0
collected 266 items

backend\tests\phase01\test_challenges.py .............                   [  4%]
backend\tests\phase01\test_http_boundary.py ..........                   [  8%]
backend\tests\phase01\test_identity.py ............................
```

```powershell
.\.venv\Scripts\python.exe -m backend.tools.smoke_phase01
```

Exit code 0.

```text
HTTP health/docs: 200 / 200
Authenticated four independent roles; anonymous jobs request: 401
Missing evidence: L0; prepare_invoice DENY
Internal SYNTHETIC observation: L2; unapproved completion DENY
Contractor self-approval / engineer approval: 403 / 403
Manager review: L3; repeated simulated completion: one receipt
Changed invoice: approval invalidated; completion DENY
Redacted audit verified; logout revocation: 401
PASS: actual localhost HTTP workflow, SYNTHETIC only; no Gemini, money movement or cloud
```

```powershell
[poll pytest session 71851]
```

Command still running at this return (session 71851); continuation below.

```text
..    [ 19%]
backend\tests\phase01\test_persistence.py ..................             [ 26%]
backend\tests\phase01\test_scope.py .........................            [ 36%]
backend\tests\phase01\test_transactions.py .........                     [ 39%]
backend\tests\phase01\test_workflow.py ................................. [ 51%]
...............                                                          [ 57%]
backend\tests\test_api.py ........                                       [ 60%]
backend\tests\test_config.py ...................                         [ 67%]
backend\tests\test_policy.py ........................................... [ 83%]
..........................................                               [ 99%]
backend\tests\test_security.py .                                         [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\project\sentinel_ladder_v2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 266 passed, 1 warning in 22.24s =======================
```

```powershell
[final poll pytest session 71851]
```

Exit code 0.

```text

```

```powershell
git status --short --branch --untracked-files=all
```

Exit code 0.

```text
## No commits yet on master
?? .env.example
?? .github/workflows/tests.yml
?? .gitignore
?? 00_START_HERE.md
?? AGENTS.md
?? ANTIGRAVITY_WINDOWS_HANDOFF.md
?? CODEX_FIRST_MESSAGE.md
?? DEMO_AND_PITCH_GUARDRAILS.md
?? FILE_MANIFEST.json
?? IMPLEMENTATION_DECISIONS.md
?? MASTER_BOOK_ALIGNMENT_CHANGELOG.md
?? README.md
?? backend/__init__.py
?? backend/app/__init__.py
?? backend/app/api.py
?? backend/app/api_models.py
?? backend/app/auth.py
?? backend/app/case_service.py
?? backend/app/config.py
?? backend/app/errors.py
?? backend/app/http_limits.py
?? backend/app/main.py
?? backend/app/models.py
?? backend/app/policy.py
?? backend/app/provisioning.py
?? backend/app/repository.py
?? backend/app/settings.py
?? backend/requirements.txt
?? backend/testing.py
?? backend/tests/conftest.py
?? backend/tests/phase01/conftest.py
?? backend/tests/phase01/test_challenges.py
?? backend/tests/phase01/test_http_boundary.py
?? backend/tests/phase01/test_identity.py
?? backend/tests/phase01/test_persistence.py
?? backend/tests/phase01/test_scope.py
?? backend/tests/phase01/test_transactions.py
?? backend/tests/phase01/test_workflow.py
?? backend/tests/test_api.py
?? backend/tests/test_config.py
?? backend/tests/test_policy.py
?? backend/tests/test_security.py
?? backend/tools/__init__.py
?? backend/tools/manage.py
?? backend/tools/smoke_phase01.py
?? contracts/DOMAIN_AND_API_CONTRACTS.md
?? docs/api_phase01.md
?? docs/architecture.md
?? docs/decisions.md
?? docs/security.md
?? fixtures/synthetic_cases.json
?? frontend/README.md
?? policies/maintenance_v1.json
?? prompts/00_BOOTSTRAP.md
?? prompts/01_POLICY_AUTH_CASES.md
?? prompts/02_SAFE_MEDIA_AND_GEMINI.md
?? prompts/03_COMPLETE_CASE_WORKFLOW.md
?? prompts/04_REDTEAM_ALERTS.md
?? prompts/05_THREE_FUNCTIONAL_PORTALS.md
?? prompts/06_CLOUD_AND_THREE_MINUTE_DEMO.md
?? prompts/07_UI_POLISH_ONLY_AFTER_GATES.md
?? pyproject.toml
?? reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt
?? reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf
?? tracking/EXECUTION_LOG.md
?? tracking/PHASE_00_REPORT.md
?? tracking/PHASE_01_BASELINE_TEST_HASHES.json
?? tracking/PHASE_GATE_REPORT_TEMPLATE.md
?? tracking/REQUIREMENT_MATRIX.md
?? tracking/SECURITY_TEST_CATALOG.md
?? tracking/STATUS_LEDGER.md
```

Additional source-inspection command (exit 0):

```powershell
rg -n 'def |now =|transaction\(' backend/app/case_service.py
```

It identified the remaining pre-lock clock read in action execution after the new regression failed. That read was moved inside the transaction and the full suite rerun. Development results are retained above: baseline 113 passed; first new slice 108 passed; first combined 257 passed; expanded regression run 265 passed/1 failed; corrected full runs 266 passed. The final full run reported **266 passed, 1 warning in 22.24s**, followed by process exit 0. Warning: unchanged Starlette HTTPX TestClient deprecation. No coverage measured. No test is blocked; Python 3.11/3.12 and remote CI were NOT RUN.

The actual localhost smoke passed after the final code change. All observations were **SYNTHETIC**, injected internally through the explicit test factory; API interactions used real HTTP and ephemeral generated credentials. No secrets or raw observations were printed. Smoke cleaned up its owned server and temporary database. Normal operation has no injection endpoint and refuses test evidence promotion.

The Phase 01 report, endpoint map, architecture/security/decisions, ledger and requirement matrix were updated. Final Git verification is appended after those artifacts are complete.


## Phase 01 final Git verification

```powershell
git status --short --branch --untracked-files=all
```

Exit 0:

```text
## No commits yet on master
?? .env.example
?? .github/workflows/tests.yml
?? .gitignore
?? 00_START_HERE.md
?? AGENTS.md
?? ANTIGRAVITY_WINDOWS_HANDOFF.md
?? CODEX_FIRST_MESSAGE.md
?? DEMO_AND_PITCH_GUARDRAILS.md
?? FILE_MANIFEST.json
?? IMPLEMENTATION_DECISIONS.md
?? MASTER_BOOK_ALIGNMENT_CHANGELOG.md
?? README.md
?? backend/__init__.py
?? backend/app/__init__.py
?? backend/app/api.py
?? backend/app/api_models.py
?? backend/app/auth.py
?? backend/app/case_service.py
?? backend/app/config.py
?? backend/app/errors.py
?? backend/app/http_limits.py
?? backend/app/main.py
?? backend/app/models.py
?? backend/app/policy.py
?? backend/app/provisioning.py
?? backend/app/repository.py
?? backend/app/settings.py
?? backend/requirements.txt
?? backend/testing.py
?? backend/tests/conftest.py
?? backend/tests/phase01/conftest.py
?? backend/tests/phase01/test_challenges.py
?? backend/tests/phase01/test_http_boundary.py
?? backend/tests/phase01/test_identity.py
?? backend/tests/phase01/test_persistence.py
?? backend/tests/phase01/test_scope.py
?? backend/tests/phase01/test_transactions.py
?? backend/tests/phase01/test_workflow.py
?? backend/tests/test_api.py
?? backend/tests/test_config.py
?? backend/tests/test_policy.py
?? backend/tests/test_security.py
?? backend/tools/__init__.py
?? backend/tools/manage.py
?? backend/tools/smoke_phase01.py
?? contracts/DOMAIN_AND_API_CONTRACTS.md
?? docs/api_phase01.md
?? docs/architecture.md
?? docs/decisions.md
?? docs/security.md
?? fixtures/synthetic_cases.json
?? frontend/README.md
?? policies/maintenance_v1.json
?? prompts/00_BOOTSTRAP.md
?? prompts/01_POLICY_AUTH_CASES.md
?? prompts/02_SAFE_MEDIA_AND_GEMINI.md
?? prompts/03_COMPLETE_CASE_WORKFLOW.md
?? prompts/04_REDTEAM_ALERTS.md
?? prompts/05_THREE_FUNCTIONAL_PORTALS.md
?? prompts/06_CLOUD_AND_THREE_MINUTE_DEMO.md
?? prompts/07_UI_POLISH_ONLY_AFTER_GATES.md
?? pyproject.toml
?? reference/MASTER_BOOK_EXTRACTED_REFERENCE.txt
?? reference/SENTINEL_LADDER_MASTER_BOOK_PREBUILD_V2.pdf
?? tracking/EXECUTION_LOG.md
?? tracking/PHASE_00_REPORT.md
?? tracking/PHASE_01_BASELINE_TEST_HASHES.json
?? tracking/PHASE_01_REPORT.md
?? tracking/PHASE_GATE_REPORT_TEMPLATE.md
?? tracking/REQUIREMENT_MATRIX.md
?? tracking/SECURITY_TEST_CATALOG.md
?? tracking/STATUS_LEDGER.md
```

```powershell
git remote -v
```

Exit 0, no output. No remote is configured. All original kit files were already untracked; the modified tracking/docs files therefore also appear as untracked. Nothing was staged or committed. Phase 01 local gate PASS; Phase 02 awaits explicit user approval.
