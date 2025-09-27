import winreg

PROXIES = None


def get_system_proxy():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
    proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
    if proxy_enable:
        proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
        return proxy_server
    return None


proxy = get_system_proxy()
if proxy:
    PROXIES = f"http://{proxy}"
    print(f"Using system proxy: {PROXIES}")
