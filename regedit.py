import winreg
#注册表中写入数据，需要管理员权限，是否能拿到。
def createReg(path):
    handle = winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT,r"")
    key = winreg.CreateKey(handle,"zjyzAutoCommit")

    winreg.SetValueEx(key,'',0,winreg.REG_SZ, "zjyzAutoCommit Protocol")
    winreg.SetValueEx(key,"URL Protocol",0,winreg.REG_SZ, "")
    newKey = winreg.CreateKey(key,"DefaultIcon")
    #文件安装路径
    winreg.SetValueEx(newKey,"",0,winreg.REG_SZ, "{}".format(path))
    newKey = winreg.CreateKey(key,"shell")
    key = winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, r"zjyzAutoCommit\shell")
    newKey = winreg.CreateKey(key,"open")
    key = winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, r"zjyzAutoCommit\shell\open")
    newKey = winreg.CreateKey(key,"command")
    winreg.SetValueEx(newKey,"",0,winreg.REG_SZ, "{}".format(path))
    winreg.CloseKey(key)
    winreg.CloseKey(newKey)
createReg(r'E:\allhomework_submit\allhomework_submit开发版_0.2(2)\allhomework_submit\allhomework_submit.exe')