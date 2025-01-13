from termcolor import cprint


DEBUG_MODE = False

def enable_debug():
    global DEBUG_MODE
    DEBUG_MODE = True

def disable_debug():
    global DEBUG_MODE
    DEBUG_MODE = False


def debug_cprint(message, color="red", on_color=None, attrs=None):
    """
    デバッグモードが有効な場合にのみcprintで出力

    Args:
        message (str): 表示するメッセージ
        color (str): 文字の色（例: 'red', 'green', 'blue'）
        on_color (str): 背景色（例: 'on_red', 'on_green'）
        attrs (list): 文字の属性（例: ['bold', 'underline']）
    """
    if DEBUG_MODE:
        cprint(message, color=color, on_color=on_color, attrs=attrs)
