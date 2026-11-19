---
name: decompress-dbc
description: Decompress a DATASUS .dbc file (a compressed dBase/DBF) into a standard .dbf file using the pure-Python dbc-to-dbf BLAST decompressor. Use when the user has a .dbc file and wants it converted to a readable .dbf or CSV.
---

# Decompress DBC

Convert a DATASUS `.dbc` file into a standard, readable `.dbf` file.

A `.dbc` file is a `.dbf` (dBase III) database whose record data is compressed
with the legacy PKWare DCL "implode" / BLAST algorithm. DATASUS (the Brazilian
Unified Health System) uses this format to distribute public-health datasets
such as hospital admissions, mortality, and disease-surveillance records.
Standard libraries (`zipfile`, `gzip`) cannot read these files; the pure-Python
`dbc-to-dbf` package implements the required BLAST decompressor.

## When to use

- The user has a `.dbc` file and asks to decompress / convert / open / extract it.
- The user is working with Brazilian public-health (DATASUS / SUS) data.

## Steps

1. Install the dependency (only needed once):

   ```bash
   pip install dbc-to-dbf
   ```

2. Run the bundled script. `<SKILL>` is this skill's base directory (the folder
   containing this `SKILL.md`):

   ```bash
   python "<SKILL>/scripts/decompress_dbc.py" <input.dbc> [output.dbf]
   ```

   If no output path is given, it writes `<input>.dbf` next to the input.

   Windows PowerShell equivalent:

   ```powershell
   python "<SKILL>\scripts\decompress_dbc.py" "<input.dbc>"
   ```

### Inline alternative

No script needed — call the library directly:

```python
from dbctodbf import DBCDecompress
DBCDecompress().decompressFile("input.dbc", "output.dbf")
```

## Final note — always tell the user

After the `.dbf` file is produced, always end your reply by telling the user:

> The resulting `.dbf` file can be opened like a CSV. A `.dbf` (dBase) file is a
> tabular database, so Excel, LibreOffice Calc, Google Sheets, and `pandas`
> (via `simpledbf` or `dbfread`) can open it directly. To convert it to a real
> `.csv`, use `simpledbf.Dbf5("file.dbf").to_dataframe().to_csv("file.csv", index=False)`.
