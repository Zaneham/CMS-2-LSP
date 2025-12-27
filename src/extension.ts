/**
 * CMS-2 Language Support Extension
 *
 * Provides Language Server Protocol support for CMS-2,
 * the US Navy's tactical combat systems language.
 */

import * as path from 'path';
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient | undefined;

export function activate(context: vscode.ExtensionContext) {
    // Get configuration
    const config = vscode.workspace.getConfiguration('cms2');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    const customServerPath = config.get<string>('serverPath') || '';

    // Determine server path
    const serverPath = customServerPath ||
        path.join(context.extensionPath, 'cms2_lsp_server.py');

    // Server options - run Python LSP server
    const serverOptions: ServerOptions = {
        run: {
            command: pythonPath,
            args: [serverPath],
            transport: TransportKind.stdio
        },
        debug: {
            command: pythonPath,
            args: [serverPath],
            transport: TransportKind.stdio
        }
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'cms2' }
        ],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.{cms2,cm2,cms}')
        },
        outputChannelName: 'CMS-2 Language Server'
    };

    // Create and start the client
    client = new LanguageClient(
        'cms2-lsp',
        'CMS-2 Language Server',
        serverOptions,
        clientOptions
    );

    // Start the client
    client.start();

    // Register status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '$(symbol-misc) CMS-2';
    statusBarItem.tooltip = 'CMS-2 Language Server Active';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Log activation
    console.log('CMS-2 Language Support activated');
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
