# CMS-2 Language Support for Visual Studio Code

Language Server Protocol (LSP) implementation for **CMS-2** (Compiler Monitor System 2), the US Navy's standard programming language for tactical combat systems.

## About CMS-2

CMS-2 was developed in 1968-1969 by Computer Sciences Corporation with Intermetrics for the US Navy. It remains in active use on:

- **Aegis Combat System** - cruisers, destroyers
- **Submarine combat control systems**
- **Naval Tactical Data System (NTDS)**
- **Aircraft carrier battle management**

Target computers include the AN/UYK-7 and AN/UYK-43, with the language still powering critical naval defence infrastructure worldwide.

## Features

- **Syntax highlighting** for CMS-2Y constructs
- **Code completion** for keywords, variables, procedures, functions
- **Hover information** with type details
- **Go to definition** for symbols
- **Find references** across the document
- **Document outline** showing programme structure
- **Support for all CMS-2 constructs:**
  - SYS-DD/SYS-PROC blocks
  - VRBL (variable) declarations
  - TABLE/FIELD definitions
  - PROCEDURE/FUNCTION blocks
  - TYPE declarations with status values

## Installation

1. Install the extension from the VS Code Marketplace
2. Ensure Python 3.8+ is installed and available in PATH
3. Open any `.cms2`, `.cm2`, or `.cms` file

## File Extensions

| Extension | Description |
|-----------|-------------|
| `.cms2`   | CMS-2 source file |
| `.cm2`    | CMS-2 source file (alternate) |
| `.cms`    | CMS-2 source file (short) |

## Language Overview

CMS-2 uses unique syntax elements:

```cms2
''This is a comment in CMS-2''

CMODE D $  ''Set constant mode to decimal''

TESTDD SYS-DD $
    VRBL COUNTER I 16 S $       ''16-bit signed integer''
    VRBL POSITION A 32 S 16 $   ''32-bit fixed-point, 16 fractional bits''
    VRBL FLAG B $               ''Boolean''
    VRBL MESSAGE H 20 $         ''20-character string''

    TYPE MODE 'OFF', 'ON', 'AUTO' $  ''Status type''

    TABLE DATA_BUFFER V MEDIUM 100 $
        FIELD VALUE A 16 S 8 $
        FIELD STATUS I 8 U $
    END-TABLE DATA_BUFFER $
END-SYS-DD TESTDD $

TESTSP SYS-PROC $
    PROCEDURE PROCESS INPUT X OUTPUT Y $
        SET Y TO X * 2 $
        RETURN $
    END-PROC PROCESS $
END-SYS-PROC TESTSP $
```

### Key Syntax Elements

- **Statement terminator:** `$` (dollar sign)
- **Comments:** `''comment text''` (double apostrophes)
- **Type specifiers:**
  - `I bits S/U` - Integer (signed/unsigned)
  - `A bits S/U frac` - Fixed-point with fractional bits
  - `F` - Floating-point
  - `B` - Boolean
  - `H length` - Character string
- **Scope modifiers:** `(EXTDEF)`, `(EXTREF)`, `(LOCREF)`, `(TRANSREF)`
- **Packing modes:** `NONE`, `MEDIUM`, `DENSE`

## Documentation Sources

This extension was developed using official US Navy documentation:

1. **CMS-2Y Programmer's Reference Manual** (M-5049), Rev 16, October 1986
   - Fleet Combat Direction Systems Support Activity, San Diego

2. **CMS-2 Compiler and Monitor System** (AN/UYK-7), August 1975
   - UNIVAC

3. **Steps Toward a Revised CMS-2**, NPS Thesis, 1973
   - Naval Postgraduate School

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `cms2.pythonPath` | Path to Python interpreter | `python` |
| `cms2.serverPath` | Path to LSP server script | (bundled) |
| `cms2.trace.server` | Trace level for debugging | `off` |

## Requirements

- Visual Studio Code 1.75.0 or later
- Python 3.8 or later

## Known Limitations

- The parser handles common CMS-2Y constructs but may not cover all extensions
- Some legacy CMS-2M (16-bit) specific features may not be fully supported
- Real-time executive features require additional context

## Licence

Copyright 2025 Zane Hambly

Licensed under the Apache Licence, Version 2.0. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## Related Projects

If you've enjoyed programming systems that track things moving through water at high speed, you may wish to consider:

- **[JOVIAL J73 LSP](https://github.com/Zaneham/jovial-lsp)** - The US Air Force's equivalent obsession. Same era, same paranoia, different element. JOVIAL keeps things airborne; CMS-2 keeps things afloat. Synergy.

- **[CORAL 66 LSP](https://github.com/Zaneham/coral66-lsp)** - What happens when the British attempt the same thing. Features HMSO documentation, Crown Copyright, and presumably works in any weather. The Royal Navy presumably ran something similar, though they'd never admit to using American ideas.

- **[HAL/S LSP](https://github.com/Zaneham/hals-lsp)** - NASA's Space Shuttle language. For when the ocean isn't remote enough and you'd prefer your real-time constraints to include vacuum and re-entry heating.

- **[Minuteman Guidance Computer Emulator](https://github.com/Zaneham/minuteman-emu)** - An emulator for the computers in those missiles your Aegis system is meant to detect. Circle of life, really.

- **[Minuteman Assembler](https://github.com/Zaneham/minuteman-assembler)** - Two-pass assembler for the D17B/D37C. Because apparently we needed a complete toolchain for the things your ship is tracking. They're writing code; you're tracking it. Everyone has a job to do.

## Acknowledgements

- Fleet Combat Direction Systems Support Activity (FCDSSA), San Diego
- Naval Postgraduate School
- US Navy tactical systems documentation archives
