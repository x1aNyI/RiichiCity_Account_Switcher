from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, simpledialog

from models.account import Account
from models.settings import Settings
from services.account_order_service import AccountOrderService
from services.account_service import AccountService
from services.environment_service import EnvironmentService
from services.launch_service import LaunchService
from services.log_service import LogService
from services.registry_service import RegistryService
from services.settings_service import SettingsService
from services.switch_service import SwitchService
from ui.feedback import FeedbackManager


class MainWindow:
    def __init__(self) -> None:
        self.logger = LogService.get_logger(self.__class__.__name__)
        self.settings_service = SettingsService()
        self.account_service = AccountService()
        self.account_order_service = AccountOrderService()
        self.registry_service = RegistryService()
        self.launch_service = LaunchService()
        self.environment_service = EnvironmentService(
            settings_service=self.settings_service,
            registry_service=self.registry_service,
            launch_service=self.launch_service,
        )
        self.switch_service = SwitchService(
            registry_service=self.registry_service,
            launch_service=self.launch_service,
        )
        self.root = tk.Tk()
        self.root.title("麻雀一番街 切号器")
        self.root.geometry("760x560")
        self.root.minsize(760, 560)
        self.root.eval("tk::PlaceWindow . center")

        self.feedback = FeedbackManager(self.root)

        self.launch_mode_var = tk.StringVar(value="steam")
        self.local_path_var = tk.StringVar(value="")
        self.summary_var = tk.StringVar(value="")
        self.environment_var = tk.StringVar(value="")
        self.selected_count_var = tk.StringVar(value="未选择账号")
        self.select_all_var = tk.BooleanVar(value=False)
        self.is_batch_delete_mode = False

        self.accounts_canvas: tk.Canvas | None = None
        self.accounts_container: tk.Frame | None = None
        self.accounts_scrollbar: tk.Scrollbar | None = None
        self.info_window: tk.Toplevel | None = None
        self.summary_text_widget: tk.Text | None = None
        self.environment_text_widget: tk.Text | None = None
        self.path_frame: tk.Frame | None = None
        self.actions_frame: tk.Frame | None = None
        self.list_frame: tk.Frame | None = None
        self.batch_delete_mode_button: tk.Button | None = None
        self.batch_delete_execute_button: tk.Button | None = None
        self.selection_frame: tk.Frame | None = None
        self.selection_count_label: tk.Label | None = None
        self.select_all_checkbox: tk.Checkbutton | None = None

        self.account_item_frames: dict[str, tk.Frame] = {}
        self.account_selection_vars: dict[str, tk.BooleanVar] = {}
        self.drag_account_id: str | None = None
        self.drag_start_y = 0
        self.drag_last_target_index: int | None = None
        self.drag_feedback_label: tk.Label | None = None

        self._build_layout()
        self._load_initial_state()

    def _build_layout(self) -> None:
        container = tk.Frame(self.root, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        title = tk.Label(container, text="麻雀一番街切号器", font=("Microsoft YaHei UI", 14, "bold"))
        title.pack(anchor="w")

        toolbar = tk.LabelFrame(container, text="运行配置", padx=12, pady=12)
        toolbar.pack(fill="x", pady=(12, 0))

        mode_frame = tk.Frame(toolbar)
        mode_frame.pack(fill="x", anchor="w")

        tk.Label(mode_frame, text="启动方式：").pack(side="left")
        tk.Radiobutton(
            mode_frame,
            text="Steam 版",
            value="steam",
            variable=self.launch_mode_var,
            command=self._on_launch_mode_change,
        ).pack(side="left")
        tk.Radiobutton(
            mode_frame,
            text="官网版",
            value="local",
            variable=self.launch_mode_var,
            command=self._on_launch_mode_change,
        ).pack(side="left", padx=(12, 0))

        self.path_frame = tk.Frame(toolbar, pady=8)
        self.path_frame.pack(fill="x")

        tk.Label(self.path_frame, text="官网路径：").pack(side="left")
        self.local_path_entry = tk.Entry(self.path_frame, textvariable=self.local_path_var, width=58, state="readonly")
        self.local_path_entry.pack(side="left", fill="x", expand=True)

        self.choose_path_button = tk.Button(self.path_frame, text="选择游戏位置", command=self._choose_local_game_path)
        self.choose_path_button.pack(side="left", padx=(8, 0))

        self.actions_frame = tk.Frame(toolbar)
        self.actions_frame.pack(fill="x", pady=(4, 0))

        tk.Button(self.actions_frame, text="启动游戏", command=self._launch_game).pack(side="left")
        tk.Button(self.actions_frame, text="导入当前登录账号", command=self._save_current_account).pack(side="left", padx=(8, 0))
        self.batch_delete_mode_button = tk.Button(
            self.actions_frame,
            text="批量删除账号",
            command=self._toggle_batch_delete_mode,
        )
        self.batch_delete_mode_button.pack(side="left", padx=(8, 0))
        tk.Button(self.actions_frame, text="查看环境信息", command=self._open_info_window).pack(side="right")

        accounts_frame = tk.LabelFrame(container, text="账号列表", padx=12, pady=12)
        accounts_frame.pack(fill="both", expand=True, pady=(12, 0))

        self.selection_frame = tk.Frame(accounts_frame)

        self.select_all_checkbox = tk.Checkbutton(
            self.selection_frame,
            text="全选",
            variable=self.select_all_var,
            command=self._toggle_select_all_accounts,
        )
        self.select_all_checkbox.pack(side="left")

        self.selection_count_label = tk.Label(self.selection_frame, textvariable=self.selected_count_var)
        self.selection_count_label.pack(side="left", padx=(12, 0))

        self.batch_delete_execute_button = tk.Button(
            self.selection_frame,
            text="批量删除",
            command=self._delete_selected_accounts,
            state="disabled",
        )
        self.batch_delete_execute_button.pack(side="right")

        self.list_frame = tk.Frame(accounts_frame)
        self.list_frame.pack(fill="both", expand=True)

        self.accounts_canvas = tk.Canvas(self.list_frame, highlightthickness=0, borderwidth=0)
        self.accounts_canvas.pack(side="left", fill="both", expand=True)

        self.accounts_scrollbar = tk.Scrollbar(self.list_frame, orient="vertical", command=self.accounts_canvas.yview)
        self.accounts_scrollbar.pack(side="right", fill="y")

        self.accounts_canvas.configure(yscrollcommand=self.accounts_scrollbar.set)
        self.accounts_canvas.bind("<Configure>", self._on_accounts_canvas_configure)

        self.accounts_container = tk.Frame(self.accounts_canvas)
        self.accounts_window_id = self.accounts_canvas.create_window((0, 0), window=self.accounts_container, anchor="nw")
        self.accounts_container.bind("<Configure>", self._on_accounts_container_configure)

        self._bind_accounts_mousewheel()
        self._refresh_batch_delete_mode_ui()

    def _load_initial_state(self) -> None:
        settings = self.settings_service.load()
        accounts = self.account_order_service.apply_order(self.account_service.load_all())
        environment_results = self.environment_service.check()

        existing_selected_ids = {account_id for account_id, var in self.account_selection_vars.items() if var.get()}
        self.account_selection_vars = {}
        for account in accounts:
            self.account_selection_vars[account.account_id] = tk.BooleanVar(
                value=self.is_batch_delete_mode and account.account_id in existing_selected_ids
            )

        self.launch_mode_var.set(settings.launch_mode)
        self.local_path_var.set(settings.local_game_path)
        self._sync_launch_mode_widgets()

        self.summary_var.set(
            f"启动方式：{'Steam 版' if settings.launch_mode == 'steam' else '官网版'}\n"
            f"官网路径：{settings.local_game_path or '未配置'}\n"
            f"数据目录：{self.account_service.accounts_file.parent}\n"
            f"进程名：{settings.exe_name}\n"
            f"账号总数：{len(accounts)}\n"
            f"日志文件：{LogService.get_log_file()}"
        )
        self.environment_var.set("\n".join(f"[{item.level.upper()}] {item.message}" for item in environment_results))
        self._refresh_info_window_content()
        self._render_accounts(accounts)
        self._refresh_selection_controls()
        self._refresh_batch_delete_mode_ui()

    def _render_accounts(self, accounts: list[Account]) -> None:
        if self.accounts_container is None:
            return

        self._clear_drag_state()
        self.account_item_frames = {}
        for child in self.accounts_container.winfo_children():
            child.destroy()

        if not accounts:
            empty_label = tk.Label(self.accounts_container, text="暂无账号，请先点击“导入当前登录账号”将当前登录账号添加到账号列表。", anchor="w")
            empty_label.pack(fill="x", anchor="w")
            return

        for account in accounts:
            self._render_account_item(account)

        if self.accounts_canvas is not None:
            self.accounts_container.update_idletasks()
            self.accounts_canvas.configure(scrollregion=self.accounts_canvas.bbox("all"))
            self.accounts_canvas.yview_moveto(0)

    def _render_account_item(self, account: Account) -> None:
        if self.accounts_container is None:
            return

        item_frame = tk.Frame(self.accounts_container, bd=1, relief="solid", padx=10, pady=10, cursor="fleur", bg="white")
        item_frame.pack(fill="x", pady=(0, 8))
        self.account_item_frames[account.account_id] = item_frame

        content_frame = tk.Frame(item_frame, bg="white")
        content_frame.pack(fill="x")
        self._bind_account_drag_events(item_frame, account.account_id)
        self._bind_account_drag_events(content_frame, account.account_id)

        selection_var = self.account_selection_vars.setdefault(account.account_id, tk.BooleanVar(value=False))
        if self.is_batch_delete_mode:
            selection_checkbox = tk.Checkbutton(
                content_frame,
                variable=selection_var,
                command=self._refresh_selection_controls,
                bg="white",
                activebackground="white",
                cursor="arrow",
            )
            selection_checkbox.pack(side="left", padx=(0, 8))

        remark_label = tk.Label(
            content_frame,
            text=account.remark or "未命名账号",
            font=("Microsoft YaHei UI", 11, "bold"),
            anchor="w",
            bg="white",
        )
        remark_label.pack(side="left", fill="x", expand=True)
        self._bind_account_drag_events(remark_label, account.account_id)

        actions_frame = tk.Frame(content_frame, cursor="arrow", bg="white")
        actions_frame.pack(side="right")

        tk.Button(
            actions_frame,
            text="切换账号",
            command=lambda current_account=account: self._switch_account(current_account),
        ).pack(side="left")

        tk.Button(
            actions_frame,
            text="编辑备注",
            command=lambda account_id=account.account_id: self._edit_account_remark(account_id),
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            actions_frame,
            text="删除账号",
            command=lambda current_account=account: self._delete_account(current_account),
        ).pack(side="left", padx=(8, 0))

    def _on_accounts_container_configure(self, _event: tk.Event) -> None:
        if self.accounts_canvas is None or self.accounts_container is None:
            return
        self.accounts_canvas.configure(scrollregion=self.accounts_canvas.bbox("all"))

    def _on_accounts_canvas_configure(self, event: tk.Event) -> None:
        if self.accounts_canvas is None or self.accounts_container is None:
            return
        self.accounts_canvas.itemconfigure(self.accounts_window_id, width=event.width)

    def _bind_accounts_mousewheel(self) -> None:
        self.root.bind_all("<MouseWheel>", self._on_accounts_mousewheel, add="+")
        self.root.bind_all("<Prior>", self._on_accounts_page_scroll, add="+")
        self.root.bind_all("<Next>", self._on_accounts_page_scroll, add="+")

    def _on_accounts_mousewheel(self, event: tk.Event) -> None:
        if self.accounts_canvas is None:
            return
        if self.root.focus_displayof() is None:
            return

        widget_under_pointer = self.root.winfo_containing(self.root.winfo_pointerx(), self.root.winfo_pointery())
        if widget_under_pointer is None or not self._is_widget_in_accounts_area(widget_under_pointer):
            return

        delta = int(-event.delta / 120) if event.delta else 0
        if delta != 0:
            self.accounts_canvas.yview_scroll(delta, "units")

    def _on_accounts_page_scroll(self, event: tk.Event) -> None:
        if self.accounts_canvas is None:
            return

        focused_widget = self.root.focus_get()
        if focused_widget is None or not self._is_widget_in_accounts_area(focused_widget):
            return

        direction = -1 if event.keysym == "Prior" else 1
        self.accounts_canvas.yview_scroll(direction, "pages")

    def _is_widget_in_accounts_area(self, widget: tk.Misc | None) -> bool:
        if widget is None or self.accounts_canvas is None:
            return False

        current_widget = widget
        while current_widget is not None:
            if current_widget == self.accounts_canvas or current_widget == self.accounts_container:
                return True
            parent_name = current_widget.winfo_parent()
            if not parent_name:
                break
            current_widget = current_widget.nametowidget(parent_name)
        return False

    def _build_settings_from_form(self, current_settings: Settings | None = None) -> Settings:
        base_settings = current_settings or self.settings_service.load()
        launch_mode = self.launch_mode_var.get()
        local_game_path = self.local_path_var.get().strip() if launch_mode == "local" else base_settings.local_game_path
        return Settings(
            launch_mode=launch_mode,
            local_game_path=local_game_path,
            exe_name=base_settings.exe_name,
        )

    def _format_info_copy_text(self) -> str:
        summary_text = self.summary_var.get().strip() or "暂无数据"
        environment_text = self.environment_var.get().strip() or "暂无数据"
        return f"【当前状态】\n{summary_text}\n\n【环境检测】\n{environment_text}"

    def _create_readonly_text(self, parent: tk.Widget) -> tk.Text:
        text_widget = tk.Text(
            parent,
            height=8,
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=2,
            pady=2,
            font=("Microsoft YaHei UI", 10),
        )
        text_widget.config(state="disabled")
        return text_widget

    def _set_text_widget_content(self, text_widget: tk.Text | None, content: str) -> None:
        if text_widget is None:
            return
        text_widget.config(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", content)
        text_widget.config(state="disabled")

    def _refresh_info_window_content(self) -> None:
        self._set_text_widget_content(self.summary_text_widget, self.summary_var.get())
        self._set_text_widget_content(self.environment_text_widget, self.environment_var.get())

    def _open_info_window(self) -> None:
        if self.info_window is not None and self.info_window.winfo_exists():
            self._refresh_info_window_content()
            self.info_window.deiconify()
            self.info_window.lift()
            self.info_window.focus_force()
            return

        self.info_window = tk.Toplevel(self.root)
        self.info_window.title("环境信息")
        self.info_window.geometry("700x500")
        self.info_window.minsize(680, 460)
        self.info_window.transient(self.root)
        self.info_window.protocol("WM_DELETE_WINDOW", self._close_info_window)

        container = tk.Frame(self.info_window, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        header_frame = tk.Frame(container)
        header_frame.pack(fill="x")

        tk.Label(header_frame, text="环境信息", font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")
        tk.Button(header_frame, text="复制信息", command=self._copy_info_content).pack(side="right")

        summary_frame = tk.LabelFrame(container, text="当前状态", padx=12, pady=12)
        summary_frame.pack(fill="both", expand=True, pady=(12, 8))
        self.summary_text_widget = self._create_readonly_text(summary_frame)
        self.summary_text_widget.pack(fill="both", expand=True)

        environment_frame = tk.LabelFrame(container, text="环境检测", padx=12, pady=12)
        environment_frame.pack(fill="both", expand=True)
        self.environment_text_widget = self._create_readonly_text(environment_frame)
        self.environment_text_widget.pack(fill="both", expand=True)

        self._refresh_info_window_content()

    def _close_info_window(self) -> None:
        if self.info_window is not None and self.info_window.winfo_exists():
            self.info_window.destroy()
        self.info_window = None
        self.summary_text_widget = None
        self.environment_text_widget = None

    def _copy_info_content(self) -> None:
        copy_text = self._format_info_copy_text()
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(copy_text)
            self.root.update_idletasks()
            self.feedback.show_success("已复制环境信息到剪贴板", parent=self.info_window or self.root)
        except tk.TclError as exc:
            self.logger.warning("复制环境信息失败：%s", exc)
            self.feedback.show_error("错误", "复制失败，请稍后重试。", parent=self.info_window or self.root)

    def _on_launch_mode_change(self) -> None:
        settings = self._build_settings_from_form()
        self.settings_service.save(settings)
        self._sync_launch_mode_widgets()
        self._load_initial_state()

    def _sync_launch_mode_widgets(self) -> None:
        is_local_mode = self.launch_mode_var.get() == "local"

        if self.path_frame is not None:
            if is_local_mode:
                if not self.path_frame.winfo_manager():
                    if self.actions_frame is not None:
                        self.path_frame.pack(fill="x", before=self.actions_frame)
                    else:
                        self.path_frame.pack(fill="x")
            elif self.path_frame.winfo_manager():
                self.path_frame.pack_forget()

        self.choose_path_button.config(state="normal" if is_local_mode else "disabled")

    def _choose_local_game_path(self) -> None:
        if self.launch_mode_var.get() != "local":
            return

        selected_path = filedialog.askopenfilename(
            title="选择官网版游戏程序",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")],
        )
        if not selected_path:
            return
        if not self.launch_service.validate_local_game_path(selected_path):
            self.feedback.show_error("错误", "所选路径不是有效的游戏可执行文件。", parent=self.root)
            return

        self.local_path_var.set(selected_path)
        settings = self._build_settings_from_form()
        self.settings_service.save(settings)
        self._load_initial_state()

    def _launch_game(self) -> None:
        try:
            settings = self._build_settings_from_form()
            if settings.launch_mode == "local" and not self.launch_service.validate_local_game_path(settings.local_game_path):
                raise FileNotFoundError("官网版游戏路径无效，请先配置正确的 .exe 文件路径。")
            self.launch_service.launch_game(settings)
            self.feedback.show_success("已发起游戏启动请求，请稍候", parent=self.root)
        except FileNotFoundError as exc:
            self.logger.error("启动游戏失败：%s", exc)
            self.feedback.show_error("错误", str(exc), parent=self.root)
        except OSError as exc:
            self.logger.exception("启动游戏异常")
            self.feedback.show_error("错误", f"启动游戏失败：{exc}", parent=self.root)

    def _save_current_account(self) -> None:
        try:
            snapshot = self.registry_service.read_current_account_snapshot()
            if not snapshot:
                self.feedback.show_warning("提示", "未读取到当前登录账号数据，请确认游戏已登录。", parent=self.root)
                return
            default_remark = f"账号{len(self.account_service.load_all()) + 1}"
            account = self.account_service.add_account(default_remark, snapshot)
            self.account_order_service.append_account(account.account_id)
            self._load_initial_state()
            self.feedback.show_success(f"已导入账号：{account.remark}", parent=self.root)
        except FileNotFoundError:
            self.logger.warning("保存账号失败：账号数据路径不存在")
            self.feedback.show_error("错误", "未找到当前登录账号数据，请先启动并登录一次游戏。", parent=self.root)
        except OSError:
            self.logger.exception("保存账号时读取账号数据失败")
            self.feedback.show_error("错误", "读取账号数据失败，请检查权限或确认游戏已正确登录。", parent=self.root)

    def _edit_account_remark(self, account_id: str) -> None:
        accounts = self.account_service.load_all()
        account = next((item for item in accounts if item.account_id == account_id), None)
        if account is None:
            self.feedback.show_error("错误", "未找到要编辑的账号。", parent=self.root)
            return

        new_remark = simpledialog.askstring("编辑备注", "请输入新的账号备注：", initialvalue=account.remark, parent=self.root)
        if new_remark is None:
            return

        normalized_remark = new_remark.strip()
        if not normalized_remark:
            self.feedback.show_warning("提示", "备注不能为空。", parent=self.root)
            return

        try:
            self.account_service.update_remark(account_id, normalized_remark)
            self._load_initial_state()
            self.feedback.show_success("账号备注已更新", parent=self.root)
        except ValueError as exc:
            self.logger.warning("编辑备注失败：%s", exc)
            self.feedback.show_error("错误", str(exc), parent=self.root)

    def _get_selected_account_ids(self) -> list[str]:
        return [account_id for account_id, var in self.account_selection_vars.items() if var.get()]

    def _clear_account_selection(self) -> None:
        for selection_var in self.account_selection_vars.values():
            selection_var.set(False)
        self.select_all_var.set(False)
        self.selected_count_var.set("未选择账号")

    def _refresh_batch_delete_mode_ui(self) -> None:
        if self.selection_frame is None:
            return

        if self.is_batch_delete_mode:
            if not self.selection_frame.winfo_manager():
                if self.list_frame is not None:
                    self.selection_frame.pack(fill="x", pady=(0, 8), before=self.list_frame)
                else:
                    self.selection_frame.pack(fill="x", pady=(0, 8))
            if self.batch_delete_mode_button is not None:
                self.batch_delete_mode_button.config(relief="sunken")
        else:
            if self.selection_frame.winfo_manager():
                self.selection_frame.pack_forget()
            if self.batch_delete_mode_button is not None:
                self.batch_delete_mode_button.config(relief="raised")

    def _refresh_selection_controls(self) -> None:
        selected_ids = self._get_selected_account_ids()
        selected_count = len(selected_ids)
        total_count = len(self.account_selection_vars)

        if self.batch_delete_execute_button is not None:
            button_state = "normal" if self.is_batch_delete_mode and selected_count > 0 else "disabled"
            self.batch_delete_execute_button.config(state=button_state)

        if self.select_all_checkbox is not None:
            if not self.is_batch_delete_mode or total_count == 0:
                self.select_all_var.set(False)
                self.select_all_checkbox.config(state="disabled")
            else:
                self.select_all_var.set(selected_count == total_count)
                self.select_all_checkbox.config(state="normal")

        if not self.is_batch_delete_mode:
            self.selected_count_var.set("未选择账号")
        elif total_count == 0:
            self.selected_count_var.set("暂无账号")
        elif selected_count == 0:
            self.selected_count_var.set(f"共 {total_count} 个账号，未选择账号")
        else:
            self.selected_count_var.set(f"共 {total_count} 个账号，已选择 {selected_count} 个")

    def _toggle_batch_delete_mode(self) -> None:
        self.is_batch_delete_mode = not self.is_batch_delete_mode
        if not self.is_batch_delete_mode:
            self._clear_account_selection()
        self._render_accounts(self.account_order_service.apply_order(self.account_service.load_all()))
        self._refresh_selection_controls()
        self._refresh_batch_delete_mode_ui()

    def _toggle_select_all_accounts(self) -> None:
        target_value = self.select_all_var.get()
        for selection_var in self.account_selection_vars.values():
            selection_var.set(target_value)
        self._refresh_selection_controls()

    def _build_delete_confirmation_message(self, accounts: list[Account]) -> str:
        remarks = [account.remark or "未命名账号" for account in accounts]
        account_lines = "\n".join(f"- {remark}" for remark in remarks)
        return (
            f"即将物理删除以下 {len(accounts)} 个账号：\n\n"
            f"{account_lines}\n\n"
            "删除后将无法从切号器中恢复，是否继续？"
        )

    def _delete_account(self, account: Account) -> None:
        confirmed = self.feedback.ask_confirm(
            "确认删除",
            self._build_delete_confirmation_message([account]),
            parent=self.root,
        )
        if not confirmed:
            return

        try:
            self.account_service.delete_account(account.account_id)
            self.account_order_service.remove_account(account.account_id)
            self._load_initial_state()
            self.feedback.show_success("账号已删除", parent=self.root)
        except OSError as exc:
            self.logger.warning("删除账号失败：%s", exc)
            self.feedback.show_error("错误", "删除账号失败，请稍后重试。", parent=self.root)

    def _delete_selected_accounts(self) -> None:
        selected_ids = self._get_selected_account_ids()
        if not selected_ids:
            self.feedback.show_warning("提示", "请先选择要删除的账号。", parent=self.root)
            return

        accounts = self.account_order_service.apply_order(self.account_service.load_all())
        selected_accounts = [account for account in accounts if account.account_id in selected_ids]
        if not selected_accounts:
            self.feedback.show_warning("提示", "未找到要删除的账号，请刷新后重试。", parent=self.root)
            self._load_initial_state()
            return

        confirmed = self.feedback.ask_confirm(
            "确认批量删除",
            self._build_delete_confirmation_message(selected_accounts),
            parent=self.root,
        )
        if not confirmed:
            return

        try:
            for account in selected_accounts:
                self.account_service.delete_account(account.account_id)
                self.account_order_service.remove_account(account.account_id)
            self.is_batch_delete_mode = False
            self._clear_account_selection()
            self._load_initial_state()
            self.feedback.show_success(f"已删除 {len(selected_accounts)} 个账号", parent=self.root)
        except OSError as exc:
            self.logger.warning("批量删除账号失败：%s", exc)
            self.feedback.show_error("错误", "批量删除账号失败，请稍后重试。", parent=self.root)

    def _switch_account(self, account: Account) -> None:
        try:
            settings = self._build_settings_from_form()
            if settings.launch_mode == "local" and not self.launch_service.validate_local_game_path(settings.local_game_path):
                raise FileNotFoundError("官网版游戏路径无效，请先配置正确的 .exe 文件路径。")
            self.switch_service.switch_account(account, settings)
            self.feedback.show_success(f"已切换到账号：{account.remark}", parent=self.root)
        except FileNotFoundError as exc:
            self.logger.warning("切号失败：%s", exc)
            self.feedback.show_error("错误", str(exc), parent=self.root)
        except TimeoutError as exc:
            self.logger.warning("切号失败：%s", exc)
            self.feedback.show_error("错误", str(exc), parent=self.root)
        except OSError:
            self.logger.exception("切号时发生异常")
            self.feedback.show_error("错误", "切号失败，请查看日志文件获取详细信息。", parent=self.root)

    def _bind_account_drag_events(self, widget: tk.Widget, account_id: str) -> None:
        widget.bind("<ButtonPress-1>", lambda event, current_account_id=account_id: self._on_account_drag_start(event, current_account_id), add="+")
        widget.bind("<B1-Motion>", self._on_account_drag_motion, add="+")
        widget.bind("<ButtonRelease-1>", self._on_account_drag_release, add="+")

    def _on_account_drag_start(self, event: tk.Event, account_id: str) -> None:
        if self._is_drag_blocked_widget(event.widget):
            self._clear_drag_state()
            return

        self.drag_account_id = account_id
        self.drag_start_y = event.y_root
        self.drag_last_target_index = None
        self._set_account_drag_highlight(account_id, active=True)

    def _on_account_drag_motion(self, event: tk.Event) -> None:
        if self.drag_account_id is None or self.accounts_container is None:
            return
        if abs(event.y_root - self.drag_start_y) < 8:
            return

        target_index = self._get_drop_target_index(event.y_root)
        if target_index is None:
            return

        self.drag_last_target_index = target_index
        self._auto_scroll_accounts(event.y_root)
        self._show_drag_feedback(target_index)

    def _on_account_drag_release(self, _event: tk.Event) -> None:
        if self.drag_account_id is None:
            return

        dragged_account_id = self.drag_account_id
        target_index = self.drag_last_target_index
        self._clear_drag_state()
        if target_index is None:
            return

        try:
            changed = self.account_order_service.move_account(dragged_account_id, target_index)
            if changed:
                self._load_initial_state()
                self.feedback.show_success("账号顺序已保存", parent=self.root, duration_ms=1500)
        except OSError as exc:
            self.logger.warning("保存账号顺序失败：%s", exc)
            self.feedback.show_error("错误", "保存账号顺序失败，请稍后重试。", parent=self.root)

    def _is_drag_blocked_widget(self, widget: tk.Misc) -> bool:
        current_widget: tk.Misc | None = widget
        while current_widget is not None:
            if isinstance(current_widget, (tk.Button, tk.Entry, tk.Text, tk.Scrollbar, tk.Radiobutton, tk.Checkbutton)):
                return True
            parent_name = current_widget.winfo_parent()
            if not parent_name:
                break
            current_widget = current_widget.nametowidget(parent_name)
        return False

    def _get_drop_target_index(self, y_root: int) -> int | None:
        if not self.account_item_frames:
            return None

        items = list(self.account_item_frames.items())
        for index, (_account_id, frame) in enumerate(items):
            top = frame.winfo_rooty()
            middle = top + frame.winfo_height() // 2
            if y_root < middle:
                return index
        return len(items) - 1

    def _show_drag_feedback(self, target_index: int) -> None:
        if self.accounts_container is None or self.accounts_canvas is None:
            return

        item_frames = list(self.account_item_frames.values())
        if not item_frames:
            return

        target_index = max(0, min(target_index, len(item_frames) - 1))
        target_frame = item_frames[target_index]

        if self.drag_feedback_label is None or not self.drag_feedback_label.winfo_exists():
            self.drag_feedback_label = tk.Label(self.accounts_canvas, bg="#4c6ef5", height=1, borderwidth=0, highlightthickness=0)

        self.accounts_container.update_idletasks()
        self.accounts_canvas.update_idletasks()

        target_y = target_frame.winfo_y()
        self.drag_feedback_label.place(x=0, y=max(target_y - 3, 0), relwidth=1, height=3)
        self.drag_feedback_label.lift()

    def _auto_scroll_accounts(self, y_root: int) -> None:
        if self.accounts_canvas is None:
            return

        scrollregion = self.accounts_canvas.cget("scrollregion")
        if not scrollregion:
            return

        try:
            _left, top, _right, bottom = [int(float(value)) for value in str(scrollregion).split()]
        except (ValueError, TypeError):
            return

        if bottom - top <= self.accounts_canvas.winfo_height():
            self.accounts_canvas.yview_moveto(0)
            return

        canvas_top = self.accounts_canvas.winfo_rooty()
        canvas_bottom = canvas_top + self.accounts_canvas.winfo_height()
        edge_threshold = 48

        if y_root < canvas_top + edge_threshold:
            self.accounts_canvas.yview_scroll(-1, "units")
        elif y_root > canvas_bottom - edge_threshold:
            self.accounts_canvas.yview_scroll(1, "units")

    def _set_account_drag_highlight(self, account_id: str, *, active: bool) -> None:
        frame = self.account_item_frames.get(account_id)
        if frame is None or not frame.winfo_exists():
            return
        background = "#eaf2ff" if active else "white"
        frame.configure(bg=background)
        for child in frame.winfo_children():
            self._sync_child_background(child, background)

    def _sync_child_background(self, widget: tk.Misc, background: str) -> None:
        try:
            widget.tk.call(str(widget), "configure", "-background", background)
        except tk.TclError:
            return
        for child in widget.winfo_children():
            self._sync_child_background(child, background)

    def _clear_drag_state(self) -> None:
        if self.drag_account_id is not None:
            self._set_account_drag_highlight(self.drag_account_id, active=False)
        self.drag_account_id = None
        self.drag_start_y = 0
        self.drag_last_target_index = None
        if self.drag_feedback_label is not None and self.drag_feedback_label.winfo_exists():
            self.drag_feedback_label.place_forget()
            self.drag_feedback_label.destroy()
        self.drag_feedback_label = None
        if self.accounts_canvas is not None:
            scrollregion = self.accounts_canvas.cget("scrollregion")
            if scrollregion:
                try:
                    _left, top, _right, bottom = [int(float(value)) for value in str(scrollregion).split()]
                except (ValueError, TypeError):
                    return
                if bottom - top <= self.accounts_canvas.winfo_height():
                    self.accounts_canvas.yview_moveto(0)

    def run(self) -> None:
        self.logger.info("主窗口启动")
        self.root.mainloop()


def main() -> None:
    MainWindow().run()
