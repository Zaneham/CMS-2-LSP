# CMS-2 Language Support for Visual Studio Code

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/ZaneHambly.cms2-lsp?label=VS%20Code%20Marketplace)](https://marketplace.visualstudio.com/items?itemName=ZaneHambly.cms2-lsp)

Language Server Protocol (LSP) implementation for **CMS-2** (Compiler Monitor System 2), the programming language that has been defending the fleet since 1968.

In the Navy, you can sail the seven seas. In the Navy, you can also write code in a language that terminates statements with dollar signs. The Village People did not mention this.

## What is CMS-2?

In 1968, the US Navy had a problem. They were building computerised combat systems for their ships, and they needed software. Lots of software. Software that could track hundreds of aircraft and missiles simultaneously. Software that could coordinate an entire battle group. Software that absolutely could not crash when someone was shooting at you.

They commissioned CMS-2.

The language was developed by Computer Sciences Corporation with Intermetrics, and it became the standard for Navy tactical systems. When an Aegis cruiser tracks an incoming missile and decides what to do about it, CMS-2 code is making that decision. When a submarine's combat system builds a picture of everything in the water around it, CMS-2 code is processing the sonar data. When an aircraft carrier coordinates forty aircraft across a thousand miles of ocean, CMS-2 code is keeping track.

### Systems Running CMS-2

| System | What It Does |
|--------|--------------|
| **Aegis Combat System** | Tracks and engages air threats for cruisers and destroyers. The most sophisticated surface warfare system ever built. |
| **Submarine Combat Control** | Everything a submarine needs to know about the water around it. Silence is important. |
| **Naval Tactical Data System (NTDS)** | Links ships, aircraft, and shore installations into one picture. The original tactical network. |
| **Aircraft Carrier Battle Management** | Coordinates flight operations while tracking the battlespace. Multitasking at scale. |

The Aegis system alone is worth understanding. It can track over 100 targets simultaneously, at ranges of hundreds of miles, and engage multiple threats at once. When you see footage of a Navy ship launching missiles at incoming targets, the computer deciding what to shoot, when to shoot, and where to aim is running CMS-2.

The system works. It has worked since the USS Ticonderoga was commissioned in 1983. Forty years of deployments. The code keeps running.

## The Hardware

CMS-2 was designed for the AN/UYK-7 and AN/UYK-43 computers. These aren't your typical machines.

The AN/UYK-7 entered service in 1969. It was designed to survive shipboard conditions: salt spray, vibration, shock, electromagnetic interference, and the occasional explosion nearby. The computer was built into a standard Navy equipment rack and could be maintained by sailors with specialized training.

Some AN/UYK-7s are still running. The Navy calls this "extended service life." Everyone else calls it "if it ain't broke, don't fix it."

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

CMS-2 has opinions. Strong opinions. Every statement ends with a dollar sign. Comments are wrapped in double apostrophes. Variables are declared with `VRBL` because apparently `VARIABLE` was too long for 1968.

```cms2
''This is a comment in CMS-2''
''The double apostrophes are not negotiable''

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

The dollar sign terminator seems odd until you think about 1968. These systems were programmed on equipment where a semicolon might get corrupted in transmission or lost in a punch card. A dollar sign is unmistakable. When your code is going onto a warship, you design for hostile conditions. The enemy isn't just the other navy; it's also the salt air.

### Key Syntax Elements

- **Statement terminator:** `$` (dollar sign, because semicolons are for civilians)
- **Comments:** `''comment text''` (double apostrophes)
- **Type specifiers:**
  - `I bits S/U` for integers (signed/unsigned)
  - `A bits S/U frac` for fixed-point with fractional bits
  - `F` for floating-point (when you trust the hardware)
  - `B` for Boolean
  - `H length` for character strings (Hollerith, because it's 1968)
- **Scope modifiers:** `(EXTDEF)`, `(EXTREF)`, `(LOCREF)`, `(TRANSREF)`
- **Packing modes:** `NONE`, `MEDIUM`, `DENSE`

Fixed-point arithmetic (`A` type) is used heavily in CMS-2. When you're tracking a target moving at Mach 2, you need predictable timing. Floating-point units in 1968 had variable execution times. Fixed-point doesn't. The extra complexity in the code bought determinism in the execution.

## Documentation Sources

This extension was developed using official US Navy documentation:

1. **CMS-2Y Programmer's Reference Manual** (M-5049), Rev 16, October 1986
   - Fleet Combat Direction Systems Support Activity, San Diego
   - 800+ pages of precise specification

2. **CMS-2 Compiler and Monitor System** (AN/UYK-7), August 1975
   - UNIVAC
   - How the compiler actually works

3. **Steps Toward a Revised CMS-2**, NPS Thesis, 1973
   - Naval Postgraduate School
   - Academic analysis of the language design

The M-5049 manual is remarkable. It was written by people who understood that ambiguity in a programming language manual could, downstream, result in missiles going the wrong direction. Every edge case is specified. Every undefined behavior is defined.

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

## Why This Matters

The Navy doesn't talk much about its software. For obvious reasons. But the systems keep running, the ships keep sailing, and somewhere in San Diego, engineers at the Fleet Combat Direction Systems Support Activity are still maintaining CMS-2 code.

The people who wrote the original Aegis software are retiring. The AN/UYK-7 documentation lives in archives and filing cabinets. But the DDG-51 destroyers are still deploying, and they're still running software in a language that most programmers have never heard of.

Someone needs to maintain this code. They shouldn't have to do it without syntax highlighting.

## Licence

Copyright 2025 Zane Hambly

Licensed under the Apache Licence, Version 2.0. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome. Particularly:
- Syntax patterns from real CMS-2 code
- Corrections from people who programmed AN/UYK systems
- War stories from FCDSSA San Diego

## Related Projects

If you've enjoyed providing tooling for systems that track things moving at Mach 2, you might also appreciate:

- **[JOVIAL J73 LSP](https://github.com/Zaneham/jovial-lsp)** - The US Air Force's equivalent. Same era, same paranoia, different element. JOVIAL keeps things airborne; CMS-2 keeps things afloat.

- **[CORAL 66 LSP](https://github.com/Zaneham/coral66-lsp)** - The Royal Navy runs different software, but the problems are the same. British engineering. Crown Copyright. Presumably works in drizzle.

- **[HAL/S LSP](https://github.com/Zaneham/hals-lsp)** - NASA's Space Shuttle language. For when the ocean isn't remote enough.

- **[MUMPS LSP](https://github.com/Zaneham/mumps-lsp)** - The language running hospital systems. Different kind of critical. Your medical records instead of your missile tracks.

- **[Minuteman Guidance Computer Emulator](https://github.com/Zaneham/minuteman-emu)** - An emulator for the computers in those missiles your Aegis system is tracking. Circle of life, really.

## Contact

Questions? Corrections? War stories from your time at Fleet Combat Direction Systems Support Activity?

zanehambly@gmail.com

All signals acknowledged. Response time better than NTDS latency. Available to discuss tactical data systems over coffee, though I can neither confirm nor deny anything classified.

## Acknowledgements

- Fleet Combat Direction Systems Support Activity (FCDSSA), San Diego
- Naval Postgraduate School
- The engineers who built Aegis
- The sailors who operate it
- Everyone who maintains code on systems that actually matter

---

*"They want you, they want you, they want you as a new recruit. They want you to write CMS-2. OCEANOGRAPHY WHAT?!"*
