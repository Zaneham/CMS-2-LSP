# CMS-2 Language Support for Visual Studio Code

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/ZaneHambly.cms2-lsp?label=VS%20Code%20Marketplace)](https://marketplace.visualstudio.com/items?itemName=ZaneHambly.cms2-lsp)

Language Server Protocol (LSP) implementation for **CMS-2** (Compiler Monitor System 2), the programming language that has been tracking incoming missiles since 1968.

## What is CMS-2?

When something is moving towards a Navy ship at Mach 2, the computer tracking it needs to be running code that works. Not code that "should work." Not code that "works on my machine." Code that works, every time, with deterministic timing measured in microseconds.

CMS-2 was developed in 1968-1969 by Computer Sciences Corporation with Intermetrics for exactly this purpose. The US Navy needed a language for tactical combat systems—the computers that detect threats, track targets, and coordinate responses across an entire battle group.

The language is still in active use on:

- **Aegis Combat System** — The air defence system on cruisers and destroyers. When you see a Navy ship launching missiles at incoming threats in the news, the computer deciding what to shoot is running CMS-2.
- **Submarine combat control systems** — The computers tracking everything in the water around a submarine. Silence is rather important.
- **Naval Tactical Data System (NTDS)** — The network linking ships, aircraft, and shore installations into a coherent picture of the battlespace.
- **Aircraft carrier battle management** — Coordinating flight operations while simultaneously tracking the surrounding airspace and ocean.

The target computers include the AN/UYK-7 and AN/UYK-43—military-spec machines built to survive whatever the ocean and enemy action can throw at them. The AN/UYK-7 dates from 1969. Some are still running.

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
4. Your tactical combat system now has syntax highlighting

## File Extensions

| Extension | Description |
|-----------|-------------|
| `.cms2`   | CMS-2 source file |
| `.cm2`    | CMS-2 source file (alternate) |
| `.cms`    | CMS-2 source file (short) |

## Language Overview

CMS-2 has opinions. Every statement ends with a dollar sign. Comments are wrapped in double apostrophes. Variables are declared with `VRBL` because apparently "VARIABLE" was too long for 1968.

```cms2
''This is a comment in CMS-2''
''Yes, the double apostrophes are mandatory''

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

The dollar sign terminator seems odd until you remember these systems were programmed on equipment where semicolons might not survive transmission. Dollar signs are unmistakable. When your code is going onto a ship, you design for hostile environments—including the teletype.

### Key Syntax Elements

- **Statement terminator:** `$` (dollar sign, because semicolons are for civilians)
- **Comments:** `''comment text''` (double apostrophes)
- **Type specifiers:**
  - `I bits S/U` — Integer (signed/unsigned)
  - `A bits S/U frac` — Fixed-point with fractional bits (for when floating-point is too unpredictable)
  - `F` — Floating-point (for when you trust your hardware)
  - `B` — Boolean
  - `H length` — Character string (Hollerith, because it's 1968)
- **Scope modifiers:** `(EXTDEF)`, `(EXTREF)`, `(LOCREF)`, `(TRANSREF)`
- **Packing modes:** `NONE`, `MEDIUM`, `DENSE`

## Documentation Sources

This extension was developed using official US Navy documentation:

1. **CMS-2Y Programmer's Reference Manual** (M-5049), Rev 16, October 1986
   — Fleet Combat Direction Systems Support Activity, San Diego

2. **CMS-2 Compiler and Monitor System** (AN/UYK-7), August 1975
   — UNIVAC

3. **Steps Toward a Revised CMS-2**, NPS Thesis, 1973
   — Naval Postgraduate School

The M-5049 manual is a remarkable document. 800+ pages of precise specification written by people who understood that ambiguity in a programming language manual could, downstream, result in missiles going the wrong direction.

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `cms2.pythonPath` | Path to Python interpreter | `python` |
| `cms2.serverPath` | Path to LSP server script | (bundled) |
| `cms2.trace.server` | Trace level for debugging | `off` |

## Requirements

- Visual Studio Code 1.75.0 or later
- Python 3.8 or later
- Optional: Security clearance (for the interesting codebases)

## Known Limitations

- The parser handles common CMS-2Y constructs but may not cover all extensions
- Some legacy CMS-2M (16-bit) specific features may not be fully supported
- Real-time executive features require additional context
- Cannot actually track incoming missiles (this is a syntax highlighter, not Aegis)

## Licence

Copyright 2025 Zane Hambly

Licensed under the Apache Licence, Version 2.0. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Particularly:
- Syntax patterns from real CMS-2 code
- Corrections from people who actually programmed AN/UYK machines
- War stories from FCDSSA San Diego

## Related Projects

If you've enjoyed providing tooling for systems that track things moving at Mach 2, you might also appreciate:

- **[JOVIAL J73 LSP](https://github.com/Zaneham/jovial-lsp)** — The US Air Force's equivalent. Same era, same paranoia, different element. JOVIAL keeps things airborne; CMS-2 keeps things afloat.

- **[CORAL 66 LSP](https://github.com/Zaneham/coral66-lsp)** — The British approach. Tornado aircraft and Royal Navy vessels. Crown Copyright and presumably works in any weather.

- **[HAL/S LSP](https://github.com/Zaneham/hals-lsp)** — NASA's Space Shuttle language. For when the ocean isn't remote enough.

- **[MUMPS LSP](https://github.com/Zaneham/mumps-lsp)** — The language running hospital systems. Different kind of life-critical. Your medical records instead of your missile tracks.

- **[Minuteman Guidance Computer Emulator](https://github.com/Zaneham/minuteman-emu)** — An emulator for the computers in those missiles your Aegis system is meant to detect. Everyone has a job to do.

## Contact

Questions? Corrections? War stories from your time at Fleet Combat Direction Systems Support Activity?

zanehambly@gmail.com — All signals acknowledged. Response time better than NTDS latency.

## Acknowledgements

- Fleet Combat Direction Systems Support Activity (FCDSSA), San Diego
- Naval Postgraduate School
- The engineers who built systems that still work after 50 years
- US Navy tactical systems documentation archives
