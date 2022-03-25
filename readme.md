# 交接文档

## 作为pyqt应用启动

### 1.准备工作

- vpn
- 虚拟环境安装

### 2.启动

- 激活虚拟环境（本机为conda activate pyqt）
- python Main.py

### 3.打包pyqt应用

- 激活虚拟环境
- 运行./make_exe.bat脚本

### 4.使用Inno Setup Compiler添加安装指导

- [Inno setup的使用方法](https://www.cnblogs.com/benpaodejiandan/p/7081011.html)

- ```
  # 管理员权限运行安装程序
  [Setup]
  PrivilegesRequired=admin
  
  
  # 修改注册表
  [Registry]
  Root: HKCR; Subkey: "allHomeworkSubmit"; ValueType:string; ValueName:"URL Protocol";ValueData:"";Flags:uninsdeletevalue
  Root: HKCR; Subkey: "allHomeworkSubmit"; ValueType:string; ValueName:"";ValueData:"allHomeworkSubmit Protocol";Flags:uninsdeletevalue
  Root: HKCR; Subkey: "allHomeworkSubmit\DefaultIcon"; ValueType:string; ValueName:"";ValueData:"{app}\{#MyAppExeName},0";Flags:uninsdeletekey
  Root: HKCR; Subkey: "allHomeworkSubmit\shell"; ValueType: none; ValueName: ""; ValueData: "" 
  Root: HKCR; Subkey: "allHomeworkSubmit\shell\open"; ValueType: none; ValueName: ""; ValueData: ""
  Root: HKCR; Subkey: "allHomeworkSubmit\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
  ```

- 在 浏览器输入 allHomeworkSubmit::\\ 即可打开应用

## 作为flask服务启动

### 目前只实现了

-  负责监控文件夹的生产者、消费者线程、
- 对于判题走前端接口的逻辑分析和实现设计、只实现了部分查询功能。

### 日后工作

- 走前端接口判作业剩余部分逻辑的实现
- flask服务
- pyinstaller 打包flask服务