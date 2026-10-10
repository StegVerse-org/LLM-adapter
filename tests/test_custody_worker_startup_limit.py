import json

from llm_adapter import custody_worker


def test_configured_limit_accepts_zero(monkeypatch):
    monkeypatch.setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "0")
    assert custody_worker.configured_limit() == 0


def test_main_uses_configured_limit_without_inventing_custody(monkeypatch, capsys):
    observed = {}

    monkeypatch.setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "0")

    def fake_run(limit=20):
        observed["limit"] = limit
        return {
            "worker": "master_records_organization_record",
            "enabled": True,
            "processed": 0,
            "recorded": 0,
            "retry": 0,
            "authority_effect": "NONE_DOWNSTREAM_RECORDING_ONLY",
        }

    monkeypatch.setattr(custody_worker, "run", fake_run)
    assert custody_worker.main() == 0
    assert observed["limit"] == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["recorded"] == 0


def test_configured_limit_rejects_invalid_values(monkeypatch):
    for value in ("-1", "101", "not-an-int"):
        monkeypatch.setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", value)
        try:
            custody_worker.configured_limit()
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid custody worker limit accepted: {value}")


def test_worker_failure_never_blocks_service_startup(monkeypatch, capsys):
    monkeypatch.setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "not-an-int")
    assert custody_worker.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gates_startup"] is False
    for field in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                  "retry_entrypoint", "owning_existing_goal", "next_attempt"):
        assert payload[field]

    monkeypatch.setenv("STEGVERSE_CUSTODY_WORKER_LIMIT", "1")

    def unreachable(limit=20):
        raise ConnectionError("master records unreachable")

    monkeypatch.setattr(custody_worker, "run", unreachable)
    assert custody_worker.main() == 0
    assert json.loads(capsys.readouterr().out)["disposition"] == "NOT_RECORDED"
