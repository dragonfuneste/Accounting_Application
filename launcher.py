import sys
import os


def resource_path(relative: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


_root = resource_path('.')
if _root not in sys.path:
    sys.path.insert(0, _root)
os.chdir(_root)


if __name__ == '__main__':
    try:
        import main  # noqa: F401
    except Exception as e:
        import traceback
        # En mode .exe sans console, écrire l'erreur dans un fichier log
        log_path = os.path.join(os.path.dirname(sys.executable)
                                if getattr(sys, 'frozen', False)
                                else _root, 'error.log')
        with open(log_path, 'w') as f:
            f.write(f"[ERREUR AU LANCEMENT]\n{e}\n\n")
            traceback.print_exc(file=f)
        # Afficher une boîte de dialogue Windows si possible
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Erreur au lancement :\n{e}\n\nDétails dans error.log",
                "Erreur",
                0x10  # MB_ICONERROR
            )
        except Exception:
            pass