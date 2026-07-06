---
name: go-go-goja-module-authoring
description: Create, refactor, validate, and package reusable go-go-goja native modules exposed via require(), including modern xgoja/v2 provider packaging. Use when converting Go domain logic into a JavaScript-facing module, implementing modules.NativeModule adapters, wiring module registration with init()+modules.Register, designing JS option/result codecs, adding runtime integration tests using engine.New()+require(), or exposing modules to generated xgoja binaries through providerapi.ProviderRegistry.
---

# Go Go Goja Module Authoring

## Workflow

### 1. Define the JS module contract first

- Define the `require("<name>")` entrypoint and exported functions/methods.
- Use lowerCamelCase option/result keys in JavaScript-facing plain-object APIs.
- If exposing Go-backed domain objects directly, explicitly document the JS property names (often exported Go field names such as `node.Type`) and why reflected Go objects are preferable to plain maps.
- Decide explicit error semantics: returned values vs thrown errors.
- Add compact decision records for major API/representation choices.

### 2. Split domain logic from JS/runtime glue

- Keep business operations in a pure Go service package (no goja dependency).
- Keep module adapter code focused on:
  - option decoding/validation
  - Go<->JS conversion
  - export wiring
- Reuse service option structs in adapter code where possible to avoid drift.

### Decision Records for Module APIs

For non-trivial module contracts, add a short decision record to the design docs or module README:

```md
### Decision: <short name>

- **Context:** What constraint or ambiguity forced the choice?
- **Options considered:** For example, Go-backed objects vs plain JS maps, callbacks vs fixed helper exports, runtime config vs build-time config.
- **Decision:** What the module exposes.
- **Rationale:** Why this fits go-go-goja patterns and user needs.
- **Consequences:** Validation benefits, JS ergonomics, compatibility risks, tests needed.
- **Status:** proposed | accepted | superseded
```

Use decision records especially when:
- exposing Go-backed objects to JS instead of lowerCamelCase plain objects,
- choosing callback/traversal APIs over one-off helper exports,
- mutating runtime behavior (for example field-name mapping),
- adding xgoja provider configuration or host-capability modules.

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

### 7. Package modules for xgoja/v2 when generated binaries should select them

A `modules.NativeModule` registered with `modules.Register` is enough for direct Go embedding when the package is imported. It is **not** enough for xgoja-generated binaries. xgoja/v2 selects modules through provider packages listed in `xgoja.yaml`, then exposes selected modules from `runtime.modules`.

Use this step when users need any of these outcomes:

- `xgoja build` can generate a binary with `require("<module>")` available.
- `xgoja gen-dts` can emit declarations for the module.
- `builtin.run`, `builtin.repl`, or `builtin.jsverbs` commands in a generated binary can use the module.
- provider-owned help, assets, jsverbs, command sets, host services, or runtime config need to travel with the module package.

Authoritative xgoja docs live in the installed `xgoja` help system. Refresh them before designing providers:

```bash
xgoja help --all
xgoja help user-guide
xgoja help xgoja-v2-reference
xgoja help provider-runtime-config-and-host-services
xgoja help migrating-xgoja-provider-engine-api
```

Key local source references in the go-go-goja repo:

- `pkg/xgoja/providerapi/module.go` — `providerapi.Module` fields and module factory contract.
- `pkg/xgoja/providerapi/provider_registry.go` — `ProviderRegistry.Package`, `ResolveModule`, duplicate validation.
- `pkg/xgoja/providerapi/help.go` — `providerapi.HelpSource` for provider-owned Glazed help docs.
- `pkg/xgoja/providers/core/core.go` — minimal provider wrapping existing native modules.
- `pkg/xgoja/providers/http/http.go` and `serve.go` — richer provider with runtime config, host services, and command sets.
- `pkg/xgoja/dtsgen` — TypeScript declaration generation from provider module descriptors.
- Example external provider pattern: `goja-text/pkg/xgoja/providers/text/text.go`.

Minimal provider pattern:

