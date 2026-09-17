"""File categories and their extensions."""

EXTENSIONS: dict[str, frozenset[str]] = {
    "Images": frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".heic"}),
    "Documents": frozenset({".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".epub"}),
    "Spreadsheets": frozenset({".xls", ".xlsx", ".ods", ".csv", ".tsv"}),
    "PDFs": frozenset({".pdf"}),
    "Audio": frozenset({".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}),
    "Video": frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv"}),
    "Archives": frozenset({".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"}),
    "Code": frozenset({".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".sh", ".sql"}),
}

CATEGORIES: tuple[str, ...] = (*EXTENSIONS, "Other")
