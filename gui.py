"""
周易起卦与解卦 GUI 桌面应用

功能：
1. 手动/自动起卦（六爻生成）
2. 起爻和动爻计算
3. 本卦、变卦分析
4. API接口测试
5. DeepSeek模型测试
6. AI深度解卦

运行方式：
python gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from typing import List, Optional

# 导入项目核心模块
from logic import (
    Line,
    cast_single_line,
    analyze_hexagram,
    interpret_hexagram,
    ai_interpret_hexagram,
)
from data import get_hexagram_by_bits

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class YiJingGUI:
    """周易起卦与解卦主界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("周易起卦与解卦系统")
        self.root.geometry("950x800")

        # 会话状态
        self.lines: List[Line] = []
        
        # 加载配置
        self.config_file = "gui_config.json"
        self.config = self._load_config()
        
        self.api_base_url = self.config.get("api_base_url", "http://localhost:8000")
        self.api_key = self.config.get("api_key", "")
        self.model_name = self.config.get("model_name", "Qwen3.6-27B")
        self.base_url = self.config.get("base_url", "https://wgooold.cn")

        # 创建界面
        self.create_widgets()

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            import os
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config = {
                "api_base_url": self.api_base_url,
                "api_key": self.api_key,
                "model_name": self.model_name,
                "base_url": self.base_url,
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def create_widgets(self):
        """创建所有界面组件"""
        # 创建选项卡
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 选项卡1：起卦与解卦
        self.tab_divination = ttk.Frame(notebook)
        notebook.add(self.tab_divination, text="起卦与解卦")
        self._create_divination_tab()

        # 选项卡2：API测试
        self.tab_api = ttk.Frame(notebook)
        notebook.add(self.tab_api, text="API测试")
        self._create_api_tab()

        # 选项卡3：模型测试
        self.tab_model = ttk.Frame(notebook)
        notebook.add(self.tab_model, text="模型测试")
        self._create_model_tab()

    def _toggle_password(self):
        """切换密码显示/隐藏"""
        if hasattr(self, 'api_key_entry') and self.api_key_entry.cget('show') == '*':
            self.api_key_entry.config(show='')
        else:
            if hasattr(self, 'api_key_entry'):
                self.api_key_entry.config(show='*')
    
    def _toggle_model_password(self):
        """切换模型测试密码显示/隐藏"""
        if hasattr(self, 'model_api_key_entry') and self.model_api_key_entry.cget('show') == '*':
            self.model_api_key_entry.config(show='')
        else:
            if hasattr(self, 'model_api_key_entry'):
                self.model_api_key_entry.config(show='*')
        
    def _save_api_config(self):
        """保存API配置"""
        if hasattr(self, 'base_url_var'):
            self.base_url = self.base_url_var.get().strip()
        if hasattr(self, 'api_key_var'):
            self.api_key = self.api_key_var.get().strip()
        if hasattr(self, 'model_combo_var'):
            self.model_name = self.model_combo_var.get().strip()
        self._save_config()
        messagebox.showinfo("成功", "配置已保存！")
    
    def _save_model_config(self):
        """保存模型配置"""
        if hasattr(self, 'model_api_key_var'):
            self.api_key = self.model_api_key_var.get().strip()
        if hasattr(self, 'base_url_var'):
            self.base_url = self.base_url_var.get().strip()
        if hasattr(self, 'model_combo_var'):
            self.model_name = self.model_combo_var.get().strip()
        self._save_config()
        messagebox.showinfo("成功", "模型配置已保存！")
    
    def _sync_api_config(self):
        """从主配置同步到API测试"""
        if hasattr(self, 'api_url_var'):
            self.api_test_url_var.set(self.api_url_var.get())
        messagebox.showinfo("成功", "已同步主配置的API URL")
    
    def _sync_model_config(self):
        """从主配置同步到模型测试"""
        if hasattr(self, 'base_url_var'):
            self.base_url_var.set(self.base_url)
        if hasattr(self, 'model_api_key_var'):
            self.model_api_key_var.set(self.api_key)
        if hasattr(self, 'model_combo_var'):
            self.model_combo_var.set(self.model_name)
        messagebox.showinfo("成功", "已同步主配置")
        
    def _create_divination_tab(self):
        """创建起卦与解卦选项卡"""
        # 左侧控制面板
        left_frame = ttk.LabelFrame(self.tab_divination, text="操作控制", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    
        # 起卦按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
    
        ttk.Button(btn_frame, text="掷下一爻", command=self._cast_next_line, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="自动起卦", command=self._auto_cast, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="重新起卦", command=self._reset_hexagram, width=15).pack(side=tk.LEFT, padx=2)
    
        # 状态显示
        self.status_var = tk.StringVar(value="尚未起卦，请点击「掷下一爻」开始")
        ttk.Label(left_frame, textvariable=self.status_var, wraplength=200).pack(fill=tk.X, pady=10)
    
        # API配置
        api_config_frame = ttk.LabelFrame(left_frame, text="API配置", padding=5)
        api_config_frame.pack(fill=tk.X, pady=5)
            
        ttk.Label(api_config_frame, text="API URL:").pack(anchor=tk.W)
        self.api_url_var = tk.StringVar(value=self.api_base_url)
        self.api_url_entry = ttk.Entry(api_config_frame, textvariable=self.api_url_var, width=30)
        self.api_url_entry.pack(fill=tk.X, pady=2)
            
        ttk.Label(api_config_frame, text="API Key:").pack(anchor=tk.W)
        self.api_key_var = tk.StringVar(value=self.api_key)
        self.api_key_entry = ttk.Entry(api_config_frame, textvariable=self.api_key_var, width=30, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=2)
            
        # 显示/隐藏API Key按钮
        show_key_btn = ttk.Button(api_config_frame, text="显示Key", 
                                  command=lambda: self._toggle_password(), width=10)
        show_key_btn.pack(pady=2)
            
        ttk.Button(api_config_frame, text="保存配置", command=self._save_api_config, width=15).pack(pady=2)
    
        # 用户问题输入
        ttk.Label(left_frame, text="占问问题:").pack(anchor=tk.W)
        self.question_text = scrolledtext.ScrolledText(left_frame, height=6, width=30)
        self.question_text.pack(fill=tk.X, pady=5)
        self.question_text.insert(tk.END, "例如：我想问最近的事业发展前景...")
    
        ttk.Button(left_frame, text="AI深度解卦", command=self._ai_interpret, width=20).pack(pady=10)
    
        # 右侧卦象显示区
        right_frame = ttk.Frame(self.tab_divination)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
        # 当前卦象
        hex_frame = ttk.LabelFrame(right_frame, text="当前卦象", padding=10)
        hex_frame.pack(fill=tk.X, pady=5)
    
        self.hex_display = tk.Text(hex_frame, height=12, width=40, font=("Courier", 12))
        self.hex_display.pack(fill=tk.X)
        self.hex_display.config(state=tk.DISABLED)
    
        # 解卦结果
        result_frame = ttk.LabelFrame(right_frame, text="解卦结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
        self.result_text = scrolledtext.ScrolledText(result_frame, height=20, width=60)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
    def _create_api_tab(self):
        """创建API测试选项卡"""
        # 顶部配置区
        config_frame = ttk.LabelFrame(self.tab_api, text="API配置", padding=10)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
    
        ttk.Label(config_frame, text="API基础URL:").grid(row=0, column=0, sticky=tk.W)
        self.api_test_url_var = tk.StringVar(value=self.api_base_url)
        self.api_url_entry = ttk.Entry(config_frame, textvariable=self.api_test_url_var, width=40)
        self.api_url_entry.grid(row=0, column=1, padx=5)
    
        ttk.Button(config_frame, text="健康检查", command=self._api_health_check, width=15).grid(row=0, column=2, padx=5)
            
        ttk.Button(config_frame, text="同步主配置", command=self._sync_api_config, width=15).grid(row=1, column=2, padx=5, pady=5)
    
        # 测试功能区
        test_frame = ttk.LabelFrame(self.tab_api, text="接口测试", padding=10)
        test_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
        btn_test_frame = ttk.Frame(test_frame)
        btn_test_frame.pack(fill=tk.X, pady=5)
    
        ttk.Button(btn_test_frame, text="测试 /cast 接口", command=self._test_cast_api, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_test_frame, text="测试 /analyze 接口", command=self._test_analyze_api, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_test_frame, text="测试 /ai 接口", command=self._test_ai_api, width=20).pack(side=tk.LEFT, padx=5)
    
        # 结果显示
        self.api_result_text = scrolledtext.ScrolledText(test_frame, height=30, width=100)
        self.api_result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def _create_model_tab(self):
        """创建模型测试选项卡"""
        # API配置区
        api_config_frame = ttk.LabelFrame(self.tab_model, text="API 配置", padding=10)
        api_config_frame.pack(fill=tk.X, padx=5, pady=5)
            
        # Base URL
        ttk.Label(api_config_frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value=self.base_url)
        base_url_entry = ttk.Entry(api_config_frame, textvariable=self.base_url_var, width=50)
        base_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            
        # API Key
        ttk.Label(api_config_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.model_api_key_var = tk.StringVar(value=self.api_key)
        self.model_api_key_entry = ttk.Entry(api_config_frame, textvariable=self.model_api_key_var, width=50, show="*")
        self.model_api_key_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
            
        # 配置按钮行
        config_btn_frame = ttk.Frame(api_config_frame)
        config_btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
            
        ttk.Button(config_btn_frame, text="刷新模型列表", command=self._fetch_models, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="保存配置", command=self._save_model_config, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="同步主配置", command=self._sync_model_config, width=15).pack(side=tk.LEFT, padx=5)
            
        # 模型选择区
        model_select_frame = ttk.LabelFrame(self.tab_model, text="LLM模型", padding=10)
        model_select_frame.pack(fill=tk.X, padx=5, pady=5)
            
        # 模型下拉框 + 检测按钮
        model_btn_frame = ttk.Frame(model_select_frame)
        model_btn_frame.pack(fill=tk.X)
            
        ttk.Label(model_btn_frame, text="模型:").pack(side=tk.LEFT, padx=5)
        self.model_combo_var = tk.StringVar(value=self.model_name)
        self.model_combo = ttk.Combobox(model_btn_frame, textvariable=self.model_combo_var, 
                                        values=["Qwen3.6-27B", "qwen-plus", "gpt-4o", "deepseek-chat"], 
                                        width=50, state="readonly")
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
        ttk.Button(model_btn_frame, text="检测模型", command=self._test_model_direct, width=12).pack(side=tk.LEFT, padx=5)
            
        # 显示/隐藏API Key
        show_key_frame = ttk.Frame(api_config_frame)
        show_key_frame.grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(show_key_frame, text="显示", command=lambda: self._toggle_model_password(), width=10).pack()
    
        # 测试区
        test_frame = ttk.LabelFrame(self.tab_model, text="模型功能测试", padding=10)
        test_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
        ttk.Label(test_frame, text="测试问题:").pack(anchor=tk.W)
        self.model_question_text = scrolledtext.ScrolledText(test_frame, height=5, width=80)
        self.model_question_text.pack(fill=tk.X, pady=5)
        self.model_question_text.insert(tk.END, "请介绍一下你自己")
    
        ttk.Button(test_frame, text="发送测试请求", command=self._test_model, width=20).pack(pady=5)
    
        # 结果显示
        self.model_result_text = scrolledtext.ScrolledText(test_frame, height=20, width=100)
        self.model_result_text.pack(fill=tk.BOTH, expand=True, pady=5)

    # ==================== 起卦与解卦功能 ====================

    def _cast_next_line(self):
        """掷下一爻"""
        if len(self.lines) < 6:
            line = cast_single_line()
            self.lines.append(line)
            self._update_hex_display()
            self.status_var.set(f"已起 {len(self.lines)} 爻，还差 {6 - len(self.lines)} 爻")

            if len(self.lines) == 6:
                self._show_interpretation()
        else:
            messagebox.showinfo("提示", "六爻已成，如需重新起卦请点击「重新起卦」")

    def _auto_cast(self):
        """自动起卦（一次性生成六爻）"""
        self.lines = [cast_single_line() for _ in range(6)]
        self._update_hex_display()
        self.status_var.set("六爻已成")
        self._show_interpretation()

    def _reset_hexagram(self):
        """重新起卦"""
        self.lines = []
        self._update_hex_display()
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("尚未起卦，请点击「掷下一爻」开始")

    def _update_hex_display(self):
        """更新卦象显示"""
        self.hex_display.config(state=tk.NORMAL)
        self.hex_display.delete(1.0, tk.END)

        if not self.lines:
            self.hex_display.insert(tk.END, "尚未起卦\n")
        else:
            self.hex_display.insert(tk.END, "当前卦象（自上而下）:\n")
            self.hex_display.insert(tk.END, "=" * 50 + "\n")
            for idx, line in reversed(list(enumerate(self.lines))):
                pos = idx + 1
                label = line.yin_yang_label
                symbol = "———" if line.is_yang else "— —"
                moving_tag = "【动】" if line.is_moving else "【静】"
                self.hex_display.insert(tk.END,
                    f"第{pos}爻: {symbol}  ({label}) {moving_tag}\n")

        self.hex_display.config(state=tk.DISABLED)

    def _show_interpretation(self):
        """显示解卦结果"""
        if len(self.lines) != 6:
            return

        result = analyze_hexagram(self.lines)
        interpretation = interpret_hexagram(result)

        self.result_text.delete(1.0, tk.END)

        # 本卦信息
        self.result_text.insert(tk.END, "【本卦】\n", "header")
        self.result_text.insert(tk.END, f"卦名: {interpretation['main_name']}\n")
        self.result_text.insert(tk.END, f"卦象: {interpretation['main_title']}\n")
        self.result_text.insert(tk.END, f"卦辞: {interpretation['main_judgement']}\n\n")

        # 变卦信息
        if 'changing_name' in interpretation:
            self.result_text.insert(tk.END, "【变卦】\n", "header")
            self.result_text.insert(tk.END, f"卦名: {interpretation['changing_name']}\n")
            self.result_text.insert(tk.END, f"卦象: {interpretation['changing_title']}\n")
            self.result_text.insert(tk.END, f"卦辞: {interpretation['changing_judgement']}\n\n")
        else:
            self.result_text.insert(tk.END, "【变卦】\n", "header")
            self.result_text.insert(tk.END, "本卦无动爻，因此不存在变卦。\n\n")

        # 动爻解读
        self.result_text.insert(tk.END, "【爻辞解读】\n", "header")
        lines_explanation = interpretation.get('lines_explanation', [])
        if not lines_explanation:
            self.result_text.insert(tk.END, "（暂无爻辞信息）\n")
        else:
            for item in lines_explanation:
                pos = item['position']
                text = item['text']
                is_moving = item.get('is_moving', False)
                tag = "【动爻】" if is_moving else "【参考】"
                self.result_text.insert(tk.END, f"第{pos}爻{tag}: {text}\n")

    def _ai_interpret(self):
        """AI深度解卦"""
        if len(self.lines) != 6:
            messagebox.showwarning("警告", "请先完成起卦（需要6爻）")
            return

        question = self.question_text.get(1.0, tk.END).strip()
        if not question or question.startswith("例如"):
            messagebox.showwarning("警告", "请输入您的占问问题")
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("警告", "请输入DeepSeek API Key")
            return

        # 更新内部变量
        self.api_key = api_key
        self.base_url = self.base_url_var.get().strip()
        self.model_name = self.model_combo_var.get().strip()
        model_name = self.model_name
        base_url = self.base_url
        self._save_config()

        def run_ai():
            try:
                self.result_text.insert(tk.END, "\n\n" + "="*60 + "\n")
                self.result_text.insert(tk.END, "🤖 【AI深度解卦】\n\n", "header")
                self.result_text.see(tk.END)

                result = analyze_hexagram(self.lines)
                ai_text = ai_interpret_hexagram(
                    result,
                    user_question=question,
                    api_key=api_key,
                    model=model_name,
                    base_url=base_url,
                )

                self.result_text.insert(tk.END, ai_text)
                self.result_text.see(tk.END)
            except Exception as e:
                messagebox.showerror("错误", f"AI解卦失败: {str(e)}")

        thread = threading.Thread(target=run_ai, daemon=True)
        thread.start()

    # ==================== API测试功能 ====================

    def _api_health_check(self):
        """API健康检查"""
        if not HAS_REQUESTS:
            messagebox.showerror("错误", "未安装requests库，请先安装: pip install requests")
            return

        url = self.api_test_url_var.get().strip()
        try:
            resp = requests.get(f"{url}/health", timeout=5)
            result = resp.json()
            self._show_api_result(f"健康检查成功:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            self._show_api_result(f"健康检查失败: {str(e)}")

    def _test_cast_api(self):
        """测试/cast接口"""
        if not HAS_REQUESTS:
            messagebox.showerror("错误", "未安装requests库")
            return

        url = self.api_test_url_var.get().strip()
        try:
            resp = requests.post(f"{url}/cast", timeout=10)
            result = resp.json()
            self._show_api_result(f"/cast 接口响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            self._show_api_result(f"/cast 接口调用失败: {str(e)}")

    def _test_analyze_api(self):
        """测试/analyze接口"""
        if not HAS_REQUESTS:
            messagebox.showerror("错误", "未安装requests库")
            return

        if len(self.lines) != 6:
            messagebox.showwarning("警告", "请先在「起卦与解卦」选项卡中完成起卦")
            return

        url = self.api_test_url_var.get().strip()
        payload = {
            "lines": [line.value for line in self.lines]
        }

        try:
            resp = requests.post(f"{url}/analyze", json=payload, timeout=10)
            result = resp.json()
            self._show_api_result(f"/analyze 接口响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            self._show_api_result(f"/analyze 接口调用失败: {str(e)}")

    def _test_ai_api(self):
        """测试/ai接口"""
        if not HAS_REQUESTS:
            messagebox.showerror("错误", "未安装requests库")
            return

        if len(self.lines) != 6:
            messagebox.showwarning("警告", "请先在「起卦与解卦」选项卡中完成起卦")
            return

        url = self.api_test_url_var.get().strip()
        api_key = self.api_key_var.get().strip() if hasattr(self, 'api_key_var') else ""
        payload = {
            "lines": [line.value for line in self.lines],
            "question": "事业运势如何？",
            "api_key": api_key
        }

        try:
            resp = requests.post(f"{url}/ai", json=payload, timeout=30)
            result = resp.json()
            self._show_api_result(f"/ai 接口响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            self._show_api_result(f"/ai 接口调用失败: {str(e)}")

    def _show_api_result(self, text):
        """显示API测试结果"""
        if hasattr(self, 'api_result_text'):
            self.api_result_text.delete(1.0, tk.END)
            self.api_result_text.insert(tk.END, text)

    # ==================== 模型测试功能 ====================

    def _fetch_models(self):
        """获取可用模型列表"""
        if not HAS_REQUESTS:
            messagebox.showerror("错误", "未安装requests库")
            return
        
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()
        
        if not api_key:
            messagebox.showwarning("警告", "请先输入API Key")
            return
        
        def run_fetch():
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                
                # 尝试多个可能的端点
                endpoints = [
                    f"{base_url}/v1/models",
                    f"{base_url}/models",
                    f"{base_url}",
                ]
                
                model_ids = []
                last_error = None
                
                for endpoint in endpoints:
                    try:
                        resp = requests.get(endpoint, headers=headers, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            models = data.get('data', [])
                            model_ids = [m.get('id', '') for m in models if m.get('id')]
                            if model_ids:
                                break
                    except Exception as e:
                        last_error = str(e)
                        continue
                
                if model_ids:
                    self.model_combo['values'] = model_ids
                    self.model_combo_var.set(model_ids[0] if model_ids else "")
                    messagebox.showinfo("成功", f"已获取 {len(model_ids)} 个模型")
                else:
                    # 使用预设模型列表
                    preset_models = ["Qwen3.6-27B", "qwen-plus", "gpt-4o", "deepseek-chat"]
                    self.model_combo['values'] = preset_models
                    self.model_combo_var.set("Qwen3.6-27B")
                    messagebox.showinfo("提示", f"未能获取模型列表，已使用预设模型\n\n错误: {last_error[:100] if last_error else 'Unknown'}")
                    
            except Exception as e:
                messagebox.showerror("错误", f"获取模型列表失败: {str(e)[:100]}")
        
        thread = threading.Thread(target=run_fetch, daemon=True)
        thread.start()

    def _test_model_direct(self):
        """直接测试选中的模型"""
        if not HAS_REQUESTS:
            messagebox.showerror("错误", "未安装requests库")
            return

        model_name = self.model_combo_var.get().strip()
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()

        if not api_key:
            messagebox.showwarning("警告", "请输入API Key")
            return

        if not model_name:
            messagebox.showwarning("警告", "请选择或输入模型名称")
            return

        def run_test():
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                }

                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": "联通性测试，请只回复'OK'"},
                    ],
                    "max_tokens": 10,
                }
                
                # 尝试多个可能的端点
                endpoints = [
                    f"{base_url}/v1/chat/completions",
                    f"{base_url}/chat/completions",
                    f"{base_url}/v1",
                ]
                
                last_error = None
                for endpoint in endpoints:
                    try:
                        resp = requests.post(
                            endpoint,
                            headers=headers,
                            json=payload,
                            timeout=30,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = (
                                data.get("choices", [{}])[0]
                                .get("message", {})
                                .get("content", "")
                                .strip()
                            )

                            usage = data.get('usage', {})
                            result_text = f"✅ 模型测试成功!\n\n"
                            result_text += f"模型: {model_name}\n"
                            result_text += f"端点: {endpoint}\n"
                            result_text += f"回复: {content}\n"
                            result_text += f"Token使用: {json.dumps(usage, ensure_ascii=False)}"

                            messagebox.showinfo("成功", result_text)
                            return
                        else:
                            last_error = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    except Exception as e:
                        last_error = str(e)
                        continue
                
                messagebox.showerror("错误", f"所有端点测试失败:\n{last_error[:200]}")

            except Exception as e:
                messagebox.showerror("错误", f"模型测试失败: {str(e)[:200]}")

        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()


def main():
    """启动GUI应用"""
    root = tk.Tk()
    app = YiJingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
