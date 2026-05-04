# Python Security and Maintainability Snippets

The Python sqlite3 API supports parameter substitution so values can be bound separately from SQL text. Parameterized SQL avoids treating user data as executable query syntax.

The ast.literal_eval function can parse Python literal structures without evaluating arbitrary expressions. It is safer than eval for simple literals, but input size and type should still be controlled.

The subprocess module is safer when commands are passed as a sequence of arguments with shell disabled. Shell invocation expands metacharacters and increases command-injection risk.

Pathlib Path.resolve can normalize paths. A review should check that resolved user paths remain under an intended base directory before reading or writing files.

