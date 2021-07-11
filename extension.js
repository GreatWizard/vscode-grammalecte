const vscode = require("vscode");
const { spawn } = require("child_process");
const path = require("path");

const _typesToString = {
  WORD: "Mot inconnu",
};

let _decorations = {};
let _decorationTypes = {};

function _transformErrorInDecoration(line, error) {
  const typeName = error.aColor
    ? `color-${error.aColor.join("-")}`
    : `color-${error.sType.toLowerCase()}`;
  const color = error.aColor ? `rgb(${error.aColor.join(",")})` : `grey`;
  if (!_decorationTypes[typeName]) {
    _decorationTypes[typeName] = vscode.window.createTextEditorDecorationType({
      backgroundColor: color,
    });
  }
  const decoration = {
    range: new vscode.Range(
      new vscode.Position(line - 1, error.nStart),
      new vscode.Position(line - 1, error.nEnd)
    ),
    hoverMessage: error.sMessage || _typesToString[error.sType],
  };
  _decorations[typeName] !== undefined
    ? _decorations[typeName].push(decoration)
    : (_decorations[typeName] = [decoration]);
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  let disposable = vscode.commands.registerCommand(
    "grammalecte.run",
    function () {
      const editor = vscode.window.activeTextEditor;
      if (editor) {
        const file = editor.document.uri.path;
        const grammalecte = spawn("python3", [
          context.asAbsolutePath("grammalecte-cli.py"),
          "--json",
          "--file",
          file,
        ]);
        grammalecte.stdout.on("data", (data) => {
          _decorations = {};
          const json = JSON.parse(data.toString());
          for (let paragraph of json.data) {
            for (let grammarError of paragraph.lGrammarErrors) {
              _transformErrorInDecoration(paragraph.iParagraph, grammarError);
            }
            for (let spellingError of paragraph.lSpellingErrors) {
              _transformErrorInDecoration(paragraph.iParagraph, spellingError);
            }
          }
          for (let typeName in _decorations) {
            if (_decorations[typeName].length > 0) {
              editor.setDecorations(
                _decorationTypes[typeName],
                _decorations[typeName]
              );
            }
          }
        });
      }
    }
  );

  context.subscriptions.push(disposable);
}
exports.activate = activate;

function deactivate() {
  _decorations = {};
  _decorationTypes = {};
}

module.exports = {
  activate,
  deactivate,
};
