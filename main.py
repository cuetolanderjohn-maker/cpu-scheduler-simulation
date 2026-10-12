import tkinter as tk
from tkinter import ttk, messagebox
import copy

class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=1):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.original_burst = burst_time

        self.start_time = -1
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.remaining_time = burst_time

class SchedulerEngine:
    def __init__(self, processes):
        self.processes = copy.deepcopy(processes)
        self.gantt_data = []  # list of (pid,start,end)

    def reset(self):
        for p in self.processes:
            p.start_time = -1
            p.completion_time = 0
            p.turnaround_time = 0
            p.waiting_time = 0
            p.remaining_time = p.burst_time
        self.gantt_data = []

    def add_gantt(self, pid, start, end):
        if end <= start:
            return
        self.gantt_data.append((pid, start, end))

    def _close_last_segment(self, last_pid, last_start, current_time):
        if last_pid is not None and last_start is not None and current_time > last_start:
            self.add_gantt(last_pid, last_start, current_time)

    def run_fcfs(self):
        self.reset()
        processes = sorted(self.processes, key=lambda x: (x.arrival_time, x.pid))
        current_time = 0

        for p in processes:
            if current_time < p.arrival_time:
                current_time = p.arrival_time
            p.start_time = current_time
            p.completion_time = current_time + p.burst_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            self.add_gantt(p.pid, p.start_time, p.completion_time)
            current_time = p.completion_time

        return self.get_metrics()

    def run_sjf(self):
        # Non-preemptive SJF
        self.reset()
        ready_queue = []
        completed = []
        input_procs = sorted(self.processes, key=lambda p: p.arrival_time)
        current_time = 0
        idx = 0

        while len(completed) < len(self.processes):
            while idx < len(input_procs) and input_procs[idx].arrival_time <= current_time:
                ready_queue.append(input_procs[idx])
                idx += 1

            if not ready_queue:
                if idx < len(input_procs):
                    current_time = input_procs[idx].arrival_time
                    continue
                break

            ready_queue.sort(key=lambda x: (x.burst_time, x.arrival_time, x.pid))
            p = ready_queue.pop(0)

            if current_time < p.arrival_time:
                current_time = p.arrival_time

            p.start_time = current_time
            p.completion_time = current_time + p.burst_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time

            self.add_gantt(p.pid, p.start_time, p.completion_time)
            current_time = p.completion_time
            completed.append(p)

        return self.get_metrics()

    def run_priority(self):
        # Non-preemptive Priority (lower number = higher priority)
        self.reset()
        ready_queue = []
        completed = []

        input_procs = sorted(self.processes, key=lambda p: p.arrival_time)
        current_time = 0
        idx = 0

        while len(completed) < len(self.processes):
            while idx < len(input_procs) and input_procs[idx].arrival_time <= current_time:
                ready_queue.append(input_procs[idx])
                idx += 1

            if not ready_queue:
                if idx < len(input_procs):
                    current_time = input_procs[idx].arrival_time
                    continue
                break

            ready_queue.sort(key=lambda x: (x.priority, x.arrival_time, x.pid))
            p = ready_queue.pop(0)

            if current_time < p.arrival_time:
                current_time = p.arrival_time

            p.start_time = current_time
            p.completion_time = current_time + p.burst_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time

            self.add_gantt(p.pid, p.start_time, p.completion_time)
            current_time = p.completion_time
            completed.append(p)

        return self.get_metrics()

    def run_rr(self, quantum=2):
        # Round Robin (time slice)
        self.reset()
        if quantum <= 0:
            quantum = 1

        for p in self.processes:
            p.remaining_time = p.burst_time

        ready_queue = []
        completed = []

        input_procs = sorted(self.processes, key=lambda p: p.arrival_time)
        current_time = 0
        idx = 0

        last_pid = None
        last_start = None

        while len(completed) < len(self.processes):
            while idx < len(input_procs) and input_procs[idx].arrival_time <= current_time:
                ready_queue.append(input_procs[idx])
                idx += 1

            if not ready_queue:
                if idx < len(input_procs):
                    current_time = input_procs[idx].arrival_time
                    continue
                break

            cur = ready_queue.pop(0)
            if cur.start_time == -1:
                cur.start_time = current_time

            exec_time = min(quantum, cur.remaining_time)
            start = current_time
            current_time += exec_time
            cur.remaining_time -= exec_time

            if last_pid == cur.pid and last_start is not None:
                pass
            else:
                self._close_last_segment(last_pid, last_start, start)
                last_pid = cur.pid
                last_start = start

            while idx < len(input_procs) and input_procs[idx].arrival_time <= current_time:
                ready_queue.append(input_procs[idx])
                idx += 1

            if cur.remaining_time > 0:
                ready_queue.append(cur)
            else:
                cur.completion_time = current_time
                cur.turnaround_time = cur.completion_time - cur.arrival_time
                cur.waiting_time = cur.turnaround_time - cur.original_burst
                completed.append(cur)

        self._close_last_segment(last_pid, last_start, current_time)
        return self.get_metrics()

    def get_metrics(self):
        total_wt = sum(p.waiting_time for p in self.processes)
        total_tat = sum(p.turnaround_time for p in self.processes)
        n = len(self.processes) if self.processes else 1
        return {
            "processes": self.processes,
            "avg_waiting": total_wt / n,
            "avg_turnaround": total_tat / n,
            "gantt_data": self.gantt_data,
        }

