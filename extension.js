const vscode = require("vscode");
const { spawn } = require("child_process");
const path = require("path");

function _transformErrorInDecorator(line, error) {
  console.log(line, error.nStart, error.nEnd, error.sMessage);
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
          const json = JSON.parse(data.toString());
          for (let paragraph of json.data) {
            for (let grammarError of paragraph.lGrammarErrors) {
              _transformErrorInDecorator(paragraph.iParagraph, grammarError);
            }
            for (let spellingError of paragraph.lSpellingErrors) {
              _transformErrorInDecorator(paragraph.iParagraph, spellingError);
            }
          }
        });
      }
    }
  );

  context.subscriptions.push(disposable);
}
exports.activate = activate;

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
