"""
CMS-2 Language Server Protocol Implementation

Provides IDE support for CMS-2 (Compiler Monitor System 2),
the US Navy's standard programming language for tactical combat systems.

Features:
- Code completion for keywords, variables, procedures
- Hover information with type details
- Go to definition
- Find references
- Document symbols/outline
- Diagnostics

Based on CMS-2Y Reference Manual (M-5049), October 1986
Fleet Combat Direction Systems Support Activity, San Diego
"""

import sys
import json
import re
from typing import Dict, List, Optional, Any

from cms2_semantic_parser import (
    CMS2SemanticParser, CMS2SemanticModel,
    VariableDefinition, TableDefinition, ProcedureDefinition,
    FunctionDefinition, TypeDefinition, FieldDefinition,
    CMS2Type
)


class CMS2LanguageServer:
    """Language Server Protocol implementation for CMS-2"""

    def __init__(self):
        self.documents: Dict[str, str] = {}
        self.models: Dict[str, CMS2SemanticModel] = {}
        self.parsers: Dict[str, CMS2SemanticParser] = {}
        self.running = True

    def run(self):
        """Main LSP loop - read JSON-RPC messages from stdin"""
        while self.running:
            try:
                message = self._read_message()
                if message:
                    response = self._handle_message(message)
                    if response:
                        self._send_message(response)
            except Exception as e:
                self._log(f"Error: {e}")

    def _read_message(self) -> Optional[Dict]:
        """Read a JSON-RPC message from stdin"""
        headers = {}
        while True:
            line = sys.stdin.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        content_length = int(headers.get('Content-Length', 0))
        if content_length > 0:
            content = sys.stdin.read(content_length)
            return json.loads(content)
        return None

    def _send_message(self, message: Dict):
        """Send a JSON-RPC message to stdout"""
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        sys.stdout.write(header + content)
        sys.stdout.flush()

    def _log(self, message: str):
        """Log a message (to stderr)"""
        sys.stderr.write(f"[CMS2-LSP] {message}\n")
        sys.stderr.flush()

    def _handle_message(self, message: Dict) -> Optional[Dict]:
        """Handle an incoming JSON-RPC message"""
        method = message.get('method', '')
        msg_id = message.get('id')
        params = message.get('params', {})

        # Requests (have id)
        if msg_id is not None:
            if method == 'initialize':
                return self._handle_initialize(msg_id, params)
            elif method == 'shutdown':
                return self._handle_shutdown(msg_id)
            elif method == 'textDocument/completion':
                return self._handle_completion(msg_id, params)
            elif method == 'textDocument/hover':
                return self._handle_hover(msg_id, params)
            elif method == 'textDocument/definition':
                return self._handle_definition(msg_id, params)
            elif method == 'textDocument/references':
                return self._handle_references(msg_id, params)
            elif method == 'textDocument/documentSymbol':
                return self._handle_document_symbols(msg_id, params)
            else:
                # Unknown request - return null result
                return {'jsonrpc': '2.0', 'id': msg_id, 'result': None}

        # Notifications (no id)
        else:
            if method == 'initialized':
                pass  # Client ready
            elif method == 'exit':
                self.running = False
            elif method == 'textDocument/didOpen':
                self._handle_did_open(params)
            elif method == 'textDocument/didChange':
                self._handle_did_change(params)
            elif method == 'textDocument/didClose':
                self._handle_did_close(params)

        return None

    def _handle_initialize(self, msg_id: int, params: Dict) -> Dict:
        """Handle initialize request"""
        capabilities = {
            'textDocumentSync': {
                'openClose': True,
                'change': 1,  # Full sync
                'save': {'includeText': True}
            },
            'completionProvider': {
                'triggerCharacters': ['.', '(', ' '],
                'resolveProvider': False
            },
            'hoverProvider': True,
            'definitionProvider': True,
            'referencesProvider': True,
            'documentSymbolProvider': True,
        }

        return {
            'jsonrpc': '2.0',
            'id': msg_id,
            'result': {
                'capabilities': capabilities,
                'serverInfo': {
                    'name': 'CMS-2 Language Server',
                    'version': '1.0.0'
                }
            }
        }

    def _handle_shutdown(self, msg_id: int) -> Dict:
        """Handle shutdown request"""
        return {'jsonrpc': '2.0', 'id': msg_id, 'result': None}

    def _handle_did_open(self, params: Dict):
        """Handle textDocument/didOpen notification"""
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        text = doc.get('text', '')

        self.documents[uri] = text
        self._parse_document(uri, text)

    def _handle_did_change(self, params: Dict):
        """Handle textDocument/didChange notification"""
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        changes = params.get('contentChanges', [])

        if changes:
            # Full sync - take last change
            text = changes[-1].get('text', '')
            self.documents[uri] = text
            self._parse_document(uri, text)

    def _handle_did_close(self, params: Dict):
        """Handle textDocument/didClose notification"""
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')

        if uri in self.documents:
            del self.documents[uri]
        if uri in self.models:
            del self.models[uri]
        if uri in self.parsers:
            del self.parsers[uri]

    def _parse_document(self, uri: str, text: str):
        """Parse a document and update its model"""
        parser = CMS2SemanticParser()
        model = parser.parse(text)
        self.parsers[uri] = parser
        self.models[uri] = model

    def _handle_completion(self, msg_id: int, params: Dict) -> Dict:
        """Handle textDocument/completion request"""
        uri = params.get('textDocument', {}).get('uri', '')
        position = params.get('position', {})
        line = position.get('line', 0)
        character = position.get('character', 0)

        items = []
        parser = self.parsers.get(uri)
        model = self.models.get(uri)

        if parser and model:
            # Get prefix for filtering
            text = self.documents.get(uri, '')
            lines = text.split('\n')
            if 0 <= line < len(lines):
                current_line = lines[line]
                prefix = current_line[:character].strip().split()[-1] if current_line[:character].strip() else ""
                prefix = prefix.upper()

                # Add keywords
                for kw in parser.RESERVED_WORDS:
                    if not prefix or kw.startswith(prefix):
                        items.append({
                            'label': kw,
                            'kind': 14,  # Keyword
                            'detail': 'CMS-2 keyword',
                            'documentation': parser._get_keyword_description(kw)
                        })

                # Add predefined functions
                for func in parser.PREDEFINED_FUNCTIONS:
                    if not prefix or func.startswith(prefix):
                        items.append({
                            'label': func,
                            'kind': 3,  # Function
                            'detail': 'Predefined function',
                            'documentation': parser._get_predefined_description(func)
                        })

                # Add symbols from model
                for name, var in model.variables.items():
                    if '.' not in name and (not prefix or name.startswith(prefix)):
                        items.append({
                            'label': name,
                            'kind': 6,  # Variable
                            'detail': parser._format_type(var),
                            'documentation': f"Variable declared at line {var.line_number + 1}"
                        })

                for name, table in model.tables.items():
                    if not prefix or name.startswith(prefix):
                        items.append({
                            'label': name,
                            'kind': 22,  # Struct
                            'detail': f"TABLE {table.table_type} {table.packing}",
                            'documentation': f"Table with {len(table.fields)} fields"
                        })

                for name, proc in model.procedures.items():
                    if not prefix or name.startswith(prefix):
                        params = ', '.join(proc.input_params + proc.output_params)
                        items.append({
                            'label': name,
                            'kind': 2,  # Method
                            'detail': f"PROCEDURE ({params})",
                            'documentation': f"Procedure at line {proc.line_start + 1}"
                        })

                for name, func in model.functions.items():
                    if not prefix or name.startswith(prefix):
                        items.append({
                            'label': name,
                            'kind': 3,  # Function
                            'detail': f"FUNCTION -> {func.return_type or 'void'}",
                            'documentation': f"Function at line {func.line_start + 1}"
                        })

                for name, typedef in model.types.items():
                    if not prefix or name.startswith(prefix):
                        items.append({
                            'label': name,
                            'kind': 25,  # Type Parameter
                            'detail': 'TYPE',
                            'documentation': f"Type defined at line {typedef.line_start + 1}"
                        })

        return {
            'jsonrpc': '2.0',
            'id': msg_id,
            'result': {'isIncomplete': False, 'items': items}
        }

    def _handle_hover(self, msg_id: int, params: Dict) -> Dict:
        """Handle textDocument/hover request"""
        uri = params.get('textDocument', {}).get('uri', '')
        position = params.get('position', {})
        line = position.get('line', 0)
        character = position.get('character', 0)

        parser = self.parsers.get(uri)
        model = self.models.get(uri)

        if parser and model:
            text = self.documents.get(uri, '')
            lines = text.split('\n')
            if 0 <= line < len(lines):
                current_line = lines[line]
                parser.lines = lines  # Update parser lines
                hover_info = parser.get_hover_info(line, character)

                if hover_info:
                    markdown = self._format_hover_markdown(hover_info)
                    return {
                        'jsonrpc': '2.0',
                        'id': msg_id,
                        'result': {
                            'contents': {
                                'kind': 'markdown',
                                'value': markdown
                            }
                        }
                    }

        return {'jsonrpc': '2.0', 'id': msg_id, 'result': None}

    def _format_hover_markdown(self, info: Dict) -> str:
        """Format hover information as Markdown"""
        info_type = info.get('type', '')
        name = info.get('name', '')

        if info_type == 'variable':
            cms2_type = info.get('cms2_type', 'UNKNOWN')
            modifier = info.get('modifier', '')
            line = info.get('line', 0)
            md = f"```cms2\nVRBL {name} {cms2_type}\n```\n"
            if modifier:
                md += f"**Modifier:** ({modifier})\n\n"
            md += f"*Declared at line {line + 1}*"
            return md

        elif info_type == 'table':
            table_type = info.get('table_type', 'V')
            packing = info.get('packing', 'NONE')
            item_count = info.get('item_count', 0)
            fields = info.get('fields', [])
            md = f"```cms2\nTABLE {name} {table_type} {packing} {item_count}\n```\n"
            if fields:
                md += "**Fields:** " + ', '.join(fields[:5])
                if len(fields) > 5:
                    md += f" (+{len(fields)-5} more)"
            return md

        elif info_type == 'procedure':
            is_exec = info.get('is_exec', False)
            input_params = info.get('input_params', [])
            output_params = info.get('output_params', [])
            proc_type = 'EXEC-PROC' if is_exec else 'PROCEDURE'
            md = f"```cms2\n{proc_type} {name}"
            if input_params:
                md += f" INPUT {', '.join(input_params)}"
            if output_params:
                md += f" OUTPUT {', '.join(output_params)}"
            md += "\n```"
            return md

        elif info_type == 'function':
            input_params = info.get('input_params', [])
            return_type = info.get('return_type', 'void')
            md = f"```cms2\nFUNCTION {name}({', '.join(input_params)}) {return_type}\n```"
            return md

        elif info_type == 'type':
            status_values = info.get('status_values', [])
            packing = info.get('packing', '')
            if status_values:
                md = f"```cms2\nTYPE {name} {', '.join(status_values[:4])}"
                if len(status_values) > 4:
                    md += '...'
                md += "\n```"
            else:
                md = f"```cms2\nTYPE {name} {packing}\n```"
            return md

        elif info_type == 'keyword':
            desc = info.get('description', '')
            return f"**{name}**\n\n{desc}"

        elif info_type == 'predefined_function':
            desc = info.get('description', '')
            return f"**{name}**\n\n{desc}\n\n*Predefined CMS-2 function*"

        return f"**{name}**"

    def _handle_definition(self, msg_id: int, params: Dict) -> Dict:
        """Handle textDocument/definition request"""
        uri = params.get('textDocument', {}).get('uri', '')
        position = params.get('position', {})
        line = position.get('line', 0)
        character = position.get('character', 0)

        model = self.models.get(uri)
        text = self.documents.get(uri, '')

        if model and text:
            lines = text.split('\n')
            if 0 <= line < len(lines):
                current_line = lines[line]

                # Find word at position
                word = self._get_word_at_position(current_line, character)
                if word:
                    # Look up the symbol
                    definition_line = self._find_definition(model, word)
                    if definition_line is not None:
                        return {
                            'jsonrpc': '2.0',
                            'id': msg_id,
                            'result': {
                                'uri': uri,
                                'range': {
                                    'start': {'line': definition_line, 'character': 0},
                                    'end': {'line': definition_line, 'character': 0}
                                }
                            }
                        }

        return {'jsonrpc': '2.0', 'id': msg_id, 'result': None}

    def _find_definition(self, model: CMS2SemanticModel, name: str) -> Optional[int]:
        """Find definition line for a symbol"""
        name = name.upper()

        # Check variables
        var = model.get_variable(name)
        if var:
            return var.line_number

        # Check tables
        table = model.get_table(name)
        if table:
            return table.line_start

        # Check procedures
        proc = model.get_procedure(name)
        if proc:
            return proc.line_start

        # Check functions
        func = model.get_function(name)
        if func:
            return func.line_start

        # Check types
        typedef = model.get_type(name)
        if typedef:
            return typedef.line_start

        return None

    def _handle_references(self, msg_id: int, params: Dict) -> Dict:
        """Handle textDocument/references request"""
        uri = params.get('textDocument', {}).get('uri', '')
        position = params.get('position', {})
        line = position.get('line', 0)
        character = position.get('character', 0)

        text = self.documents.get(uri, '')
        references = []

        if text:
            lines = text.split('\n')
            if 0 <= line < len(lines):
                word = self._get_word_at_position(lines[line], character)
                if word:
                    # Find all occurrences
                    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                    for i, line_text in enumerate(lines):
                        for match in pattern.finditer(line_text):
                            references.append({
                                'uri': uri,
                                'range': {
                                    'start': {'line': i, 'character': match.start()},
                                    'end': {'line': i, 'character': match.end()}
                                }
                            })

        return {'jsonrpc': '2.0', 'id': msg_id, 'result': references}

    def _handle_document_symbols(self, msg_id: int, params: Dict) -> Dict:
        """Handle textDocument/documentSymbol request"""
        uri = params.get('textDocument', {}).get('uri', '')
        model = self.models.get(uri)
        parser = self.parsers.get(uri)
        symbols = []

        if model and parser:
            # Add SYS-DD blocks
            for name, block in model.sys_data_blocks.items():
                symbols.append({
                    'name': name,
                    'kind': 2,  # Module
                    'range': {
                        'start': {'line': block.line_start, 'character': 0},
                        'end': {'line': block.line_end or block.line_start, 'character': 0}
                    },
                    'selectionRange': {
                        'start': {'line': block.line_start, 'character': 0},
                        'end': {'line': block.line_start, 'character': len(name)}
                    },
                    'detail': 'SYS-DD'
                })

            # Add SYS-PROC blocks
            for name, block in model.sys_proc_blocks.items():
                detail = 'SYS-PROC-REN' if block.is_reentrant else 'SYS-PROC'
                symbols.append({
                    'name': name,
                    'kind': 2,  # Module
                    'range': {
                        'start': {'line': block.line_start, 'character': 0},
                        'end': {'line': block.line_end or block.line_start, 'character': 0}
                    },
                    'selectionRange': {
                        'start': {'line': block.line_start, 'character': 0},
                        'end': {'line': block.line_start, 'character': len(name)}
                    },
                    'detail': detail
                })

            # Add variables
            seen = set()
            for name, var in model.variables.items():
                if name not in seen and '.' not in name:
                    seen.add(name)
                    symbols.append({
                        'name': name,
                        'kind': 13,  # Variable
                        'range': {
                            'start': {'line': var.line_number, 'character': 0},
                            'end': {'line': var.line_number, 'character': 0}
                        },
                        'selectionRange': {
                            'start': {'line': var.line_number, 'character': 0},
                            'end': {'line': var.line_number, 'character': len(name)}
                        },
                        'detail': parser._format_type(var)
                    })

            # Add tables
            for name, table in model.tables.items():
                symbols.append({
                    'name': name,
                    'kind': 23,  # Struct
                    'range': {
                        'start': {'line': table.line_start, 'character': 0},
                        'end': {'line': table.line_end or table.line_start, 'character': 0}
                    },
                    'selectionRange': {
                        'start': {'line': table.line_start, 'character': 0},
                        'end': {'line': table.line_start, 'character': len(name)}
                    },
                    'detail': f"TABLE {table.table_type}"
                })

            # Add procedures
            for name, proc in model.procedures.items():
                detail = 'EXEC-PROC' if proc.is_exec else 'PROCEDURE'
                symbols.append({
                    'name': name,
                    'kind': 6,  # Method
                    'range': {
                        'start': {'line': proc.line_start, 'character': 0},
                        'end': {'line': proc.line_end or proc.line_start, 'character': 0}
                    },
                    'selectionRange': {
                        'start': {'line': proc.line_start, 'character': 0},
                        'end': {'line': proc.line_start, 'character': len(name)}
                    },
                    'detail': detail
                })

            # Add functions
            for name, func in model.functions.items():
                symbols.append({
                    'name': name,
                    'kind': 12,  # Function
                    'range': {
                        'start': {'line': func.line_start, 'character': 0},
                        'end': {'line': func.line_end or func.line_start, 'character': 0}
                    },
                    'selectionRange': {
                        'start': {'line': func.line_start, 'character': 0},
                        'end': {'line': func.line_start, 'character': len(name)}
                    },
                    'detail': f"FUNCTION -> {func.return_type or 'void'}"
                })

            # Add types
            for name, typedef in model.types.items():
                symbols.append({
                    'name': name,
                    'kind': 26,  # TypeParameter
                    'range': {
                        'start': {'line': typedef.line_start, 'character': 0},
                        'end': {'line': typedef.line_end or typedef.line_start, 'character': 0}
                    },
                    'selectionRange': {
                        'start': {'line': typedef.line_start, 'character': 0},
                        'end': {'line': typedef.line_start, 'character': len(name)}
                    },
                    'detail': 'TYPE'
                })

        return {'jsonrpc': '2.0', 'id': msg_id, 'result': symbols}

    def _get_word_at_position(self, line: str, character: int) -> Optional[str]:
        """Get the word at a position in a line"""
        for match in re.finditer(r'\b([A-Z][A-Z0-9_]*)\b', line, re.IGNORECASE):
            if match.start() <= character <= match.end():
                return match.group(1).upper()
        return None


def main():
    """Main entry point"""
    server = CMS2LanguageServer()
    server.run()


if __name__ == '__main__':
    main()