class SmartAdvisor:
    @staticmethod
    def analyze_and_recommend(processes):
        if not processes:
            return "No processes to analyze.", None

        burst_times = [p.burst_time for p in processes]
        priorities = [p.priority for p in processes]

        avg_bt = sum(burst_times) / len(burst_times)
        max_bt = max(burst_times)
        min_bt = min(burst_times)
        bt_variance = sum((bt - avg_bt) ** 2 for bt in burst_times) / len(burst_times)

        has_priority_differences = len(set(priorities)) > 1
        burst_spread = max_bt - min_bt

        if has_priority_differences:
            rec = "Priority"
            reasons = [
                "Priorities differ across processes",
                "Priority scheduling tends to reduce waiting for high-priority jobs",
            ]
        elif burst_spread > 3 and bt_variance > 10:
            rec = "SJF"
            reasons = [
                "Burst times vary significantly",
                "SJF runs shorter jobs first, often lowering average waiting",
            ]
        elif max_bt <= 5:
            rec = "RR"
            reasons = [
                "Burst times are relatively short",
                "Round Robin provides fairness with minimal overhead",
            ]
        else:
            rec = "FCFS"
            reasons = [
                "Dataset is moderate/consistent",
                "FCFS is simple and low overhead",
            ]

        msg = "=== SMART ADVISOR (Heuristic) ===\n"
        msg += f"Avg Burst: {avg_bt:.2f}\n"
        msg += f"Variance: {bt_variance:.2f}\n\n"
        msg += f"RECOMMENDATION: {rec}\n\n"
        msg += "Reasons:\n"
        for r in reasons:
            msg += f"  • {r}\n"

        return msg, rec




class OSSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COEPRO5 Group 5 Scheduler")
        self.root.geometry("1700x950")

        # Refined Dark Theme Colors
        self.bg_dark = "#0d1117"
        self.bg_card = "#161b22"
        self.bg_input = "#0d1117"
        self.accent_blue = "#58a6ff"
        self.accent_cyan = "#79c0ff"
        self.text_primary = "#c9d1d9"
        self.text_secondary = "#8b949e"
        self.border_color = "#30363d"
        self.success_green = "#3fb950"
        self.warning_yellow = "#d29922"

        self.root.configure(bg=self.bg_dark)

        self.processes = []
        self.quantum_default = 2

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self):
        """Configure refined dark theme styles - easy on the eyes"""
        style = ttk.Style()
        style.theme_use("clam")

        # Define custom colors
        style.configure("Treeview", background=self.bg_card, foreground=self.text_primary, fieldbackground=self.bg_card)
        style.configure("Treeview.Heading", background=self.bg_input, foreground=self.text_primary)
        style.map("Treeview", background=[("selected", self.accent_blue)])

        # Frames
        style.configure("Dark.TFrame", background=self.bg_dark)
        style.configure("Card.TFrame", background=self.bg_card, relief="flat")
        style.configure("Card.TLabelframe", background=self.bg_card, foreground=self.text_primary, relief="solid", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background=self.bg_card, foreground=self.accent_cyan, font=("Segoe UI", 10, "bold"))

        # Labels
        style.configure("Title.TLabel", background=self.bg_dark, foreground=self.accent_cyan, font=("Segoe UI", 20, "bold"))
        style.configure("Heading.TLabel", background=self.bg_card, foreground=self.text_primary, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=self.bg_card, foreground=self.text_secondary, font=("Segoe UI", 9))

        # Entries
        style.configure("TEntry", fieldbackground=self.bg_input, background=self.bg_input, foreground=self.text_primary, 
                       relief="solid", borderwidth=1, padding=5)
        style.map("TEntry", fieldbackground=[("focus", self.bg_input)], foreground=[("focus", self.accent_cyan)])

        # Buttons
        style.configure("TButton", background=self.bg_input, foreground=self.text_primary, relief="solid", borderwidth=1, padding=8, font=("Segoe UI", 9))
        style.map("TButton", background=[("active", self.accent_blue), ("pressed", self.accent_cyan)], foreground=[("active", "#ffffff")])

        style.configure("Primary.TButton", background=self.accent_blue, foreground=self.bg_dark, font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Primary.TButton", background=[("active", self.accent_cyan)], foreground=[("active", self.bg_dark)])

        style.configure("Secondary.TButton", background=self.border_color, foreground=self.text_primary, font=("Segoe UI", 9), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", self.accent_blue)])

        # Radiobuttons
        style.configure("TRadiobutton", background=self.bg_card, foreground=self.text_primary, font=("Segoe UI", 9))
        style.map("TRadiobutton", background=[("active", self.bg_card)], foreground=[("active", self.accent_cyan)])

    def _build_ui(self):
        # Title Bar
        title_frame = tk.Frame(self.root, bg=self.bg_dark, height=60)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_frame.pack_propagate(False)

        title = tk.Label(
            title_frame,
            text="⚙  CPU Process Scheduler",
            font=("Segoe UI", 22, "bold"),
            fg=self.accent_cyan,
            bg=self.bg_dark,
        )
        title.pack(side=tk.LEFT, padx=20, pady=10)

        subtitle = tk.Label(
            title_frame,
            text="Scheduling Algorithm Simulator for COEPRO5",
            font=("Segoe UI", 9),
            fg=self.text_secondary,
            bg=self.bg_dark,
        )
        subtitle.pack(side=tk.LEFT, padx=20)

        # Main container
        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # LEFT PANEL - Input
        left = ttk.LabelFrame(main, text=" Add Process ", style="Card.TLabelframe", padding=15)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        input_frame = ttk.Frame(left, style="Card.TFrame")
        input_frame.pack(fill=tk.X)

        # Register validation commands
        vcmd_pid = (self.root.register(self._validate_pid), '%P')
        vcmd_range = (self.root.register(self._validate_range), '%P')

        # Process ID (alphanumeric, 1-100)
        ttk.Label(input_frame, text="Process ID:", style="TLabel").grid(row=0, column=0, sticky=tk.W, pady=(0, 6))
        self.entry_pid = ttk.Entry(input_frame, width=18, validate='key', validatecommand=vcmd_pid)
        self.entry_pid.grid(row=0, column=1, sticky=tk.EW, pady=(0, 6), padx=(10, 0))

        # Arrival Time (1-100)
        ttk.Label(input_frame, text="Arrival Time:", style="TLabel").grid(row=1, column=0, sticky=tk.W, pady=(0, 6))
        self.entry_at = ttk.Entry(input_frame, width=18, validate='key', validatecommand=vcmd_range)
        self.entry_at.grid(row=1, column=1, sticky=tk.EW, pady=(0, 6), padx=(10, 0))

        # Burst Time (1-100)
        ttk.Label(input_frame, text="Burst Time:", style="TLabel").grid(row=2, column=0, sticky=tk.W, pady=(0, 6))
        self.entry_bt = ttk.Entry(input_frame, width=18, validate='key', validatecommand=vcmd_range)
        self.entry_bt.grid(row=2, column=1, sticky=tk.EW, pady=(0, 6), padx=(10, 0))

        # Priority (1-100)
        ttk.Label(input_frame, text="Priority:", style="TLabel").grid(row=3, column=0, sticky=tk.W, pady=(0, 12))
        self.entry_prio = ttk.Entry(input_frame, width=18, validate='key', validatecommand=vcmd_range)
        self.entry_prio.insert(0, "1")
        self.entry_prio.grid(row=3, column=1, sticky=tk.EW, pady=(0, 12), padx=(10, 0))

        input_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(left, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=(15, 0))

        add_btn = ttk.Button(button_frame, text="+ Add Process", command=self.add_process, style="Primary.TButton")
        add_btn.pack(fill=tk.X, pady=(0, 6))

        clear_btn = ttk.Button(button_frame, text="Clear All", command=self.clear_processes, style="Secondary.TButton")
        clear_btn.pack(fill=tk.X, pady=(0, 6))

        arrival_btn = ttk.Button(button_frame, text="View Arrivals", command=self.view_arrival_times_gantt, style="Secondary.TButton")
        arrival_btn.pack(fill=tk.X)

        # Process List
        ttk.Label(left, text="Added Processes:", style="Heading.TLabel").pack(anchor=tk.W, pady=(20, 8))

        list_frame = ttk.Frame(left, style="Card.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

        self.listbox = tk.Listbox(
            list_frame,
            height=16,
            bg=self.bg_input,
            fg=self.text_primary,
            selectbackground=self.accent_blue,
            selectforeground=self.bg_dark,
            border=0,
            font=("Segoe UI", 8),
            highlightthickness=0,
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scroll.set)

        # CENTER PANEL - Algorithm Selection
        center = ttk.LabelFrame(main, text=" Select Algorithm ", style="Card.TLabelframe", padding=15)
        center.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.algo_var = tk.StringVar(value="FCFS")

        algo_frame = ttk.Frame(center, style="Card.TFrame")
        algo_frame.pack(fill=tk.X)

        for text, val in [
            ("FCFS", "FCFS"),
            ("SJF", "SJF"),
            ("Priority", "Priority"),
            ("Round Robin", "RR"),
        ]:
            rb = ttk.Radiobutton(algo_frame, text=text, variable=self.algo_var, value=val, style="TRadiobutton")
            rb.pack(anchor=tk.W, pady=5)

        # Quantum (1-100)
        ttk.Label(center, text="Quantum (RR):", style="Heading.TLabel").pack(anchor=tk.W, pady=(18, 6))
        self.entry_q = ttk.Entry(center, width=18, validate='key', validatecommand=vcmd_range)
        self.entry_q.insert(0, str(self.quantum_default))
        self.entry_q.pack(fill=tk.X, pady=(0, 15))

        # Run buttons
        run_btn = ttk.Button(center, text="Run Schedule", command=self.run_scheduler, style="Primary.TButton")
        run_btn.pack(fill=tk.X, pady=(0, 6))

        advisor_btn = ttk.Button(center, text="Smart Advisor", command=self.run_advisor, style="Secondary.TButton")
        advisor_btn.pack(fill=tk.X)

        # RIGHT PANEL - Results and Gantt
        right = ttk.Frame(main, style="Dark.TFrame")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Metrics
        metrics_frame = ttk.LabelFrame(right, text=" Performance Metrics ", style="Card.TLabelframe", padding=12)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))

        self.metric_algo = tk.Label(metrics_frame, text="Algorithm: —", font=("Segoe UI", 10, "bold"), fg=self.accent_cyan, bg=self.bg_card)
        self.metric_algo.pack(anchor=tk.W, pady=4)

        self.metric_wt = tk.Label(metrics_frame, text="Avg Waiting Time: — ms", font=("Segoe UI", 9), fg=self.text_secondary, bg=self.bg_card)
        self.metric_wt.pack(anchor=tk.W, pady=3)

        self.metric_tat = tk.Label(metrics_frame, text="Avg Turnaround Time: — ms", font=("Segoe UI", 9), fg=self.text_secondary, bg=self.bg_card)
        self.metric_tat.pack(anchor=tk.W, pady=3)

        # Results Table
        results_frame = ttk.LabelFrame(right, text=" Process Details ", style="Card.TLabelframe", padding=12)
        results_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        table_frame = ttk.Frame(results_frame, style="Card.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(
            table_frame,
            height=8,
            bg=self.bg_input,
            fg=self.text_primary,
            border=0,
            font=("Consolas", 8),
            highlightthickness=0,
            insertbackground=self.accent_blue,
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scroll_r = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scroll_r.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scroll_r.set)

        # Gantt Chart
        gantt_frame = ttk.LabelFrame(right, text=" Gantt Chart Visualization ", style="Card.TLabelframe", padding=12)
        gantt_frame.pack(fill=tk.BOTH, expand=True)

        self.gantt_canvas = tk.Canvas(
            gantt_frame,
            bg=self.bg_input,
            highlightthickness=1,
            highlightbackground=self.border_color,
            bd=0,
            relief="flat",
        )
        self.gantt_canvas.pack(fill=tk.BOTH, expand=True)

    def _validate_pid(self, P):
        """Validate Process ID: alphanumeric, max 3 characters"""
        if P == '':
            return True
        if len(P) > 3:
            return False
        # Allow alphanumeric only
        return P.isalnum()

    def _validate_range(self, P):
        """Validate numeric input: 1-100"""
        if P == '':
            return True
        # Only allow digits
        if not P.isdigit():
            return False
        # Max 3 digits (up to 999 for intermediate input)
        if len(P) > 3:
            return False
        # Check range 1-100
        try:
            num = int(P)
            return 1 <= num <= 100
        except ValueError:
            return False

    def add_process(self):
        try:
            pid = self.entry_pid.get().strip()
            at = int(self.entry_at.get())
            bt = int(self.entry_bt.get())
            prio = int(self.entry_prio.get())

            if not pid or at < 1 or at > 100 or bt < 1 or bt > 100 or prio < 1 or prio > 100:
                messagebox.showerror("Input Error", "Ensure: PID is set, AT/BT/Priority in range 1-100")
                return

            p = Process(pid, at, bt, prio)
            self.processes.append(p)
            self.listbox.insert(tk.END, f"P{pid}  AT={at}  BT={bt}  Prio={prio}")

            self.entry_pid.delete(0, tk.END)
            self.entry_at.delete(0, tk.END)
            self.entry_bt.delete(0, tk.END)
            self.entry_prio.delete(0, tk.END)
            self.entry_prio.insert(0, "1")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers in range 1-100!")

    def clear_processes(self):
        self.processes = []
        self.listbox.delete(0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.gantt_canvas.delete("all")
        self.metric_algo.config(text="Algorithm: —")
        self.metric_wt.config(text="Avg Waiting Time: — ms")
        self.metric_tat.config(text="Avg Turnaround Time: — ms")

    def view_arrival_times_gantt(self):
        """Display Gantt chart showing process arrival times"""
        if not self.processes:
            messagebox.showwarning("No Data", "Please add processes first")
            return

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "PROCESS ARRIVAL ANALYSIS\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        self.results_text.insert(tk.END, "  PID    AT    BT   Priority\n")
        self.results_text.insert(tk.END, "  " + "─" * 32 + "\n")

        sorted_procs = sorted(self.processes, key=lambda p: (p.arrival_time, p.pid))
        for p in sorted_procs:
            line = f"  {str(p.pid):<6} {p.arrival_time:<5} {p.burst_time:<4} {p.priority:<5}\n"
            self.results_text.insert(tk.END, line)

        self.render_arrival_times_gantt()

    def run_scheduler(self):
        if not self.processes:
            messagebox.showwarning("No Data", "Please add processes first")
            return

        algo = self.algo_var.get()
        try:
            quantum = int(self.entry_q.get()) if self.entry_q.get() else self.quantum_default
        except ValueError:
            quantum = self.quantum_default

        engine = SchedulerEngine(self.processes)

        if algo == "FCFS":
            result = engine.run_fcfs()
        elif algo == "SJF":
            result = engine.run_sjf()
        elif algo == "Priority":
            result = engine.run_priority()
        elif algo == "RR":
            result = engine.run_rr(quantum)
        else:
            result = engine.run_fcfs()

        self.display_results(result, algo)

    def _sim_all_algorithms(self, quantum):
        algos = [
            ("FCFS", lambda e: e.run_fcfs()),
            ("SJF", lambda e: e.run_sjf()),
            ("Priority", lambda e: e.run_priority()),
            ("RR", lambda e: e.run_rr(quantum)),
        ]

        results = {}
        for name, fn in algos:
            e = SchedulerEngine(self.processes)
            results[name] = fn(e)
        return results

    def run_advisor(self):
        if not self.processes:
            messagebox.showwarning("No Data", "Please add processes first")
            return

        try:
            quantum = int(self.entry_q.get()) if self.entry_q.get() else self.quantum_default
        except ValueError:
            quantum = self.quantum_default

        heuristic_msg, _ = SmartAdvisor.analyze_and_recommend(self.processes)

        try:
            all_results = self._sim_all_algorithms(quantum)
            best_algo = min(all_results.keys(), key=lambda k: all_results[k]["avg_waiting"])
            best = all_results[best_algo]

            self.display_results(best, best_algo)
            self.results_text.insert(tk.END, "\n\n" + heuristic_msg)
        except Exception:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, heuristic_msg)

    def display_results(self, result, algo_name):
        processes = result["processes"]
        avg_wt = result["avg_waiting"]
        avg_tat = result["avg_turnaround"]
        gantt_data = result["gantt_data"]

        self.metric_algo.config(text=f"Algorithm: {algo_name}")
        self.metric_wt.config(text=f"Avg Waiting Time: {avg_wt:.2f} ms")
        self.metric_tat.config(text=f"Avg Turnaround Time: {avg_tat:.2f} ms")

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"{algo_name} SCHEDULING RESULTS\n")
        self.results_text.insert(tk.END, "=" * 65 + "\n\n")
        self.results_text.insert(tk.END, "  PID   AT   BT   P   ST   CT   TAT    WT\n")
        self.results_text.insert(tk.END, "  " + "─" * 48 + "\n")
        
        for p in sorted(processes, key=lambda x: int(x.pid) if str(x.pid).isdigit() else x.pid):
            line = f"  {str(p.pid):<5} {p.arrival_time:<4} {p.burst_time:<3} {p.priority:<2} {p.start_time:<4} {p.completion_time:<3} {p.turnaround_time:<6} {p.waiting_time:.1f}\n"
            self.results_text.insert(tk.END, line)

        self.render_gantt(gantt_data)

    def render_arrival_times_gantt(self):
        """Render professional Gantt chart showing arrival times"""
        self.gantt_canvas.delete("all")

        if not self.processes:
            return

        canvas_w = max(1000, int(self.gantt_canvas.winfo_width()))
        canvas_h = max(300, int(self.gantt_canvas.winfo_height()))

        arrival_times = [p.arrival_time for p in self.processes]
        max_time = max(arrival_times) + max([p.burst_time for p in self.processes]) if self.processes else 10
        
        margin_left = 120
        margin_right = 30
        margin_top = 40
        margin_bottom = 50
        plot_w = canvas_w - margin_left - margin_right

        # Background
        self.gantt_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill=self.bg_input, outline=self.border_color)

        # Title
        self.gantt_canvas.create_text(
            canvas_w // 2, 20,
            text="Process Arrival Times",
            fill=self.text_primary,
            font=("Segoe UI", 12, "bold"),
            anchor="center"
        )

        # Color palette
        colors = ["#58a6ff", "#79c0ff", "#3fb950", "#d29922", "#f85149", "#a371f7", "#bc8ef1"]
        sorted_procs = sorted(self.processes, key=lambda p: (p.arrival_time, p.pid))
        color_map = {p.pid: colors[i % len(colors)] for i, p in enumerate(sorted_procs)}

        axis_y = margin_top + 20
        bar_spacing = 40

        # Draw process labels
        for idx, p in enumerate(sorted_procs):
            y = axis_y + idx * bar_spacing
            self.gantt_canvas.create_text(
                margin_left - 15, y,
                text=f"P{p.pid}",
                fill=self.text_primary,
                font=("Segoe UI", 9, "bold"),
                anchor="e"
            )

        # Grid lines
        for idx in range(len(sorted_procs)):
            y = axis_y + idx * bar_spacing
            self.gantt_canvas.create_line(
                margin_left, y, margin_left + plot_w, y,
                fill=self.border_color, width=1
            )

        # Time axis
        time_axis_y = axis_y + len(sorted_procs) * bar_spacing + 10
        self.gantt_canvas.create_line(
            margin_left, time_axis_y, margin_left + plot_w, time_axis_y,
            fill=self.accent_blue, width=2
        )

        # Time ticks
        tick_count = min(15, max_time + 1)
        for i in range(tick_count + 1):
            t = i
            if max_time > 0:
                x = margin_left + (t / max_time) * plot_w
            else:
                x = margin_left
            
            self.gantt_canvas.create_line(
                x, time_axis_y - 5, x, time_axis_y,
                fill=self.accent_blue, width=1
            )
            
            self.gantt_canvas.create_text(
                x, time_axis_y + 15,
                text=str(i),
                fill=self.text_secondary,
                font=("Segoe UI", 8),
                anchor="center"
            )

        # Draw arrival markers
        for idx, p in enumerate(sorted_procs):
            y = axis_y + idx * bar_spacing
            x_arrival = margin_left + (p.arrival_time / max_time) * plot_w if max_time > 0 else margin_left
            
            color = color_map[p.pid]
            
            # Vertical indicator
            self.gantt_canvas.create_line(
                x_arrival, y - 12, x_arrival, y + 12,
                fill=color, width=3
            )
            
            # Circle marker
            self.gantt_canvas.create_oval(
                x_arrival - 5, y - 5, x_arrival + 5, y + 5,
                fill=color, outline=self.text_primary, width=1
            )
            
            # Time label
            self.gantt_canvas.create_text(
                x_arrival, y - 18,
                text=f"AT={p.arrival_time}",
                fill=self.accent_cyan,
                font=("Segoe UI", 7, "bold"),
                anchor="center"
            )

    def render_gantt(self, gantt_data):
        """Render professional Gantt chart"""
        self.gantt_canvas.delete("all")

        if not gantt_data:
            return

        canvas_w = max(1000, int(self.gantt_canvas.winfo_width()))
        canvas_h = max(300, int(self.gantt_canvas.winfo_height()))

        times = [s for _, s, _ in gantt_data] + [e for _, _, e in gantt_data]
        t_start = min(times)
        t_end = max(times)
        total_time = max(1, t_end - t_start)

        margin_left = 120
        margin_right = 30
        margin_top = 40
        margin_bottom = 50
        plot_w = canvas_w - margin_left - margin_right

        # Background
        self.gantt_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill=self.bg_input, outline=self.border_color)

        # Title
        self.gantt_canvas.create_text(
            canvas_w // 2, 20,
            text="CPU Process Schedule",
            fill=self.text_primary,
            font=("Segoe UI", 12, "bold"),
            anchor="center"
        )

        # Colors
        colors = ["#58a6ff", "#79c0ff", "#3fb950", "#d29922", "#f85149", "#a371f7", "#bc8ef1"]
        pid_list = sorted({pid for pid, _, _ in gantt_data}, key=lambda x: int(x) if str(x).isdigit() else x)
        color_map = {pid: colors[i % len(colors)] for i, pid in enumerate(pid_list)}

        axis_y = margin_top + 20
        bar_spacing = 40
        bar_height = 24

        # Labels
        for idx, pid in enumerate(pid_list):
            y = axis_y + idx * bar_spacing
            self.gantt_canvas.create_text(
                margin_left - 15, y,
                text=f"P{pid}",
                fill=self.text_primary,
                font=("Segoe UI", 9, "bold"),
                anchor="e"
            )

        # Grid
        for idx in range(len(pid_list)):
            y = axis_y + idx * bar_spacing
            self.gantt_canvas.create_line(
                margin_left, y, margin_left + plot_w, y,
                fill=self.border_color, width=1
            )

        # Time axis
        time_axis_y = axis_y + len(pid_list) * bar_spacing + 10
        self.gantt_canvas.create_line(
            margin_left, time_axis_y, margin_left + plot_w, time_axis_y,
            fill=self.accent_blue, width=2
        )

        # Time ticks
        tick_count = min(20, int(t_end - t_start) + 1)
        for i in range(tick_count + 1):
            t = t_start + i * (total_time / max(1, tick_count))
            x = margin_left + (t - t_start) / total_time * plot_w if total_time > 0 else margin_left
            
            self.gantt_canvas.create_line(
                x, time_axis_y - 5, x, time_axis_y,
                fill=self.accent_blue, width=1
            )
            
            self.gantt_canvas.create_text(
                x, time_axis_y + 15,
                text=f"{int(t)}",
                fill=self.text_secondary,
                font=("Segoe UI", 8),
                anchor="center"
            )

        # Draw bars
        pid_to_idx = {pid: idx for idx, pid in enumerate(pid_list)}
        
        for pid, s, e in gantt_data:
            if pid not in pid_to_idx:
                continue
            
            idx = pid_to_idx[pid]
            y = axis_y + idx * bar_spacing
            
            x1 = margin_left + ((s - t_start) / total_time) * plot_w if total_time > 0 else margin_left
            x2 = margin_left + ((e - t_start) / total_time) * plot_w if total_time > 0 else margin_left
            
            if x2 < x1:
                x1, x2 = x2, x1
            
            if x2 - x1 < 2:
                x2 = x1 + 2
            
            color = color_map.get(pid, "#999999")
            
            # Bar with border
            self.gantt_canvas.create_rectangle(
                x1, y - bar_height // 2,
                x2, y + bar_height // 2,
                fill=color, outline=self.text_primary, width=1
            )
            
            # Label
            duration = int(e - s)
            mid_x = (x1 + x2) / 2
            
            if x2 - x1 > 25:
                self.gantt_canvas.create_text(
                    mid_x, y,
                    text=f"{duration}",
                    fill=self.bg_dark,
                    font=("Segoe UI", 8, "bold"),
                    anchor="center"
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = OSSchedulerGUI(root)
    root.mainloop()
