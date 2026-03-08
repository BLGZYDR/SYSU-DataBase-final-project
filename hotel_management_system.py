#使用前先创建数据库并插入数据，然后找到connect_to_database函数修改数据库连接
import mysql.connector
from mysql.connector import Error
import datetime
import getpass
import hashlib
import sys
from prettytable import PrettyTable
import time
from enum import Enum
import subprocess
import os
import shutil
from pathlib import Path


class RoleEnum(Enum):
    FRONT_DESK = "前台"
    ADMIN = "管理员"


class RoomStatusEnum(Enum):
    AVAILABLE = "空闲"
    RESERVED = "预留"
    OCCUPIED = "已入住"


class OrderStatusEnum(Enum):
    BOOKED = "已预订"
    CANCELLED = "已取消"
    CHECKED_IN = "已入住"
    COMPLETED = "已完成"


class RoomTypeEnum(Enum):
    STANDARD = "标准房"
    KING_BED = "大床房"
    TWIN_BED = "双床房"
    FAMILY_SUITE = "家庭套房"


class HotelManagementSystem:
    def validate_phone(self, phone):
        """验证电话号码（必须是11位纯数字）"""
        # 检查长度是否为11位
        if len(phone) != 11:
            return False

        # 检查是否全部为数字
        if not phone.isdigit():
            return False

        return True

    def validate_id_card(self, id_card):
        # 检查长度是否为18位
        if len(id_card) != 18:
            return False

        # 检查是否全部为数字
        if not id_card.isdigit():
            return False

        return True

    def find_guest_by_info(self, phone, id_card):
        """根据电话和身份证查询客人信息
        返回：(found, guest_info, message)
        - found: True/False 表示是否找到
        - guest_info: 如果找到则返回客人信息字典，否则为None
        - message: 错误信息或说明
        """
        try:
            cursor = self.connection.cursor(dictionary=True)

            # 先尝试用身份证查询
            cursor.execute("SELECT * FROM guest WHERE id_card = %s", (id_card,))
            guest_by_id_card = cursor.fetchone()

            # 再尝试用电话查询
            cursor.execute("SELECT * FROM guest WHERE phone = %s", (phone,))
            guest_by_phone = cursor.fetchone()

            # 情况1：两个都查到了，且是同一个人
            if guest_by_id_card and guest_by_phone:
                if guest_by_id_card['guest_id'] == guest_by_phone['guest_id']:
                    return True, guest_by_id_card, "查询成功"
                else:
                    # 身份证和电话对应不同的客人
                    return False, None, "错误：身份证和电话号码不属于同一个人"

            # 情况2：只有身份证查到记录
            elif guest_by_id_card and not guest_by_phone:
                return False, None, "错误：该身份证已存在，但电话号码不匹配"

            # 情况3：只有电话查到记录
            elif guest_by_phone and not guest_by_id_card:
                return False, None, "错误：该电话号码已存在，但身份证不匹配"

            # 情况4：两个都没查到
            else:
                return False, None, "未找到匹配的客人记录"

        except Error as e:
            print(f"查询客人信息错误: {e}")
            return False, None, f"查询错误: {e}"
        finally:
            if 'cursor' in locals():
                cursor.close()

    def __init__(self):
        self.connection = None
        self.current_guest_id = None
        self.current_operator_id = None
        self.current_operator_role = None
        self.current_operator_name = None
        self.connect_to_database()

    def connect_to_database(self):
        """连接到MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host='127.0.0.1',
                port=3306,
                user='root',  # 修改为你的MySQL用户名
                password='2015Xz0202',  # 修改为你的MySQL密码
                database='hotel_management',
                charset='utf8mb4'
            )
            if self.connection.is_connected():
                print("成功连接到数据库")
                return True
        except Error as e:
            print(f"数据库连接错误: {e}")
            return False

    def hash_password(self, password):
        """对密码进行哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_admin_permission(self, feature_name):
        """检查管理员权限"""
        if self.current_operator_role != "ADMIN":  # 注意：数据库中存储的是"ADMIN"，不是"管理员"
            print(f"权限不足：只有管理员可以进行{feature_name}操作")
            return False
        return True

    def check_operator_permission(self):
        """检查操作员权限（非客人权限）"""
        if not self.current_operator_id:
            print("请先登录操作员账号")
            return False
        return True

    def get_status_display(self, status):
        """获取状态的中文显示"""
        status_map = {
            'AVAILABLE': '✅ 空闲',
            'OCCUPIED': '🔴 已入住',
            'RESERVED': '🟡 预留',
            'BOOKED': '📅 已预订',
            'CHECKED_IN': '🏨 已入住',
            'COMPLETED': '✅ 已完成',
            'CANCELLED': '❌ 已取消'
        }
        return status_map.get(status, status)

    def get_role_display(self, role):
        """获取角色的中文显示"""
        role_map = {
            'FRONT_DESK': '前台',
            'ADMIN': '管理员'
        }
        return role_map.get(role, role)

    def get_room_type_display(self, room_type):
        """获取房型的中文显示"""
        room_type_map = {
            'STANDARD': '标准房',
            'KING_BED': '大床房',
            'TWIN_BED': '双床房',
            'FAMILY_SUITE': '家庭套房'
        }
        return room_type_map.get(room_type, room_type)

    def main_menu(self):
        """主菜单"""
        while True:
            print("\n" + "=" * 50)
            print("宾馆客房管理系统")
            print("=" * 50)
            print("1. 客人系统")
            print("2. 操作员系统")
            print("3. 退出系统")
            print("=" * 50)

            choice = input("请选择 (1-3): ").strip()

            if choice == '1':
                self.guest_system()
            elif choice == '2':
                self.operator_system()
            elif choice == '3':
                print("感谢使用宾馆客房管理系统，再见！")
                if self.connection.is_connected():
                    self.connection.close()
                sys.exit(0)
            else:
                print("无效选择，请重新输入")

    def guest_system(self):
        """客人系统"""
        while True:
            print("\n" + "-" * 40)
            print("客人系统")
            print("-" * 40)
            print("1. 查询房间状态")
            print("2. 预订房间")
            print("3. 查看订单")
            print("4. 取消订单")
            print("5. 返回主菜单")
            print("-" * 40)

            choice = input("请选择 (1-5): ").strip()  # 更新为1-5

            if choice == '1':
                self.query_room_status()
            elif choice == '2':
                self.make_reservation()
            elif choice == '3':
                self.view_guest_orders()
            elif choice == '4':  # 新增取消订单功能
                self.cancel_reservation()
            elif choice == '5':  # 更新编号
                return
            else:
                print("无效选择，请重新输入")

    def operator_system(self):
        """操作员系统"""
        # 首先需要登录
        if not self.operator_login():
            return

        while True:
            print("\n" + "-" * 40)
            print("操作员系统")
            print(f"当前用户: {self.current_operator_name} ({self.get_role_display(self.current_operator_role)})")
            print("-" * 40)
            print("1. 客房管理")
            print("2. 客人登记")
            print("3. 结账退房")
            print("4. 查询功能")
            print("5. 报表系统")
            print("6. 查看操作日志")
            print("7. 数据库管理")  # 新增
            print("8. 返回主菜单")
            print("-" * 40)

            choice = input("请选择 (1-8): ").strip()

            if choice == '1':
                self.room_management()
            elif choice == '2':
                self.check_in()
            elif choice == '3':
                self.check_out()
            elif choice == '4':
                self.query_system()
            elif choice == '5':
                self.report_system()
            elif choice == '6':
                self.view_logs()
            elif choice == '7':  # 新增
                self.database_management()
            elif choice == '8':
                self.current_operator_id = None
                self.current_operator_role = None
                self.current_operator_name = None
                return
            else:
                print("无效选择，请重新输入")

    def operator_login(self):
        """操作员登录"""
        print("\n" + "-" * 40)
        print("操作员登录")
        print("-" * 40)

        account_name = input("账号: ").strip()
        password = input("密码: ").strip()

        # 简单验证
        if not account_name or not password:
            print("账号和密码不能为空！")
            return False

        return self._verify_login(account_name, password)

    def _verify_login(self, account_name, password):
        """验证登录的公共方法"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM operator WHERE account_name = %s"
            cursor.execute(query, (account_name,))
            operator = cursor.fetchone()

            if operator:
                # 直接对比明文密码
                if operator['password'] == password:
                    self.current_operator_id = operator['operator_id']
                    self.current_operator_role = operator['role_name']  # 数据库中是"ADMIN"或"FRONT_DESK"
                    self.current_operator_name = operator['account_name']
                    print(f"登录成功！欢迎 {operator['account_name']} ({self.get_role_display(operator['role_name'])})")
                    return True
                else:
                    print("密码错误！")
                    return False
            else:
                print("账号不存在！")
                return False

        except Error as e:
            print(f"登录错误: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def query_room_status(self):
        """查询房间状态（客人）"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            print("\n" + "-" * 60)
            print("房间状态查询")
            print("-" * 60)

            # 查询所有房型（只查询未删除的房间）- 使用app.py的数据库结构
            cursor.execute("SELECT DISTINCT type_name FROM room WHERE is_deleted = False")
            room_types = cursor.fetchall()

            print("可选房型:")
            for i, rt in enumerate(room_types, 1):
                print(f"{i}. {self.get_room_type_display(rt['type_name'])}")

            print("0. 显示所有房间")

            choice = input("请选择房型 (0-显示所有): ").strip()

            if choice == '0':
                query = """
                SELECT room_number, type_name, base_price, status 
                FROM room 
                WHERE is_deleted = False
                ORDER BY room_number
                """
                cursor.execute(query)
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(room_types):
                        room_type = room_types[idx]['type_name']
                        query = """
                        SELECT room_number, type_name, base_price, status 
                        FROM room 
                        WHERE type_name = %s AND is_deleted = False
                        ORDER BY room_number
                        """
                        cursor.execute(query, (room_type,))
                    else:
                        print("无效选择")
                        return
                except ValueError:
                    print("无效输入")
                    return

            rooms = cursor.fetchall()

            if not rooms:
                print("没有找到符合条件的房间")
                return

            # 使用PrettyTable美化输出
            table = PrettyTable()
            table.field_names = ["房间号", "房型", "价格", "状态"]

            for room in rooms:
                status_display = self.get_status_display(room['status'])
                table.add_row([
                    room['room_number'],
                    self.get_room_type_display(room['type_name']),
                    f"¥{room['base_price']}",
                    status_display
                ])

            print(table)

            # 统计信息
            total_rooms = len(rooms)
            available_rooms = len([r for r in rooms if r['status'] == 'AVAILABLE'])
            occupied_rooms = len([r for r in rooms if r['status'] == 'OCCUPIED'])
            reserved_rooms = len([r for r in rooms if r['status'] == 'RESERVED'])

            print(f"\n统计信息:")
            print(f"总房间数: {total_rooms}")
            print(f"空闲房间: {available_rooms}")
            print(f"已入住: {occupied_rooms}")
            print(f"预留: {reserved_rooms}")

        except Error as e:
            print(f"查询错误: {e}")

    def make_reservation(self):
        """客人预订房间"""
        print("\n" + "=" * 60)
        print("房间预订")
        print("=" * 60)

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 1. 获取预订人信息
            print("\n请输入预订人信息:")

            # 验证并输入姓名
            while True:
                guest_name = input("姓名: ").strip()
                if guest_name:
                    break
                print("姓名不能为空，请重新输入")

            # 验证电话号码
            while True:
                phone = input("电话 (11位数字): ").strip()
                if self.validate_phone(phone):
                    break
                print("电话号码格式错误：必须是11位纯数字")

            # 验证身份证号
            while True:
                id_card = input("身份证号 (18位数字): ").strip()
                if self.validate_id_card(id_card):
                    break
                print("身份证号格式错误：必须是18位纯数字")

            # 检查预订人是否已存在（使用新的验证逻辑）
            found, guest_info, message = self.find_guest_by_info(phone, id_card)

            # 创建集合来存储已经添加的身份证号和电话号码
            added_id_cards = set()
            added_phones = set()

            if found:
                # 找到现有客人
                booker_guest_id = guest_info['guest_id']
                print(f"欢迎回来，{guest_name}！")

                # 将预订人身份证号和电话添加到集合
                added_id_cards.add(id_card)
                added_phones.add(phone)

                # 检查姓名是否一致（可选，如果一致最好）
                if guest_info['guest_name'] != guest_name:
                    update_name = input(
                        f"系统记录姓名为：{guest_info['guest_name']}，是否更新为{guest_name}？(y/n): ").strip().lower()
                    if update_name == 'y':
                        update_query = "UPDATE guest SET guest_name = %s WHERE guest_id = %s"
                        cursor.execute(update_query, (guest_name, booker_guest_id))
            else:
                # 显示查询错误信息
                print(f"\n{message}")

                # 只有当两者都查不到时，才询问是否创建新客人
                if "未找到匹配的客人记录" in message:
                    print("系统未找到您的信息，请确认是否要创建新客人记录")
                    create_new = input("是否创建新客人记录? (y/n): ").strip().lower()

                    if create_new != 'y':
                        print("预订取消，请核对您的身份证和电话号码")
                        return

                    # 再次确认
                    confirm_create = input(
                        f"确认创建新客人记录：\n姓名: {guest_name}\n电话: {phone}\n身份证: {id_card}\n确认创建? (y/n): ").strip().lower()
                    if confirm_create != 'y':
                        print("预订取消")
                        return

                    # 创建新客人记录
                    insert_guest = """
                    INSERT INTO guest (guest_name, phone, id_card)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_guest, (guest_name, phone, id_card))
                    self.connection.commit()
                    booker_guest_id = cursor.lastrowid
                    print(f"新客人登记成功！")

                    # 将新创建的预订人身份证号和电话添加到集合
                    added_id_cards.add(id_card)
                    added_phones.add(phone)
                else:
                    # 查询错误（身份证或电话不匹配），不允许继续预订
                    print("请核对您的身份证和电话号码信息，确保两者对应同一个人")
                    print("如需帮助，请联系前台工作人员")
                    return

            # 2. 输入同行人数并收集同行人员信息
            try:
                total_people = int(input("\n同行总人数 (包括预订人): ").strip())
                if total_people <= 0:
                    print("人数必须大于0")
                    return
            except ValueError:
                print("请输入有效的数字")
                return

            # 存储所有同行人员的guest_id（包括预订人）
            guest_ids = [booker_guest_id]

            # 如果有其他同行人员，收集他们的信息（使用相同的严格验证）
            if total_people > 1:
                print(f"\n请填写其他{total_people - 1}位同行人员的信息:")
                i = 1
                while i < total_people:
                    print(f"\n第{i}位同行人员:")

                    # 验证并输入姓名
                    while True:
                        other_name = input("姓名: ").strip()
                        if other_name:
                            break
                        print("姓名不能为空，请重新输入")

                    # 验证电话号码
                    while True:
                        other_phone = input("电话 (11位数字): ").strip()
                        if self.validate_phone(other_phone):
                            # 检查电话号码是否已经添加过
                            if other_phone in added_phones:
                                print("错误：该电话号码已在本次预订中添加过，请重新输入第{i}位同行人员的全部信息！")
                                # 跳出内层循环，重新开始输入该同行人员的全部信息
                                break
                            break
                        print("电话号码格式错误：必须是11位纯数字")

                    # 如果电话号码已存在，重新开始该同行人员的输入
                    if other_phone in added_phones:
                        print(f"请重新输入第{i}位同行人员的完整信息")
                        continue

                    # 验证身份证号
                    while True:
                        other_id_card = input("身份证号 (18位数字): ").strip()
                        if self.validate_id_card(other_id_card):
                            # 检查身份证号是否已经添加过
                            if other_id_card in added_id_cards:
                                print(f"错误：该身份证号已在本次预订中添加过，请重新输入第{i}位同行人员的全部信息！")
                                # 跳出内层循环，重新开始输入该同行人员的全部信息
                                break
                            break
                        print("身份证号格式错误：必须是18位纯数字")

                    # 如果身份证号已存在，重新开始该同行人员的输入
                    if other_id_card in added_id_cards:
                        print(f"请重新输入第{i}位同行人员的完整信息")
                        continue

                    # 检查该同行人员是否已存在（使用相同的严格验证）
                    found, other_guest_info, message = self.find_guest_by_info(other_phone, other_id_card)

                    if found:
                        # 找到现有客人
                        other_guest_id = other_guest_info['guest_id']
                        print(f"第{i}位同行人员已找到现有记录")

                        # 检查姓名是否一致（可选）
                        if other_guest_info['guest_name'] != other_name:
                            update_name = input(
                                f"系统记录姓名为：{other_guest_info['guest_name']}，是否更新为{other_name}？(y/n): ").strip().lower()
                            if update_name == 'y':
                                update_query = "UPDATE guest SET guest_name = %s WHERE guest_id = %s"
                                cursor.execute(update_query, (other_name, other_guest_id))

                        guest_ids.append(other_guest_id)
                        added_id_cards.add(other_id_card)  # 添加到已添加集合
                        added_phones.add(other_phone)  # 添加到已添加电话集合
                        i += 1  # 只有成功添加后才增加计数器
                    else:
                        # 显示查询错误信息
                        print(f"\n{message}")

                        if "未找到匹配的客人记录" in message:
                            print("系统未找到该同行人员信息")
                            create_other = input("是否为此同行人员创建新记录? (y/n): ").strip().lower()

                            if create_other != 'y':
                                print(f"第{i}位同行人员输入取消，请重新输入第{i}位同行人员的信息")
                                # 不增加i，继续循环重新输入该同行人员
                                continue

                            # 再次确认
                            confirm_create = input(
                                f"确认创建新客人记录：\n姓名: {other_name}\n电话: {other_phone}\n身份证: {other_id_card}\n确认创建? (y/n): ").strip().lower()
                            if confirm_create != 'y':
                                print(f"第{i}位同行人员输入取消，请重新输入第{i}位同行人员的信息")
                                # 不增加i，继续循环重新输入该同行人员
                                continue

                            # 创建新客人记录
                            insert_other_guest = """
                            INSERT INTO guest (guest_name, phone, id_card)
                            VALUES (%s, %s, %s)
                            """
                            cursor.execute(insert_other_guest, (other_name, other_phone, other_id_card))
                            self.connection.commit()
                            other_guest_id = cursor.lastrowid
                            guest_ids.append(other_guest_id)
                            added_id_cards.add(other_id_card)  # 添加到已添加集合
                            added_phones.add(other_phone)  # 添加到已添加电话集合
                            print(f"第{i}位同行人员记录成功！")
                            i += 1  # 成功添加后才增加计数器
                        else:
                            # 查询错误（身份证或电话不匹配），要求重新输入该同行人员的信息
                            print(f"身份证和电话信息不匹配，请重新输入该位同行人员的信息")
                            # 不增加i，继续循环重新输入该同行人员

            # 检查是否成功添加了所有同行人员
            if len(guest_ids) != total_people:
                print(f"\n警告：成功添加了{len(guest_ids)}位客人，但您最初指定了{total_people}位。")
                print("是否继续预订？(y-使用已添加的客人继续预订, n-取消预订)")
                continue_choice = input("请选择: ").strip().lower()
                if continue_choice != 'y':
                    print("预订已取消")
                    return

            # 3. 显示可用房型（只显示未删除的房间）
            print("\n可用房型:")
            cursor.execute("""
                SELECT type_name, base_price, COUNT(*) as available_count
                FROM room 
                WHERE status = 'AVAILABLE' AND is_deleted = False
                GROUP BY type_name, base_price
                ORDER BY base_price
            """)

            room_types = cursor.fetchall()

            if not room_types:
                print("目前没有空闲房间")
                return

            for i, rt in enumerate(room_types, 1):
                print(
                    f"{i}. {self.get_room_type_display(rt['type_name'])} - ¥{rt['base_price']}/晚 - 剩余{rt['available_count']}间")

            # 4. 选择房间
            selected_rooms = []
            total_rooms = 0

            while True:
                try:
                    choice = input("\n选择房型编号 (输入0完成选择): ").strip()
                    if choice == '0':
                        break

                    idx = int(choice) - 1
                    if 0 <= idx < len(room_types):
                        room_type = room_types[idx]

                        try:
                            room_count = int(
                                input(f"选择{self.get_room_type_display(room_type['type_name'])}的数量: ").strip())

                            # 检查是否有足够房间
                            if room_count > room_type['available_count']:
                                print(f"该房型只有{room_type['available_count']}间可用")
                                continue

                            # 获取具体房间（只获取未删除的房间）
                            cursor.execute("""
                                SELECT room_id, room_number 
                                FROM room 
                                WHERE type_name = %s AND status = 'AVAILABLE' AND is_deleted = False
                                LIMIT %s
                            """, (room_type['type_name'], room_count))

                            rooms = cursor.fetchall()

                            for room in rooms:
                                selected_rooms.append({
                                    'room_id': room['room_id'],
                                    'room_number': room['room_number'],
                                    'type_name': room_type['type_name'],
                                    'price': room_type['base_price']
                                })

                            total_rooms += room_count
                            print(f"已选择{room_count}间{self.get_room_type_display(room_type['type_name'])}")

                        except ValueError:
                            print("请输入有效的数量")
                    else:
                        print("无效选择")
                except ValueError:
                    print("请输入有效的编号")

            if not selected_rooms:
                print("未选择任何房间")
                return

            # 5. 输入入住日期
            print("\n入住日期:")
            today = datetime.date.today()

            try:
                check_in_str = input(f"入住日期 (YYYY-MM-DD, 默认今天{today}): ").strip()
                if not check_in_str:
                    check_in_date = today
                else:
                    check_in_date = datetime.datetime.strptime(check_in_str, '%Y-%m-%d').date()

                check_out_str = input("退房日期 (YYYY-MM-DD): ").strip()
                check_out_date = datetime.datetime.strptime(check_out_str, '%Y-%m-%d').date()

                # 验证：入住时间必须小于退房时间
                if check_out_date <= check_in_date:
                    print("错误：退房日期必须晚于入住日期！")
                    return

                # 计算天数
                days = (check_out_date - check_in_date).days

            except ValueError:
                print("日期格式错误，请使用YYYY-MM-DD格式")
                return

            # 6. 计算总金额
            total_amount = sum(room['price'] for room in selected_rooms) * days

            # 7. 显示预订信息
            print("\n" + "=" * 60)
            print("预订信息确认")
            print("=" * 60)
            print(f"预订人: {guest_name}")
            print(f"身份证: {id_card}")
            print(f"电话: {phone}")
            print(f"同行总人数: {total_people}")
            print(f"入住时间: {check_in_date} 至 {check_out_date} ({days}晚)")
            print(f"总房间数: {total_rooms}")
            print("\n预订房间:")
            for room in selected_rooms:
                print(
                    f"  - {room['room_number']} ({self.get_room_type_display(room['type_name'])}): ¥{room['price']}/晚")
            print(f"\n总金额: ¥{total_amount}")

            # 8. 确认预订
            confirm = input("\n确认预订? (y/n): ").strip().lower()
            if confirm != 'y':
                print("预订已取消")
                return

            # 9. 创建订单
            insert_order = """
            INSERT INTO `order` (
                guest_id, order_status, total_people, total_rooms,
                expect_check_in_time, expect_check_out_time, total_amount, order_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """

            cursor.execute(insert_order, (
                booker_guest_id, 'BOOKED', total_people, total_rooms,
                check_in_date, check_out_date, total_amount
            ))
            order_id = cursor.lastrowid

            # 10. 添加所有订单-客人关联（包括预订人和所有同行人员）
            for guest_id in guest_ids:
                insert_order_guest = """
                INSERT INTO order_guest (order_id, guest_id)
                VALUES (%s, %s)
                """
                cursor.execute(insert_order_guest, (order_id, guest_id))

            # 11. 添加订单-房间关联并更新房间状态
            for room in selected_rooms:
                # 添加关联
                insert_order_room = """
                INSERT INTO order_room (order_id, room_id, type_name, price)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_order_room, (order_id, room['room_id'], room['type_name'], room['price']))

                # 更新房间状态
                update_room = """
                UPDATE room SET status = 'RESERVED' WHERE room_id = %s
                """
                cursor.execute(update_room, (room['room_id'],))

            self.connection.commit()

            print(f"\n预订成功！订单号: {order_id}")
            print(f"请凭订单号和身份证在入住时办理登记手续")

        except Error as e:
            self.connection.rollback()
            print(f"预订错误: {e}")

    def view_guest_orders(self):
        """客人查看订单（包含作为预订人和参与者的订单）"""
        print("\n" + "=" * 60)
        print("订单查询")
        print("=" * 60)

        # 选择查询方式
        print("\n查询方式:")
        print("1. 按身份证查询")
        print("2. 按电话查询")
        choice = input("请选择查询方式 (1-2): ").strip()

        id_card = None
        phone = None

        if choice == '1':
            # 验证身份证号
            while True:
                id_card = input("请输入身份证号: ").strip()
                if self.validate_id_card(id_card):
                    break
                print("身份证号格式错误，请输入18位身份证号")
        elif choice == '2':
            # 验证电话号码
            while True:
                phone = input("请输入电话号码: ").strip()
                if self.validate_phone(phone):
                    break
                print("电话号码格式错误，请输入11位数字")
        else:
            print("无效选择")
            return

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 查询客人信息
            if choice == '1':
                cursor.execute("SELECT guest_id, guest_name FROM guest WHERE id_card = %s", (id_card,))
            else:
                cursor.execute("SELECT guest_id, guest_name FROM guest WHERE phone = %s", (phone,))

            guest = cursor.fetchone()

            if not guest:
                print("未找到该客人的信息")
                return

            guest_id = guest['guest_id']
            print(f"\n客人: {guest['guest_name']}")

            # 修改查询：查找客人作为预订人或参与者的所有订单
            query = """
            SELECT DISTINCT o.order_id, o.order_status, o.total_people, o.total_rooms,
                   o.expect_check_in_time, o.expect_check_out_time, 
                   o.total_amount, o.order_time,
                   CASE 
                       WHEN o.guest_id = %s THEN '预订人'
                       ELSE '同住人'
                   END as guest_role
            FROM `order` o
            LEFT JOIN order_guest og ON o.order_id = og.order_id
            WHERE (o.guest_id = %s OR og.guest_id = %s)
            ORDER BY o.order_time DESC
            """

            cursor.execute(query, (guest_id, guest_id, guest_id))
            orders = cursor.fetchall()

            if not orders:
                print("没有找到订单")
                return

            # 显示订单（添加角色列）
            table = PrettyTable()
            table.field_names = ["订单号", "状态", "角色", "入住日期", "退房日期", "人数", "房间数", "金额", "下单时间"]

            for order in orders:
                status_display = self.get_status_display(order['order_status'])

                table.add_row([
                    order['order_id'],
                    status_display,
                    order['guest_role'],
                    order['expect_check_in_time'],
                    order['expect_check_out_time'],
                    order['total_people'],
                    order['total_rooms'],
                    f"¥{order['total_amount']}",
                    order['order_time'].strftime('%Y-%m-%d %H:%M')
                ])

            print(table)

            # 查看订单详情
            try:
                order_id = input("\n输入订单号查看详情 (0返回): ").strip()
                if order_id == '0':
                    return

                order_id = int(order_id)

                # 检查客人是否有权限查看该订单
                cursor.execute("""
                    SELECT o.order_id, o.order_status, g.guest_name, g.id_card,
                           CASE 
                               WHEN o.guest_id = %s THEN '预订人'
                               ELSE '同住人'
                           END as guest_role
                    FROM `order` o
                    LEFT JOIN order_guest og ON o.order_id = og.order_id
                    LEFT JOIN guest g ON (o.guest_id = g.guest_id OR og.guest_id = g.guest_id)
                    WHERE o.order_id = %s 
                      AND (o.guest_id = %s OR og.guest_id = %s)
                      AND g.guest_id = %s
                    LIMIT 1
                """, (guest_id, order_id, guest_id, guest_id, guest_id))

                order_check = cursor.fetchone()

                if not order_check:
                    print("您无权查看此订单或订单不存在")
                    return

                # 查询订单详情（只查询未删除的房间）
                query = """
                SELECT r.room_number, r.type_name, orm.price, r.status
                FROM order_room orm
                JOIN room r ON orm.room_id = r.room_id
                WHERE orm.order_id = %s AND r.is_deleted = False
                """

                cursor.execute(query, (order_id,))
                rooms = cursor.fetchall()

                if rooms:
                    print(f"\n订单 {order_id} 详情:")
                    print(f"您的角色: {order_check['guest_role']}")

                    room_table = PrettyTable()
                    room_table.field_names = ["房间号", "房型", "价格/晚", "状态"]

                    for room in rooms:
                        room_table.add_row([
                            room['room_number'],
                            self.get_room_type_display(room['type_name']),
                            f"¥{room['price']}",
                            self.get_status_display(room['status'])
                        ])

                    print(room_table)

                    # 查询订单基本信息
                    cursor.execute("""
                        SELECT o.order_status, o.expect_check_in_time, 
                               o.expect_check_out_time, o.total_amount, o.guest_id as booker_id
                        FROM `order` o
                        WHERE o.order_id = %s
                    """, (order_id,))

                    order_info = cursor.fetchone()

                    if order_info:
                        print(f"\n订单状态: {self.get_status_display(order_info['order_status'])}")
                        print(f"入住时间: {order_info['expect_check_in_time']}")
                        print(f"退房时间: {order_info['expect_check_out_time']}")
                        print(f"总金额: ¥{order_info['total_amount']}")

                        # 只有预订人才可以取消订单
                        if order_info['booker_id'] == guest_id and order_info['order_status'] == 'BOOKED':
                            cancel_choice = input("\n是否要取消此预订? (y/n): ").strip().lower()
                            if cancel_choice == 'y':
                                confirm = input("确认取消预订? 取消后将无法恢复 (y/n): ").strip().lower()
                                if confirm == 'y':
                                    self.cancel_order_by_id(order_id, rooms, cursor)
                        elif order_info['order_status'] == 'BOOKED':
                            print("\n提示：您是该订单的同住人，请联系预订人取消订单")
                else:
                    print("未找到该订单的房间信息")

            except ValueError:
                print("无效的订单号")

        except Error as e:
            print(f"查询错误: {e}")

    def cancel_reservation(self):
        """取消预订"""
        print("\n" + "=" * 60)
        print("取消订单")
        print("=" * 60)

        # 选择查询方式
        print("\n查询方式:")
        print("1. 按身份证查询")
        print("2. 按电话查询")
        choice = input("请选择查询方式 (1-2): ").strip()

        id_card = None
        phone = None

        if choice == '1':
            # 验证身份证号
            while True:
                id_card = input("请输入身份证号: ").strip()
                if self.validate_id_card(id_card):
                    break
                print("身份证号格式错误，请输入18位身份证号")
        elif choice == '2':
            # 验证电话号码
            while True:
                phone = input("请输入电话号码: ").strip()
                if self.validate_phone(phone):
                    break
                print("电话号码格式错误，请输入11位数字")
        else:
            print("无效选择")
            return

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 查询客人信息
            if choice == '1':
                cursor.execute("SELECT guest_id, guest_name FROM guest WHERE id_card = %s", (id_card,))
            else:
                cursor.execute("SELECT guest_id, guest_name FROM guest WHERE phone = %s", (phone,))

            guest = cursor.fetchone()

            if not guest:
                print("未找到该客人的信息")
                return

            # 查询该客人的已预订订单
            query = """
            SELECT o.order_id, o.expect_check_in_time, o.expect_check_out_time,
                   o.total_amount, o.order_time
            FROM `order` o
            WHERE o.guest_id = %s AND o.order_status = 'BOOKED'
            ORDER BY o.expect_check_in_time
            """

            cursor.execute(query, (guest['guest_id'],))
            pending_orders = cursor.fetchall()

            if not pending_orders:
                print("没有可取消的预订订单")
                return

            print(f"\n客人: {guest['guest_name']}")
            print("\n可取消的预订订单:")
            table = PrettyTable()
            table.field_names = ["订单号", "入住日期", "退房日期", "金额", "下单时间"]

            for order in pending_orders:
                table.add_row([
                    order['order_id'],
                    order['expect_check_in_time'],
                    order['expect_check_out_time'],
                    f"¥{order['total_amount']}",
                    order['order_time'].strftime('%Y-%m-%d %H:%M')
                ])

            print(table)

            try:
                order_id = int(input("\n请输入要取消的订单号 (0返回): ").strip())
                if order_id == 0:
                    return

                # 验证订单是否属于该客人
                cursor.execute("""
                    SELECT order_id FROM `order` 
                    WHERE order_id = %s AND guest_id = %s AND order_status = 'BOOKED'
                """, (order_id, guest['guest_id']))

                if not cursor.fetchone():
                    print("订单号无效或订单状态不可取消")
                    return

                # 查询订单房间信息（只查询未删除的房间）
                room_query = """
                SELECT r.room_number, r.type_name, r.status
                FROM order_room orm
                JOIN room r ON orm.room_id = r.room_id
                WHERE orm.order_id = %s AND r.is_deleted = False
                """

                cursor.execute(room_query, (order_id,))
                rooms = cursor.fetchall()

                if not rooms:
                    print("未找到该订单的房间信息")
                    return

                # 显示订单详情
                print(f"\n订单 {order_id} 详情:")
                for room in rooms:
                    print(f"  - {room['room_number']} ({self.get_room_type_display(room['type_name'])})")

                # 确认取消
                confirm = input("\n确认取消此订单? 取消后将无法恢复 (y/n): ").strip().lower()
                if confirm != 'y':
                    print("取消操作已取消")
                    return

                # 调用取消订单的方法
                self.cancel_order_by_id(order_id, rooms, cursor)

            except ValueError:
                print("无效的订单号")

        except Error as e:
            print(f"取消订单错误: {e}")

    def cancel_order_by_id(self, order_id, rooms, cursor):
        """根据订单ID取消订单（通用方法）"""
        try:
            # 开始事务
            cursor.execute("START TRANSACTION")

            # 1. 更新订单状态为已取消
            update_order = "UPDATE `order` SET order_status = 'CANCELLED' WHERE order_id = %s"
            cursor.execute(update_order, (order_id,))

            # 2. 更新房间状态为空闲
            for room in rooms:
                update_room = """
                UPDATE room SET status = 'AVAILABLE' 
                WHERE room_number = %s AND is_deleted = False
                """
                cursor.execute(update_room, (room['room_number'],))

            # 提交事务
            self.connection.commit()

            print(f"\n订单 {order_id} 已成功取消！")
            print(f"房间状态已更新为空闲")

        except Error as e:
            # 回滚事务
            self.connection.rollback()
            print(f"取消订单失败: {e}")
            print("请稍后重试或联系管理员")

    def room_management(self):
        """客房管理（操作员）"""
        if not self.check_admin_permission("客房管理"):
            return

        while True:
            print("\n" + "-" * 40)
            print("客房管理")
            print("-" * 40)
            print("1. 添加客房")
            print("2. 删除客房")
            print("3. 修改房价")
            print("4. 修改房型")
            print("5. 查看所有客房")
            print("6. 返回")
            print("-" * 40)

            choice = input("请选择 (1-6): ").strip()

            if choice == '1':
                self.add_room()
            elif choice == '2':
                self.delete_room()
            elif choice == '3':
                self.modify_room_price()
            elif choice == '4':
                self.modify_room_type()
            elif choice == '5':
                self.view_all_rooms()
            elif choice == '6':
                return
            else:
                print("无效选择")

    def add_room(self):
        """添加客房"""
        if not self.check_admin_permission("添加客房"):
            return

        print("\n" + "-" * 40)
        print("添加客房")
        print("-" * 40)

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 获取房间信息
            room_number = input("房间号: ").strip()

            # 检查房间号是否已存在（只检查未删除的房间）
            cursor.execute("SELECT room_id, is_deleted FROM room WHERE room_number = %s", (room_number,))

            # 读取所有结果，避免"Unread result found"错误
            existing_rooms = cursor.fetchall()

            # 检查是否存在未删除的房间
            active_room_exists = False
            deleted_room_exists = False

            for room in existing_rooms:
                if not room['is_deleted']:
                    active_room_exists = True
                    break
                else:
                    deleted_room_exists = True

            if active_room_exists:
                # 存在未删除的房间
                print("该房号已存在且未删除，添加失败！")
                return
            elif deleted_room_exists:
                # 存在已删除的房间，创建新记录
                print(f"房间号 {room_number} 已被删除，将创建新记录")
            else:
                # 完全不存在该房间号
                print(f"房间号 {room_number} 不存在，将创建新记录")

            # 获取房间信息
            print("\n可选房型:")
            print("1. STANDARD (标准房)")
            print("2. KING_BED (大床房)")
            print("3. TWIN_BED (双床房)")
            print("4. FAMILY_SUITE (家庭套房)")

            type_choice = input("选择房型 (1-4): ").strip()
            type_map = {
                '1': 'STANDARD',
                '2': 'KING_BED',
                '3': 'TWIN_BED',
                '4': 'FAMILY_SUITE'
            }

            if type_choice not in type_map:
                print("无效的房型选择")
                return

            type_name = type_map[type_choice]

            try:
                base_price = float(input("基础价格: ").strip())
                # 验证价格不能为负
                if base_price < 0:
                    print("错误：价格不能为负数！")
                    return
            except ValueError:
                print("请输入有效的数字")
                return

            # 在执行数据库操作前自动备份
            operation_details = f"添加客房: 房间号={room_number}, 房型={type_name}, 价格={base_price}"
            if not self.auto_backup_for_room_operation("ADD_ROOM", operation_details):
                print("自动备份失败，操作已取消")
                return

            # 插入新房间记录（保持is_deleted=False）
            insert_query = """
            INSERT INTO room (type_name, base_price, room_number, status, is_deleted)
            VALUES (%s, %s, %s, 'AVAILABLE', False)
            """

            cursor.execute(insert_query, (type_name, base_price, room_number))

            # 获取新插入的房间ID
            new_room_id = cursor.lastrowid

            # 记录日志 - 添加操作时间，并关联room_id
            log_query = """
            INSERT INTO room_add_delete_log (operator_id, room_id, room_number, type_name, operation_type, operation_time)
            VALUES (%s, %s, %s, %s, 'add', NOW())
            """
            cursor.execute(log_query, (self.current_operator_id, new_room_id, room_number, type_name))

            self.connection.commit()

            print(f"房间 {room_number} ({self.get_room_type_display(type_name)}) 添加成功！（新记录，ID: {new_room_id}）")

        except Error as e:
            self.connection.rollback()
            print(f"添加房间错误: {e}")
            import traceback
            traceback.print_exc()  # 打印详细错误信息
        finally:
            if 'cursor' in locals():
                cursor.close()

    def delete_room(self):
        """删除客房（软删除）"""
        if not self.check_admin_permission("删除客房"):
            return

        print("\n" + "-" * 40)
        print("删除客房")
        print("-" * 40)

        room_number = input("请输入要删除的房间号: ").strip()

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 检查房间是否存在且未删除
            cursor.execute("SELECT room_id, type_name, status FROM room WHERE room_number = %s AND is_deleted = False",
                           (room_number,))
            room = cursor.fetchone()

            if not room:
                print("房间不存在或已被删除")
                return

            # 检查房间状态
            if room['status'] != 'AVAILABLE':
                print(f"房间状态为'{self.get_status_display(room['status'])}'，不能删除")
                return

            # 确认删除
            confirm = input(f"确认删除房间 {room_number}? (y/n): ").strip().lower()
            if confirm != 'y':
                print("删除取消")
                return

            # 在执行数据库操作前自动备份
            operation_details = f"删除客房: 房间号={room_number}, 房型={room['type_name']}, 当前状态={room['status']}"
            if not self.auto_backup_for_room_operation("DELETE_ROOM", operation_details):
                print("自动备份失败，操作已取消")
                return

            # 软删除：将is_deleted设置为True
            update_query = "UPDATE room SET is_deleted = True WHERE room_id = %s"
            cursor.execute(update_query, (room['room_id'],))

            # 记录日志 - 添加操作时间，并关联room_id
            log_query = """
            INSERT INTO room_add_delete_log (operator_id, room_id, room_number, type_name, operation_type, operation_time)
            VALUES (%s, %s, %s, %s, 'delete', NOW())
            """
            cursor.execute(log_query, (self.current_operator_id, room['room_id'], room_number, room['type_name']))

            self.connection.commit()

            print(f"房间 {room_number} 已标记为删除！")

        except Error as e:
            self.connection.rollback()
            print(f"删除房间错误: {e}")

    def modify_room_price(self):
        """修改房价"""
        if not self.check_admin_permission("修改房价"):
            return

        print("\n" + "-" * 40)
        print("修改房价")
        print("-" * 40)

        # 显示房型选择菜单
        print("选择要修改价格的房型:")
        print("1. STANDARD (标准房)")
        print("2. KING_BED (大床房)")
        print("3. TWIN_BED (双床房)")
        print("4. FAMILY_SUITE (家庭套房)")

        type_choice = input("请选择房型 (1-4): ").strip()

        # 定义数字到房型的映射
        type_map = {
            '1': 'STANDARD',
            '2': 'KING_BED',
            '3': 'TWIN_BED',
            '4': 'FAMILY_SUITE'
        }

        if type_choice not in type_map:
            print("无效的房型选择")
            return

        room_type = type_map[type_choice]

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 检查房型是否存在（只查询未删除的房间）
            cursor.execute("SELECT base_price FROM room WHERE type_name = %s AND is_deleted = False LIMIT 1",
                           (room_type,))
            room = cursor.fetchone()

            if not room:
                print("该房型不存在或所有房间已被删除")
                return

            old_price = room['base_price']
            print(f"{self.get_room_type_display(room_type)}当前价格: ¥{old_price}")

            try:
                new_price = float(input("新价格: ").strip())
                # 验证价格不能为负
                if new_price < 0:
                    print("错误：价格不能为负数！")
                    return
            except ValueError:
                print("请输入有效的价格")
                return

            # 确认修改
            confirm = input(
                f"确认将{self.get_room_type_display(room_type)}价格从¥{old_price}修改为¥{new_price}? (y/n): ").strip().lower()
            if confirm != 'y':
                print("修改取消")
                return

            # 在执行数据库操作前自动备份
            operation_details = f"修改房价: 房型={room_type}, 原价={old_price}, 新价={new_price}"
            if not self.auto_backup_for_room_operation("MODIFY_PRICE", operation_details):
                print("自动备份失败，操作已取消")
                return

            # 更新价格（只更新未删除的房间）
            update_query = "UPDATE room SET base_price = %s WHERE type_name = %s AND is_deleted = False"
            cursor.execute(update_query, (new_price, room_type))

            # 记录日志
            log_query = """
            INSERT INTO room_type_price_change_log (operator_id, room_type, old_price, new_price, change_time)
            VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(log_query, (self.current_operator_id, room_type, old_price, new_price))

            self.connection.commit()

            print(f"{self.get_room_type_display(room_type)}价格修改成功！")

        except Error as e:
            self.connection.rollback()
            print(f"修改价格错误: {e}")

    def modify_room_type(self):
        """修改房型"""
        if not self.check_admin_permission("修改房型"):
            return

        print("\n" + "-" * 40)
        print("修改房型")
        print("-" * 40)

        room_number = input("请输入要修改房型的房间号: ").strip()

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 获取房间信息（只查询未删除的房间）
            cursor.execute(
                "SELECT room_id, type_name, base_price, status FROM room WHERE room_number = %s AND is_deleted = False",
                (room_number,))
            room = cursor.fetchone()

            if not room:
                print("房间不存在或已被删除")
                return

            if room['status'] != 'AVAILABLE':
                print(f"房间状态为'{self.get_status_display(room['status'])}'，不能修改房型")
                return

            old_type = room['type_name']
            old_price = room['base_price']
            print(f"当前房型: {self.get_room_type_display(old_type)}")
            print(f"当前价格: ¥{old_price}")

            # 定义房型与默认价格的映射
            room_type_default_prices = {
                'STANDARD': 299,
                'KING_BED': 399,
                'TWIN_BED': 459,
                'FAMILY_SUITE': 899
            }

            print("\n可选新房型:")
            print("1. STANDARD (标准房) - 默认¥299")
            print("2. KING_BED (大床房) - 默认¥399")
            print("3. TWIN_BED (双床房) - 默认¥459")
            print("4. FAMILY_SUITE (家庭套房) - 默认¥899")

            type_choice = input("选择新房型 (1-4): ").strip()
            type_map = {
                '1': 'STANDARD',
                '2': 'KING_BED',
                '3': 'TWIN_BED',
                '4': 'FAMILY_SUITE'
            }

            if type_choice not in type_map:
                print("无效的房型选择")
                return

            new_type = type_map[type_choice]
            default_price = room_type_default_prices[new_type]

            # 提示用户可以自定义价格
            print(f"\n{self.get_room_type_display(new_type)}的默认价格为: ¥{default_price}")

            # 获取自定义价格
            while True:
                price_input = input(f"请输入新的价格 (默认¥{default_price}, 直接回车使用默认价格): ").strip()

                if not price_input:  # 用户直接回车，使用默认价格
                    new_price = default_price
                    break

                try:
                    new_price = float(price_input)
                    if new_price < 0:
                        print("错误：价格不能为负数！")
                        continue
                    if new_price == 0:
                        print("警告：价格设置为0，确定吗？")
                        confirm_zero = input("确认将价格设置为0? (y/n): ").strip().lower()
                        if confirm_zero != 'y':
                            continue
                    break
                except ValueError:
                    print("请输入有效的数字")

            # 显示修改信息
            print(f"\n修改详情:")
            print(f"房间号: {room_number}")
            print(f"房型: {self.get_room_type_display(old_type)} → {self.get_room_type_display(new_type)}")
            print(f"价格: ¥{old_price} → ¥{new_price}")

            # 确认修改
            confirm = input(f"\n确认修改? (y/n): ").strip().lower()
            if confirm != 'y':
                print("修改取消")
                return

            # 在执行数据库操作前自动备份
            operation_details = f"修改房型: 房间号={room_number}, 原房型={old_type}¥{old_price}, 新房型={new_type}¥{new_price}"
            if not self.auto_backup_for_room_operation("MODIFY_TYPE", operation_details):
                print("自动备份失败，操作已取消")
                return

            # 更新房型和价格
            update_query = "UPDATE room SET type_name = %s, base_price = %s WHERE room_id = %s"
            cursor.execute(update_query, (new_type, new_price, room['room_id']))

            # 记录房型调整日志
            log_query = """
            INSERT INTO room_type_change_log 
            (operator_id, room_id, room_number, old_type, new_type, change_time)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(log_query, (
                self.current_operator_id,
                room['room_id'],
                room_number,
                old_type,
                new_type
            ))

            self.connection.commit()

            print(f"\n房间{room_number}修改成功！")
            print(f"房型: {self.get_room_type_display(old_type)} → {self.get_room_type_display(new_type)}")
            print(f"价格: ¥{old_price} → ¥{new_price}")

        except Error as e:
            self.connection.rollback()
            print(f"修改房型错误: {e}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()

    def view_all_rooms(self):
        """查看所有客房（只显示未删除的）"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            query = """
            SELECT room_number, type_name, base_price, status 
            FROM room 
            WHERE is_deleted = False
            ORDER BY room_number
            """

            cursor.execute(query)
            rooms = cursor.fetchall()

            if not rooms:
                print("没有房间信息")
                return

            table = PrettyTable()
            table.field_names = ["房间号", "房型", "价格", "状态"]

            for room in rooms:
                table.add_row([
                    room['room_number'],
                    self.get_room_type_display(room['type_name']),
                    f"¥{room['base_price']}",
                    self.get_status_display(room['status'])
                ])

            print(table)

            # 统计信息
            total_rooms = len(rooms)
            available_rooms = len([r for r in rooms if r['status'] == 'AVAILABLE'])
            occupied_rooms = len([r for r in rooms if r['status'] == 'OCCUPIED'])
            reserved_rooms = len([r for r in rooms if r['status'] == 'RESERVED'])

            print(f"\n统计信息:")
            print(f"总房间数: {total_rooms}")
            print(f"空闲房间: {available_rooms}")
            print(f"已入住: {occupied_rooms}")
            print(f"预留: {reserved_rooms}")
            if total_rooms > 0:
                print(f"入住率: {(occupied_rooms / total_rooms * 100):.1f}%")

        except Error as e:
            print(f"查询错误: {e}")

    def check_in(self):
        """办理入住登记"""
        if not self.check_operator_permission():
            return

        print("\n" + "=" * 60)
        print("办理入住登记")
        print("=" * 60)

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 查询待入住的预订订单（移除日期限制）
            query = """
            SELECT o.order_id, g.guest_name, g.phone, g.id_card,
                   o.total_people, o.total_rooms, o.expect_check_in_time,
                   o.expect_check_out_time, o.total_amount
            FROM `order` o
            JOIN guest g ON o.guest_id = g.guest_id
            WHERE o.order_status = 'BOOKED'
            ORDER BY o.expect_check_in_time
            """

            cursor.execute(query)
            pending_orders = cursor.fetchall()

            if not pending_orders:
                print("没有待入住的预订订单")
                return

            print("\n待入住订单:")
            table = PrettyTable()
            table.field_names = ["订单号", "客人", "电话", "入住日期", "退房日期", "人数", "房间数", "金额"]

            for order in pending_orders:
                table.add_row([
                    order['order_id'],
                    order['guest_name'],
                    order['phone'],
                    order['expect_check_in_time'],
                    order['expect_check_out_time'],
                    order['total_people'],
                    order['total_rooms'],
                    f"¥{order['total_amount']}"
                ])

            print(table)

            try:
                order_id = int(input("\n请输入要办理入住的订单号 (0返回): ").strip())
                if order_id == 0:
                    return

                # 查找订单
                order = None
                for o in pending_orders:
                    if o['order_id'] == order_id:
                        order = o
                        break

                if not order:
                    print("订单号无效")
                    return

                # 显示订单详情
                print(f"\n订单 {order_id} 详情:")
                print(f"客人: {order['guest_name']}")
                print(f"电话: {order['phone']}")
                print(f"身份证: {order['id_card']}")
                print(f"入住: {order['expect_check_in_time']}")
                print(f"退房: {order['expect_check_out_time']}")
                print(f"人数: {order['total_people']}")
                print(f"房间数: {order['total_rooms']}")

                # 查询订单房间（只查询未删除的房间）
                room_query = """
                SELECT r.room_number, r.type_name, orm.price
                FROM order_room orm
                JOIN room r ON orm.room_id = r.room_id
                WHERE orm.order_id = %s AND r.is_deleted = False
                """

                cursor.execute(room_query, (order_id,))
                rooms = cursor.fetchall()

                print("\n预订房间:")
                for room in rooms:
                    print(f"  - {room['room_number']} ({self.get_room_type_display(room['type_name'])})")

                # 最终确认入住
                confirm = input("\n确认办理入住? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("入住取消")
                    return

                # 更新订单状态
                update_order = "UPDATE `order` SET order_status = 'CHECKED_IN' WHERE order_id = %s"
                cursor.execute(update_order, (order_id,))

                # 更新房间状态
                for room in rooms:
                    update_room = """
                    UPDATE room SET status = 'OCCUPIED' 
                    WHERE room_number = %s AND is_deleted = False
                    """
                    cursor.execute(update_room, (room['room_number'],))

                self.connection.commit()

                print(f"\n订单 {order_id} 入住办理成功！")

            except ValueError:
                print("无效的订单号")

        except Error as e:
            self.connection.rollback()
            print(f"办理入住错误: {e}")

    def check_out(self):
        """办理退房结账 - 修改：营收应计入入住日期"""
        if not self.check_operator_permission():
            return

        print("\n" + "=" * 60)
        print("办理退房结账")
        print("=" * 60)

        try:
            cursor = self.connection.cursor(dictionary=True)

            # 查询已入住的订单
            query = """
            SELECT o.order_id, g.guest_name, g.phone,
                   o.expect_check_in_time, o.expect_check_out_time,
                   o.total_amount, o.total_people, o.total_rooms
            FROM `order` o
            JOIN guest g ON o.guest_id = g.guest_id
            WHERE o.order_status = 'CHECKED_IN'
            ORDER BY o.expect_check_out_time
            """

            cursor.execute(query)
            check_out_orders = cursor.fetchall()

            if not check_out_orders:
                print("没有待退房的订单")
                return

            print("\n待退房订单:")
            table = PrettyTable()
            table.field_names = ["订单号", "客人", "电话", "入住日期", "退房日期", "金额"]

            for order in check_out_orders:
                table.add_row([
                    order['order_id'],
                    order['guest_name'],
                    order['phone'],
                    order['expect_check_in_time'],
                    order['expect_check_out_time'],
                    f"¥{order['total_amount']}"
                ])

            print(table)

            try:
                order_id = int(input("\n请输入要退房的订单号 (0返回): ").strip())
                if order_id == 0:
                    return

                # 查找订单
                order = None
                for o in check_out_orders:
                    if o['order_id'] == order_id:
                        order = o
                        break

                if not order:
                    print("订单号无效")
                    return

                # 显示订单详情
                print(f"\n订单 {order_id} 详情:")
                print(f"客人: {order['guest_name']}")
                print(f"电话: {order['phone']}")
                print(f"入住: {order['expect_check_in_time']}")
                print(f"计划退房: {order['expect_check_out_time']}")
                print(f"应收金额: ¥{order['total_amount']}")

                # 查询订单房间（只查询未删除的房间）
                room_query = """
                SELECT r.room_number, r.type_name
                FROM order_room orm
                JOIN room r ON orm.room_id = r.room_id
                WHERE orm.order_id = %s AND r.is_deleted = False
                """

                cursor.execute(room_query, (order_id,))
                rooms = cursor.fetchall()

                print("\n入住房间:")
                for room in rooms:
                    print(f"  - {room['room_number']} ({self.get_room_type_display(room['type_name'])})")

                # 确认退房
                confirm = input("\n确认办理退房? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("退房取消")
                    return

                # 更新订单状态
                update_order = "UPDATE `order` SET order_status = 'COMPLETED' WHERE order_id = %s"
                cursor.execute(update_order, (order_id,))

                # 更新房间状态为空闲
                for room in rooms:
                    update_room = "UPDATE room SET status = 'AVAILABLE' WHERE room_number = %s AND is_deleted = False"
                    cursor.execute(update_room, (room['room_number'],))

                # 注意：这里不再更新当日营收报表，因为营收应在订单创建时或入住时计入入住日期
                # 营收统计将在生成报表时按入住日期重新计算

                self.connection.commit()

                print(f"\n订单 {order_id} 退房办理成功！")
                print(f"已收取 ¥{order['total_amount']}")
                print("注意：营收已计入订单的创建日期")

            except ValueError:
                print("无效的订单号")

        except Error as e:
            self.connection.rollback()
            print(f"办理退房错误: {e}")

    def query_system(self):
        """查询系统"""
        while True:
            print("\n" + "-" * 40)
            print("查询系统")
            print("-" * 40)
            print("1. 查询客人信息")
            print("2. 查询订单详情")
            print("3. 查询房间状态")
            print("4. 返回")
            print("-" * 40)

            choice = input("请选择 (1-4): ").strip()

            if choice == '1':
                self.query_guest_info()
            elif choice == '2':
                self.query_order_details()
            elif choice == '3':
                self.query_room_status_operator()
            elif choice == '4':
                return
            else:
                print("无效选择")

    def query_guest_info(self):
        """查询客人信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            print("\n" + "-" * 40)
            print("查询客人信息")
            print("-" * 40)

            print("查询方式:")
            print("1. 按姓名查询")
            print("2. 按电话查询")
            print("3. 按身份证查询")

            choice = input("请选择查询方式 (1-3): ").strip()

            if choice == '1':
                name = input("请输入客人姓名: ").strip()
                query = "SELECT * FROM guest WHERE guest_name LIKE %s"
                cursor.execute(query, (f"%{name}%",))
            elif choice == '2':
                phone = input("请输入电话: ").strip()
                query = "SELECT * FROM guest WHERE phone LIKE %s"
                cursor.execute(query, (f"%{phone}%",))
            elif choice == '3':
                id_card = input("请输入身份证: ").strip()
                query = "SELECT * FROM guest WHERE id_card = %s"
                cursor.execute(query, (id_card,))
            else:
                print("无效选择")
                return

            guests = cursor.fetchall()

            if not guests:
                print("没有找到客人信息")
                return

            table = PrettyTable()
            table.field_names = ["ID", "姓名", "电话", "身份证"]

            for guest in guests:
                table.add_row([
                    guest['guest_id'],
                    guest['guest_name'],
                    guest['phone'],
                    guest['id_card']
                ])

            print(table)

        except Error as e:
            print(f"查询错误: {e}")

    def query_order_details(self):
        """查询订单详情"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            order_id = input("请输入订单号: ").strip()

            if not order_id:
                print("订单号不能为空")
                return

            # 查询订单基本信息
            query = """
            SELECT o.*, g.guest_name, g.phone, g.id_card
            FROM `order` o
            JOIN guest g ON o.guest_id = g.guest_id
            WHERE o.order_id = %s
            """

            cursor.execute(query, (order_id,))
            order = cursor.fetchone()

            if not order:
                print("订单不存在")
                return

            print(f"\n订单 {order_id} 详情:")
            print("-" * 40)
            print(f"订单状态: {self.get_status_display(order['order_status'])}")
            print(f"客人姓名: {order['guest_name']}")
            print(f"电话: {order['phone']}")
            print(f"身份证: {order['id_card']}")
            print(f"入住时间: {order['expect_check_in_time']}")
            print(f"退房时间: {order['expect_check_out_time']}")
            print(f"总人数: {order['total_people']}")
            print(f"总房间数: {order['total_rooms']}")
            print(f"总金额: ¥{order['total_amount']}")
            print(f"下单时间: {order['order_time'].strftime('%Y-%m-%d %H:%M')}")

            # 查询订单房间（只查询未删除的房间）
            room_query = """
            SELECT r.room_number, r.type_name, orm.price, r.status
            FROM order_room orm
            JOIN room r ON orm.room_id = r.room_id
            WHERE orm.order_id = %s AND r.is_deleted = False
            """

            cursor.execute(room_query, (order_id,))
            rooms = cursor.fetchall()

            if rooms:
                print("\n房间信息:")
                room_table = PrettyTable()
                room_table.field_names = ["房间号", "房型", "价格/晚", "状态"]

                for room in rooms:
                    room_table.add_row([
                        room['room_number'],
                        self.get_room_type_display(room['type_name']),
                        f"¥{room['price']}",
                        self.get_status_display(room['status'])
                    ])

                print(room_table)

            # 查询同住客人
            guest_query = """
            SELECT g.guest_name, g.phone, g.id_card
            FROM order_guest og
            JOIN guest g ON og.guest_id = g.guest_id
            WHERE og.order_id = %s
            """

            cursor.execute(guest_query, (order_id,))
            other_guests = cursor.fetchall()

            if len(other_guests) > 1:
                print("\n同住客人:")
                for guest in other_guests[1:]:  # 跳过预订人
                    print(f"  - {guest['guest_name']} ({guest['id_card']})")

        except Error as e:
            print(f"查询错误: {e}")

    def query_room_status_operator(self):
        """操作员查询房间状态（更详细）"""
        self.view_all_rooms()

    def report_system(self):
        """报表系统"""
        if not self.check_admin_permission("报表系统"):
            return

        while True:
            print("\n" + "-" * 40)
            print("报表系统")
            print("-" * 40)
            print("1. 生成总体营收报表")
            print("2. 生成房型营收报表")
            print("3. 生成当日营收报表")
            print("4. 查看历史报表")
            print("5. 返回")
            print("-" * 40)

            choice = input("请选择 (1-5): ").strip()

            if choice == '1':
                self.generate_total_revenue_report()
            elif choice == '2':
                self.generate_room_type_report()
            elif choice == '3':
                self.generate_day_revenue_report()
            elif choice == '4':
                self.view_history_reports()
            elif choice == '5':
                return
            else:
                print("无效选择")

    def generate_total_revenue_report(self):
        """生成总体营收报表 - 统计所有未被取消的订单"""
        if not self.check_admin_permission("生成总体营收报表"):
            return

        try:
            cursor = self.connection.cursor(dictionary=True)

            print("\n" + "=" * 60)
            print("生成总体营收报表")
            print("=" * 60)
            print("说明：统计数据库中所有完成的订单（COMPLETED）")

            # 查询统计数据 - 所有未被取消的订单
            query = """
            SELECT 
                DATE(o.order_time) as order_date,
                COUNT(DISTINCT o.order_id) as orders_count,
                SUM(o.total_people) as total_guest,
                SUM(o.total_amount) as total_revenue
            FROM `order` o
            WHERE o.order_status IN ('COMPLETED')
            GROUP BY DATE(o.order_time)
            ORDER BY order_date
            """

            cursor.execute(query)
            stats_by_date = cursor.fetchall()

            if not stats_by_date:
                print("没有找到已完成的订单数据")
                return

            # 计算总计
            total_query = """
            SELECT 
                COUNT(DISTINCT o.order_id) as orders_count,
                SUM(o.total_people) as total_guest,
                SUM(o.total_amount) as total_revenue
            FROM `order` o
            WHERE o.order_status IN ('BOOKED', 'CHECKED_IN', 'COMPLETED')
            """

            cursor.execute(total_query)
            total_stats = cursor.fetchone()

            # 显示报表
            print(f"\n总体营收报表")
            print(f"统计时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 80)

            # 按日期显示明细
            table = PrettyTable()
            table.field_names = ["订单日期", "订单数", "客人总数", "总营收"]

            for stat in stats_by_date:
                table.add_row([
                    stat['order_date'],
                    stat['orders_count'],
                    stat['total_guest'],
                    f"¥{stat['total_revenue']:.2f}"
                ])

            print(table)
            print("-" * 80)
            print(
                f"总计: {total_stats['orders_count']}个订单, {total_stats['total_guest']}位客人, 总营收: ¥{total_stats['total_revenue']:.2f}")

            # 询问是否保存报表
            save = input("\n是否保存此报表? (y/n): ").strip().lower()
            if save == 'y':
                # 保存总体报表
                insert_query = """
                INSERT INTO total_revenue_report (operator_id, orders_count, total_guest, total_revenue)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    self.current_operator_id,
                    total_stats['orders_count'], total_stats['total_guest'], total_stats['total_revenue']
                ))

                self.connection.commit()
                print("报表已保存")

        except Error as e:
            print(f"生成报表错误: {e}")
            import traceback
            traceback.print_exc()

    def generate_room_type_report(self):
        """生成房型营收报表 - 统计所有完成的订单，按房型分开计算"""
        if not self.check_admin_permission("生成房型营收报表"):
            return

        try:
            cursor = self.connection.cursor(dictionary=True)

            print("\n" + "=" * 60)
            print("生成房型营收报表")
            print("=" * 60)
            print("说明：统计数据库中所有完成的订单（COMPLETED）")

            # 修改后的查询：按房型分开计算营收
            query = """
            SELECT 
                orm.type_name as room_type,
                DATE(o.order_time) as order_date,
                COUNT(DISTINCT o.order_id) as order_count,
                SUM(orm.price * DATEDIFF(o.expect_check_out_time, o.expect_check_in_time)) as total_revenue
            FROM `order` o
            JOIN order_room orm ON o.order_id = orm.order_id
            WHERE o.order_status = 'COMPLETED'
            GROUP BY orm.type_name, DATE(o.order_time)
            ORDER BY orm.type_name, order_date
            """

            cursor.execute(query)
            results = cursor.fetchall()

            if not results:
                print("没有找到已完成的订单数据")
                return

            # 按房型汇总
            room_type_summary = {}
            for row in results:
                room_type = row['room_type']
                if room_type not in room_type_summary:
                    room_type_summary[room_type] = {
                        'total_orders': 0,
                        'total_revenue': 0,
                        'daily_data': []
                    }

                room_type_summary[room_type]['total_orders'] += row['order_count']
                room_type_summary[room_type]['total_revenue'] += float(row['total_revenue'])
                room_type_summary[room_type]['daily_data'].append({
                    'date': row['order_date'],
                    'orders': row['order_count'],
                    'revenue': float(row['total_revenue'])
                })

            # 显示报表
            print(f"\n房型营收报表（按房型分开计算）")
            print(f"统计时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 80)

            # 显示汇总信息
            summary_table = PrettyTable()
            summary_table.field_names = ["房型", "订单数", "总营收", "占比"]

            total_revenue_all = sum(rt['total_revenue'] for rt in room_type_summary.values())

            for room_type, data in sorted(room_type_summary.items()):
                percentage = (data['total_revenue'] / total_revenue_all * 100) if total_revenue_all > 0 else 0
                summary_table.add_row([
                    self.get_room_type_display(room_type),
                    data['total_orders'],
                    f"¥{data['total_revenue']:.2f}",
                    f"{percentage:.1f}%"
                ])

            print("房型营收汇总:")
            print(summary_table)

            # 显示每日明细（可选）
            show_detail = input("\n是否显示每日明细? (y/n): ").strip().lower()
            if show_detail == 'y':
                for room_type, data in sorted(room_type_summary.items()):
                    print(f"\n{self.get_room_type_display(room_type)} 每日明细:")
                    detail_table = PrettyTable()
                    detail_table.field_names = ["订单日期", "订单数", "当日营收"]

                    for daily in sorted(data['daily_data'], key=lambda x: x['date']):
                        detail_table.add_row([
                            daily['date'],
                            daily['orders'],
                            f"¥{daily['revenue']:.2f}"
                        ])

                    print(detail_table)

            print(f"\n总营收: ¥{total_revenue_all:.2f}")

            # 询问是否保存报表
            save = input("\n是否保存此报表? (y/n): ").strip().lower()
            if save == 'y':
                for room_type, data in room_type_summary.items():
                    insert_query = """
                    INSERT INTO room_type_report (operator_id, room_type, total_revenue)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        self.current_operator_id, room_type, data['total_revenue']
                    ))

                self.connection.commit()
                print("报表已保存")

        except Error as e:
            print(f"生成报表错误: {e}")
            import traceback
            traceback.print_exc()

    def generate_day_revenue_report(self):
        """生成当日营收报表 - 修改：按订单创建日期统计"""
        if not self.check_admin_permission("生成当日营收报表"):
            return

        try:
            cursor = self.connection.cursor(dictionary=True)

            print("\n" + "=" * 60)
            print("生成当日营收报表")
            print("=" * 60)

            # 日期输入处理
            while True:
                date_str = input("日期 (YYYY-MM-DD, 留空为今天): ").strip()
                if not date_str:
                    report_date = datetime.date.today()
                    break
                else:
                    try:
                        report_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                        break
                    except ValueError:
                        print("日期格式错误，请使用YYYY-MM-DD格式，或留空使用今天日期")
                        continue

            # 查询当日数据 - 按订单创建日期统计，只统计非取消订单
            query = """
            SELECT 
                COUNT(DISTINCT o.order_id) as orders_count,
                SUM(o.total_people) as total_guest,
                SUM(o.total_amount) as total_revenue
            FROM `order` o
            WHERE DATE(o.order_time) = %s
              AND o.order_status IN ('COMPLETED', 'CHECKED_IN', 'BOOKED')
            """

            cursor.execute(query, (report_date,))
            stats = cursor.fetchone()

            # 查询订单明细
            detail_query = """
            SELECT 
                o.order_id,
                g.guest_name,
                o.total_people,
                o.total_rooms,
                o.total_amount,
                o.order_status,
                o.order_time
            FROM `order` o
            JOIN guest g ON o.guest_id = g.guest_id
            WHERE DATE(o.order_time) = %s
              AND o.order_status IN ('COMPLETED', 'CHECKED_IN', 'BOOKED')
            ORDER BY o.order_time
            """

            cursor.execute(detail_query, (report_date,))
            order_details = cursor.fetchall()

            # 显示报表
            print(f"\n当日营收报表（订单创建日期: {report_date}）")
            print("-" * 80)

            if stats['orders_count']:
                print(f"订单数量: {stats['orders_count']}")
                print(f"客人总数: {stats['total_guest']}")
                print(f"当日营收: ¥{stats['total_revenue']}")
                print("-" * 80)

                # 显示订单明细
                if order_details:
                    print("订单明细:")
                    detail_table = PrettyTable()
                    detail_table.field_names = ["订单号", "客人", "人数", "房间数", "金额", "状态", "创建时间"]

                    for order in order_details:
                        detail_table.add_row([
                            order['order_id'],
                            order['guest_name'],
                            order['total_people'],
                            order['total_rooms'],
                            f"¥{order['total_amount']}",
                            self.get_status_display(order['order_status']),
                            order['order_time'].strftime('%H:%M:%S')
                        ])

                    print(detail_table)
            else:
                print(f"{report_date} 没有订单创建数据")

            # 查询趋势数据（最近7天）- 按订单创建日期统计
            trend_query = """
            SELECT 
                DATE(order_time) as date,
                COUNT(DISTINCT order_id) as orders_count,
                SUM(total_amount) as total_revenue
            FROM `order`
            WHERE order_status IN ('COMPLETED', 'CHECKED_IN', 'BOOKED')
              AND DATE(order_time) >= DATE_SUB(%s, INTERVAL 7 DAY)
              AND DATE(order_time) <= %s
            GROUP BY DATE(order_time)
            ORDER BY date
            """

            cursor.execute(trend_query, (report_date, report_date))
            trend_data = cursor.fetchall()

            if len(trend_data) > 0:
                print(f"\n最近7天趋势（按订单创建日期统计）:")
                trend_table = PrettyTable()
                trend_table.field_names = ["订单日期", "订单数", "营收"]

                for day in trend_data:
                    trend_table.add_row([
                        day['date'],
                        day['orders_count'],
                        f"¥{day['total_revenue']}"
                    ])

                print(trend_table)

            # 检查是否已有今日报表
            check_query = "SELECT template_id FROM day_revenue_report WHERE date = %s"
            cursor.execute(check_query, (report_date,))
            existing_report = cursor.fetchone()

            if existing_report:
                update = input(f"\n{report_date}已有报表，是否更新? (y/n): ").strip().lower()
                if update == 'y':
                    update_query = """
                    UPDATE day_revenue_report 
                    SET operator_id = %s,
                        total_guest = %s,
                        total_revenue = %s
                    WHERE date = %s
                    """
                    cursor.execute(update_query, (
                        self.current_operator_id,
                        stats['total_guest'] if stats['total_guest'] else 0,
                        stats['total_revenue'] if stats['total_revenue'] else 0,
                        report_date
                    ))
                    self.connection.commit()
                    print("报表已更新")
            else:
                save = input("\n是否保存此报表? (y/n): ").strip().lower()
                if save == 'y':
                    insert_query = """
                    INSERT INTO day_revenue_report (operator_id, date, total_guest, total_revenue)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        self.current_operator_id,
                        report_date,
                        stats['total_guest'] if stats['total_guest'] else 0,
                        stats['total_revenue'] if stats['total_revenue'] else 0
                    ))
                    self.connection.commit()
                    print("报表已保存")

        except Error as e:
            print(f"生成报表错误: {e}")

    def view_history_reports(self):
        """查看历史报表"""
        if not self.check_admin_permission("查看历史报表"):
            return

        while True:
            print("\n" + "-" * 40)
            print("查看历史报表")
            print("-" * 40)
            print("1. 查看总体营收报表")
            print("2. 查看房型营收报表")
            print("3. 查看当日营收报表")
            print("4. 返回")
            print("-" * 40)

            choice = input("请选择 (1-4): ").strip()

            try:
                cursor = self.connection.cursor(dictionary=True)

                if choice == '1':
                    query = """
                    SELECT tr.*, o.account_name as operator_name
                    FROM total_revenue_report tr
                    JOIN operator o ON tr.operator_id = o.operator_id
                    ORDER BY tr.template_id DESC
                    LIMIT 10
                    """
                    cursor.execute(query)
                    reports = cursor.fetchall()

                    if reports:
                        print("\n最近10份总体营收报表:")
                        table = PrettyTable()
                        table.field_names = ["ID", "操作员", "订单数", "客人总数", "总营收"]

                        for report in reports:
                            table.add_row([
                                report['template_id'],
                                report['operator_name'],
                                report['orders_count'],
                                report['total_guest'],
                                f"¥{report['total_revenue']}"
                            ])

                        print(table)
                    else:
                        print("没有总体营收报表")

                elif choice == '2':
                    query = """
                    SELECT rtr.*, o.account_name as operator_name
                    FROM room_type_report rtr
                    JOIN operator o ON rtr.operator_id = o.operator_id
                    ORDER BY rtr.template_id DESC
                    LIMIT 20
                    """
                    cursor.execute(query)
                    reports = cursor.fetchall()

                    if reports:
                        print("\n最近20份房型营收报表:")
                        table = PrettyTable()
                        table.field_names = ["ID", "操作员", "房型", "营收"]

                        for report in reports:
                            table.add_row([
                                report['template_id'],
                                report['operator_name'],
                                self.get_room_type_display(report['room_type']),
                                f"¥{report['total_revenue']}"
                            ])

                        print(table)
                    else:
                        print("没有房型营收报表")

                elif choice == '3':
                    query = """
                    SELECT drr.*, o.account_name as operator_name
                    FROM day_revenue_report drr
                    JOIN operator o ON drr.operator_id = o.operator_id
                    ORDER BY drr.date DESC
                    LIMIT 10
                    """
                    cursor.execute(query)
                    reports = cursor.fetchall()

                    if reports:
                        print("\n最近10份当日营收报表:")
                        table = PrettyTable()
                        table.field_names = ["ID", "操作员", "日期", "客人总数", "当日营收"]

                        for report in reports:
                            table.add_row([
                                report['template_id'],
                                report['operator_name'],
                                report['date'],
                                report['total_guest'],
                                f"¥{report['total_revenue']}"
                            ])

                        print(table)
                    else:
                        print("没有当日营收报表")

                elif choice == '4':
                    return
                else:
                    print("无效选择")

            except Error as e:
                print(f"查询错误: {e}")

    def view_logs(self):
        """查看操作日志"""
        if not self.check_admin_permission("查看操作日志"):
            return

        while True:
            print("\n" + "-" * 40)
            print("操作日志")
            print("-" * 40)
            print("1. 查看房价调整日志")
            print("2. 查看房间增减日志")
            print("3. 查看房型调整日志")
            print("4. 返回")
            print("-" * 40)

            choice = input("请选择 (1-4): ").strip()

            try:
                cursor = self.connection.cursor(dictionary=True)

                if choice == '1':
                    query = """
                    SELECT l.*, o.account_name as operator_name
                    FROM room_type_price_change_log l
                    JOIN operator o ON l.operator_id = o.operator_id
                    ORDER BY l.change_time DESC
                    LIMIT 20
                    """
                    cursor.execute(query)
                    logs = cursor.fetchall()

                    if logs:
                        print("\n房价调整日志:")
                        table = PrettyTable()
                        table.field_names = ["操作员", "房型", "原价", "新价", "调整时间"]

                        for log in logs:
                            table.add_row([
                                log['operator_name'],
                                self.get_room_type_display(log['room_type']),
                                f"¥{log['old_price']}",
                                f"¥{log['new_price']}",
                                log['change_time'].strftime('%Y-%m-%d %H:%M')
                            ])

                        print(table)
                    else:
                        print("没有房价调整日志")

                elif choice == '2':
                    query = """
                    SELECT l.*, o.account_name as operator_name
                    FROM room_add_delete_log l
                    JOIN operator o ON l.operator_id = o.operator_id
                    ORDER BY l.operation_time DESC
                    LIMIT 20
                    """
                    cursor.execute(query)
                    logs = cursor.fetchall()

                    if logs:
                        print("\n房间增减日志:")
                        table = PrettyTable()
                        table.field_names = ["操作员", "房间号", "房型", "操作类型", "操作时间"]

                        for log in logs:
                            op_type = "添加" if log['operation_type'] == 'add' else "删除"
                            table.add_row([
                                log['operator_name'],
                                log['room_number'],
                                self.get_room_type_display(log['type_name']),
                                op_type,
                                log['operation_time'].strftime('%Y-%m-%d %H:%M')
                            ])

                        print(table)
                    else:
                        print("没有房间增减日志")

                elif choice == '3':
                    query = """
                    SELECT l.*, o.account_name as operator_name
                    FROM room_type_change_log l
                    JOIN operator o ON l.operator_id = o.operator_id
                    ORDER BY l.change_time DESC
                    LIMIT 20
                    """
                    cursor.execute(query)
                    logs = cursor.fetchall()

                    if logs:
                        print("\n房型调整日志:")
                        table = PrettyTable()
                        table.field_names = ["操作员", "房间号", "原房型", "新房型", "调整时间"]

                        for log in logs:
                            table.add_row([
                                log['operator_name'],
                                log['room_number'],
                                self.get_room_type_display(log['old_type']),
                                self.get_room_type_display(log['new_type']),
                                log['change_time'].strftime('%Y-%m-%d %H:%M')
                            ])

                        print(table)
                    else:
                        print("没有房型调整日志")

                elif choice == '4':
                    return
                else:
                    print("无效选择")

            except Error as e:
                print(f"查询错误: {e}")

    def database_management(self):
        """数据库管理（备份和恢复）"""
        if not self.check_admin_permission("数据库管理"):
            return

        while True:
            print("\n" + "-" * 40)
            print("数据库管理")
            print("-" * 40)
            print("1. 备份数据库")
            print("2. 恢复数据库")
            print("3. 查看备份列表")
            print("4. 删除备份")
            print("5. 查看备份日志")  # 新增
            print("6. 返回")
            print("-" * 40)

            choice = input("请选择 (1-6): ").strip()

            if choice == '1':
                self.backup_database()
            elif choice == '2':
                self.restore_database()
            elif choice == '3':
                self.list_backups()
            elif choice == '4':
                self.delete_backup()
            elif choice == '5':  # 新增
                self.view_backup_logs()
            elif choice == '6':
                return
            else:
                print("无效选择")

    def auto_backup_for_room_operation(self, operation_type, operation_details):
        """客房管理操作前的自动备份"""
        print("\n正在执行自动备份...")

        try:
            # 创建备份目录
            backup_dir = Path("database_backups")
            backup_dir.mkdir(exist_ok=True)

            # 生成备份文件名（包含时间戳和操作类型）
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"hotel_backup_{operation_type}_{timestamp}.sql"

            # MySQL连接信息
            config = {
                'host': '127.0.0.1',
                'port': 3306,
                'user': 'root',
                'password': '2015Xz0202',
                'database': 'hotel_management'
            }

            # 构建mysqldump命令
            cmd = [
                'mysqldump',
                f'--host={config["host"]}',
                f'--port={config["port"]}',
                f'--user={config["user"]}',
                f'--password={config["password"]}',
                '--databases',
                config['database'],
                '--routines',
                '--triggers',
                '--events',
                '--single-transaction',
                '--add-drop-database',
                '--result-file', str(backup_file)
            ]

            # 执行备份命令
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # 记录备份日志，关联操作详情
            self.log_backup_operation(
                operation_type,
                str(backup_file),
                True,
                f"客房管理操作备份: {operation_details}"
            )

            print("✓ 自动备份成功！")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ 自动备份失败: {e}")
            if e.stderr:
                print(f"错误信息: {e.stderr}")
            self.log_backup_operation(operation_type, "", False, f"备份失败: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ 自动备份过程中发生错误: {e}")
            self.log_backup_operation(operation_type, "", False, f"备份失败: {str(e)}")
            return False

    def backup_database(self):
        """备份数据库到SQL文件"""
        print("\n" + "=" * 60)
        print("数据库备份")
        print("=" * 60)

        # 创建备份目录
        backup_dir = Path("database_backups")
        backup_dir.mkdir(exist_ok=True)

        # 生成备份文件名（包含时间戳）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"hotel_backup_{timestamp}.sql"

        # MySQL连接信息
        config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '2015Xz0202',
            'database': 'hotel_management'
        }

        try:
            print(f"正在备份数据库到: {backup_file}")

            # 构建mysqldump命令
            cmd = [
                'mysqldump',
                f'--host={config["host"]}',
                f'--port={config["port"]}',
                f'--user={config["user"]}',
                f'--password={config["password"]}',
                '--databases',
                config['database'],
                '--routines',  # 包括存储过程和函数
                '--triggers',  # 包括触发器
                '--events',  # 包括事件
                '--single-transaction',
                '--add-drop-database',
                '--result-file', str(backup_file)
            ]

            # 执行备份命令
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            print("✓ 数据库备份成功！")
            print(f"备份文件: {backup_file}")
            print(f"文件大小: {os.path.getsize(backup_file) / 1024:.2f} KB")

            # 记录备份日志
            self.log_backup_operation('BACKUP', str(backup_file), True, "手动备份成功")

        except subprocess.CalledProcessError as e:
            print(f"✗ 备份失败: {e}")
            if e.stderr:
                print(f"错误信息: {e.stderr}")
            self.log_backup_operation('BACKUP', str(backup_file), False, str(e))
        except Exception as e:
            print(f"✗ 备份过程中发生错误: {e}")
            self.log_backup_operation('BACKUP', str(backup_file), False, str(e))

    def restore_database(self):
        """从备份文件恢复数据库"""
        print("\n" + "=" * 60)
        print("数据库恢复")
        print("=" * 60)

        # 检查备份目录
        backup_dir = Path("database_backups")
        if not backup_dir.exists() or not any(backup_dir.iterdir()):
            print("没有找到备份文件！")
            return

        # 列出备份文件（包含操作详情）
        backup_files = list(backup_dir.glob("*.sql"))
        backup_files.sort(key=os.path.getmtime, reverse=True)

        print("\n可用备份文件:")
        for i, file in enumerate(backup_files, 1):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
            file_size = os.path.getsize(file) / 1024

            # 获取备份日志中的操作详情
            operation_details = self.get_backup_operation_details(str(file))

            print(f"{i}. {file.name}")
            print(f"   时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   大小: {file_size:.2f} KB")
            print(f"   操作: {operation_details}")
            print()

        try:
            choice = int(input("选择要恢复的备份文件编号 (0取消): ").strip())
            if choice == 0:
                return
            if choice < 1 or choice > len(backup_files):
                print("无效的选择")
                return

            backup_file = backup_files[choice - 1]

            # 获取备份文件的操作详情
            operation_details = self.get_backup_operation_details(str(backup_file))

            # 确认恢复操作
            print(f"\n⚠️ 警告：即将恢复数据库到备份状态！")
            print(f"备份文件: {backup_file.name}")
            print(f"备份时间: {datetime.datetime.fromtimestamp(os.path.getmtime(backup_file))}")
            print(f"操作详情: {operation_details}")

            confirm = input("\n此操作将覆盖当前所有数据！确认恢复？(y/n): ").strip().lower()
            if confirm != 'y':
                print("恢复操作已取消")
                return

            # 二次确认
            confirm2 = input("请再次确认，输入'CONFIRM'继续: ").strip()
            if confirm2 != 'CONFIRM':
                print("恢复操作已取消")
                return

            print("正在恢复数据库...")

            # MySQL连接信息
            config = {
                'host': '127.0.0.1',
                'port': 3306,
                'user': 'root',
                'password': '2015Xz0202',
                'database': 'hotel_management'
            }

            # 关闭当前数据库连接
            if self.connection and self.connection.is_connected():
                self.connection.close()
                print("已关闭当前数据库连接")

            # 构建mysql命令
            cmd = [
                'mysql',
                f'--host={config["host"]}',
                f'--port={config["port"]}',
                f'--user={config["user"]}',
                f'--password={config["password"]}',
                config['database'],
                '<', str(backup_file)
            ]

            # 在Windows上使用不同的方式执行命令
            import sys
            if sys.platform == 'win32':
                # Windows上使用subprocess.run重定向输入
                with open(backup_file, 'r', encoding='utf-8') as f:
                    mysql_cmd = [
                        'mysql',
                        f'--host={config["host"]}',
                        f'--port={config["port"]}',
                        f'--user={config["user"]}',
                        f'--password={config["password"]}',
                        config['database']
                    ]
                    process = subprocess.run(
                        mysql_cmd,
                        stdin=f,
                        capture_output=True,
                        text=True,
                        check=True
                    )
            else:
                # Linux/Mac上使用shell重定向
                cmd_str = f"mysql -h{config['host']} -P{config['port']} -u{config['user']} -p{config['password']} {config['database']} < {backup_file}"
                process = subprocess.run(
                    cmd_str,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )

            print("✓ 数据库恢复成功！")

            # 重新连接数据库
            self.connect_to_database()

            # 记录恢复日志
            self.log_backup_operation('RESTORE', str(backup_file), True, f"恢复成功，操作详情: {operation_details}")

            print("\n⚠️ 提示：恢复完成，建议重新登录系统")
            logout = input("是否立即退出系统？(y/n): ").strip().lower()
            if logout == 'y':
                print("系统即将退出...")
                sys.exit(0)

        except ValueError:
            print("请输入有效的数字")
        except subprocess.CalledProcessError as e:
            print(f"✗ 恢复失败: {e}")
            if e.stderr:
                print(f"错误信息: {e.stderr}")

            # 尝试重新连接数据库
            try:
                self.connect_to_database()
                if self.connection and self.connection.is_connected():
                    print("已重新连接到数据库")
            except:
                print("无法重新连接数据库，请检查数据库状态")

            self.log_backup_operation('RESTORE', str(backup_file), False, str(e))
        except Exception as e:
            print(f"✗ 恢复过程中发生错误: {e}")
            # 尝试重新连接数据库
            try:
                self.connect_to_database()
            except:
                pass
            self.log_backup_operation('RESTORE', str(backup_file), False, str(e))

    def list_backups(self):
        """查看备份文件列表（包含操作详情）"""
        print("\n" + "=" * 60)
        print("备份文件列表")
        print("=" * 60)

        backup_dir = Path("database_backups")
        if not backup_dir.exists():
            print("备份目录不存在")
            return

        backup_files = list(backup_dir.glob("*.sql"))
        if not backup_files:
            print("没有找到备份文件")
            return

        # 按修改时间排序，最新的在前
        backup_files.sort(key=os.path.getmtime, reverse=True)

        # 使用PrettyTable显示
        table = PrettyTable()
        table.field_names = ["编号", "文件名", "备份时间", "文件大小", "操作类型", "操作详情", "状态"]

        total_size = 0
        for i, file in enumerate(backup_files, 1):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
            file_size_kb = os.path.getsize(file) / 1024
            total_size += file_size_kb

            # 获取备份日志中的操作详情
            operation_type, operation_details = self.get_backup_operation_details_with_type(str(file))

            # 检查文件是否完整（简单的检查：文件大小大于1KB）
            status = "✅ 完整" if os.path.getsize(file) > 1024 else "⚠️ 可能损坏"

            # 截断操作详情以避免表格过宽
            if len(operation_details) > 30:
                operation_display = operation_details[:27] + "..."
            else:
                operation_display = operation_details

            table.add_row([
                i,
                file.name,
                file_time.strftime('%Y-%m-%d %H:%M:%S'),
                f"{file_size_kb:.2f} KB",
                operation_type,
                operation_display,
                status
            ])

        print(table)
        print(f"\n总计: {len(backup_files)} 个备份文件")
        print(f"总大小: {total_size:.2f} KB ({total_size / 1024:.2f} MB)")

        # 显示磁盘空间信息
        try:
            disk_usage = shutil.disk_usage(backup_dir)
            free_space_gb = disk_usage.free / (1024 ** 3)
            print(f"剩余磁盘空间: {free_space_gb:.2f} GB")
        except:
            pass

    def delete_backup(self):
        """删除备份文件"""
        print("\n" + "=" * 60)
        print("删除备份文件")
        print("=" * 60)

        backup_dir = Path("database_backups")
        if not backup_dir.exists():
            print("备份目录不存在")
            return

        backup_files = list(backup_dir.glob("*.sql"))
        if not backup_files:
            print("没有找到备份文件")
            return

        backup_files.sort(key=os.path.getmtime, reverse=True)

        print("\n备份文件:")
        for i, file in enumerate(backup_files, 1):
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
            operation_details = self.get_backup_operation_details(str(file))
            print(f"{i}. {file.name} ({file_time.strftime('%Y-%m-%d %H:%M')})")
            print(f"   操作: {operation_details}")
            print()

        try:
            choice = int(input("\n选择要删除的备份文件编号 (0取消): ").strip())
            if choice == 0:
                return
            if choice < 1 or choice > len(backup_files):
                print("无效的选择")
                return

            backup_file = backup_files[choice - 1]

            # 获取操作详情
            operation_details = self.get_backup_operation_details(str(backup_file))

            # 确认删除
            confirm = input(
                f"确认删除备份文件 '{backup_file.name}'？\n操作详情: {operation_details}\n(y/n): ").strip().lower()
            if confirm != 'y':
                print("删除操作已取消")
                return

            # 删除文件
            backup_file.unlink()
            print(f"✓ 备份文件 '{backup_file.name}' 已删除")

            # 记录删除日志
            self.log_backup_operation('DELETE', str(backup_file), True, f"删除成功，原操作: {operation_details}")

        except ValueError:
            print("请输入有效的数字")
        except Exception as e:
            print(f"删除失败: {e}")
            self.log_backup_operation('DELETE', str(backup_file), False, str(e))

    def get_backup_operation_details(self, backup_file_path):
        """获取备份文件的操作详情"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'backup_logs'")
            if not cursor.fetchone():
                return "无操作详情记录"

            # 查询备份日志
            query = """
            SELECT operation_type, message 
            FROM backup_logs 
            WHERE backup_file = %s 
            ORDER BY operation_time DESC 
            LIMIT 1
            """

            cursor.execute(query, (backup_file_path,))
            log = cursor.fetchone()

            if log:
                # 格式化操作类型
                operation_type_map = {
                    'BACKUP': '手动备份',
                    'ADD_ROOM': '添加客房',
                    'DELETE_ROOM': '删除客房',
                    'MODIFY_PRICE': '修改房价',
                    'MODIFY_TYPE': '修改房型',
                    'RESTORE': '恢复操作',
                    'DELETE': '删除备份'
                }

                operation_type_display = operation_type_map.get(log['operation_type'], log['operation_type'])
                return f"{operation_type_display}: {log['message']}"
            else:
                return "无操作详情记录"

        except Exception as e:
            return f"获取操作详情失败: {str(e)}"

    def get_backup_operation_details_with_type(self, backup_file_path):
        """获取备份文件的操作类型和详情"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'backup_logs'")
            if not cursor.fetchone():
                return "未知", "无操作详情记录"

            # 查询备份日志
            query = """
            SELECT operation_type, message 
            FROM backup_logs 
            WHERE backup_file = %s 
            ORDER BY operation_time DESC 
            LIMIT 1
            """

            cursor.execute(query, (backup_file_path,))
            log = cursor.fetchone()

            if log:
                # 格式化操作类型
                operation_type_map = {
                    'BACKUP': '手动备份',
                    'ADD_ROOM': '添加客房',
                    'DELETE_ROOM': '删除客房',
                    'MODIFY_PRICE': '修改房价',
                    'MODIFY_TYPE': '修改房型',
                    'RESTORE': '恢复操作',
                    'DELETE': '删除备份'
                }

                operation_type_display = operation_type_map.get(log['operation_type'], log['operation_type'])
                return operation_type_display, log['message']
            else:
                return "未知", "无操作详情记录"

        except Exception as e:
            return "错误", f"获取失败: {str(e)}"

    def log_backup_operation(self, operation_type, backup_file, success, message):
        """记录备份/恢复操作日志"""
        try:
            cursor = self.connection.cursor()

            # 创建备份日志表（如果不存在）
            create_table = """
            CREATE TABLE IF NOT EXISTS backup_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                operator_id INT,
                operation_type ENUM('BACKUP', 'RESTORE', 'DELETE', 'ADD_ROOM', 'DELETE_ROOM', 'MODIFY_PRICE', 'MODIFY_TYPE'),
                backup_file VARCHAR(500),
                success BOOLEAN,
                message TEXT,
                operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES operator(operator_id) ON DELETE SET NULL
            )
            """
            cursor.execute(create_table)

            # 插入日志记录
            insert_log = """
            INSERT INTO backup_logs (operator_id, operation_type, backup_file, success, message)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_log, (
                self.current_operator_id,
                operation_type,
                backup_file,
                success,
                message
            ))

            self.connection.commit()

        except Exception as e:
            print(f"日志记录失败: {e}")
            # 不抛出异常，避免影响主流程
        finally:
            if 'cursor' in locals():
                cursor.close()

    def view_backup_logs(self):
        """查看备份操作日志"""
        try:
            cursor = self.connection.cursor(dictionary=True)

            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'backup_logs'")
            if not cursor.fetchone():
                print("暂无备份操作日志")
                return

            # 查询日志
            query = """
            SELECT bl.*, o.account_name as operator_name
            FROM backup_logs bl
            LEFT JOIN operator o ON bl.operator_id = o.operator_id
            ORDER BY bl.operation_time DESC
            LIMIT 50
            """

            cursor.execute(query)
            logs = cursor.fetchall()

            if not logs:
                print("暂无备份操作日志")
                return

            table = PrettyTable()
            table.field_names = ["时间", "操作员", "操作类型", "文件", "状态", "信息"]

            for log in logs:
                operation_type_map = {
                    'BACKUP': '手动备份',
                    'RESTORE': '恢复',
                    'DELETE': '删除备份',
                    'ADD_ROOM': '添加客房',
                    'DELETE_ROOM': '删除客房',
                    'MODIFY_PRICE': '修改房价',
                    'MODIFY_TYPE': '修改房型'
                }

                status = "✅ 成功" if log['success'] else "❌ 失败"
                filename = os.path.basename(log['backup_file']) if log['backup_file'] else "N/A"

                table.add_row([
                    log['operation_time'].strftime('%Y-%m-%d %H:%M'),
                    log['operator_name'] or "系统",
                    operation_type_map.get(log['operation_type'], log['operation_type']),
                    filename,
                    status,
                    log['message'][:30] + "..." if len(log['message']) > 30 else log['message']
                ])

            print("\n备份操作日志:")
            print(table)

        except Exception as e:
            print(f"查看日志失败: {e}")


def main():
    """主函数"""
    print("正在启动宾馆客房管理系统...")

    # 创建系统实例
    system = HotelManagementSystem()

    if system.connection and system.connection.is_connected():
        system.main_menu()
    else:
        print("无法连接到数据库，请检查数据库配置")


if __name__ == "__main__":
    main()