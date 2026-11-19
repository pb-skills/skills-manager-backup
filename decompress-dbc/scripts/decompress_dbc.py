#!/usr/bin/env python3
"""
Decompress a DATASUS .dbc file (compressed dBase/DBF) into a standard .dbf file.

DATASUS (the Brazilian Unified Health System) distributes public health datasets
as ``.dbc`` files. These are ``.dbf`` (dBase III) files whose record data is
compressed with the legacy PKWare DCL "implode" / BLAST algorithm. Modern
libraries such as ``zipfile`` and ``gzip`` cannot read them.

This script uses the ``dbc-to-dbf`` package, which provides a pure-Python BLAST
decompressor.

Install the dependency first:

    pip install dbc-to-dbf

Usage:

    python decompress_dbc.py <input.dbc> [output.dbf]

Examples:

    python decompress_dbc.py tb_inf_2010-01.dbc
        # writes tb_inf_2010-01.dbf in the same folder

    python decompress_dbc.py tb_inf_2010-01.dbc out/tb_inf.dbf
        # writes to an explicit path
"""

import sys
from pathlib import Path


def decompress(input_path: Path, output_path: Path) -> None:
    """Decompress a single .dbc file to a .dbf file."""
    try:
        from dbctodbf import DBCDecompress
    except ImportError:
        sys.exit(
            "The 'dbc-to-dbf' package is not installed.\n"
            "Install it with:  pip install dbc-to-dbf"
        )

    DBCDecompress().decompressFile(str(input_path), str(output_path))


def main() -> None:
    args = sys.argv[1:]

    if not args:
        sys.exit(__doc__)

    input_path = Path(args[0])

    if len(args) >= 2:
        output_path = Path(args[1])
    else:
        output_path = input_path.with_suffix(".dbf")

    if not input_path.is_file():
        sys.exit(f"Error: input file not found: {input_path}")

    print(f"Decompressing {input_path} -> {output_path} ...")
    decompress(input_path, output_path)
    print(f"Done. Output written to {output_path} ({output_path.stat().st_size} bytes)")
    print(
        "Tip: a .dbf file is a tabular database and can be opened like a CSV "
        "(Excel, LibreOffice Calc, Google Sheets, or pandas via simpledbf/dbfread)."
    )


if __name__ == "__main__":
    main()
