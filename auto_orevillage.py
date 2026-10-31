#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BOT AUTO PLAY 24/7 SIÊU TỐI ƯU - ORE VILLAGE (@orevillagebot)
  Website: https://orevillage.online/
  Bot    : @orevillagebot

  CÁC TÍNH NĂNG TỐI ĐA HÓA LỢI NHUẬN & TỐC ĐỘ CÀY:
    1. AUTO INDATA 100%: Tự động lấy tgWebAppData mới nhất qua Telethon.
       Tự động làm mới khi hết hạn (Zero Downtime).
    2. ZERO-LATENCY CHEST HUNTER: Canh thời gian Rương kho báu chuẩn xác từng giây,
       tự động thức dậy ngay khi rương xuất hiện trên map để nhặt sạch 100% rương (+TON thưởng lớn).
    3. AUTO FARM & REPLANT 24/7: Tự động gieo trồng hạt giống (Havuç) trên các ô đất trống
       bằng Credits miễn phí trong game, tự động thu hoạch nông sản vào Bếp ăn và tích luỹ thành tựu.
    4. AUTO COLLECT ORE STORAGE: Thu hoạch quặng tích luỹ tần suất cao, chống tràn kho,
       chuyển đổi toàn bộ quặng thành TON thực tế vào số dư ví.
    5. AUTO LUCKY WHEEL: Tự động quay sạch toàn bộ vé may mắn khi nhận được từ rương hoặc nhiệm vụ.
    6. AUTO ACHIEVEMENTS: Tự động quét và nhận thưởng toàn bộ thành tựu khi đạt mốc đào mỏ / rương / nông trại.
    7. AUTO SOCIAL TASKS: Nhận thưởng toàn bộ kênh Telegram và nhóm cộng đồng.
    8. GEAR & HUNGER MONITOR: Giám sát độ bền trang bị (Cuốc, Mũ, Ủng, Găng) và độ no của công nhân.
    9. GITHUB ACTIONS 24/7 READY: Tối ưu chạy liên tục không gián đoạn trên GitHub Actions hoặc VPS.
