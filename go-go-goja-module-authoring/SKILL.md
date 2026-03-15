---
name: go-go-goja-module-authoring
description: Create, refactor, and validate reusable go-go-goja native modules exposed via require(). Use when converting Go domain logic into a JavaScript-facing module, implementing modules.NativeModule adapters, wiring module registration with init()+modules.Register, designing JS option/result codecs, or adding runtime integration tests using engine.New()+require().
---

# Go Go Goja Module Authoring

## Workflow

### 1. Define the JS module contract first

- Define the `require("<name>")` entrypoint and exported functions/methods.
- Use lowerCamelCase option/result keys in JavaScript-facing APIs.
- Decide explicit error semantics: returned values vs thrown errors.

### 2. Split domain logic from JS/runtime glue

- Keep business operations in a pure Go service package (no goja dependency).
- Keep module adapter code focused on:
  - option decoding/validation
  - Go<->JS conversion
  - export wiring
- Reuse service option structs in adapter code where possible to avoid drift.

### 3. Implement a native module adapter

- Implement `modules.NativeModule` with:
  - `Name() string`
  - `Doc() string`
  - `Loader(*goja.Runtime, *goja.Object)`
- Register in `init()` with `modules.Register(&module{})`.
- In `Loader`, read `exports := moduleObj.Get("exports").(*goja.Object)` and set exports there.
- Prefer `modules.SetExport(...)` for wrapped exports where call logging is useful.

### 4. Ensure module loading works in runtime creation path

- Confirm module package is imported somewhere that runs before `engine.New()` usage.
- Typical pattern: blank import of module package in the consumer runtime/app.
- Verify runtime usage with:
  - `vm, _ := ggjengine.New()`
  - `vm.RunString('const mod = require("<name>")')`

### 5. Add tests at two levels

- Service tests (pure Go): validate business behavior independent of goja.
- Runtime integration tests: boot go-go-goja runtime and execute JS using `require("<name>")`.
- Use temp dirs/files in tests and assert real output side-effects, not only non-error execution.

### 6. Update documentation for onboarding

- Add a minimal "Using as a go-go-goja Native Module" snippet.
- Include one realistic JS usage example and one Go embedding example.
- Document any API migrations (for example, PascalCase to lowerCamel changes).

### 7. Validate in both local and CI-style modes

- Run:
  - `go test ./... -count=1`
  - `GOWORK=off go test ./... -count=1`
  - `GOWORK=off make lint` (if available)
- Fix failures before adding more features.

## Guardrails

- Do not put domain operations in `Loader`.
- Do not expose Go-internal naming conventions directly to JS API shape.
- Do not skip integration tests for `require("<name>")` loading.
- Do not rely on global runtime mutation when a native module adapter is intended.

## References

- `references/goja-git-pattern.md` for a proven adapter + service + integration-test shape.
- `references/validation-checklist.md` for pre-merge checks and acceptance criteria.
