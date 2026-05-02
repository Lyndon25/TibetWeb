# Archive Scripts

This directory contains legacy scripts that have been superseded by the unified workflow in `scripts/`.

## Superseded Scripts

| Old Script | Merged Into |
|-----------|------------|
| `rebuild_en_from_source.py` | `../rebuild_en.py` |
| `fix_en_content.py` | `../rebuild_en.py` |
| `fix_mixed_lang.py` | `../rebuild_en.py` (`--strict`) |
| `fix_en_body_images_from_zh.py` | `../sync_images.py` |
| `fix_en_image_distribution.py` | `../sync_images.py` |
| `fix_image_counts.py` | `../sync_images.py` |
| `scan_en_chinese.py` / `v2` | `../deep_audit.py` |
| `scan_mixed_lang.py` | `../deep_audit.py` |
| `scan_zh_english.py` | `../deep_audit.py` |
| `final_verify.py` | `../build.py --validate` |

> These archived files are kept for reference but are no longer maintained.