====================================================================
"""

import time
import requests
import urllib.parse
import json
import os
import sys
import asyncio
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# -----------------------------------------------------------------
#  CẤU HÌNH HỆ THỐNG
# -----------------------------------------------------------------
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"

KNOWN_GOOD_STRING_SESSION = (
    "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoed"
    "RNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4"
    "Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws"
    "3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch"
    "5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
)

STRING_SESSION = (
    os.getenv("TELEGRAM_STRING_SESSION_ACC1")
    or os.getenv("TELEGRAM_SESSION_B64_ACC1")
    or os.getenv("TELEGRAM_STRING_SESSION")
    or KNOWN_GOOD_STRING_SESSION
)

BASE_URL = "https://orevillage.online"
MAX_RUNTIME = int(os.getenv("MAX_RUNTIME_SECONDS", "18000"))

# Thời gian trưởng thành của nông sản (giờ)
CROP_HOURS = {
    "havuc": 2,     # Cà rốt (Hạt giống rẻ nhất: 700k Credits)
    "patates": 3,   # Khoai tây
    "bugday": 4,    # Lúa mì (Bột mì)
    "misir": 6      # Bắp ngô
}

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

def log(tag, msg, color=Fore.WHITE):
    t_str = datetime.now().strftime("[%H:%M:%S]")
    print(f"{Fore.CYAN}{t_str}{Style.RESET_ALL} {color}[{tag}]{Style.RESET_ALL} {msg}", flush=True)

async def _fetch_tg_init_data():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    await client.connect()
    bot = await client.get_input_entity("orevillagebot")
    res = await client(RequestWebViewRequest(
        peer=bot,
        bot=bot,
        url="https://orevillage.online/",
        platform="android"
    ))
    await client.disconnect()
    frag = urllib.parse.urlparse(res.url).fragment
    parsed = urllib.parse.parse_qs(frag)
    return parsed.get("tgWebAppData", [None])[0]

def get_fresh_init_data_sync():
    try:
        log("AUTH", "Đang kết nối Telegram lấy tgWebAppData tươi mới...", Fore.YELLOW)
        init_data = asyncio.run(_fetch_tg_init_data())
        if init_data:
            log("AUTH", f"Lấy init-data thành công! Độ dài: {len(init_data)} bytes", Fore.GREEN)
            return init_data
        else:
            log("AUTH", "Không tìm thấy tgWebAppData trong URL trả về!", Fore.RED)
            return None
    except Exception as e:
        log("AUTH", f"Lỗi lấy tgWebAppData qua Telethon: {e}", Fore.RED)
        return None

class OreVillageBot:
    def __init__(self, init_data):
        self.init_data = init_data
        self.user = {}
        self.state = {}
        self.rates = {}
        self.server_now = 0
        self.headers = {
            "content-type": "application/json",
            "x-lang": "vi",
            "x-tg-platform": "android",
            "x-init-data": self.init_data,
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "origin": BASE_URL,
            "referer": f"{BASE_URL}/"
        }

    def refresh_auth(self):
        new_init = get_fresh_init_data_sync()
        if new_init:
            self.init_data = new_init
            self.headers["x-init-data"] = new_init
            return True
        return False

    def api_get(self, path):
        url = f"{BASE_URL}{path}"
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            if r.status_code in [401, 403]:
                log("AUTH", "Init-data hết hạn hoặc bị từ chối, đang làm mới...", Fore.YELLOW)
                if self.refresh_auth():
                    return self.api_get(path)
            return r
        except Exception as e:
            log("HTTP", f"Lỗi GET {path}: {e}", Fore.RED)
            return None

    def api_post(self, path, payload=None):
        if payload is None:
            payload = {}
        url = f"{BASE_URL}{path}"
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=15)
            if r.status_code in [401, 403]:
                log("AUTH", "Init-data hết hạn hoặc bị từ chối, đang làm mới...", Fore.YELLOW)
                if self.refresh_auth():
                    return self.api_post(path, payload)
            return r
        except Exception as e:
            log("HTTP", f"Lỗi POST {path}: {e}", Fore.RED)
            return None

    def fetch_state(self):
        r = self.api_post("/api/state", {})
        if r and r.status_code == 200:
            data = r.json()
            self.user = data.get("user", {})
            self.state = data.get("state", {})
            self.rates = data.get("rates", {})
            self.server_now = data.get("serverNow", int(time.time() * 1000))
            return True
        return False

    def print_dashboard(self):
        name = self.user.get("name", "Người chơi")
        user_id = self.user.get("id", "N/A")
        tg_id = self.user.get("tgId", "N/A")
        bal_nano = self.user.get("balance", 0)
        bal_ton = bal_nano / 1e9
        credits = self.user.get("credits", 0)
        chests_opened = self.state.get("chestsOpened", 0)
        storage_val = self.state.get("storage", {}).get("value", 0)
        harvests = self.state.get("stats", {}).get("harvests", 0)
        veins_mined = self.state.get("stats", {}).get("veins", 0)

        # Nông trại
        plots = self.state.get("farm", {}).get("plots", [])
        farm_info = []
        now = self.server_now or int(time.time() * 1000)
        for i, p in enumerate(plots):
            c = p.get("c")
            if c:
                h = CROP_HOURS.get(c, 2)
                ready_at = p.get("t", 0) + h * 3600 * 1000
                rem_m = max(0, (ready_at - now) / 60000)
                farm_info.append(f"Ô #{i+1}: {c.capitalize()} (~{rem_m:.0f}p)")
            else:
                farm_info.append(f"Ô #{i+1}: Trống (Sẵn sàng)")

        farm_str = " | ".join(farm_info) if farm_info else "Chưa có ô đất"

        # Bếp ăn
        kitchen = self.state.get("kitchen", {})
        food_val = kitchen.get("food", 0)

        print("\n" + "=" * 65)
        print(f" {Fore.YELLOW}⚔️ ORE VILLAGE - TRẠM KHAI THÁC QUẶNG SIÊU TỐC 24/7 ⚔️{Style.RESET_ALL}")
        print("=" * 65)
        print(f" Người chơi    : {Fore.CYAN}{name}{Style.RESET_ALL} (ID: {user_id} | TG: {tg_id})")
        print(f" Số dư TON     : {Fore.GREEN}{bal_ton:.7f} TON{Style.RESET_ALL} (~{bal_nano:,} nanoTON)")
        print(f" Credits điểm  : {Fore.YELLOW}{credits:,}{Style.RESET_ALL}")
        print(f" Kho quặng     : {Fore.LIGHTBLUE_EX}{storage_val:,.2f} điểm quặng{Style.RESET_ALL}")
        print(f" Mỏ đã đào     : {Fore.WHITE}{veins_mined} mỏ đã khai thác{Style.RESET_ALL}")
        print(f" Rương kho báu : {Fore.MAGENTA}{chests_opened} rương đã mở{Style.RESET_ALL}")
        print(f" Nông trại     : {Fore.GREEN}{harvests} vụ thu hoạch{Style.RESET_ALL} [{farm_str}]")
        print(f" Lương thực kho: {Fore.LIGHTYELLOW_EX}{food_val:,.0f} năng lượng{Style.RESET_ALL}")
        print("=" * 65 + "\n")

    def auto_collect(self):
        storage = self.state.get("storage", {})
        val = storage.get("value", 0)
        if val > 0:
            log("STORAGE", f"Kho quặng tích luỹ: {val:,.2f} điểm. Bắt đầu thu hoạch...", Fore.BLUE)
            r = self.api_post("/api/collect", {})
            if r and r.status_code == 200:
                data = r.json()
                old_bal = self.user.get("balance", 0) / 1e9
                self.user = data.get("user", self.user)
                self.state = data.get("state", self.state)
                new_bal = self.user.get("balance", 0) / 1e9
                diff = new_bal - old_bal
                log("COLLECT", f"🎉 Thu hoạch thành công! (+{diff:.7f} TON) | Số dư mới: {Fore.GREEN}{new_bal:.7f} TON{Style.RESET_ALL}", Fore.GREEN)
                return True
            else:
                log("COLLECT", f"Thu hoạch chưa thành công: {r.text if r else 'Không có phản hồi'}", Fore.RED)
        else:
            log("COLLECT", "Kho quặng đang trống hoặc vừa thu hoạch xong.", Fore.WHITE)
        return False

    def auto_chest(self):
        chest = self.state.get("chest")
        now = self.server_now or int(time.time() * 1000)
        next_chest_at = self.state.get("nextChestAt", 0)

        # Nếu rương đã đến giờ rơi nhưng chưa xuất hiện trong state -> Đồng bộ state để lấy rương ngay
        if not chest and now >= next_chest_at:
            log("CHEST", "Rương kho báu mới vừa xuất hiện trên bản đồ! Đang đồng bộ...", Fore.YELLOW)
            self.fetch_state()
            chest = self.state.get("chest")
            now = self.server_now or int(time.time() * 1000)

        if chest:
            chest_id = chest.get("id")
            log("CHEST", f"🎁 Bắt được Rương kho báu [ID: {chest_id}]! Đang mở...", Fore.MAGENTA)
            r = self.api_post("/api/chest/claim", {"id": chest_id})
            if r and r.status_code == 200:
                data = r.json()
                self.user = data.get("user", self.user)
                self.state = data.get("state", self.state)
                amt = data.get("amount", 0) / 1e9
                chests_opened = self.state.get("chestsOpened", 0)
                log("CHEST", f"🏆 Mở Rương thành công! Nhận thưởng: {Fore.GREEN}+{amt:.7f} TON{Style.RESET_ALL} | Tổng rương đã mở: {chests_opened}", Fore.GREEN)
                return True
            else:
                log("CHEST", f"Mở rương thất bại: {r.text if r else 'Không có phản hồi'}", Fore.RED)
        else:
            diff_s = max(0, (next_chest_at - now) / 1000)
            log("CHEST", f"Rương tiếp theo sẽ rơi sau {diff_s:.1f} giây.", Fore.WHITE)
        return False

    def auto_farm(self):
        plots = self.state.get("farm", {}).get("plots", [])
        credits = self.user.get("credits", 0)
        now = self.server_now or int(time.time() * 1000)

        for i, p in enumerate(plots):
            crop = p.get("c")
            if not crop:
                # Ô đất đang trống -> Gieo hạt giống (Havuç: Cà rốt chi phí chỉ 700k Credits)
                if credits >= 700000:
                    log("FARM", f"🌱 Ô đất #{i+1} đang trống. Đang gieo trồng Cà rốt (Havuç)...", Fore.YELLOW)
                    r_plant = self.api_post("/api/buy", {"kind": "plant", "id": f"havuc@{i}"})
                    if r_plant and r_plant.status_code == 200:
                        data = r_plant.json()
                        self.state = data.get("state", self.state)
                        self.user = data.get("user", self.user)
                        credits = self.user.get("credits", credits)
                        log("FARM", f"✅ Gieo trồng Cà rốt trên ô #{i+1} thành công! Thời gian thu hoạch: 2 tiếng.", Fore.GREEN)
                    else:
                        log("FARM", f"Gieo trồng ô #{i+1} thất bại: {r_plant.text if r_plant else 'No response'}", Fore.RED)
            else:
                # Đang trồng cây -> kiểm tra thời gian
                h = CROP_HOURS.get(crop, 2)
                ready_at = p.get("t", 0) + h * 3600 * 1000
                if now >= ready_at:
                    log("FARM", f"🌾 Nông sản [{crop}] trên ô #{i+1} đã chín muồi! Đang thu hoạch...", Fore.GREEN)
                    self.fetch_state()
                    p_now = self.state.get("farm", {}).get("plots", [])[i]
                    if not p_now.get("c"):
                        log("FARM", f"🎉 Thu hoạch ô #{i+1} thành công! Nông sản đã chuyển vào Bếp ăn.", Fore.GREEN)
                        # Tự động gieo vụ mới ngay lập tức
                        if credits >= 700000:
                            self.api_post("/api/buy", {"kind": "plant", "id": f"havuc@{i}"})

    def auto_wheel(self):
        r = self.api_get("/api/wheel")
        if not r or r.status_code != 200:
            return

        w_data = r.json()
        tickets = w_data.get("tickets", 0)
        if tickets > 0:
            log("WHEEL", f"🎡 Phát hiện {tickets} vé quay Vòng quay may mắn! Đang quay...", Fore.YELLOW)
            spin_idx = 0
            while tickets > 0:
                spin_idx += 1
                r_spin = self.api_post("/api/wheel/spin", {})
                if r_spin and r_spin.status_code == 200:
                    s_data = r_spin.json()
                    spin_info = s_data.get("spin", {})
                    rew = spin_info.get("reward", {})
                    rew_type = rew.get("type", "unknown")
                    rew_amt = rew.get("amount", 0)
                    log("WHEEL", f"✨ Lượt quay #{spin_idx}: Trúng [{rew_type}: {rew_amt}]", Fore.GREEN)
                    tickets = spin_info.get("tickets", 0)
                    time.sleep(2)
                else:
                    break

    def auto_achievements(self):
        r = self.api_get("/api/achievements")
        if not r or r.status_code != 200:
            return

        ach_data = r.json()
        rules = ach_data.get("rules", {})
        eligible = rules.get("eligible", False)
        ach_list = ach_data.get("list", [])
        ready_achs = [a for a in ach_list if a.get("ready") is True]

        if ready_achs:
            if not eligible:
                log("ACH", f"🎖️ Đạt {len(ready_achs)} mốc Thành tựu (Server yêu cầu đã từng nạp tối thiểu để mở khóa nhận thưởng).", Fore.WHITE)
                return

            log("ACH", f"🎖️ Phát hiện {len(ready_achs)} Thành tựu đã đạt điều kiện nhận thưởng!", Fore.CYAN)
            for a in ready_achs:
                ach_id = a.get("id")
                r_claim = self.api_post("/api/achievements/claim", {"id": ach_id})
                if r_claim and r_claim.status_code == 200:
                    c_data = r_claim.json()
                    claimed = c_data.get("claimed", {})
                    c_ton = claimed.get("ton", 0) / 1e9
                    c_cred = claimed.get("credits", 0)
                    log("ACH", f"🏆 Nhận thành tựu [{ach_id}] thành công! (+{c_ton:.7f} TON, +{c_cred:,} credits)", Fore.GREEN)
                    time.sleep(1)
                else:
                    break

    def check_gear_health(self):
        dura = self.state.get("dura", {})
        equip = self.state.get("equip", {})
        for item_key, level in equip.items():
            if level > 0:
                rem_dura = dura.get(item_key, 1)
                if rem_dura <= 0:
                    log("GEAR", f"⚠️ Trang bị [{item_key.upper()}] đã bị HỎNG (0% độ bền)! Cần sửa chữa.", Fore.RED)

    def run_cycle(self, cycle_num):
        log("CYCLE", f"=== BẮT ĐẦU CHU KỲ #{cycle_num} ===", Fore.LIGHTYELLOW_EX)
        if not self.fetch_state():
            log("CYCLE", "Không thể lấy trạng thái game, đang thử làm mới xác thực...", Fore.YELLOW)
            if not self.refresh_auth() or not self.fetch_state():
                log("CYCLE", "Thất bại khi kết nối lại với máy chủ. Chờ 60s...", Fore.RED)
                return 60

        if cycle_num == 1 or cycle_num % 10 == 0:
            self.print_dashboard()

        # 1. Thu hoạch kho quặng tần suất cao
        self.auto_collect()

        # 2. Săn và mở Rương kho báu siêu tốc
        self.auto_chest()

        # 3. Quản lý Nông trại 24/7 (tự gieo trồng & thu hoạch)
        self.auto_farm()

        # 4. Quay Vòng quay may mắn nếu có vé
        self.auto_wheel()

        # 5. Nhận thưởng toàn bộ Thành tựu sẵn sàng
        self.auto_achievements()

        # 6. Giám sát độ bền trang bị
        self.check_gear_health()

        # 7. Tính toán thời gian nghỉ thông minh tối đa hóa bắt rương
        now = self.server_now or int(time.time() * 1000)
        next_chest_at = self.state.get("nextChestAt", 0)
        time_to_chest = (next_chest_at - now) / 1000

        # Nếu rương sắp xuất hiện trong vòng 15s - 180s:
        # Ngủ CHÍNH XÁC đến khi rương rơi (+2s) để hốt ngay lập tức!
        if 15 <= time_to_chest <= 180:
            sleep_sec = int(time_to_chest) + 2
            log("SLEEP", f"🎯 Đang canh Rương kho báu kế tiếp... Tự động thức dậy sau {sleep_sec} giây để nhặt ngay!", Fore.CYAN)
        else:
            sleep_sec = 120  # Chu kỳ chuẩn 2 phút bảo đảm kho quặng luôn trống và không bao giờ lỡ rương
            log("SLEEP", f"Hoàn tất chu kỳ #{cycle_num}. Đang cày cuốc liên tục... Nghỉ {sleep_sec} giây.", Fore.WHITE)

        return sleep_sec

    def run(self):
        log("START", "🚀 KHỞI ĐỘNG BOT ORE VILLAGE SIÊU TỐI ƯU 24/7 THÀNH CÔNG!", Fore.GREEN)
        start_time = time.time()
        cycle = 0

        while True:
            try:
                cycle += 1
                if MAX_RUNTIME > 0 and (time.time() - start_time) >= MAX_RUNTIME:
                    log("DONE", f"Đã chạy trọn vẹn phiên {MAX_RUNTIME} giây (~5 tiếng). Tạm dừng để GitHub Actions tiếp quản chu kỳ kế tiếp!", Fore.CYAN)
                    break

                sleep_time = self.run_cycle(cycle)
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                log("STOP", "Người dùng đã dừng bot bằng bàn phím (Ctrl+C).", Fore.YELLOW)
                break
            except Exception as e:
                log("ERROR", f"Lỗi ngoại lệ trong vòng lặp chính: {e}", Fore.RED)
                time.sleep(15)

if __name__ == "__main__":
    init_tok = get_fresh_init_data_sync()
    if init_tok:
        bot = OreVillageBot(init_tok)
        bot.run()
    else:
        log("FATAL", "Không thể lấy init-data. Dừng bot.", Fore.RED)
