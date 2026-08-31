from pathlib import Path
import sys,traceback

def main():
    from angel.ui import launch
    launch()

if __name__=="__main__":
    try:
        main()
    except Exception:
        base=Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent
        (base/"AngelAI_startup_error.log").write_text(traceback.format_exc(),encoding="utf-8")
        raise
