# goja-git Pattern

Use this pattern when building a new go-go-goja module similar to `require("git")`.

## 1. Package layout

```text
pkg/
  <domainservice>/          # pure Go service logic
  <adapter>/                # goja adapter helpers and codecs
  modules/
    <modname>/
      module.go             # NativeModule impl + init() registration
```

Recommended split:
- service package: no goja imports
- adapter package: runtime export/validation only
- module package: `modules.NativeModule` registration and exports wiring

## 2. Native module skeleton

```go
package <modname>mod

import (
  "github.com/dop251/goja"
  "github.com/go-go-golems/go-go-goja/modules"
  "github.com/<org>/<repo>/pkg/<adapter>"
)

type module struct{}

var _ modules.NativeModule = (*module)(nil)

func (m *module) Name() string { return "<modname>" }

func (m *module) Doc() string {
  return `
<modname> module.
Functions:
  doThing(options)
`
}

func (m *module) Loader(vm *goja.Runtime, moduleObj *goja.Object) {
  exports := moduleObj.Get("exports").(*goja.Object)
  obj := <adapter>.New<ModuleObject>(vm)
  _ = exports.Set("doThing", obj.Get("doThing"))
}

func init() {
  modules.Register(&module{})
}
```

## 3. Runtime integration test pattern

```go
func TestRequireModule(t *testing.T) {
  vm, _ := ggjengine.New()

  dir := t.TempDir()
  if err := vm.Set("TEST_DIR", dir); err != nil {
    t.Fatalf("set TEST_DIR: %v", err)
  }

  script := `
const m = require("<modname>");
const out = m.doThing({ dir: TEST_DIR });
if (!out) throw new Error("expected output");
`
  if _, err := vm.RunString(script); err != nil {
    t.Fatalf("run script: %v", err)
  }
}
```

## 4. JS API compatibility policy

Use lowerCamel keys for JS options and results.

If migrating from legacy PascalCase:
- either support both temporarily via normalization
- or enforce lowerCamel and document the breaking change

Do not mix naming styles in examples.

## 5. Lessons from goja-git

- Keep `pkg/modules/<modname>/module.go` very small and stable.
- Keep long-running domain changes in service tests, not in module loader tests.
- Integration-test `require("<modname>")` for at least one end-to-end operation path.
