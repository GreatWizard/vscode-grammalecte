const vscode = require("vscode");
const { spawn } = require("child_process");

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  let disposable = vscode.commands.registerCommand(
    "grammalecte.run",
    function () {
      const grammalecte = spawn("python3", [
        "grammalecte-cli.py",
        "-f",
        "demo/input-file/input.txt",
      ]);
      grammalecte.stdout.on("data", (data) => {
        vscode.window.showInformationMessage(`stdout: ${data}`);
      });
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
