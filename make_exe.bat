pyinstaller --collect-all=pyzbar ^
    --add-data="config.json;." ^
    --add-data="icon;icon" ^
    -n "allhomework_submit" ^
    Main.py
    