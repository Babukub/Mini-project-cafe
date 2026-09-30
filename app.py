import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from cafe import Cafe
from models import Drink, Dessert

TYPE_BY_LABEL = {Drink.LABEL: Drink.KIND, Dessert.LABEL: Dessert.KIND}


# ======================================================================
# CafeApp : หน้าต่างหลัก สืบทอดจาก tk.Tk (Inheritance จากคลาสของไลบรารี)
# ======================================================================
class CafeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Coffee Shop - ระบบจัดการร้านกาแฟ")
        self.geometry("1050x640")
        self.cafe = Cafe()
        self.order = self.cafe.new_order()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab_order = ttk.Frame(notebook)
        self.tab_menu = ttk.Frame(notebook)
        self.tab_report = ttk.Frame(notebook)
        notebook.add(self.tab_order, text="  สั่งอาหาร  ")
        notebook.add(self.tab_menu, text="  จัดการเมนู  ")
        notebook.add(self.tab_report, text="  สรุปยอดขาย  ")
        notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_report())

        self._build_order_tab()
        self._build_menu_tab()
        self._build_report_tab()
        self.refresh_menu_lists()
        self.refresh_cart()

    # ------------------------------------------------------------------
    # แท็บ 1: สั่งอาหาร
    # ------------------------------------------------------------------
    def _build_order_tab(self):
        left = ttk.LabelFrame(self.tab_order, text="เมนู")
        left.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        right = ttk.LabelFrame(self.tab_order, text="ตะกร้า / ชำระเงิน")
        right.pack(side="right", fill="both", expand=True, padx=6, pady=6)

        # --- ค้นหา + กรอง ---
        bar = ttk.Frame(left)
        bar.pack(fill="x", padx=6, pady=6)
        ttk.Label(bar, text="ค้นหา:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_menu_lists())
        ttk.Entry(bar, textvariable=self.search_var, width=18).pack(side="left", padx=4)
        self.filter_var = tk.StringVar(value="ทั้งหมด")
        cb = ttk.Combobox(bar, textvariable=self.filter_var, state="readonly", width=12,
                          values=["ทั้งหมด", Drink.LABEL, Dessert.LABEL])
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_menu_lists())

        # --- ตารางเมนู ---
        self.order_menu_tree = ttk.Treeview(left, columns=("name", "cat", "price"),
                                            show="headings", height=14, selectmode="browse")
        for col, text, w in [("name", "ชื่อเมนู", 160), ("cat", "ประเภท", 90), ("price", "ราคา", 70)]:
            self.order_menu_tree.heading(col, text=text)
            self.order_menu_tree.column(col, width=w, anchor="center" if col != "name" else "w")
        self.order_menu_tree.pack(fill="both", expand=True, padx=6)
        self.order_menu_tree.bind("<<TreeviewSelect>>", self.on_menu_select)

        # --- เลือกตัวเลือก + จำนวน ---
        pick = ttk.Frame(left)
        pick.pack(fill="x", padx=6, pady=8)
        ttk.Label(pick, text="ตัวเลือก:").pack(side="left")
        self.option_var = tk.StringVar()
        self.option_box = ttk.Combobox(pick, textvariable=self.option_var, state="readonly", width=12)
        self.option_box.pack(side="left", padx=4)
        ttk.Label(pick, text="จำนวน:").pack(side="left", padx=(8, 0))
        self.qty_var = tk.IntVar(value=1)
        ttk.Spinbox(pick, from_=1, to=50, textvariable=self.qty_var, width=5).pack(side="left", padx=4)
        ttk.Button(pick, text="เพิ่มลงตะกร้า", command=self.add_to_cart).pack(side="left", padx=8)

        # --- สมาชิก ---
        mem = ttk.Frame(right)
        mem.pack(fill="x", padx=6, pady=6)
        ttk.Label(mem, text="เบอร์สมาชิก:").pack(side="left")
        self.phone_var = tk.StringVar()
        ttk.Entry(mem, textvariable=self.phone_var, width=14).pack(side="left", padx=4)
        ttk.Button(mem, text="ตรวจสอบ", command=self.check_member).pack(side="left")
        ttk.Button(mem, text="สมัครสมาชิก", command=self.register_member).pack(side="left", padx=4)
        self.customer_label = ttk.Label(right, text="", foreground="#0a5")
        self.customer_label.pack(anchor="w", padx=8)

        # --- ตะกร้า ---
        self.cart_tree = ttk.Treeview(right, columns=("name", "opt", "qty", "unit", "sub"),
                                      show="headings", height=11, selectmode="browse")
        for col, text, w in [("name", "เมนู", 120), ("opt", "ตัวเลือก", 80), ("qty", "จำนวน", 50),
                             ("unit", "ราคา/หน่วย", 80), ("sub", "รวม", 70)]:
            self.cart_tree.heading(col, text=text)
            self.cart_tree.column(col, width=w, anchor="w" if col == "name" else "center")
        self.cart_tree.pack(fill="both", expand=True, padx=6, pady=4)

        btns = ttk.Frame(right)
        btns.pack(fill="x", padx=6)
        ttk.Button(btns, text="ลบรายการที่เลือก", command=self.remove_from_cart).pack(side="left")
        ttk.Button(btns, text="ล้างตะกร้า", command=self.clear_cart).pack(side="left", padx=6)

        self.sum_label = ttk.Label(right, text="", font=("TkDefaultFont", 11, "bold"), justify="left")
        self.sum_label.pack(anchor="w", padx=8, pady=8)
        ttk.Button(right, text="ชำระเงิน", command=self.checkout).pack(fill="x", padx=6, pady=(0, 6))

    def on_menu_select(self, _event=None):
        sel = self.order_menu_tree.selection()
        if not sel:
            return
        item = self.cafe.get_menu(int(sel[0]))
        opts = item.options()                      # Polymorphism: Drink/Dessert ให้ตัวเลือกต่างกัน
        self.option_box["values"] = opts
        self.option_var.set(opts[0])

    def add_to_cart(self):
        sel = self.order_menu_tree.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเมนูก่อน")
            return
        try:
            qty = int(self.qty_var.get())
            self.order.add_item(self.cafe.get_menu(int(sel[0])), qty, self.option_var.get())
        except (ValueError, tk.TclError) as e:
            messagebox.showerror("ผิดพลาด", f"จำนวนไม่ถูกต้อง\n{e}")
            return
        self.refresh_cart()

    def remove_from_cart(self):
        sel = self.cart_tree.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกรายการในตะกร้า")
            return
        self.order.remove_item(int(sel[0]))
        self.refresh_cart()

    def clear_cart(self):
        self.order.clear()
        self.refresh_cart()

    def check_member(self):
        member = self.cafe.find_member(self.phone_var.get())
        if member is None:
            messagebox.showinfo("ไม่พบสมาชิก", "ไม่พบเบอร์นี้ในระบบ (กด 'สมัครสมาชิก' ได้)")
            return
        self.order.customer = member
        self.refresh_cart()

    def register_member(self):
        name = simpledialog.askstring("สมัครสมาชิก", "ชื่อ-นามสกุล:", parent=self)
        if name is None:
            return
        phone = simpledialog.askstring("สมัครสมาชิก", "เบอร์โทร:", initialvalue=self.phone_var.get(), parent=self)
        if phone is None:
            return
        try:
            member = self.cafe.register_member(name, phone)
        except ValueError as e:
            messagebox.showerror("สมัครไม่สำเร็จ", str(e))
            return
        self.phone_var.set(member.phone)
        self.order.customer = member
        messagebox.showinfo("สำเร็จ", f"สมัครสมาชิกให้ {member.name} เรียบร้อย")
        self.refresh_cart()

    def checkout(self):
        try:
            record = self.cafe.checkout(self.order)
        except ValueError as e:
            messagebox.showwarning("ชำระเงินไม่ได้", str(e))
            return
        lines = [f"ใบเสร็จ #{record['order_id']}   {record['time']}", f"ลูกค้า: {record['customer']}", "-" * 34]
        for it in record["items"]:
            lines.append(f"{it['name']} ({it['option']}) x{it['qty']}   {it['subtotal']:.0f}")
        lines += ["-" * 34, f"รวม: {record['subtotal']:.2f}", f"ส่วนลด: {record['discount']:.2f}",
                  f"สุทธิ: {record['total']:.2f} บาท"]
        messagebox.showinfo("ชำระเงินสำเร็จ", "\n".join(lines))
        self.order = self.cafe.new_order()
        self.phone_var.set("")
        self.refresh_cart()

    def refresh_cart(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        for i, it in enumerate(self.order.items):
            self.cart_tree.insert("", "end", iid=str(i), values=(
                it.menu_item.name, it.option, it.qty, f"{it.unit_price():.0f}", f"{it.subtotal():.0f}"))
        self.customer_label.config(text="ลูกค้า: " + self.order.customer.label())
        self.sum_label.config(text=(f"รวม: {self.order.subtotal():.2f} บาท\n"
                                    f"ส่วนลด: {self.order.discount():.2f} บาท\n"
                                    f"สุทธิ: {self.order.total():.2f} บาท"))

# ------------------------------------------------------------------
    # แท็บ 2: จัดการเมนู (เพิ่ม / แก้ไข / ลบ)
# ------------------------------------------------------------------
    def _build_menu_tab(self):
        form = ttk.LabelFrame(self.tab_menu, text="ข้อมูลเมนู")
        form.pack(fill="x", padx=10, pady=10)
        self.m_name = tk.StringVar()
        self.m_price = tk.StringVar()
        self.m_type = tk.StringVar(value=Drink.LABEL)
        ttk.Label(form, text="ชื่อ:").grid(row=0, column=0, padx=6, pady=8)
        ttk.Entry(form, textvariable=self.m_name, width=22).grid(row=0, column=1)
        ttk.Label(form, text="ราคา:").grid(row=0, column=2, padx=6)
        ttk.Entry(form, textvariable=self.m_price, width=10).grid(row=0, column=3)
        ttk.Label(form, text="ประเภท:").grid(row=0, column=4, padx=6)
        self.m_type_box = ttk.Combobox(form, textvariable=self.m_type, state="readonly", width=12,
                                       values=[Drink.LABEL, Dessert.LABEL])
        self.m_type_box.grid(row=0, column=5)
        ttk.Button(form, text="เพิ่มเมนูใหม่", command=self.add_menu).grid(row=1, column=1, pady=6)
        ttk.Button(form, text="บันทึกการแก้ไข", command=self.update_menu).grid(row=1, column=2, columnspan=2)
        ttk.Button(form, text="ลบเมนูที่เลือก", command=self.delete_menu).grid(row=1, column=4, columnspan=2)

        self.manage_tree = ttk.Treeview(self.tab_menu, columns=("id", "name", "cat", "price"),
                                        show="headings", height=15, selectmode="browse")
        for col, text, w in [("id", "รหัส", 60), ("name", "ชื่อเมนู", 220), ("cat", "ประเภท", 120), ("price", "ราคา", 90)]:
            self.manage_tree.heading(col, text=text)
            self.manage_tree.column(col, width=w, anchor="center")
        self.manage_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.manage_tree.bind("<<TreeviewSelect>>", self.on_manage_select)

    def on_manage_select(self, _event=None):
        sel = self.manage_tree.selection()
        if sel:
            item = self.cafe.get_menu(int(sel[0]))
            self.m_name.set(item.name)
            self.m_price.set(f"{item.price:.0f}")
            self.m_type.set(item.LABEL)

    def add_menu(self):
        try:
            self.cafe.add_menu(TYPE_BY_LABEL[self.m_type.get()], self.m_name.get(), self.m_price.get())
        except ValueError as e:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", str(e))
            return
        self.m_name.set("")
        self.m_price.set("")
        self.refresh_menu_lists()

    def update_menu(self):
        sel = self.manage_tree.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเมนูที่ต้องการแก้ไข")
            return
        try:
            self.cafe.update_menu(int(sel[0]), self.m_name.get(), self.m_price.get())
        except ValueError as e:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", str(e))
            return
        self.refresh_menu_lists()

    def delete_menu(self):
        sel = self.manage_tree.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกเมนูที่ต้องการลบ")
            return
        if messagebox.askyesno("ยืนยัน", "ต้องการลบเมนูนี้ใช่หรือไม่?"):
            self.cafe.remove_menu(int(sel[0]))
            self.refresh_menu_lists()

    def refresh_menu_lists(self):
        self.order_menu_tree.delete(*self.order_menu_tree.get_children())
        for m in self.cafe.search_menu(self.search_var.get(), self.filter_var.get()):
            self.order_menu_tree.insert("", "end", iid=str(m.id), values=(m.name, m.LABEL, f"{m.price:.0f}"))
        self.manage_tree.delete(*self.manage_tree.get_children())
        for m in self.cafe.search_menu():
            self.manage_tree.insert("", "end", iid=str(m.id), values=(m.id, m.name, m.LABEL, f"{m.price:.0f}"))
