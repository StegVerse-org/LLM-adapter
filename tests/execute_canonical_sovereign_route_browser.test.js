"use strict";

const assert = require("assert");
const adapter = require("../web_runtime/execute_canonical_sovereign_route.js");

(async function () {
  const endpoint = "https://stegverse.org/stegos-bootstrap/local-model";
  const proof = {
    schema: "stegverse.sovereign-local-model-proof/v1",
    goal_id: "SOVEREIGN-LOCAL-MODEL-001",
    state: "VERIFIED_REFERENCE_MODEL_RUNTIME",
    model_id: "stegverse-reference-lm-v1",
    model_hash: "5c1a425a40cd63cf5f4bb4cc28c3eebaad9713a42cfdcfb85e025d3371013a4d",
    proof_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    production_llm_equivalent: false,
    authority_effect: "NONE",
    endpoint: endpoint,
    endpoint_transport: "SERVICE_WORKER_LOCAL_INTERCEPT",
    service_worker_scope: "https://stegverse.org/stegos-bootstrap/",
    github_token_required: false,
    third_party_execution_platform_required: false,
    predicates: {
      real_model_process_observed: false,
      private_endpoint_only: false,
      browser_service_worker_runtime_observed: true,
      device_local_intercepted_endpoint: true,
      network_egress_required: false,
      real_inference_response_observed: true,
      measured_usage_persistable: true,
      local_training_observed: true,
      third_party_inference_required: false,
      model_output_grants_authority: false
    }
  };
  const proofHash = await adapter.sha256(proof);
  const route = {
    schema_version: "stegverse.tvc.sovereign-local-model-route-receipt.v1",
    state: "ROUTE_ADMITTED",
    route_authority: "StegVerse-Labs/TVC",
    runtime: "stegverse-reference-browser",
    model_id: proof.model_id,
    endpoint: endpoint,
    endpoint_transport: "SERVICE_WORKER_LOCAL_INTERCEPT",
    runtime_proof_schema: proof.schema,
    runtime_proof_state: proof.state,
    canonical_micro_node_proof_consumed: true,
    runtime_proof_hash: proofHash,
    credential_requirement: "NONE",
    github_token_required: false,
    third_party_execution_platform_required: false,
    execution_authority: false,
    authority_effect: "NONE",
    reason: "verified sovereign local runtime may be routed without credentials"
  };
  route.receipt_hash = await adapter.sha256(route);
  const fakeResponse = {
    ok: true,
    headers: { get: (name) => name === "X-StegVerse-Execution" ? "SERVICE_WORKER_LOCAL_INTERCEPT" : null },
    json: async () => ({
      id: "chatcmpl-test",
      model: proof.model_id,
      choices: [{ message: { content: "bounded local result" }, finish_reason: "stop" }],
      usage: { prompt_tokens: 4, completion_tokens: 3, total_tokens: 7, latency_ms: 1.25 },
      stegverse: {
        model_hash: proof.model_hash,
        training: { training_tokens: 1, order: 2, external_training_service_required: false },
        third_party_inference_required: false,
        authority_effect: "NONE"
      }
    })
  };
  const execution = await adapter.execute({
    proof,
    route,
    session_id: "session-browser-test",
    transition_id: "transition-browser-test",
    measurement_id: "measurement-browser-test",
    prompt: "test local inference",
    fetcher: async (url, options) => {
      assert.strictEqual(url, endpoint + "/v1/chat/completions");
      assert.strictEqual(options.credentials, "omit");
      assert.strictEqual(options.cache, "no-store");
      assert.ok(!JSON.stringify(options).includes("Authorization"));
      return fakeResponse;
    }
  });
  assert.strictEqual(execution.state, "EXECUTED");
  assert.strictEqual(execution.route_receipt_hash, route.receipt_hash);
  assert.strictEqual(execution.runtime_proof_hash, proofHash);
  assert.strictEqual(execution.provider_usage_event.entry_point, "llm_adapter");
  assert.strictEqual(execution.provider_usage_event.measurement_source, "provider_trace");
  assert.strictEqual(execution.provider_usage_event.metrics.total_tokens.value, "7");
  assert.strictEqual(execution.binding_receipt.runtime_proof_hash, proof.proof_hash);
  assert.ok(Object.values(execution.binding_receipt.authority).every((value) => value === false));
  assert.strictEqual(execution.github_token_required, false);
  assert.strictEqual(execution.third_party_execution_platform_required, false);
  assert.strictEqual(execution.execution_authority, false);
  assert.strictEqual(execution.authority_effect, "NONE");
  const eventCopy = { ...execution.provider_usage_event };
  delete eventCopy.event_sha256;
  assert.strictEqual(execution.provider_usage_event.event_sha256, await adapter.sha256(eventCopy));
  process.stdout.write("LLM_ADAPTER_BROWSER_SOVEREIGN_ROUTE_PASS\n");
}()).catch((error) => { console.error(error); process.exit(1); });
