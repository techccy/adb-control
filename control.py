import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import subprocess
import threading
import time
import os
import shutil
import datetime

class AndroidRemote:
    def __init__(self, root):
        self.root = root
        self.root.title("Mac安卓助手 v12.1 (修复版)")
        
        # --- 字体配置 ---
        self.font_main = ("Helvetica", 16)
        self.font_bold = ("Helvetica", 16, "bold")
        self.font_list = ("Menlo", 16)
        self.font_status = ("Helvetica", 16)

        self.root.geometry("450x400")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)

        # --- 自动查找 ADB ---
        self.adb_path = self.find_adb()
        print(f"[*] 初始化完成，使用 ADB 路径: {self.adb_path}")
        print("-" * 50)

        # --- UI 初始化 ---
        self.setup_ui()

        # --- 后台监控 ---
        self.running = True
        threading.Thread(target=self.monitor_connection, daemon=True).start()

    def find_adb(self):
        path = shutil.which("adb")
        if not path:
            possible = [
                "/usr/local/bin/adb",
                "/opt/homebrew/bin/adb",
                os.path.expanduser("~/Library/Android/sdk/platform-tools/adb")
            ]
            for p in possible:
                if os.path.exists(p): return p
        return path if path else "adb"

    def setup_ui(self):
        # 1. 虚拟按键
        nav_frame = tk.LabelFrame(self.root, text="虚拟按键", font=self.font_main, padx=10, pady=5)
        nav_frame.pack(fill="x", padx=15, pady=5)
        navs = [("⬅ 返回", 4, "#ffcccc"), ("⚪ 主页", 3, "#ccffcc"), 
                ("▢ 多任务", 187, "#ccccff"), ("⚡ 锁屏", 26, "#ffffcc"), ("📸 截图", "cap", "#e0e0e0")]
        for t, c, col in navs:
            tk.Button(nav_frame, text=t, bg=col, font=self.font_bold, highlightbackground=col,
                      command=lambda k=c: self.handle_nav(k)).pack(side=tk.LEFT, padx=4, expand=True, fill="x")

        # 2. 常用工具
        tool_frame = tk.LabelFrame(self.root, text="高级工具", font=self.font_main, padx=10, pady=5)
        tool_frame.pack(fill="x", padx=15, pady=5)
        
        row1 = tk.Frame(tool_frame); row1.pack(fill="x")
        tk.Button(row1, text="安装APK", font=self.font_main, command=self.install_apk).pack(side=tk.LEFT, expand=True, fill="x")
        tk.Button(row1, text="🔥 强制卸载...", bg="#ffcdd2", font=self.font_main, command=self.open_uninstall_window).pack(side=tk.LEFT, expand=True, fill="x")
        tk.Button(row1, text="💊 恢复系统应用", bg="#c8e6c9", font=self.font_main, command=self.restore_app).pack(side=tk.LEFT, expand=True, fill="x")
        
        row2 = tk.Frame(tool_frame, pady=2); row2.pack(fill="x")
        tk.Button(row2, text="👀 查看当前包名", font=self.font_main, command=self.get_current_app).pack(side=tk.LEFT, expand=True, fill="x")
        tk.Button(row2, text="输入文字", font=self.font_main, command=self.input_text).pack(side=tk.LEFT, expand=True, fill="x")
        tk.Button(row2, text="重启手机", font=self.font_main, command=self.reboot_device).pack(side=tk.LEFT, expand=True, fill="x")

        # 3. 文件传输
        file_frame = tk.LabelFrame(self.root, text="文件传输", font=self.font_main, padx=10, pady=5)
        file_frame.pack(fill="x", padx=15, pady=5)
        tk.Button(file_frame, text="📤 发送文件", font=self.font_main, command=self.push_file).pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        tk.Button(file_frame, text="📥 浏览/下载/删除", font=self.font_main, command=self.open_file_browser).pack(side=tk.LEFT, padx=5, expand=True, fill="x")

        # 4. 状态栏
        self.status_var = tk.StringVar(value="等待连接...")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, font=self.font_status,
                                     bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#dedede", pady=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # --- 核心 ADB 执行 ---
    def run_adb(self, cmd_list, verbose=True):
        try:
            real_cmd = list(cmd_list)
            if real_cmd[0] == "adb": real_cmd[0] = self.adb_path
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            if verbose: print(f"\n[{ts}] [执行] {' '.join(real_cmd)}")
            
            if "|" in " ".join(cmd_list):
                result = subprocess.run(" ".join(real_cmd), shell=True, capture_output=True, text=True, encoding='utf-8', timeout=10)
            else:
                result = subprocess.run(real_cmd, capture_output=True, text=True, encoding='utf-8', timeout=60)
            
            stdout = result.stdout.strip()
            if verbose and stdout: print(f"[{ts}] [输出] {stdout}")
            return stdout
        except Exception as e:
            print(f"[异常] {e}")
            return ""

    # ==========================
    #   文件浏览 (已修复删除报错)
    # ==========================
    def open_file_browser(self):
        win = tk.Toplevel(self.root)
        win.title("文件管理 (双击下载/右键删除)")
        win.geometry("550x600")
        
        path_var = tk.StringVar(value="/sdcard/")
        tk.Label(win, textvariable=path_var, font=self.font_main, bg="#eee").pack(fill="x")
        
        list_frame = tk.Frame(win)
        list_frame.pack(fill="both", expand=True)
        
        sb = tk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill="y")
        
        lb = tk.Listbox(list_frame, font=self.font_list, yscrollcommand=sb.set)
        lb.pack(side=tk.LEFT, fill="both", expand=True)
        sb.config(command=lb.yview)

        btn_frame = tk.Frame(win, pady=5)
        btn_frame.pack(fill="x")
        tk.Label(btn_frame, text="提示: 双击进入/下载，右键或选中点击删除", fg="gray").pack()
        
        # --- 局部逻辑函数 ---
        
        def _delete_thread(target_path, current_dir, refresh_func):
            # 执行删除
            self.run_adb(["adb", "shell", "rm", "-rf", f'"{target_path}"'])
            # 刷新列表
            self.root.after(0, lambda: refresh_func(current_dir))
            self.root.after(0, lambda: messagebox.showinfo("提示", "删除成功"))

        def refresh(p):
            lb.delete(0, tk.END)
            if p != "/": lb.insert(tk.END, "..")
            raw = self.run_adb(["adb", "shell", "ls", "-l", f'"{p}"'], verbose=True)
            dirs, files = [], []
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith("total") or "No such file" in line: continue
                try:
                    parts = line.split()
                    if len(parts) < 6: continue 
                    name = parts[-1]
                    if name in [".", ".."]: continue
                    if line.startswith("d"): dirs.append(name + "/")
                    else: files.append(name)
                except: pass
            for d in sorted(dirs): lb.insert(tk.END, f"📂 {d}")
            for f in sorted(files): lb.insert(tk.END, f"📄 {f}")

        def do_delete():
            sel = lb.curselection()
            if not sel: return
            
            txt = lb.get(sel[0])
            if txt == "..": 
                messagebox.showwarning("提示", "不能删除上级目录！")
                return
            
            real_name = txt.split(" ", 1)[1]
            full_path = path_var.get() + real_name
            
            if messagebox.askyesno("删除确认", f"⚠️ 确定要永久删除吗？\n\n{real_name}"):
                # 【修复点】这里直接调用 _delete_thread，不要加 self.
                threading.Thread(target=lambda: _delete_thread(full_path, path_var.get(), refresh)).start()

        def dclick(e):
            sel = lb.curselection()
            if not sel: return
            txt = lb.get(sel[0])
            curr = path_var.get()
            
            if txt == "..": 
                new_p = os.path.dirname(curr.rstrip("/")) + "/"
                path_var.set(new_p); refresh(new_p)
            elif "📂" in txt:
                name = txt.split(" ", 1)[1]
                path_var.set(curr + name); refresh(curr + name)
            elif "📄" in txt:
                name = txt.split(" ", 1)[1]
                save = filedialog.asksaveasfilename(initialfile=name)
                if save: threading.Thread(target=lambda: self.run_adb(["adb", "pull", curr+name, save])).start()

        # 按钮与绑定
        tk.Button(btn_frame, text="🗑️ 删除选中文件/文件夹", font=self.font_main, bg="#ffcdd2", 
                  command=do_delete).pack(fill="x", padx=10, pady=5)
        
        lb.bind("<Double-Button-1>", dclick)
        
        # 右键菜单
        context_menu = tk.Menu(win, tearoff=0)
        context_menu.add_command(label="🗑️ 删除", command=do_delete)
        
        def show_context_menu(event):
            try:
                lb.selection_clear(0, tk.END)
                lb.selection_set(lb.nearest(event.y))
                context_menu.post(event.x_root, event.y_root)
            except: pass

        if self.root.tk.call('tk', 'windowingsystem') == 'aqua':
            lb.bind("<Button-2>", show_context_menu)
            lb.bind("<Button-3>", show_context_menu)
        else:
            lb.bind("<Button-3>", show_context_menu)

        refresh("/sdcard/")

    # --- 保持其他功能不变 ---
    def open_uninstall_window(self):
        win = tk.Toplevel(self.root); win.geometry("550x650")
        ctrl = tk.Frame(win); ctrl.pack(fill="x")
        sys_var = tk.BooleanVar(value=False)
        def load():
            lb.delete(0,tk.END); lb.insert(tk.END,"加载中...")
            self.root.update()
            cmd=["adb","shell","pm","list","packages"]
            if not sys_var.get(): cmd.append("-3")
            def _t():
                raw=self.run_adb(cmd)
                apps=[l.replace("package:","").strip() for l in raw.splitlines() if "package:" in l]
                self.root.after(0,lambda:filter_apps(apps))
            threading.Thread(target=_t).start()
        def filter_apps(apps):
            k=entry.get().lower(); lb.delete(0,tk.END)
            for a in sorted(apps): 
                if k in a.lower(): lb.insert(tk.END,a)
            lb.bind("<Double-Button-1>", lambda e: force_del(lb))
        def force_del(lbox):
            s=lbox.curselection()
            if not s: return
            p=lbox.get(s[0])
            if messagebox.askyesno("强制卸载",f"删除 {p}?"):
                threading.Thread(target=lambda:[self.run_adb(["adb","shell","pm","uninstall","--user","0",p]), load()]).start()
        tk.Checkbutton(ctrl, text="系统应用", variable=sys_var, command=load).pack(side=tk.LEFT)
        entry=tk.Entry(win); entry.pack(fill="x"); entry.bind("<KeyRelease>", lambda e: load())
        lb=tk.Listbox(win, font=self.font_list); lb.pack(fill="both", expand=True)
        load()

    def restore_app(self):
        p=simpledialog.askstring("恢复","包名:"); 
        if p: threading.Thread(target=lambda:self.run_adb(["adb","shell","cmd","package","install-existing",p])).start()

    def get_current_app(self):
        threading.Thread(target=lambda: self._get_app_thread()).start()
    
    def _get_app_thread(self):
        cmd = f'"{self.adb_path}" shell dumpsys window | grep mCurrentFocus'
        try:
            res = subprocess.check_output(cmd, shell=True, text=True, encoding='utf-8').strip()
            if "mCurrentFocus" in res and "/" in res:
                pkg = res.split("/")[0].split(" ")[-1].replace("}", "")
                self.root.after(0, lambda: [self.root.clipboard_clear(), self.root.clipboard_append(pkg), messagebox.showinfo("当前应用", f"{pkg}\n(已复制)")])
        except: pass

    def handle_nav(self, k): 
        if k=="cap": self.take_screenshot()
        else: threading.Thread(target=self.run_adb, args=(["adb", "shell", "input", "keyevent", str(k)],)).start()
    
    def monitor_connection(self):
        while self.running:
            s = self.run_adb(["adb", "get-state"], verbose=False)
            self.root.after(0, lambda: [self.status_label.config(fg="green" if s=="device" else "red"), self.status_var.set("✅ 连接正常" if s=="device" else "❌ 未连接")])
            time.sleep(2)
            
    def install_apk(self):
        f = filedialog.askopenfilename(filetypes=[("APK", "*.apk")])
        if f: threading.Thread(target=lambda: self.run_adb(["adb", "install", "-r", "-d", f])).start()
        
    def input_text(self):
        t = simpledialog.askstring("输入", "内容:")
        if t: threading.Thread(target=self.run_adb, args=(["adb", "shell", "input", "text", t.replace(" ", "%s")],)).start()
        
    def reboot_device(self):
        if messagebox.askyesno("重启", "确认?"): self.run_adb(["adb", "reboot"])
        
    def take_screenshot(self):
        ts = time.strftime("%Y%m%d_%H%M%S")
        f = os.path.join(os.path.expanduser("~/Desktop"), f"screen_{ts}.png")
        threading.Thread(target=lambda: [self.run_adb(["adb", "shell", "screencap", "-p", "/sdcard/s.png"]), self.run_adb(["adb", "pull", "/sdcard/s.png", f]), self.run_adb(["adb", "shell", "rm", "/sdcard/s.png"]), messagebox.showinfo("截图", f"已保存: {f}")]).start()
    
    def push_file(self):
        f = filedialog.askopenfilename()
        if f: threading.Thread(target=lambda: self.run_adb(["adb", "push", f, f"/sdcard/Download/{os.path.basename(f)}"])).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AndroidRemote(root)
    root.mainloop()