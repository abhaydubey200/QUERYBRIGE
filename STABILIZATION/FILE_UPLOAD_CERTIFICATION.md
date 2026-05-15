# File Upload Certification

## 1. Memory Safety
- [x] **Chunked Processing**: CSV and Excel files are now handled via DuckDB views and Pandas chunking where applicable.
- [x] **RAM Bounding**: Initialized `FileConnector` with limited memory sessions.
- [x] **Large File Survival**: Verified 500MB CSV load without process termination.

## 2. Capability Matrix
| Format | Engine | Discovery | Streaming |
|--------|--------|-----------|-----------|
| CSV    | DuckDB | Automatic | Native    |
| XLSX   | Pandas | Sheet-wise| Chunked   |
| XLS    | Pandas | Sheet-wise| Chunked   |

## 3. Storage Security
- [x] **Path Isolation**: Uploaded files are strictly isolated in the `/storage/uploads/` directory.
- [x] **Permission Verification**: `validate_credentials()` checks OS-level read permissions before attempting to query.
