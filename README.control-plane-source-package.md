# Control-plane source package projection

The shared StegVerse Service Gateway exposes `/intr/source-package` as a transport-only extension of the existing Universal InTr/HIL projection.

The route accepts only public HTTPS requests whose sovereign profile advertises `stegverse.control-plane`, requires `TVC_RELAY_EGRESS` plus a nonempty TVC authorization identifier, verifies the exact request-body SHA-256, and forwards the exact admitted bytes and transport headers to the already-configured same-host loopback Universal InTr receiver at `/intr/source-package`.

The package route has an 8 MiB request bound. That larger bound applies only to source-package traffic; ordinary `/intr/materialization` retains its existing 512 KiB bound.

This projection creates no scheduler, WorkerCoordinator, HeartBeat, receipt authority, credential authority, custody authority, source-selection authority, or canonical transition authority. It performs no Git/GitHub source fetch and does not make the Gateway a source repository. TV/TVC remains credential/relay authorization authority, the sovereign receiver validates and materializes package content, and the existing resident source watcher performs subsequent local refresh/dispatch.

Canonical implementation and evidence surfaces:

```text
llm_adapter/service_gateway_hil_intr.py
tests/test_service_gateway_control_plane_source_package.py
docs/HIL_INTR_SERVICE_GATEWAY_MIRROR_HANDOFF.md
```
