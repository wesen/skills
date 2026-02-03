# Validation checklist

## Expected JSON mapping

- snake_case fields -> camelCase JSON keys
- int64 fields -> JSON strings (protojson)
- Struct fields -> JSON object (open shape)

## End-to-end steps

1) Run `buf generate`
2) Emit JSON from Go using `protojson`
3) Decode with `fromJson` in TS
4) Validate:
   - `schema_version` round-trips
   - int64 fields are `bigint` in TS
   - Struct contents appear as plain JS objects
   - map fields are objects with string values
   - repeated fields are arrays

## Common failures

- buf v2 config uses `plugin:` instead of `remote:`
- `@bufbuild/protobuf` runtime version mismatches protoc-gen-es output
- `JSON.stringify` fails on BigInt without a replacer
