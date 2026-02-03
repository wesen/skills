# Templates

## Minimal repo layout

```
proto/
go/
web/
```

## Example proto schema

```proto
syntax = "proto3";

package sem.example.v1;

import "google/protobuf/struct.proto";

option go_package = "example/go/gen/proto/sem/example/v1;examplev1";

message ExamplePayloadV1 {
  uint32 schema_version = 1;
  string item_id = 2;
  int64 sequence_id = 3;
  Data data = 4;
  google.protobuf.Struct extra = 5;
  map<string, string> labels = 6;
  repeated string tags = 7;

  message Data {
    string mode = 1;
    int64 started_at_ms = 2;
  }
}
```

## Buf config (v2)

`buf.yaml`
```yaml
version: v2
name: buf.build/local/example

deps:
  - buf.build/googleapis/googleapis
```

`buf.gen.yaml`
```yaml
version: v2
plugins:
  - remote: buf.build/bufbuild/es
    out: web/src/pb
    opt:
      - target=ts
      - import_extension=none
  - remote: buf.build/protocolbuffers/go
    out: go/gen
    opt:
      - paths=source_relative
```

## Go protojson emitter (SEM-style)

```go
payload := &examplev1.ExamplePayloadV1{SchemaVersion: 1, ItemId: "item-123"}
bytes, _ := protojson.Marshal(payload) // camelCase JSON
// wrap: { sem: true, event: { type, id, data: <payload> } }
```

## TypeScript decoder

```ts
import { fromJson } from "@bufbuild/protobuf";
import { ExamplePayloadV1Schema } from "./pb/proto/sem/example/v1/example_event_pb";

const pb = fromJson(ExamplePayloadV1Schema, event.data as any);
const seq = pb.sequenceId; // bigint
```

## Optional schema dump

```bash
go run ./go/cmd/schema-dump --message sem.example.v1.ExamplePayloadV1 --out out/schema.json
```
