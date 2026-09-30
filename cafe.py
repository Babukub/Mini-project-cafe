import json
import os
from models import create_menu_item, Order, MemberCustomer

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cafe_data.json")


class Cafe:
    def __init__(self, data_file=DATA_FILE):
        self.__data_file = data_file      # private
        self.__menu = {}                  # id -> MenuItem
        self.__members = {}               # phone -> MemberCustomer
        self.__history = []               # list ของ dict (ออเดอร์ที่ชำระแล้ว)
        self.__next_menu_id = 1
        self.__next_order_id = 1
        if os.path.exists(data_file):
            self.load()
        else:
            self._seed()

    # ---------------- เมนู (Create / Read / Update / Delete) ----------------
    def add_menu(self, kind, name, price):
        item = create_menu_item(kind, self.__next_menu_id, name, price)
        self.__menu[item.id] = item
        self.__next_menu_id += 1
        self.save()
        return item

    def update_menu(self, item_id, name, price):
        item = self.__menu[item_id]
        item.name = name        # ผ่าน setter (มี validation)
        item.price = price
        self.save()

    def remove_menu(self, item_id):
        del self.__menu[item_id]
        self.save()

    def get_menu(self, item_id):
        return self.__menu[item_id]

    def search_menu(self, keyword="", label="ทั้งหมด"):
        keyword = keyword.strip().lower()
        return [m for m in self.__menu.values()
                if keyword in m.name.lower() and (label == "ทั้งหมด" or m.LABEL == label)]

    # ---------------- สมาชิก ----------------
    def find_member(self, phone):
        return self.__members.get(phone.strip())

    def register_member(self, name, phone):
        phone = phone.strip()
        if not name.strip() or not phone:
            raise ValueError("กรุณากรอกชื่อและเบอร์โทร")
        if phone in self.__members:
            raise ValueError("เบอร์นี้เป็นสมาชิกอยู่แล้ว")
        member = MemberCustomer(name.strip(), phone)
        self.__members[phone] = member
        self.save()
        return member

    # ---------------- ออเดอร์ / ขาย ----------------
    def new_order(self):
        return Order(self.__next_order_id)

    def checkout(self, order):
        if not order.items:
            raise ValueError("ตะกร้าว่าง")
        order.customer.earn_points(order.total())     # Polymorphism
        record = order.to_dict()
        self.__history.append(record)
        self.__next_order_id += 1
        self.save()
        return record

    @property
    def history(self):
        return list(self.__history)

    def total_sales(self):
        return sum(r["total"] for r in self.__history)

    def best_seller(self):
        count = {}
        for r in self.__history:
            for it in r["items"]:
                count[it["name"]] = count.get(it["name"], 0) + it["qty"]
        if not count:
            return "-"
        name = max(count, key=count.get)
        return f"{name} ({count[name]} ชิ้น)"

    # ---------------- บันทึก / โหลดไฟล์ ----------------
    def save(self):
        data = {
            "next_menu_id": self.__next_menu_id,
            "next_order_id": self.__next_order_id,
            "menu": [m.to_dict() for m in self.__menu.values()],
            "members": [m.to_dict() for m in self.__members.values()],
            "history": self.__history,
        }
        with open(self.__data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        with open(self.__data_file, encoding="utf-8") as f:
            data = json.load(f)
        self.__next_menu_id = data["next_menu_id"]
        self.__next_order_id = data["next_order_id"]
        for d in data["menu"]:
            self.__menu[d["id"]] = create_menu_item(d["kind"], d["id"], d["name"], d["price"])
        for d in data["members"]:
            self.__members[d["phone"]] = MemberCustomer(d["name"], d["phone"], d["points"])
        self.__history = data["history"]

    def _seed(self):
        """เมนูเริ่มต้น เมื่อเปิดโปรแกรมครั้งแรก"""
        for kind, name, price in [
            ("drink", "อเมริกาโน่", 50), ("drink", "ลาเต้", 60),
            ("drink", "ชาไทย", 45), ("drink", "โกโก้เย็น", 55),
            ("dessert", "บราวนี่", 65), ("dessert", "ชีสเค้ก", 80),
            ("dessert", "วาฟเฟิล", 70),
        ]:
            self.add_menu(kind, name, price)