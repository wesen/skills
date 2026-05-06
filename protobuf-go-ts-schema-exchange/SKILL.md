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

## CI setup

If `go generate` runs `buf generate` (e.g. via a `//go:generate` directive), install `buf` in CI before `go generate`:

```yaml
- run: go install github.com/bufbuild/buf/cmd/buf@v1.68.3
- run: go generate ./...
```

`actions/setup-go` puts `$GOPATH/bin` on `PATH`, so the installed binary is immediately available.

## RTK Query / Frontend Integration

When consuming protobuf payloads in a React/RTK Query frontend, prefer **generated TypeScript protobuf types** over hand-written type mirrors. Keep normalization out of RTK Query and transform only at widget boundaries.

### Recommended pattern

1. Generate TypeScript bindings from the same `.proto` files the backend uses.
2. Use `fromJson` in RTK Query `transformResponse` to convert wire JSON into typed protobuf messages.
3. Let RTK Query cache store the protobuf shapes directly — no normalization pass.
4. Transform to widget-specific props inside components with `useMemo`.

### Why this works

- Single source of truth: `.proto` is the contract; both Go and TS codegen from it.
- No information loss: the full proto shape is available to every consumer.
- Localized transforms: a `ShowList` widget groups by month, a `ShowDetail` widget flattens lineup — each does its own `useMemo` without a global normalization schema.
- Reusable transformers: if multiple widgets need the same derived shape, extract a helper — but keep it close to the components, not in the API layer.

### Example: RTK Query endpoint with generated types

```ts
import { ShowList } from "./generated/pyxis/v1/show_pb";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const publicApi = createApi({
  baseQuery: fetchBaseQuery({ baseUrl: "/api/public" }),
  endpoints: (builder) => ({
    getShows: builder.query<ShowList, void>({
      query: () => "/shows",
      // Go backend emits camelCase JSON via protojson.Marshal
      // fromJson converts it back into the protobuf message
      transformResponse: (response: unknown) => ShowList.fromJson(response),
    }),
  }),
});
```

### Example: widget-level transform

```ts
import { useMemo } from "react";
import { Show } from "./generated/pyxis/v1/show_pb";

function ShowListWidget({ shows }: { shows: Show[] }) {
  const grouped = useMemo(() => groupByMonth(shows), [shows]);
  return (
    <div>
      {grouped.map(([month, items]) => (
        <MonthGroup key={month} month={month} shows={items} />
      ))}
    </div>
  );
}
```

### What to remove from hand-written type packages

- Any interface that is a 1:1 mirror of an API response shape (e.g., `Show`, `AppShow`, `Submission`).
- Normalization schemas that map API responses into entity dictionaries.
- Manual `camelCase` field renaming (protojson handles this).

### What to keep in hand-written type packages

- Widget prop interfaces that are genuinely different from wire shapes.
- Aggregated/computed types (e.g., `DashboardSummary`).
- Frontend-specific view models (e.g., `CalendarEvent` with display state).

## Pitfalls to avoid

- Use Buf v2 `remote:` plugin syntax in `buf.gen.yaml`.
- Match protoc-gen-es v2 with `@bufbuild/protobuf` v2.
- Expect `int64` in JSON to be strings; `fromJson` yields `bigint`.
- `google.protobuf.Struct` becomes a JsonObject in TS, not a Struct message.
- With `paths=source_relative`, generated outputs keep the `proto/` prefix; align `go_package` accordingly.
- Do **not** put `fromJson` calls inside Redux slices or normalization middleware — keep it in `transformResponse` so the cache holds typed proto messages.

## References

- `references/templates.md`
- `references/validation.md`
