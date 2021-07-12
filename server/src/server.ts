import {
  createConnection,
  TextDocuments,
  Diagnostic,
  DiagnosticSeverity,
  Range,
  Position,
  ProposedFeatures,
  InitializeParams,
  TextDocumentSyncKind,
  InitializeResult,
} from "vscode-languageserver/node";
import { TextDocument } from "vscode-languageserver-textdocument";
import { spawn } from "child_process";
import * as path from "path";

const connection = createConnection(ProposedFeatures.all);

const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

let hasDiagnosticRelatedInformationCapability = false;

connection.onInitialize((params: InitializeParams) => {
  const capabilities = params.capabilities;

  hasDiagnosticRelatedInformationCapability = !!(
    capabilities.textDocument &&
    capabilities.textDocument.publishDiagnostics &&
    capabilities.textDocument.publishDiagnostics.relatedInformation
  );

  const result: InitializeResult = {
    capabilities: {
      textDocumentSync: TextDocumentSyncKind.Incremental,
    },
  };

  return result;
});

documents.onDidChangeContent((change) => {
  validateTextDocument(change.document);
});

const _typesToString: any = {
  WORD: "Mot inconnu",
};

function _transformErrorIntoDiagnostic(line: number, error: any) {
  const diagnostic: Diagnostic = {
    severity: DiagnosticSeverity.Error,
    range: Range.create(
      Position.create(line - 1, error.nStart),
      Position.create(line - 1, error.nEnd)
    ),
    message: error.sMessage || _typesToString[error.sType],
    source: "Grammalecte",
  };
  return diagnostic;
}

async function validateTextDocument(textDocument: TextDocument): Promise<void> {
  const file = textDocument.uri;

  const grammalecte = spawn("python3", [
    "/Users/guillaumeg/workspace/vscode-grammalecte/grammalecte-cli.py",
    "--json",
    "--file",
    file.split("file://")[1],
  ]);

  grammalecte.stdout.on("data", (data) => {
    const diagnostics: Diagnostic[] = [];
    const json = JSON.parse(data.toString());
    for (const paragraph of json.data) {
      for (const grammarError of paragraph.lGrammarErrors) {
        diagnostics.push(
          _transformErrorIntoDiagnostic(paragraph.iParagraph, grammarError)
        );
      }

      for (const spellingError of paragraph.lSpellingErrors) {
        diagnostics.push(
          _transformErrorIntoDiagnostic(paragraph.iParagraph, spellingError)
        );
      }
    }

    connection.sendDiagnostics({ uri: textDocument.uri, diagnostics });
  });
}

documents.listen(connection);

connection.listen();
