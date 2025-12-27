"""
CMS-2 (Compiler Monitor System 2) Semantic Parser
Builds AST and Semantic Model for Navy Tactical Combat Systems Language

CMS-2 is the US Navy's standard programming language for tactical combat
systems, running on Aegis cruisers, submarines, and carriers since 1968.

Based on CMS-2Y Programmer's Reference Manual (M-5049) Rev 16, October 1986
Fleet Combat Direction Systems Support Activity, San Diego
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class CMS2Type(Enum):
    """CMS-2 data types (modes)"""
    INTEGER = "I"           # Integer (I bits S/U)
    FIXED = "A"             # Fixed-point (A bits S/U frac)
    FLOAT = "F"             # Floating-point (F, F(T), F(R), F(S), F(D))
    BOOLEAN = "B"           # Boolean (single bit)
    CHAR = "H"              # Character (H length or C length)
    STATUS = "STATUS"       # Status (enumeration)
    UNIVERSAL = "UNIV"      # Universal type (bit string)
    TABLE = "TABLE"         # Table type
    UNKNOWN = "UNKNOWN"


@dataclass
class VariableDefinition:
    """Represents a CMS-2 VRBL (variable) declaration"""
    name: str
    var_type: CMS2Type
    bits: Optional[int] = None           # Bit length for I, A types
    signed: bool = True                  # S = signed, U = unsigned
    frac_bits: Optional[int] = None      # Fractional bits for A type
    char_length: Optional[int] = None    # Length for H/C type
    status_values: List[str] = field(default_factory=list)  # For STATUS type
    is_preset: bool = False              # Has preset value
    preset_value: Optional[str] = None
    modifier: Optional[str] = None       # EXTDEF, EXTREF, LOCREF, TRANSREF
    line_number: int = 0
    column_start: int = 0
    column_end: int = 0
    parent_block: Optional[str] = None


@dataclass
class TableDefinition:
    """Represents a CMS-2 TABLE declaration"""
    name: str
    table_type: str = "V"                # V = vertical, H = horizontal
    packing: str = "NONE"                # NONE, MEDIUM, DENSE
    item_count: Optional[int] = None     # Number of items
    item_typed: bool = False             # Is item-typed (has type spec)
    type_spec: Optional[str] = None      # Type specification
    fields: Dict[str, 'FieldDefinition'] = field(default_factory=dict)
    is_indirect: bool = False
    major_index: Optional[str] = None    # Major index variable
    modifier: Optional[str] = None
    line_start: int = 0
    line_end: int = 0


@dataclass
class FieldDefinition:
    """Represents a CMS-2 FIELD declaration within a TABLE"""
    name: str
    field_type: CMS2Type
    bits: Optional[int] = None
    signed: bool = True
    frac_bits: Optional[int] = None
    char_length: Optional[int] = None
    start_word: Optional[int] = None     # User-packed position
    start_bit: Optional[int] = None      # User-packed position
    preset_values: List[str] = field(default_factory=list)
    line_number: int = 0
    parent_table: Optional[str] = None


@dataclass
class ProcedureDefinition:
    """Represents a CMS-2 PROCEDURE declaration"""
    name: str
    is_exec: bool = False                # EXEC-PROC
    input_params: List[str] = field(default_factory=list)
    output_params: List[str] = field(default_factory=list)
    exit_params: List[str] = field(default_factory=list)
    modifier: Optional[str] = None       # EXTDEF, EXTREF, LOCREF, TRANSREF
    local_vars: Dict[str, VariableDefinition] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0
    body_start: int = 0


@dataclass
class FunctionDefinition:
    """Represents a CMS-2 FUNCTION declaration"""
    name: str
    input_params: List[str] = field(default_factory=list)
    return_type: Optional[str] = None    # Type specification
    modifier: Optional[str] = None
    local_vars: Dict[str, VariableDefinition] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0


@dataclass
class TypeDefinition:
    """Represents a CMS-2 TYPE declaration"""
    name: str
    base_type: Optional[str] = None
    packing: str = "NONE"
    status_values: List[str] = field(default_factory=list)
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0


@dataclass
class SystemDataBlock:
    """Represents a CMS-2 SYS-DD block"""
    name: str
    variables: Dict[str, VariableDefinition] = field(default_factory=dict)
    tables: Dict[str, TableDefinition] = field(default_factory=dict)
    types: Dict[str, TypeDefinition] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0


@dataclass
class SystemProcBlock:
    """Represents a CMS-2 SYS-PROC block"""
    name: str
    is_reentrant: bool = False           # SYS-PROC-REN
    procedures: Dict[str, ProcedureDefinition] = field(default_factory=dict)
    functions: Dict[str, FunctionDefinition] = field(default_factory=dict)
    local_data: Dict[str, VariableDefinition] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0


class CMS2SemanticModel:
    """
    Semantic model of a CMS-2 program
    Tracks variables, tables, procedures, functions, and system blocks
    """

    def __init__(self):
        self.variables: Dict[str, VariableDefinition] = {}
        self.tables: Dict[str, TableDefinition] = {}
        self.types: Dict[str, TypeDefinition] = {}
        self.procedures: Dict[str, ProcedureDefinition] = {}
        self.functions: Dict[str, FunctionDefinition] = {}
        self.sys_data_blocks: Dict[str, SystemDataBlock] = {}
        self.sys_proc_blocks: Dict[str, SystemProcBlock] = {}

        self.current_scope: str = "GLOBAL"
        self.scope_stack: List[str] = []
        self.constant_mode: str = "D"    # D = decimal, O = octal

    def add_variable(self, var: VariableDefinition):
        """Add a variable definition"""
        key = f"{self.current_scope}.{var.name}" if self.current_scope != "GLOBAL" else var.name
        self.variables[var.name] = var
        self.variables[key] = var

    def get_variable(self, name: str) -> Optional[VariableDefinition]:
        """Get variable by name, checking scopes"""
        scoped_name = f"{self.current_scope}.{name}"
        if scoped_name in self.variables:
            return self.variables[scoped_name]
        if name in self.variables:
            return self.variables[name]
        return None

    def add_table(self, table: TableDefinition):
        """Add a table definition"""
        self.tables[table.name] = table

    def get_table(self, name: str) -> Optional[TableDefinition]:
        """Get table by name"""
        return self.tables.get(name)

    def add_procedure(self, proc: ProcedureDefinition):
        """Add a procedure definition"""
        self.procedures[proc.name] = proc

    def get_procedure(self, name: str) -> Optional[ProcedureDefinition]:
        """Get procedure by name"""
        return self.procedures.get(name)

    def add_function(self, func: FunctionDefinition):
        """Add a function definition"""
        self.functions[func.name] = func

    def get_function(self, name: str) -> Optional[FunctionDefinition]:
        """Get function by name"""
        return self.functions.get(name)

    def add_type(self, typedef: TypeDefinition):
        """Add a type definition"""
        self.types[typedef.name] = typedef

    def get_type(self, name: str) -> Optional[TypeDefinition]:
        """Get type by name"""
        return self.types.get(name)

    def get_all_symbols(self) -> List[str]:
        """Get all symbol names for completion"""
        symbols = []
        symbols.extend(self.variables.keys())
        symbols.extend(self.tables.keys())
        symbols.extend(self.procedures.keys())
        symbols.extend(self.functions.keys())
        symbols.extend(self.types.keys())
        return list(set(s for s in symbols if '.' not in s))


class CMS2SemanticParser:
    """
    Parses CMS-2 code and builds a semantic model
    Based on CMS-2Y Reference Manual (M-5049)
    """

    # CMS-2 Reserved Words (from manual Section 3.3)
    RESERVED_WORDS = {
        'ABS', 'ALG', 'AND', 'BASE', 'BEGIN', 'BIT', 'BY', 'CAT', 'CHAR',
        'CHECKID', 'CIRC', 'CLOSE', 'CMODE', 'COMMENT', 'COMP', 'CORAD',
        'CORRECT', 'CSWITCH', 'DATA', 'DATAPOOL', 'DEBUG', 'DECODE',
        'DEFID', 'DENSE', 'DEP', 'DIRECT', 'DISPLAY', 'ELSE', 'ELSIF',
        'ENCODE', 'END', 'ENDFILE', 'EQ', 'EQUALS', 'EVENP', 'EXCHANGE',
        'EXEC', 'EXIT', 'FIELD', 'FILE', 'FIND', 'FOR', 'FORMAT', 'FROM',
        'FUNCTION', 'GOTO', 'GT', 'GTEQ', 'HEAD', 'IF', 'INDIRECT',
        'INPUT', 'INTO', 'INVALID', 'LIBS', 'LOG', 'LT', 'LTEQ', 'MEANS',
        'MEDIUM', 'MODE', 'NITEMS', 'NONE', 'NOT', 'OCM', 'OODP', 'OPEN',
        'OPTIONS', 'OR', 'OUTPUT', 'OVERFLOW', 'OVERLAY', 'PRINT', 'PTRACE',
        'PUNCH', 'RANGE', 'READ', 'REGS', 'RESUME', 'RETURN', 'SAVING',
        'SET', 'SHIFT', 'SNAP', 'SPILL', 'STOP', 'SWAP', 'SWITCH', 'SYSTEM',
        'TABLE', 'THEN', 'THRU', 'TO', 'TRACE', 'TYPE', 'UNTIL', 'USING',
        'VALID', 'VARY', 'VARYING', 'VRBL', 'WHILE', 'WITH', 'WITHIN', 'XOR',
        # Additional keywords
        'SYS-DD', 'SYS-PROC', 'SYS-PROC-REN', 'END-SYS-DD', 'END-SYS-PROC',
        'LOC-DD', 'END-LOC-DD', 'AUTO-DD', 'END-AUTO-DD',
        'PROCEDURE', 'END-PROC', 'EXEC-PROC', 'END-FUNCTION',
        'END-TABLE', 'END-TYPE', 'END-SWITCH',
        'EXTDEF', 'EXTREF', 'LOCREF', 'TRANSREF',
        'CONVERTIN', 'CONVERTOUT', 'STRINGFORM', 'INPUTLIST', 'OUTPUTLIST',
        'P-SWITCH', 'END-P-SW', 'L-SWITCH', 'SYS-INDEX', 'LOC-INDEX',
        'LOAD-VRBL', 'NOTFOUND', 'FOUND', 'CASE', 'LOOP', 'KEY1', 'KEY2', 'KEY3',
    }

    # Predefined function names (universal scope)
    PREDEFINED_FUNCTIONS = {
        'ACDS2', 'BAMS', 'FIRST', 'DRF', 'SCALF', 'ACDS', 'CNT', 'ICDS',
        'POS', 'SIN', 'ALDG', 'COMPF', 'IEXP', 'PRED', 'SUCC', 'ANDF',
        'CONF', 'ISIN', 'RAD', 'TDEF', 'ASIN2', 'COS', 'LAST', 'ROTATEHP',
        'VECTORHP', 'ASIN', 'EXP', 'LENGTH', 'REM', 'VECTORP', 'ATAN2',
        'FIL', 'LN', 'ROTATEP', 'XORF', 'ATAN', 'ICOS', 'ALOG', 'ACOS',
        'ACOS2',
    }

    # Status constant pattern 'VALUE'
    STATUS_VALUE_PATTERN = re.compile(r"'([A-Z][A-Z0-9]*)'", re.IGNORECASE)

    def __init__(self):
        self.model = CMS2SemanticModel()
        self.lines: List[str] = []
        self.current_line_num = 0

        # Parser state
        self.in_sys_dd = False
        self.current_sys_dd: Optional[str] = None
        self.in_sys_proc = False
        self.current_sys_proc: Optional[str] = None
        self.in_table_block = False
        self.current_table: Optional[str] = None
        self.in_type_block = False
        self.current_type: Optional[str] = None
        self.in_procedure = False
        self.current_procedure: Optional[str] = None
        self.in_function = False
        self.current_function: Optional[str] = None
        self.in_loc_dd = False

    def parse(self, cms2_code: str) -> CMS2SemanticModel:
        """
        Parse CMS-2 code and return semantic model
        """
        self.model = CMS2SemanticModel()
        self.lines = cms2_code.split('\n')
        self.current_line_num = 0

        # Reset state
        self._reset_state()

        # Multi-statement buffer (CMS-2 statements end with $)
        statement_buffer = ""

        for i, line in enumerate(self.lines):
            self.current_line_num = i

            # Remove comments ('' to '' in CMS-2)
            line = self._remove_comments(line)

            stripped = line.strip()
            if not stripped:
                continue

            # Accumulate multi-line statements
            statement_buffer += " " + stripped

            # Check if statement is complete (ends with $)
            while '$' in statement_buffer:
                dollar_pos = statement_buffer.find('$')
                statement = statement_buffer[:dollar_pos].strip()
                statement_buffer = statement_buffer[dollar_pos + 1:].strip()

                if statement:
                    self._parse_statement(statement, i)

        return self.model

    def _reset_state(self):
        """Reset parser state"""
        self.in_sys_dd = False
        self.current_sys_dd = None
        self.in_sys_proc = False
        self.current_sys_proc = None
        self.in_table_block = False
        self.current_table = None
        self.in_type_block = False
        self.current_type = None
        self.in_procedure = False
        self.current_procedure = None
        self.in_function = False
        self.current_function = None
        self.in_loc_dd = False

    def _remove_comments(self, line: str) -> str:
        """Remove CMS-2 comments (enclosed in double apostrophes)"""
        result = []
        in_comment = False
        i = 0
        while i < len(line):
            if i + 1 < len(line) and line[i:i+2] == "''":
                in_comment = not in_comment
                i += 2
            elif not in_comment:
                result.append(line[i])
                i += 1
            else:
                i += 1
        return ''.join(result)

    def _parse_statement(self, statement: str, line_num: int):
        """Parse a complete statement (ending with $)"""
        upper = statement.upper().strip()

        # System structure
        if 'SYS-DD' in upper and 'END-SYS-DD' not in upper:
            self._parse_sys_dd_start(statement, line_num)
        elif 'END-SYS-DD' in upper:
            self._handle_end_sys_dd(statement, line_num)
        elif 'SYS-PROC' in upper and 'END-SYS-PROC' not in upper:
            self._parse_sys_proc_start(statement, line_num)
        elif 'END-SYS-PROC' in upper:
            self._handle_end_sys_proc(statement, line_num)
        elif upper.startswith('LOC-DD') or ' LOC-DD' in upper:
            self.in_loc_dd = True
        elif 'END-LOC-DD' in upper:
            self.in_loc_dd = False

        # Declarations
        elif upper.startswith('VRBL') or ' VRBL ' in upper or upper.startswith('(EXTDEF) VRBL') \
                or upper.startswith('(EXTREF) VRBL') or upper.startswith('(LOCREF) VRBL') \
                or upper.startswith('(TRANSREF) VRBL'):
            self._parse_vrbl_declaration(statement, line_num)
        elif upper.startswith('TABLE') or ' TABLE ' in upper:
            self._parse_table_declaration(statement, line_num)
        elif 'END-TABLE' in upper:
            self._handle_end_table(statement, line_num)
        elif upper.startswith('FIELD'):
            self._parse_field_declaration(statement, line_num)
        elif upper.startswith('TYPE') and 'END-TYPE' not in upper:
            self._parse_type_declaration(statement, line_num)
        elif 'END-TYPE' in upper:
            self._handle_end_type(statement, line_num)
        elif upper.startswith('PROCEDURE') or ' PROCEDURE ' in upper \
                or upper.startswith('(EXTDEF) PROCEDURE') or upper.startswith('(EXTREF) PROCEDURE'):
            self._parse_procedure_declaration(statement, line_num)
        elif upper.startswith('EXEC-PROC') or ' EXEC-PROC ' in upper:
            self._parse_exec_proc_declaration(statement, line_num)
        elif 'END-PROC' in upper:
            self._handle_end_proc(statement, line_num)
        elif upper.startswith('FUNCTION') or ' FUNCTION ' in upper:
            self._parse_function_declaration(statement, line_num)
        elif 'END-FUNCTION' in upper:
            self._handle_end_function(statement, line_num)
        elif upper.startswith('CMODE'):
            self._parse_cmode(statement, line_num)

    def _parse_sys_dd_start(self, statement: str, line_num: int):
        """Parse SYS-DD block start"""
        # Pattern: <name> SYS-DD $
        match = re.match(r'([A-Z][A-Z0-9_]*)\s+SYS-DD', statement, re.IGNORECASE)
        if match:
            name = match.group(1).upper()
            block = SystemDataBlock(name=name, line_start=line_num)
            self.model.sys_data_blocks[name] = block
            self.current_sys_dd = name
            self.in_sys_dd = True
            self.model.current_scope = name

    def _handle_end_sys_dd(self, statement: str, line_num: int):
        """Handle END-SYS-DD"""
        if self.current_sys_dd and self.current_sys_dd in self.model.sys_data_blocks:
            self.model.sys_data_blocks[self.current_sys_dd].line_end = line_num
        self.in_sys_dd = False
        self.current_sys_dd = None
        self.model.current_scope = "GLOBAL"

    def _parse_sys_proc_start(self, statement: str, line_num: int):
        """Parse SYS-PROC block start"""
        # Pattern: <name> SYS-PROC $ or <name> SYS-PROC-REN $
        is_reentrant = 'SYS-PROC-REN' in statement.upper()
        match = re.match(r'([A-Z][A-Z0-9_]*)\s+SYS-PROC', statement, re.IGNORECASE)
        if match:
            name = match.group(1).upper()
            block = SystemProcBlock(name=name, is_reentrant=is_reentrant, line_start=line_num)
            self.model.sys_proc_blocks[name] = block
            self.current_sys_proc = name
            self.in_sys_proc = True
            self.model.current_scope = name

    def _handle_end_sys_proc(self, statement: str, line_num: int):
        """Handle END-SYS-PROC"""
        if self.current_sys_proc and self.current_sys_proc in self.model.sys_proc_blocks:
            self.model.sys_proc_blocks[self.current_sys_proc].line_end = line_num
        self.in_sys_proc = False
        self.current_sys_proc = None
        self.model.current_scope = "GLOBAL"

    def _parse_vrbl_declaration(self, statement: str, line_num: int):
        """Parse VRBL (variable) declaration"""
        # Patterns:
        # VRBL name I bits S|U $
        # VRBL name A bits S|U frac $
        # VRBL name F $
        # VRBL name B $
        # VRBL name H chars $ or VRBL name C chars $
        # VRBL (name1, name2) type $
        # (EXTDEF) VRBL name type $

        stmt = statement.strip()

        # Check for modifier
        modifier = None
        for mod in ['(EXTDEF)', '(EXTREF)', '(LOCREF)', '(TRANSREF)']:
            if stmt.upper().startswith(mod):
                modifier = mod[1:-1]  # Remove parentheses
                stmt = stmt[len(mod):].strip()
                break

        # Handle multiple names in parentheses: VRBL (A, B, C) type
        multi_match = re.match(
            r'VRBL\s*\(([^)]+)\)\s+(.+)',
            stmt, re.IGNORECASE
        )
        if multi_match:
            names = [n.strip() for n in multi_match.group(1).split(',')]
            type_spec = multi_match.group(2).strip()
            for name in names:
                self._create_variable(name, type_spec, modifier, line_num)
            return

        # Single name pattern: VRBL name type
        single_match = re.match(
            r'VRBL\s+([A-Z][A-Z0-9_]*)\s+(.+)',
            stmt, re.IGNORECASE
        )
        if single_match:
            name = single_match.group(1).upper()
            type_spec = single_match.group(2).strip()
            self._create_variable(name, type_spec, modifier, line_num)

    def _create_variable(self, name: str, type_spec: str, modifier: Optional[str], line_num: int):
        """Create a variable definition from type specification"""
        var_type = CMS2Type.UNKNOWN
        bits = None
        signed = True
        frac_bits = None
        char_length = None
        status_values = []
        preset_value = None

        # Parse type specification
        type_upper = type_spec.upper().strip()

        # Integer: I bits S|U
        int_match = re.match(r'I\s+(\d+)\s+(S|U)', type_upper)
        if int_match:
            var_type = CMS2Type.INTEGER
            bits = int(int_match.group(1))
            signed = int_match.group(2) == 'S'

        # Fixed-point: A bits S|U frac
        fixed_match = re.match(r'A\s+(\d+)\s+(S|U)\s+(\d+)', type_upper)
        if fixed_match:
            var_type = CMS2Type.FIXED
            bits = int(fixed_match.group(1))
            signed = fixed_match.group(2) == 'S'
            frac_bits = int(fixed_match.group(3))

        # Floating-point: F or F(T|R|S|D)
        float_match = re.match(r'F(\s*\([TRSD]\))?', type_upper)
        if float_match and not int_match and not fixed_match:
            var_type = CMS2Type.FLOAT

        # Boolean: B
        if type_upper.startswith('B') and not type_upper.startswith('BY'):
            var_type = CMS2Type.BOOLEAN

        # Character: H length or C length
        char_match = re.match(r'[HC]\s*(\d+)', type_upper)
        if char_match:
            var_type = CMS2Type.CHAR
            char_length = int(char_match.group(1))

        # Status: S 'val1', 'val2', ... or status values
        if "'" in type_spec:
            status_values = self.STATUS_VALUE_PATTERN.findall(type_spec)
            if status_values:
                var_type = CMS2Type.STATUS

        # Check for preset value (P value)
        preset_match = re.search(r'\bP\s+(.+?)(?:\s|$)', type_spec, re.IGNORECASE)
        if preset_match:
            preset_value = preset_match.group(1)

        var = VariableDefinition(
            name=name,
            var_type=var_type,
            bits=bits,
            signed=signed,
            frac_bits=frac_bits,
            char_length=char_length,
            status_values=status_values,
            is_preset=preset_value is not None,
            preset_value=preset_value,
            modifier=modifier,
            line_number=line_num,
            parent_block=self.current_sys_dd or self.current_sys_proc
        )

        self.model.add_variable(var)

        # Add to current block if applicable
        if self.current_sys_dd and self.current_sys_dd in self.model.sys_data_blocks:
            self.model.sys_data_blocks[self.current_sys_dd].variables[name] = var
        if self.current_procedure and self.current_procedure in self.model.procedures:
            self.model.procedures[self.current_procedure].local_vars[name] = var

    def _parse_table_declaration(self, statement: str, line_num: int):
        """Parse TABLE declaration"""
        # Pattern: TABLE name V|H [packing] [type] count $
        stmt = statement.strip()

        match = re.match(
            r'TABLE\s+([A-Z][A-Z0-9_]*)\s+'
            r'([VH])\s*'
            r'(NONE|MEDIUM|DENSE)?\s*'
            r'(?:\(([^)]+)\))?\s*'
            r'(?:INDIRECT\s+)?'
            r'(\d+|[A-Z][A-Z0-9_]*)?',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1).upper()
            table_type = match.group(2).upper() if match.group(2) else 'V'
            packing = match.group(3).upper() if match.group(3) else 'NONE'
            type_spec = match.group(4) if match.group(4) else None
            count_str = match.group(5) if match.group(5) else None

            item_count = None
            if count_str and count_str.isdigit():
                item_count = int(count_str)

            is_indirect = 'INDIRECT' in stmt.upper()

            # Check for major index (MJ name)
            major_index = None
            mj_match = re.search(r'\bMJ\s+([A-Z][A-Z0-9]*)', stmt, re.IGNORECASE)
            if mj_match:
                major_index = mj_match.group(1).upper()

            table = TableDefinition(
                name=name,
                table_type=table_type,
                packing=packing,
                item_count=item_count,
                item_typed=type_spec is not None,
                type_spec=type_spec,
                is_indirect=is_indirect,
                major_index=major_index,
                line_start=line_num
            )

            self.model.add_table(table)
            self.current_table = name
            self.in_table_block = True

            if self.current_sys_dd and self.current_sys_dd in self.model.sys_data_blocks:
                self.model.sys_data_blocks[self.current_sys_dd].tables[name] = table

    def _handle_end_table(self, statement: str, line_num: int):
        """Handle END-TABLE"""
        if self.current_table and self.current_table in self.model.tables:
            self.model.tables[self.current_table].line_end = line_num
        self.in_table_block = False
        self.current_table = None

    def _parse_field_declaration(self, statement: str, line_num: int):
        """Parse FIELD declaration within TABLE"""
        # Pattern: FIELD name type [word bit] [P preset] $
        stmt = statement.strip()

        match = re.match(
            r'FIELD\s+([A-Z][A-Z0-9_]*)\s+'
            r'([IAFBHC])\s*'
            r'(\d+)?\s*'
            r'(S|U)?\s*'
            r'(\d+)?\s*'
            r'(?:(\d+)\s+(\d+))?\s*'  # word bit
            r'(?:P\s+(.+))?',
            stmt, re.IGNORECASE
        )

        if match and self.current_table:
            name = match.group(1).upper()
            type_char = match.group(2).upper()
            bits = int(match.group(3)) if match.group(3) else None
            signed = match.group(4) != 'U' if match.group(4) else True
            frac_bits = int(match.group(5)) if match.group(5) else None
            start_word = int(match.group(6)) if match.group(6) else None
            start_bit = int(match.group(7)) if match.group(7) else None
            preset = match.group(8)

            type_map = {
                'I': CMS2Type.INTEGER,
                'A': CMS2Type.FIXED,
                'F': CMS2Type.FLOAT,
                'B': CMS2Type.BOOLEAN,
                'H': CMS2Type.CHAR,
                'C': CMS2Type.CHAR,
            }
            field_type = type_map.get(type_char, CMS2Type.UNKNOWN)

            field = FieldDefinition(
                name=name,
                field_type=field_type,
                bits=bits,
                signed=signed,
                frac_bits=frac_bits,
                char_length=bits if type_char in ('H', 'C') else None,
                start_word=start_word,
                start_bit=start_bit,
                preset_values=[preset] if preset else [],
                line_number=line_num,
                parent_table=self.current_table
            )

            if self.current_table in self.model.tables:
                self.model.tables[self.current_table].fields[name] = field

    def _parse_type_declaration(self, statement: str, line_num: int):
        """Parse TYPE declaration"""
        # Pattern: TYPE name packing $ ... END-TYPE name $
        # or TYPE name 'val1', 'val2', ... $ (status type)
        stmt = statement.strip()

        # Status type
        if "'" in stmt:
            match = re.match(r'TYPE\s+([A-Z][A-Z0-9_]*)\s+(.+)', stmt, re.IGNORECASE)
            if match:
                name = match.group(1).upper()
                rest = match.group(2)
                status_values = self.STATUS_VALUE_PATTERN.findall(rest)

                typedef = TypeDefinition(
                    name=name,
                    status_values=status_values,
                    line_start=line_num
                )
                self.model.add_type(typedef)
                if self.current_sys_dd and self.current_sys_dd in self.model.sys_data_blocks:
                    self.model.sys_data_blocks[self.current_sys_dd].types[name] = typedef
        else:
            # Structured type
            match = re.match(
                r'TYPE\s+([A-Z][A-Z0-9_]*)\s*(NONE|MEDIUM|DENSE)?',
                stmt, re.IGNORECASE
            )
            if match:
                name = match.group(1).upper()
                packing = match.group(2).upper() if match.group(2) else 'NONE'

                typedef = TypeDefinition(
                    name=name,
                    packing=packing,
                    line_start=line_num
                )
                self.model.add_type(typedef)
                self.current_type = name
                self.in_type_block = True

    def _handle_end_type(self, statement: str, line_num: int):
        """Handle END-TYPE"""
        if self.current_type and self.current_type in self.model.types:
            self.model.types[self.current_type].line_end = line_num
        self.in_type_block = False
        self.current_type = None

    def _parse_procedure_declaration(self, statement: str, line_num: int):
        """Parse PROCEDURE declaration"""
        # Pattern: [modifier] PROCEDURE name [INPUT params] [OUTPUT params] [EXIT params] $
        stmt = statement.strip()

        # Check for modifier
        modifier = None
        for mod in ['(EXTDEF)', '(EXTREF)', '(LOCREF)', '(TRANSREF)']:
            if stmt.upper().startswith(mod):
                modifier = mod[1:-1]
                stmt = stmt[len(mod):].strip()
                break

        match = re.match(
            r'PROCEDURE\s+([A-Z][A-Z0-9_]*)\s*'
            r'(?:INPUT\s+(.*?))?'
            r'(?:\s+OUTPUT\s+(.*?))?'
            r'(?:\s+EXIT\s+(.*))?',
            stmt, re.IGNORECASE | re.DOTALL
        )

        if match:
            name = match.group(1).upper()
            input_str = match.group(2) or ""
            output_str = match.group(3) or ""
            exit_str = match.group(4) or ""

            input_params = [p.strip().upper() for p in input_str.split(',') if p.strip()]
            output_params = [p.strip().upper() for p in output_str.split(',') if p.strip()]
            exit_params = [p.strip().upper() for p in exit_str.split(',') if p.strip()]

            proc = ProcedureDefinition(
                name=name,
                is_exec=False,
                input_params=input_params,
                output_params=output_params,
                exit_params=exit_params,
                modifier=modifier,
                line_start=line_num
            )

            self.model.add_procedure(proc)
            self.current_procedure = name
            self.in_procedure = True

            if self.current_sys_proc and self.current_sys_proc in self.model.sys_proc_blocks:
                self.model.sys_proc_blocks[self.current_sys_proc].procedures[name] = proc

    def _parse_exec_proc_declaration(self, statement: str, line_num: int):
        """Parse EXEC-PROC (executive procedure) declaration"""
        stmt = statement.strip()

        modifier = None
        for mod in ['(EXTDEF)', '(EXTREF)']:
            if stmt.upper().startswith(mod):
                modifier = mod[1:-1]
                stmt = stmt[len(mod):].strip()
                break

        match = re.match(
            r'EXEC-PROC\s+([A-Z][A-Z0-9_]*)\s*'
            r'(?:INPUT\s+([^$]*))?',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1).upper()
            input_str = match.group(2) or ""
            input_params = [p.strip().upper() for p in input_str.split(',') if p.strip()]

            proc = ProcedureDefinition(
                name=name,
                is_exec=True,
                input_params=input_params,
                modifier=modifier,
                line_start=line_num
            )

            self.model.add_procedure(proc)
            self.current_procedure = name
            self.in_procedure = True

    def _handle_end_proc(self, statement: str, line_num: int):
        """Handle END-PROC"""
        if self.current_procedure and self.current_procedure in self.model.procedures:
            self.model.procedures[self.current_procedure].line_end = line_num
        self.in_procedure = False
        self.current_procedure = None

    def _parse_function_declaration(self, statement: str, line_num: int):
        """Parse FUNCTION declaration"""
        # Pattern: [modifier] FUNCTION name ([params]) [type] $
        stmt = statement.strip()

        modifier = None
        for mod in ['(EXTDEF)', '(EXTREF)', '(LOCREF)', '(TRANSREF)']:
            if stmt.upper().startswith(mod):
                modifier = mod[1:-1]
                stmt = stmt[len(mod):].strip()
                break

        match = re.match(
            r'FUNCTION\s+([A-Z][A-Z0-9_]*)\s*'
            r'\(([^)]*)\)\s*'
            r'(.+)?',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1).upper()
            params_str = match.group(2) or ""
            return_type = match.group(3).strip() if match.group(3) else None

            input_params = [p.strip().upper() for p in params_str.split(',') if p.strip()]

            func = FunctionDefinition(
                name=name,
                input_params=input_params,
                return_type=return_type,
                modifier=modifier,
                line_start=line_num
            )

            self.model.add_function(func)
            self.current_function = name
            self.in_function = True

    def _handle_end_function(self, statement: str, line_num: int):
        """Handle END-FUNCTION"""
        if self.current_function and self.current_function in self.model.functions:
            self.model.functions[self.current_function].line_end = line_num
        self.in_function = False
        self.current_function = None

    def _parse_cmode(self, statement: str, line_num: int):
        """Parse CMODE (constant mode) declaration"""
        if 'O' in statement.upper():
            self.model.constant_mode = 'O'  # Octal
        else:
            self.model.constant_mode = 'D'  # Decimal

    def get_completions_at_position(self, line: int, column: int) -> List[str]:
        """Get completion suggestions at a specific position"""
        if line < 0 or line >= len(self.lines):
            return []

        current_line = self.lines[line]
        prefix = current_line[:column].strip().split()[-1] if current_line[:column].strip() else ""
        prefix = prefix.upper()

        completions = []

        # Add keywords
        for kw in self.RESERVED_WORDS:
            if not prefix or kw.startswith(prefix):
                completions.append(kw)

        # Add predefined functions
        for func in self.PREDEFINED_FUNCTIONS:
            if not prefix or func.startswith(prefix):
                completions.append(func)

        # Add symbols from model
        for symbol in self.model.get_all_symbols():
            if not prefix or symbol.upper().startswith(prefix):
                completions.append(symbol)

        return sorted(set(completions))

    def get_hover_info(self, line: int, column: int) -> Optional[Dict]:
        """Get hover information at a specific position"""
        if line < 0 or line >= len(self.lines):
            return None

        current_line = self.lines[line]

        # Find word at position
        word_match = None
        for match in re.finditer(r"\b([A-Z][A-Z0-9]*)\b", current_line, re.IGNORECASE):
            if match.start() <= column <= match.end():
                word_match = match
                break

        if not word_match:
            return None

        word = word_match.group(1).upper()

        # Check if it's a variable
        var = self.model.get_variable(word)
        if var:
            type_str = self._format_type(var)
            return {
                'type': 'variable',
                'name': var.name,
                'cms2_type': type_str,
                'modifier': var.modifier,
                'line': var.line_number
            }

        # Check if it's a table
        table = self.model.get_table(word)
        if table:
            return {
                'type': 'table',
                'name': table.name,
                'table_type': table.table_type,
                'packing': table.packing,
                'item_count': table.item_count,
                'fields': list(table.fields.keys()),
                'line_start': table.line_start,
                'line_end': table.line_end
            }

        # Check if it's a procedure
        proc = self.model.get_procedure(word)
        if proc:
            return {
                'type': 'procedure',
                'name': proc.name,
                'is_exec': proc.is_exec,
                'input_params': proc.input_params,
                'output_params': proc.output_params,
                'exit_params': proc.exit_params,
                'line_start': proc.line_start,
                'line_end': proc.line_end
            }

        # Check if it's a function
        func = self.model.get_function(word)
        if func:
            return {
                'type': 'function',
                'name': func.name,
                'input_params': func.input_params,
                'return_type': func.return_type,
                'line_start': func.line_start,
                'line_end': func.line_end
            }

        # Check if it's a type
        typedef = self.model.get_type(word)
        if typedef:
            return {
                'type': 'type',
                'name': typedef.name,
                'status_values': typedef.status_values,
                'packing': typedef.packing,
                'fields': list(typedef.fields.keys()),
                'line_start': typedef.line_start
            }

        # Check if it's a keyword
        if word in self.RESERVED_WORDS:
            return {
                'type': 'keyword',
                'name': word,
                'description': self._get_keyword_description(word)
            }

        # Check if it's a predefined function
        if word in self.PREDEFINED_FUNCTIONS:
            return {
                'type': 'predefined_function',
                'name': word,
                'description': self._get_predefined_description(word)
            }

        return None

    def _format_type(self, var: VariableDefinition) -> str:
        """Format type specification for display"""
        if var.var_type == CMS2Type.INTEGER:
            sign = 'S' if var.signed else 'U'
            return f"I {var.bits} {sign}"
        elif var.var_type == CMS2Type.FIXED:
            sign = 'S' if var.signed else 'U'
            return f"A {var.bits} {sign} {var.frac_bits}"
        elif var.var_type == CMS2Type.FLOAT:
            return "F"
        elif var.var_type == CMS2Type.BOOLEAN:
            return "B"
        elif var.var_type == CMS2Type.CHAR:
            return f"H {var.char_length}"
        elif var.var_type == CMS2Type.STATUS:
            vals = ', '.join(var.status_values[:3])
            if len(var.status_values) > 3:
                vals += '...'
            return f"STATUS ({vals})"
        return var.var_type.value

    def _get_keyword_description(self, keyword: str) -> str:
        """Get description for a CMS-2 keyword"""
        descriptions = {
            'VRBL': 'Variable declaration',
            'TABLE': 'Table (array/structure) declaration',
            'FIELD': 'Field within a table or type',
            'TYPE': 'Type definition',
            'PROCEDURE': 'Procedure (subroutine) declaration',
            'FUNCTION': 'Function declaration',
            'EXEC-PROC': 'Executive procedure (runs in task state from executive)',
            'SYS-DD': 'System Data Division - global data declarations',
            'SYS-PROC': 'System Procedure block',
            'SYS-PROC-REN': 'Re-entrant System Procedure block',
            'LOC-DD': 'Local Data Division',
            'SET': 'Assignment statement',
            'IF': 'Conditional statement',
            'THEN': 'Then clause of IF',
            'ELSE': 'Else clause of IF',
            'ELSIF': 'Else-if clause',
            'GOTO': 'Unconditional branch',
            'RETURN': 'Return from procedure/function',
            'EXIT': 'Exit from loop',
            'STOP': 'Stop program execution',
            'BEGIN': 'Begin block',
            'END': 'End block or loop',
            'VARY': 'Counted loop (FOR loop)',
            'WHILE': 'While loop',
            'LOOP': 'General loop construct',
            'CASE': 'Case/switch statement',
            'FIND': 'Table search operation',
            'DIRECT': 'Begin direct (assembly) code block',
            'INPUT': 'Input parameter list',
            'OUTPUT': 'Output parameter/statement',
            'CORAD': 'Core address (memory address) function',
            'DENSE': 'Dense packing mode',
            'MEDIUM': 'Medium packing mode',
            'NONE': 'No packing (word-aligned)',
            'INDIRECT': 'Indirect table (pointer-based)',
            'EXTDEF': 'External definition (exported)',
            'EXTREF': 'External reference (imported)',
            'LOCREF': 'Local reference',
            'TRANSREF': 'Transient reference (uses transient base register)',
        }
        return descriptions.get(keyword, f'CMS-2 keyword: {keyword}')

    def _get_predefined_description(self, name: str) -> str:
        """Get description for a predefined function"""
        descriptions = {
            'SIN': 'Sine function (floating-point)',
            'COS': 'Cosine function (floating-point)',
            'ASIN': 'Arcsine function',
            'ACOS': 'Arccosine function',
            'ATAN': 'Arctangent function',
            'ATAN2': 'Two-argument arctangent',
            'EXP': 'Exponential function (e^x)',
            'LN': 'Natural logarithm',
            'ALOG': 'Natural logarithm (alias)',
            'IEXP': 'Fixed-point exponential',
            'ISIN': 'Fixed-point sine',
            'ICOS': 'Fixed-point cosine',
            'BAMS': 'Radians to BAMS conversion',
            'RAD': 'BAMS to radians conversion',
            'ABS': 'Absolute value',
            'FIRST': 'First value of status type',
            'LAST': 'Last value of status type',
            'PRED': 'Predecessor value',
            'SUCC': 'Successor value',
            'LENGTH': 'Length of character string',
            'CNT': 'Count function',
            'REM': 'Remainder function',
            'POS': 'Position function',
        }
        return descriptions.get(name, f'Predefined function: {name}')


# Example usage and test
if __name__ == '__main__':
    test_code = '''
''CMS-2 Test Program''
TESTDD SYS-DD $

CMODE D $  ''Decimal mode''

''Variable declarations''
VRBL ALTITUDE I 16 S $
VRBL AIRSPEED A 16 S 4 $
VRBL STATUS_OK B $
VRBL PILOT_NAME H 20 $
VRBL (LAT, LON) A 32 S 16 $

''Status type''
TYPE MODE 'OFF', 'STANDBY', 'ACTIVE', 'ALERT' $

''Table declaration''
TABLE WAYPOINTS V MEDIUM 100 $
  FIELD WP_LAT A 32 S 16 $
  FIELD WP_LON A 32 S 16 $
  FIELD WP_ALT I 16 S $
  FIELD WP_NAME H 8 $
END-TABLE WAYPOINTS $

END-SYS-DD TESTDD $

TESTSP SYS-PROC $

PROCEDURE UPDATE_POS INPUT LAT, LON OUTPUT DISTANCE $
  SET ALTITUDE TO ALTITUDE + 1 $
END-PROC UPDATE_POS $

FUNCTION CALC_DIST(P1, P2) A 32 S 8 $
  RETURN (0) $
END-FUNCTION CALC_DIST $

END-SYS-PROC TESTSP $
'''

    parser = CMS2SemanticParser()
    model = parser.parse(test_code)

    print("=" * 60)
    print("CMS-2 Semantic Parser Test")
    print("=" * 60)

    print(f"\nSystem Data Blocks ({len(model.sys_data_blocks)}):")
    for name, block in model.sys_data_blocks.items():
        print(f"  {name} (lines {block.line_start}-{block.line_end})")

    print(f"\nSystem Proc Blocks ({len(model.sys_proc_blocks)}):")
    for name, block in model.sys_proc_blocks.items():
        print(f"  {name} (lines {block.line_start}-{block.line_end})")

    print(f"\nVariables ({len([v for v in model.variables.values() if '.' not in v.name])}):")
    seen = set()
    for var in model.variables.values():
        if var.name not in seen:
            seen.add(var.name)
            print(f"  {var.name}: {parser._format_type(var)}")

    print(f"\nTables ({len(model.tables)}):")
    for name, table in model.tables.items():
        print(f"  {name} {table.table_type} {table.packing} [{table.item_count} items]")
        for fname, field in table.fields.items():
            print(f"    .{fname}: {field.field_type.value}")

    print(f"\nTypes ({len(model.types)}):")
    for name, typedef in model.types.items():
        if typedef.status_values:
            print(f"  {name}: STATUS {typedef.status_values}")
        else:
            print(f"  {name}: {typedef.packing}")

    print(f"\nProcedures ({len(model.procedures)}):")
    for name, proc in model.procedures.items():
        params = f"INPUT {proc.input_params}" if proc.input_params else ""
        params += f" OUTPUT {proc.output_params}" if proc.output_params else ""
        print(f"  {name} {params}")

    print(f"\nFunctions ({len(model.functions)}):")
    for name, func in model.functions.items():
        print(f"  {name}({', '.join(func.input_params)}) -> {func.return_type}")
