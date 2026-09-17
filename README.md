# Smart File Organizer

A small Python tool that sorts loose files into folders by type. Use the CLI for quick automation or the local web interface to preview the same moves visually.

Download folders become cluttered fast. Smart File Organizer gives every visible file a predictable destination, keeps existing files safe with numbered names, and reports exactly what happened.

## What it does

- Sorts files into **Images, Documents, Spreadsheets, PDFs, Audio, Video, Archives, Code,** or **Other**.
- Previews moves without writing anything. The preview and execution use the same organizer code.
- Creates category folders when needed and never overwrites an existing file.
- Ignores hidden files, links, and subfolders; only the chosen folder's direct files are processed.
- Shows processed, moved, ignored, error, and elapsed-time totals; the CLI can save a JSON report.

## Install

Requires **Python 3.12+**. From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[web]'
```

## CLI

```bash
python -m smart_organizer organize ~/Downloads --dry-run
python -m smart_organizer organize ~/Downloads
python -m smart_organizer organize ~/Downloads --report ~/organizer-report.json
```

The installed command `smart-organizer` works too. For example, `smart-organizer organize ~/Downloads --dry-run`.

Preview output:

```text
photo.jpg -> Images/photo.jpg
document.pdf -> PDFs/document_1.pdf
Processed: 2
Planned by category:
  Images: 1
  PDFs: 1
Ignored: 0
Errors: 0
Elapsed: 0.001s
```

`--dry-run` does not change files or create a report, so it cannot be combined with `--report`. The JSON report includes counts, ignored entries, errors, elapsed time, and each file's destination and status. See [a complete example](examples/sample-report.json).

## Web Interface

```bash
smart-organizer web
# Or, from the project root:
python -m smart_organizer web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Enter an absolute local folder path and select **Analyze Folder**. Preview changes is on by default. Review the destinations, then select **Organize Files** and confirm inside the page. Turning preview off changes the main action to **Organize Folder**, which also asks for confirmation.

For a portfolio preview with real backend data, select **Use demo folder** and analyze it. You can also open [the demo preview](http://127.0.0.1:8000/?demo=1) directly. The seven files in [`demo-files/`](demo-files/) are empty fixtures, so previewing them is safe and does not change the repository.

Screenshot placeholder: `docs/smart-file-organizer-ui.png` — add your own capture after running the demo preview.

The server binds to `127.0.0.1` by default. The web API accepts only explicit absolute directories without `..` or symlink components. It does not recurse or serve files from the chosen folder.

## Project structure

```text
smart_organizer/
  cli.py          # CLI commands
  organizer.py    # shared planning and moving logic
  classifier.py   # extension lookup
  config.py       # categories and extensions
  reporter.py     # structured summary and JSON report
  web/
    routes.py     # FastAPI page and API
    templates/    # HTML
    static/       # CSS and vanilla JavaScript
tests/            # pytest tests
demo-files/       # safe portfolio fixtures
examples/         # sample JSON report
```

## Tests

```bash
python -m pip install -e '.[web,dev]'
python -m pytest
```

## Tech

Python 3.12+, FastAPI, HTML, CSS, vanilla JavaScript, and pytest. The CLI uses Python's standard library and works independently of the optional web dependencies.
