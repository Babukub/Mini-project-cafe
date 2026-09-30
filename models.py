from abc import ABC, abstractmethod
from datetime import datetime


# ======================================================================
# 1) MenuItem : คลาสแม่แบบ Abstract ของ "เมนู" ทุกชนิด
# ======================================================================
class MenuItem(ABC):
    def __init__(self, item_id, name, price):
        self.__id = item_id          # private  -> Encapsulation
        self.__name = ""
        self.__price = 0.0
        self.name = name             # เรียกผ่าน setter เพื่อตรวจสอบค่า
        self.price = price

    # ---- Encapsulation: getter / setter พร้อมตรวจสอบข้อมูล ----
    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        value = str(value).strip()
        if not value:
            raise ValueError("ชื่อเมนูต้องไม่ว่าง")
        self.__name = value

    @property
    def price(self):
        return self.__price

    @price.setter
    def price(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError("ราคาต้องมากกว่า 0")
        self.__price = value

    # ---- Abstraction: เมธอดที่ลูกทุกคลาส "ต้อง" เขียนเอง ----
    @abstractmethod
    def get_price(self, option=None):
        """คำนวณราคาตามตัวเลือก (ขนาด/ท็อปปิ้ง)"""

    @abstractmethod
    def options(self):
        """รายการตัวเลือกที่เลือกได้"""

    KIND = ""    # ใช้เก็บลง JSON
    LABEL = ""   # ชื่อที่แสดงบนหน้าจอ

    def to_dict(self):
        return {"kind": self.KIND, "id": self.id, "name": self.name, "price": self.price}


# ======================================================================
# 2) Drink / Dessert : สืบทอดจาก MenuItem (Inheritance)
#    และ override get_price / options ต่างกัน (Polymorphism)
# ======================================================================
class Drink(MenuItem):
    KIND = "drink"
    LABEL = "เครื่องดื่ม"
    SIZES = {"S": 0, "M": 10, "L": 20}      # บวกเพิ่มตามขนาดแก้ว

    def get_price(self, option=None):       # Override
        return self.price + self.SIZES.get(option or "S", 0)

    def options(self):                      # Override
        return list(self.SIZES.keys())


class Dessert(MenuItem):
    KIND = "dessert"
    LABEL = "ของหวาน"
    EXTRAS = {"ปกติ": 0, "เพิ่มไอศกรีม": 15}

    def get_price(self, option=None):       # Override (คำนวณคนละแบบกับ Drink)
        return self.price + self.EXTRAS.get(option or "ปกติ", 0)

    def options(self):                      # Override
        return list(self.EXTRAS.keys())


def create_menu_item(kind, item_id, name, price):
    """สร้างวัตถุเมนูตามชนิด (ใช้ตอนเพิ่มเมนู / โหลดไฟล์)"""
    classes = {Drink.KIND: Drink, Dessert.KIND: Dessert}
    return classes[kind](item_id, name, price)


# ======================================================================
# 3) Customer / MemberCustomer : ลูกค้าทั่วไป และ สมาชิก
# ======================================================================
class Customer:
    def __init__(self, name="ลูกค้าทั่วไป", phone=""):
        self.__name = name           # private
        self._phone = phone          # protected

    @property
    def name(self):
        return self.__name

    @property
    def phone(self):
        return self._phone

    def discount_rate(self):
        return 0.0                   # ลูกค้าทั่วไปไม่มีส่วนลด

    def earn_points(self, total):
        pass                         # ลูกค้าทั่วไปไม่สะสมแต้ม

    def label(self):
        return f"{self.name} (ไม่ใช่สมาชิก)"


class MemberCustomer(Customer):      # Inheritance
    DISCOUNT = 0.10

    def __init__(self, name, phone, points=0):
        super().__init__(name, phone)
        self.__points = int(points)  # private

    @property
    def points(self):
        return self.__points

    def discount_rate(self):         # Override -> สมาชิกลด 10%
        return self.DISCOUNT

    def earn_points(self, total):    # Override -> ทุก 10 บาท ได้ 1 แต้ม
        self.__points += int(total // 10)

    def label(self):                 # Override
        return f"{self.name} (สมาชิก ลด {int(self.DISCOUNT*100)}% | {self.points} แต้ม)"

    def to_dict(self):
        return {"name": self.name, "phone": self.phone, "points": self.points}


# ======================================================================
# 4) OrderItem : รายการหนึ่งบรรทัดในตะกร้า
# ======================================================================
class OrderItem:
    def __init__(self, menu_item, qty=1, option=None):
        self.menu_item = menu_item
        self.option = option
        self.qty = qty

    @property
    def qty(self):
        return self.__qty

    @qty.setter
    def qty(self, value):
        value = int(value)
        if value < 1:
            raise ValueError("จำนวนต้องอย่างน้อย 1")
        self.__qty = value

    def unit_price(self):
        return self.menu_item.get_price(self.option)   # Polymorphism: ไม่สนว่าเป็น Drink/Dessert

    def subtotal(self):
        return self.unit_price() * self.qty


# ======================================================================
# 5) Order : ออเดอร์ 1 ใบ (ตะกร้า + ลูกค้า)
# ======================================================================
class Order:
    def __init__(self, order_id, customer=None):
        self.order_id = order_id
        self.customer = customer or Customer()
        self.items = []
        self.created_at = datetime.now()

    def add_item(self, menu_item, qty=1, option=None):
        for it in self.items:                      # ถ้ามีเมนู+ตัวเลือกเดิม ให้บวกจำนวน
            if it.menu_item.id == menu_item.id and it.option == option:
                it.qty = it.qty + qty
                return
        self.items.append(OrderItem(menu_item, qty, option))

    def remove_item(self, index):
        del self.items[index]

    def clear(self):
        self.items.clear()

    def subtotal(self):
        return sum(it.subtotal() for it in self.items)

    def discount(self):
        return self.subtotal() * self.customer.discount_rate()

    def total(self):
        return self.subtotal() - self.discount()

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "time": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "customer": self.customer.name,
            "items": [{"name": i.menu_item.name, "option": i.option,
                       "qty": i.qty, "subtotal": i.subtotal()} for i in self.items],
            "subtotal": self.subtotal(),
            "discount": self.discount(),
            "total": self.total(),
        }