```go
package myprovider

import (
    "fmt"

    "github.com/dop251/goja_nodejs/require"
    "github.com/go-go-golems/go-go-goja/modules"
    "github.com/go-go-golems/go-go-goja/pkg/tsgen/spec"
    "github.com/go-go-golems/go-go-goja/pkg/xgoja/providerapi"
    _ "github.com/acme/project/pkg/gojamodules/mymodule"
)

const PackageID = "acme-project"

var moduleNames = []string{"mymodule"}

func Register(registry *providerapi.ProviderRegistry) error {
    entries := make([]providerapi.Entry, 0, len(moduleNames))
    for _, name := range moduleNames {
        mod := modules.GetModule(name)
        if mod == nil {
            return fmt.Errorf("module %q is not registered", name)
        }
        entries = append(entries, nativeModuleEntry(mod))
    }
    return registry.Package(PackageID, entries...)
}

func nativeModuleEntry(mod modules.NativeModule) providerapi.Module {
    return providerapi.Module{
        Name:        mod.Name(),
        DefaultAs:   mod.Name(),
        Description: mod.Doc(),
        TypeScript:  nativeModuleTypeScript(mod),
        NewModuleFactory: func(providerapi.ModuleSetupContext) (require.ModuleLoader, error) {
            return mod.Loader, nil
        },
    }
}

func nativeModuleTypeScript(mod modules.NativeModule) *spec.Module {
    declarer, ok := mod.(modules.TypeScriptDeclarer)
    if !ok {
        return nil
    }
    return declarer.TypeScriptModule()
}
```

Minimal `xgoja.yaml` shape for consumers:

```yaml
schema: xgoja/v2
name: my-tool

go:
  module: xgoja.generated/my-tool
  version: "1.26"

providers:
  - id: acme
    import: github.com/acme/project/pkg/xgoja/providers/myprovider
    register: Register

runtime:
  modules:
    - provider: acme
      name: mymodule
      as: mymodule

commands:
  - id: run
    type: builtin.run
    name: run
  - id: repl
    type: builtin.repl
    name: repl
  - id: verbs
    type: builtin.jsverbs
    name: verbs
    sources: [verbs]

sources:
  - id: verbs
    kind: jsverbs
    from:
      dir: ./verbs

artifacts:
  - id: binary
    type: binary
    output: dist/my-tool
```

Provider tests should cover:

- `Register(providerapi.NewProviderRegistry())` succeeds.
- `ResolveModule(PackageID, "<module>")` finds each module.
- TypeScript descriptors are present for `modules.TypeScriptDeclarer` modules.
- `NewModuleFactory(...).Loader` can satisfy a runtime `require("<module>")` smoke test if the provider has config or host-service behavior.
- `xgoja doctor -f examples/xgoja/.../xgoja.yaml` and, when practical, `xgoja gen-dts` or `xgoja build` works for an example spec.

### 8. Validate in both local and CI-style modes

- Run:
  - `go test ./... -count=1`
  - `GOWORK=off go test ./... -count=1`
  - `GOWORK=off make lint` (if available)
- For xgoja providers, also run:
  - `xgoja doctor -f examples/xgoja/<example>/xgoja.yaml`
  - `xgoja gen-dts -f examples/xgoja/<example>/xgoja.yaml --out /tmp/<example>.d.ts` when TypeScript declarations are part of the contract
  - `xgoja build -f examples/xgoja/<example>/xgoja.yaml` when build time is acceptable
- Fix failures before adding more features.

## Guardrails

- Do not put domain operations in `Loader`.
- Do not expose Go-internal naming conventions directly to JS API shape unless this is an explicit, documented decision for Go-backed domain objects.
- Do not skip integration tests for `require("<name>")` loading.
- Do not rely on global runtime mutation when a native module adapter is intended.
- Do not assume `modules.Register` alone makes a module available to xgoja-generated binaries; add an xgoja provider package and example `xgoja.yaml` when generated-binary use is required.
- Do not expose side-effectful modules to safe project-loading runtimes unless the product explicitly requires that boundary change; prefer separate xgoja runtime module selections for safe and execution-capable contexts.
- Do not bury major API/representation choices in prose; write decision records.

## References

- `references/goja-git-pattern.md` for a proven adapter + service + integration-test shape.
- `references/validation-checklist.md` for pre-merge checks and acceptance criteria.
