"""Fixed subprocess entrypoint: credential-free environment, local synthetic SUT."""

import json
import socket
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from .assurance_corpus import artifact, canonical, load_corpus, policy_for
from .assurance_models import Observed, Profile
from .assurance_scoring import compare, summarize


def execute(profile, version, expected_hash, expected_corpus):
    from .assurance_executor import APIHarness, binding, pure
    current = artifact(profile,version)
    scenarios, labels, corpus = load_corpus()
    if current["sha256"] != expected_hash or corpus["sha256"] != expected_corpus:
        raise ValueError("Artifact/corpus changed")
    policy = policy_for(profile)
    results = []
    with TemporaryDirectory(prefix="sentinel-assurance-worker-") as folder:
        harness = APIHarness(folder,policy)
        try:
            for scenario in scenarios:
                try:
                    observed = (pure(scenario,policy) if scenario.target == "POLICY" else
                                binding(scenario,policy) if scenario.target == "APPROVAL_BINDING" else harness.execute(scenario))
                except Exception:
                    observed = Observed(decision=None,error_code="EXECUTION_ERROR")
                results.append(compare(scenario,labels[(scenario.id,scenario.version)],observed))
        finally:
            harness.close()
    return dict(results=[item.model_dump(mode="json") for item in results],summary=summarize(results,len(scenarios)),
                corpus=corpus,artifact=current,source="SYNTHETIC",isolated_approval_rows=0)


def main():
    original = socket.socket.connect
    def only_local(sock,address):
        if isinstance(address,tuple) and address[0] == "127.0.0.1":
            return original(sock,address)  # Windows asyncio self-pipe only.
        raise RuntimeError("External network disabled in assurance worker")
    socket.socket.connect = only_local
    socket.create_connection = lambda *a,**k: (_ for _ in ()).throw(RuntimeError("Network disabled"))
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw)>16384: raise ValueError("Worker request too large")
        request = json.loads(raw)
        if set(request) != {"profile","version","artifact_sha256","corpus_sha256"}: raise ValueError("Invalid worker request")
        started = monotonic()
        result = execute(Profile(request["profile"]),int(request["version"]),request["artifact_sha256"],request["corpus_sha256"])
        result["elapsed_seconds"] = monotonic()-started
        print(canonical(result))
        return 0
    except Exception:
        print(canonical(dict(error_code="ISOLATED_EXECUTION_FAILED")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
