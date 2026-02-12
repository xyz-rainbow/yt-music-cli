import base64
import subprocess
import logging
import os
from rich.control import Control

logger = logging.getLogger(__name__)

def copy_to_clipboard(app, text: str, silent: bool = False):
    """
    Robust system-agnostic clipboard copy with multiple fallbacks.
    Sequence: xclip -> wl-copy -> pyperclip -> OSC 52.
    """
    success = False
    
    # 1. Try xclip (X11)
    try:
        subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True, capture_output=True)
        success = True
    except Exception:
        pass
        
    # 2. Try wl-copy (Wayland)
    if not success:
        try:
            subprocess.run(['wl-copy'], input=text.encode('utf-8'), check=True, capture_output=True)
            success = True
        except Exception:
            pass

    # 3. Try Pyperclip
    if not success:
        try:
            import pyperclip
            pyperclip.copy(text)
            success = True
        except Exception:
            pass

    # 4. Fallback: OSC 52 (Terminal-level escape sequence)
    if not success:
        try:
            # 52;c; means copy to clipboard
            payload = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            
            # Standard OSC 52
            seq = f"\x1b]52;c;{payload}\x07"
            
            # If in tmux, wrap it to allow passthrough
            if 'TMUX' in os.environ:
                seq = f"\x1bPtmux;\x1b{seq}\x1b\\"
            
            # Use raw write if possible to ensure the sequence isn't escaped
            import sys
            sys.stdout.write(seq)
            sys.stdout.flush()
            success = True
        except Exception as e:
            logger.warning(f"Clipboard all fallbacks failed: {e}")

    if success:
        if not silent:
            app.notify("¡Copiado al portapapeles!")
    else:
        if not silent:
            app.notify("No se pudo copiar automáticamente.", severity="error")
    
    return success
