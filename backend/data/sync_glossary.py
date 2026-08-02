"""
glossary_master.csv <-> glossary_master.xlsx 双向同步。

为什么要有这个：直接在文本编辑器里改 CSV 很难看清中文对齐、逐行核对，
用 Numbers/Excel 这种表格界面舒服得多。但 rag.py 和所有评测脚本只读
CSV，xlsx 只是给人编辑用的界面，两边必须手动同步，不会自动联动。

工作流：
    python data/sync_glossary.py to-xlsx   # CSV -> xlsx，生成/刷新可编辑表格
    (用 Numbers/Excel 打开 xlsx，改完保存)
    python data/sync_glossary.py to-csv    # xlsx -> CSV，写回真正生效的文件

每次覆盖前都会先把目标文件备份到 data/backups/，误操作可以找回来。
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

DATA = Path(__file__).parent
CSV = DATA / "glossary_master.csv"
XLSX = DATA / "glossary_master.xlsx"
BACKUPS = DATA / "backups"


def _backup(path: Path):
    if not path.exists():
        return
    BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUPS / f"{path.stem}.{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    print(f"备份 {path.name} -> {dest.relative_to(DATA)}")


def to_xlsx():
    df = pd.read_csv(CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    _backup(XLSX)
    df.to_excel(XLSX, index=False)
    print(f"已生成 {XLSX.name}（{len(df)} 行）")


def to_csv():
    df = pd.read_excel(XLSX, dtype=str, keep_default_na=False)
    expected = ["Type", "Category", "Romanized", "Variants", "Cantonese", "Mandarin", "English", "needs_review"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        sys.exit(f"缺少必须的列: {missing}，没有写入，检查 xlsx 有没有被改动了表头")
    _backup(CSV)
    df.to_csv(CSV, index=False, encoding="utf-8")
    print(f"已写回 {CSV.name}（{len(df)} 行）")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "to-xlsx":
        to_xlsx()
    elif cmd == "to-csv":
        to_csv()
    else:
        print(__doc__)
