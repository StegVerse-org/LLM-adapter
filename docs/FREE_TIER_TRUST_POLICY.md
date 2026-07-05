# Free Tier Trust Policy Boundary

## Purpose

This document defines the bounded live-use trust layer for the StegVerse governed LLM entry point.

The free tier must prove the core governance claim through real governed inquiries, not static demonstration material.

A user can ask a real question, receive a bounded answer, inspect the governing transition, replay the path within limits, and see why the output was admitted, denied, deferred, or quarantined.

## Boundary rule

Free access is not unlimited access. A static demo is not sufficient trust proof. A bounded governed inquiry is the minimum viable trust unit.

The free tier should be live enough to build user confidence while bounded enough to protect provider cost, connector exposure, retention cost, and governance reliability.

## Trust-forming inquiry path

A meaningful free trial should allow a user to experience several distinct governance cases:

1. normal governed answer;
2. answer with receipt inspection;
3. stale-evidence warning or quarantine;
4. source-comparison or evidence-bounded answer;
5. refusal, qualification, or defer decision;
6. limited replay of a recent transition;
7. limited reconstruction of a recent session path.

The target trust window is:

- 3 to 10 meaningful inquiries: curiosity-level trust.
- 20 to 50 meaningful inquiries: reliance-level evaluation.

## Recommended free tier envelope

- tier: free
- governed inquiries per day: 5
- trial governed inquiries total: 25
- receipt inspection: enabled
- receipt exports per day: 1
- replays per day: 1
- reconstruction scope: recent-session limited
- private connectors: disabled
- sample connectors: enabled
- premium models: disabled
- bring-your-own provider key: allowed if separately governed
- retention: short window or hash-pointer only
- upgrade trigger: quota, retention, connector, or premium-model need

## Paid tier differentiation

The paid tier should not sell belief. It should sell capacity and operational depth:

- larger inquiry quotas;
- premium model routing;
- private connectors;
- longer receipt retention;
- deeper replay and reconstruction;
- team or organization workspaces;
- API access;
- custom policies and delegations;
- exportable audit packets;
- enterprise deployment options.

## Required non-claims

The free tier does not claim that:

- a provider response is authority;
- a free-tier receipt is permanent retention;
- a replay grants execution authority;
- a reconstruction grants commit-time standing;
- a sample connector proves private connector access;
- an upgrade changes admissibility requirements.

## Adapter implementation posture

This policy is currently a boundary and product-governance contract. The adapter implementation should add executable enforcement only after the quota manifest, receipt limit contract, replay limit contract, and Site display contract are installed.

Until then, implementations must remain side-effect free by default and must not call live providers unless explicitly configured through a governed provider boundary.
