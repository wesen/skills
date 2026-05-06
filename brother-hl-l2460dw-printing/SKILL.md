---
name: brother-hl-l2460dw-printing
description: Print PDFs on the Brother_HL_L2460DW printer, using duplex settings that were verified to work.
---

# Brother HL-L2460DW Printing

Use this when the user wants to print on the Brother HL-L2460DW.

## Verified duplex settings

Printer name:
- `Brother_HL_L2460DW`

Verified working duplex command:

```bash
lp -d Brother_HL_L2460DW \
  -o sides=two-sided-long-edge \
  -o Duplex=DuplexNoTumble \
  /path/to/file.pdf
```

## Notes

- The queue default may still report `sides=one-sided`, so always pass the duplex options explicitly when the user wants duplex.
- If duplex behavior is uncertain, first generate and print a 2-page test PDF.
- Alternative duplex values advertised by CUPS are:
  - `Duplex=DuplexNoTumble`
  - `Duplex=DuplexTumble`
- The verified working combination is:
  - `sides=two-sided-long-edge`
  - `Duplex=DuplexNoTumble`

## Quick checks

```bash
lpstat -p -d
lpoptions -p Brother_HL_L2460DW -l | rg -i 'sides|duplex|two-sided'
```
