(function (root) {
  "use strict";

  var EXECUTION_SCHEMA = "stegverse.llm_adapter.canonical_sovereign_route_execution/v1";
  var REQUEST_SCHEMA = "stegverse.llm_adapter.provider_request.v0.1";
  var RESPONSE_SCHEMA = "stegverse.llm_adapter.provider_response.v0.1";
  var ROUTE_SCHEMA = "stegverse.tvc.sovereign-local-model-route-receipt.v1";
  var RUNTIME_SCHEMA = "stegverse.sovereign-local-model-proof/v1";
  var DEVICE_ENDPOINT = "https://stegverse.org/stegos-bootstrap/local-model";
  var METRIC_NAMES = ["prompt_tokens", "completion_tokens", "total_tokens", "latency_ms"];

  function cryptoApi() {
    if (root.crypto && root.crypto.subtle) { return root.crypto; }
    if (typeof require === "function") { return require("crypto").webcrypto; }
    throw new Error("WebCrypto unavailable");
  }
  function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
  function stableJson(value) {
    if (value === null || typeof value !== "object") { return JSON.stringify(value); }
    if (Array.isArray(value)) { return "[" + value.map(stableJson).join(",") + "]"; }
    return "{" + Object.keys(value).sort(cmp).map(function (key) { return JSON.stringify(key) + ":" + stableJson(value[key]); }).join(",") + "}";
  }
  function hex(bytes) { return Array.prototype.map.call(bytes, function (b) { return b.toString(16).padStart(2, "0"); }).join(""); }
  function sha256(value) {
    var text = typeof value === "string" ? value : stableJson(value);
    return cryptoApi().subtle.digest("SHA-256", new TextEncoder().encode(text)).then(function (digest) { return hex(new Uint8Array(digest)); });
  }
  function isoSeconds() { return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00"); }
  function decimalString(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) { throw new Error("provider_response_usage_invalid"); }
    return String(value);
  }
  function requireCondition(condition, reason) { if (!condition) { throw new Error(reason); } }

  function validateRuntimeProof(proof) {
    requireCondition(proof && proof.schema === RUNTIME_SCHEMA, "unsupported_sovereign_local_model_proof");
    requireCondition(proof.goal_id === "SOVEREIGN-LOCAL-MODEL-001", "local_model_goal_identity_mismatch");
    requireCondition(proof.state === "VERIFIED_REFERENCE_MODEL_RUNTIME", "local_model_runtime_not_verified");
    requireCondition(proof.authority_effect === "NONE", "local_model_proof_authority_escalation");
    var p = proof.predicates || {};
    var processPath = p.real_model_process_observed === true && p.private_endpoint_only === true;
    var devicePath = p.browser_service_worker_runtime_observed === true && p.device_local_intercepted_endpoint === true && p.network_egress_required === false && proof.endpoint_transport === "SERVICE_WORKER_LOCAL_INTERCEPT" && proof.endpoint === DEVICE_ENDPOINT;
    requireCondition(processPath || devicePath, "local_model_runtime_execution_surface_not_verified");
    ["real_inference_response_observed", "measured_usage_persistable", "local_training_observed"].forEach(function (name) {
      requireCondition(p[name] === true, "local_model_runtime_predicates_failed:" + name);
    });
    requireCondition(p.third_party_inference_required === false, "third_party_inference_dependency_detected");
    requireCondition(p.model_output_grants_authority === false, "model_output_authority_detected");
    requireCondition(proof.github_token_required === false, "github_token_dependency_detected");
    requireCondition(proof.third_party_execution_platform_required === false, "third_party_execution_platform_dependency_detected");
    requireCondition(typeof proof.proof_hash === "string" && /^[0-9a-f]{64}$/.test(proof.proof_hash), "local_model_proof_hash_missing");
    requireCondition(typeof proof.model_hash === "string" && /^[0-9a-f]{64}$/.test(proof.model_hash), "local_model_hash_evidence_missing");
    return proof;
  }

  function validateRoute(route, proof) {
    requireCondition(route && route.schema_version === ROUTE_SCHEMA, "tvc_route_schema_mismatch");
    requireCondition(route.state === "ROUTE_ADMITTED", "tvc_route_not_admitted");
    requireCondition(route.route_authority === "StegVerse-Labs/TVC", "tvc_route_authority_mismatch");
    requireCondition(route.credential_requirement === "NONE", "tvc_route_credential_requirement_not_none");
    requireCondition(route.github_token_required === false, "tvc_route_github_token_dependency");
    requireCondition(route.third_party_execution_platform_required === false, "tvc_route_third_party_platform_dependency");
    requireCondition(route.execution_authority === false && route.authority_effect === "NONE", "tvc_route_authority_escalation");
    requireCondition(route.canonical_micro_node_proof_consumed === true, "tvc_route_noncanonical_proof");
    requireCondition(route.model_id === proof.model_id, "tvc_route_model_identity_mismatch");
    var endpoint = String(route.endpoint || "").replace(/\/$/, "");
    requireCondition(Boolean(endpoint), "tvc_route_endpoint_missing");
    if (route.endpoint_transport === "SERVICE_WORKER_LOCAL_INTERCEPT") {
      requireCondition(endpoint === DEVICE_ENDPOINT, "device_local_endpoint_mismatch");
    }
    return sha256(proof).then(function (proofHash) {
      requireCondition(route.runtime_proof_hash === proofHash, "tvc_route_runtime_proof_hash_mismatch");
      var withoutReceipt = {};
      Object.keys(route).forEach(function (key) { if (key !== "receipt_hash") { withoutReceipt[key] = route[key]; } });
      return sha256(withoutReceipt).then(function (routeHash) {
        requireCondition(route.receipt_hash === routeHash, "tvc_route_receipt_hash_mismatch");
        return { endpoint: endpoint, transportEndpoint: endpoint + "/v1/chat/completions", proofHash: proofHash, routeHash: routeHash };
      });
    });
  }

  function buildProviderRequest(proof, sessionId, transitionId, prompt) {
    return {
      schema_version: REQUEST_SCHEMA,
      created_at: isoSeconds(),
      provider: "stegverse-local",
      model: proof.model_id,
      messages: [{ role: "user", content: prompt }],
      purpose: "answer",
      allowed_sources: ["model_knowledge"],
      temperature: 0,
      metadata: {
        session_id: sessionId,
        transition_id: transitionId,
        runtime_proof_hash: proof.proof_hash,
        runtime_model_hash: proof.model_hash,
        runtime_proof_schema: proof.schema,
        production_llm_equivalent: Boolean(proof.production_llm_equivalent)
      }
    };
  }

  function buildUsageEvent(responseHash, proof, sessionId, transitionId, measurementId, usage) {
    var metrics = {};
    METRIC_NAMES.forEach(function (name) {
      var value = usage[name];
      metrics[name] = {
        value: decimalString(value),
        unit: name === "latency_ms" ? "milliseconds" : "tokens",
        evidence_class: "MEASURED",
        source_ref: "provider_response:" + responseHash
      };
    });
    var event = {
      schema_version: "1.0.0",
      event_type: "TRANSITION_USAGE_RECORDED",
      measurement_id: measurementId,
      session_id: sessionId,
      transition_id: transitionId,
      parent_transition_id: null,
      origin_entry_point: "ecosystem_chat",
      entry_point: "llm_adapter",
      entry_point_role: "machine_readable_translation_and_interoperability",
      interaction_type: "sovereign_local_model_inference",
      metric_owner: "llm_adapter",
      measurement_source: "provider_trace",
      route_kind: "EXTERNAL_RECURSIVE",
      provider: "stegverse-local",
      model: proof.model_id,
      metrics: metrics,
      receipt_refs: ["local-runtime-proof:" + proof.proof_hash, "provider-response:" + responseHash],
      timestamp: null,
      invariants: {
        provider_output_is_authority: false,
        usage_event_is_authority: false,
        usage_event_is_admissibility: false,
        session_identity_preserved: true,
        transition_lineage_preserved: true
      }
    };
    return sha256(event).then(function (eventHash) { event.event_sha256 = eventHash; return event; });
  }

  function execute(options) {
    options = options || {};
    var proof = validateRuntimeProof(options.proof || {});
    var route = options.route || {};
    var sessionId = String(options.session_id || "");
    var transitionId = String(options.transition_id || "");
    var measurementId = String(options.measurement_id || "");
    var prompt = String(options.prompt || "");
    var fetcher = options.fetcher || root.fetch;
    requireCondition(sessionId && transitionId && measurementId && prompt, "same_execution_identity_or_prompt_missing");
    requireCondition(typeof fetcher === "function", "fetcher_missing");

    return validateRoute(route, proof).then(function (binding) {
      var request = buildProviderRequest(proof, sessionId, transitionId, prompt);
      return sha256(request).then(function (requestHash) {
        var payload = { model: proof.model_id, messages: request.messages, temperature: request.temperature };
        return fetcher(binding.transportEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "omit",
          cache: "no-store",
          body: JSON.stringify(payload)
        }).then(function (httpResponse) {
          requireCondition(httpResponse && httpResponse.ok, "provider_http_failure");
          if (route.endpoint_transport === "SERVICE_WORKER_LOCAL_INTERCEPT") {
            requireCondition(httpResponse.headers && httpResponse.headers.get("X-StegVerse-Execution") === "SERVICE_WORKER_LOCAL_INTERCEPT", "device_local_execution_escape_detected");
          }
          return httpResponse.json();
        }).then(function (body) {
          var output = body && body.choices && body.choices[0] && body.choices[0].message && body.choices[0].message.content;
          requireCondition(typeof output === "string" && output.trim(), "provider_output_missing");
          var usage = body.usage || {};
          METRIC_NAMES.forEach(function (name) { requireCondition(typeof usage[name] === "number" && Number.isFinite(usage[name]), "provider_response_usage_invalid:" + name); });
          var stegverse = body.stegverse || {};
          requireCondition(stegverse.model_hash === proof.model_hash, "runtime_model_hash_mismatch");
          requireCondition(stegverse.third_party_inference_required === false, "provider_response_third_party_dependency");
          requireCondition(stegverse.authority_effect === "NONE", "provider_response_authority_escalation");
          var metadata = {
            provider_mode: "stegverse_local_openai_compatible",
            sovereign_endpoint: true,
            third_party_execution_platform_required: false,
            provider_credential_required: false,
            response_id: body.id || "unresolved",
            finish_reason: (body.choices[0] || {}).finish_reason || "unresolved",
            usage: usage,
            runtime_model: body.model || proof.model_id,
            model_hash: stegverse.model_hash,
            training: stegverse.training,
            third_party_inference_required: stegverse.third_party_inference_required,
            authority_effect: stegverse.authority_effect
          };
          var responseCore = {
            schema_version: RESPONSE_SCHEMA,
            provider: "stegverse-local",
            model: proof.model_id,
            output: output,
            request_hash: requestHash,
            metadata: metadata
          };
          return sha256(responseCore).then(function (responseHash) {
            return buildUsageEvent(responseHash, proof, sessionId, transitionId, measurementId, usage).then(function (usageEvent) {
              var measuredUsage = {};
              METRIC_NAMES.forEach(function (name) { measuredUsage[name] = usageEvent.metrics[name]; });
              var bindingReceipt = {
                schema: "stegverse.llm_adapter.sovereign_local_model_binding/v1",
                task_id: "LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019",
                source_proof_schema: proof.schema,
                session_id: sessionId,
                transition_id: transitionId,
                measurement_id: measurementId,
                provider: "stegverse-local",
                model_id: proof.model_id,
                model_hash: proof.model_hash,
                runtime_proof_hash: proof.proof_hash,
                request_hash: requestHash,
                response_hash: responseHash,
                provider_usage_event_sha256: usageEvent.event_sha256,
                measured_usage: measuredUsage,
                provider_usage_custody_recorded: false,
                provider_usage_reconstruction_pass: false,
                production_scale_llm_observed: false,
                reference_model_only: true,
                activation_complete: false,
                remaining_activation_predicates: ["provider_usage_master_records_custody", "provider_usage_master_records_reconstruction_pass", "production_scale_sovereign_llm", "same_execution_transition_reconstruction_pass"],
                authority: {
                  provider_output_grants_authority: false,
                  usage_event_grants_authority: false,
                  binding_receipt_grants_authority: false
                }
              };
              return sha256(output).then(function (responseTextHash) {
                return {
                  schema: EXECUTION_SCHEMA,
                  task_id: "LLMA-SOVEREIGN-CARRIER-EXECUTION-020",
                  state: "EXECUTED",
                  session_id: sessionId,
                  transition_id: transitionId,
                  measurement_id: measurementId,
                  route_authority: "StegVerse-Labs/TVC",
                  route_receipt_hash: binding.routeHash,
                  runtime_proof_hash: binding.proofHash,
                  route_base_endpoint: binding.endpoint,
                  transport_endpoint: binding.transportEndpoint,
                  model_id: proof.model_id,
                  model_hash: proof.model_hash,
                  request_hash: requestHash,
                  response_hash: responseHash,
                  response_text_sha256: responseTextHash,
                  measured_usage: measuredUsage,
                  provider_usage_event: usageEvent,
                  master_records_usage: { custody_recorded: false, reconstructability: "PENDING_SAME_EXECUTION_RECONSTRUCTION", authority_effect: "NONE" },
                  binding_receipt: bindingReceipt,
                  provider_usage_custody_recorded: false,
                  provider_usage_reconstruction_pass: false,
                  reference_model_only: true,
                  credential_requirement: "NONE",
                  github_token_required: false,
                  third_party_execution_platform_required: false,
                  execution_authority: false,
                  authority_effect: "NONE",
                  next_transition: "MASTER_RECORDS_SAME_EXECUTION_TRANSITION_RECONSTRUCTION",
                  provider_response: body
                };
              });
            });
          });
        });
      });
    });
  }

  var api = { stableJson: stableJson, sha256: sha256, validateRuntimeProof: validateRuntimeProof, validateRoute: validateRoute, execute: execute };
  root.StegVerseLLMAdapterPortable = api;
  if (typeof module !== "undefined" && module.exports) { module.exports = api; }
}(typeof self !== "undefined" ? self : globalThis));
