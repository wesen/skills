---
name: protobuf-go-ts-schema-exchange
description: "Schema-first workflow for sharing protobuf-defined payloads between Go and TypeScript with JSON transport, Buf codegen, protojson, and @bufbuild/protobuf. Use when creating proto schemas, generating Go/TS code, emitting JSON payloads, decoding with fromJson, handling int64/Struct, or validating end-to-end payloads."
---

# Protobuf Go/TS Schema Exchange

## Quick start

- Define a protobuf schema with a `schema_version` field and stable package name.
- Configure Buf v2 with `remote:` plugins and generate Go + TS outputs.
- Emit JSON in Go using `protojson` (camelCase field names).
- Decode JSON in TS using `fromJson` and validate `int64` and Struct behaviors.

## Workflow

1) Author the protobuf schema (see `references/templates.md`).
2) Configure Buf v2 generation for Go + TS (see `references/templates.md`).
3) Generate outputs with `buf generate`.
4) Emit JSON in Go with `protojson` and a SEM-style envelope.
5) Decode in TS with `fromJson` and validate BigInt/Struct handling.
6) Run the validation checklist (see `references/validation.md`).

## Pitfalls to avoid

- Use Buf v2 `remote:` plugin syntax in `buf.gen.yaml`.
- Match protoc-gen-es v2 with `@bufbuild/protobuf` v2.
- Expect `int64` in JSON to be strings; `fromJson` yields `bigint`.
- `google.protobuf.Struct` becomes a JsonObject in TS, not a Struct message.
- With `paths=source_relative`, generated outputs keep the `proto/` prefix; align `go_package` accordingly.

## References

- `references/templates.md`
- `references/validation.md`
