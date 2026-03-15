# Validation Checklist

Run this checklist before marking a go-go-goja module task complete.

## Runtime and module checks

- `engine.New()` creates a runtime without panic.
- JavaScript can `require("<modname>")` successfully.
- At least one JS snippet exercises a real exported function (not just import-only).

## API and adapter checks

- JS options use lowerCamel keys in examples and tests.
- Required fields are validated with clear errors.
- Adapter layer reuses service option/result types where possible.
- Loader code only wires exports; no business logic embedded in loader.

## Tests

- Service-level tests exist for domain behavior.
- Runtime integration tests exist for `require("<modname>")`.
- Temp files/dirs are used in tests (no machine-specific absolute paths).

## Commands

Run in module repo:

```bash
go test ./... -count=1
GOWORK=off go test ./... -count=1
```

If lint target exists:

```bash
GOWORK=off make lint
```

## Docs

- README has:
  - Go embedding example (`engine.New()` + blank import + `require("<modname>")`)
  - JavaScript usage example
- Any API migration notes are explicit.

## Acceptance criteria

- Module is loadable via `require("<modname>")` in go-go-goja runtime.
- Core module behavior is covered by tests and passes in local + CI-like mode.
- Module structure preserves clean service vs adapter boundaries.
