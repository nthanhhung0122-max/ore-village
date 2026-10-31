#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BOT AUTO PLAY 24/7 TOÀN DIỆN - ORE VILLAGE (@orevillagebot)
  Website: https://orevillage.online/
  Bot    : @orevillagebot

  TÍNH NĂNG TỰ ĐỘNG 100%:
    1. AUTO INDATA 100%: Tự động kết nối Telethon lấy init-data mới nhất.
    2. AUTO HARVEST / COLLECT: Tự động thu hoạch toàn bộ quặng từ Kho tích luỹ
       chuyển đổi thành TON thực tế vào số dư người chơi.
    3. AUTO CHEST HUNTER: Tự động canh giờ chính xác từng giây để bắt và mở
       toàn bộ Rương kho báu xuất hiện trên bản đồ (+TON thưởng lớn).
    4. AUTO LUCKY WHEEL: Tự động quay Vòng quay may mắn khi có vé hoặc lượt quay miễn phí.
    5. AUTO ACHIEVEMENTS: Tự động kiểm tra và nhận thưởng toàn bộ Thành tựu khi đạt mốc.
    6. AUTO SOCIAL TASKS: Tự động kiểm tra và nhận thưởng các nhiệm vụ cộng đồng / kênh Telegram.
    7. 24/7 NON-STOP & GITHUB ACTIONS: Hỗ trợ chạy liên tục trên GitHub Actions hoặc VPS/Máy tính cá nhân.
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
MAX_RUNTIME = int(os.getenv("MAX_RUNTIME_SECONDS", "18000"))  # Mặc định ~5 tiếng cho GitHub Actions

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
        earned = self.user.get("earned", 0) / 1e9
        chests_opened = self.state.get("chestsOpened", 0)
        storage_val = self.state.get("storage", {}).get("value", 0)

        print("\n" + "=" * 62)
        print(f" {Fore.YELLOW}⚔️ ORE VILLAGE - TRẠM KHAI THÁC QUẶNG TỰ ĐỘNG 24/7 ⚔️{Style.RESET_ALL}")
        print("=" * 62)
        print(f" Người chơi   : {Fore.CYAN}{name}{Style.RESET_ALL} (ID: {user_id} | TG: {tg_id})")
        print(f" Số dư TON    : {Fore.GREEN}{bal_ton:.7f} TON{Style.RESET_ALL} (~{bal_nano:,} nanoTON)")
        print(f" Credits điểm : {Fore.YELLOW}{credits:,}{Style.RESET_ALL}")
        print(f" Đã kiếm được : {Fore.GREEN}{earned:.7f} TON{Style.RESET_ALL}")
        print(f" Quặng tích luỹ: {Fore.LIGHTBLUE_EX}{storage_val:,.2f} điểm quặng{Style.RESET_ALL}")
        print(f" Rương đã mở  : {Fore.MAGENTA}{chests_opened} rương kho báu{Style.RESET_ALL}")
        print("=" * 62 + "\n")

    def auto_collect(self):
        storage = self.state.get("storage", {})
        val = storage.get("value", 0)
        if val > 0:
            log("STORAGE", f"Kho đang chứa {val:,.2f} điểm quặng. Bắt đầu thu hoạch...", Fore.BLUE)
            r = self.api_post("/api/collect", {})
            if r and r.status_code == 200:
                data = r.json()
                self.user = data.get("user", self.user)
                self.state = data.get("state", self.state)
                new_bal = self.user.get("balance", 0) / 1e9
                log("COLLECT", f"🎉 Thu hoạch thành công! Số dư mới: {Fore.GREEN}{new_bal:.7f} TON{Style.RESET_ALL}", Fore.GREEN)
                return True
            else:
                log("COLLECT", f"Thu hoạch chưa thành công: {r.text if r else 'Không có phản hồi'}", Fore.RED)
        else:
            log("COLLECT", "Kho quặng đang rỗng hoặc vừa thu hoạch xong.", Fore.WHITE)
        return False

    def auto_chest(self):
        # 1. Kiểm tra rương đang có trên bản đồ
        chest = self.state.get("chest")
        now = self.server_now or int(time.time() * 1000)
        next_chest_at = self.state.get("nextChestAt", 0)

        if not chest and now >= next_chest_at:
            # Canh giờ đúng lúc rương xuất hiện -> sync state để lấy rương
            log("CHEST", "Thời gian rương mới đã đến! Đang đồng bộ bản đồ...", Fore.YELLOW)
            self.fetch_state()
            chest = self.state.get("chest")
            now = self.server_now or int(time.time() * 1000)

        if chest:
            chest_id = chest.get("id")
            log("CHEST", f"🎁 Phát hiện Rương kho báu trên bản đồ [ID: {chest_id}]! Đang mở...", Fore.MAGENTA)
            r = self.api_post("/api/chest/claim", {"id": chest_id})
            if r and r.status_code == 200:
                data = r.json()
                self.user = data.get("user", self.user)
                self.state = data.get("state", self.state)
                amt = data.get("amount", 0) / 1e9
                chests_opened = self.state.get("chestsOpened", 0)
                log("CHEST", f"🏆 Mở Rương thành công! Thưởng: {Fore.GREEN}+{amt:.7f} TON{Style.RESET_ALL} | Tổng rương đã mở: {chests_opened}", Fore.GREEN)
                return True
            else:
                log("CHEST", f"Mở rương thất bại: {r.text if r else 'Không có phản hồi'}", Fore.RED)
        else:
            diff_s = max(0, (next_chest_at - now) / 1000)
            log("CHEST", f"Chưa có rương mới. Rương tiếp theo sẽ xuất hiện sau {diff_s:.1f} giây.", Fore.WHITE)
        return False

    def auto_wheel(self):
        r = self.api_get("/api/wheel")
        if not r or r.status_code != 200:
            return

        w_data = r.json()
        tickets = w_data.get("tickets", 0)
        if tickets > 0:
            log("WHEEL", f"🎡 Phát hiện {tickets} vé quay Vòng quay may mắn! Bắt đầu quay...", Fore.YELLOW)
            spin_count = 0
            while tickets > 0:
                spin_count += 1
                r_spin = self.api_post("/api/wheel/spin", {})
                if r_spin and r_spin.status_code == 200:
                    s_data = r_spin.json()
                    spin_info = s_data.get("spin", {})
                    rew = spin_info.get("reward", {})
                    rew_type = rew.get("type", "unknown")
                    rew_amt = rew.get("amount", 0)
                    log("WHEEL", f"✨ Lượt quay #{spin_count}: Trúng thưởng [{rew_type}: {rew_amt}]", Fore.GREEN)
                    tickets = spin_info.get("tickets", 0)
                    time.sleep(2)
                else:
                    log("WHEEL", f"Lỗi quay: {r_spin.text if r_spin else 'No response'}", Fore.RED)
                    break
        else:
            log("WHEEL", "Không có vé quay may mắn khả dụng.", Fore.WHITE)

    def auto_achievements(self):
        r = self.api_get("/api/achievements")
        if not r or r.status_code != 200:
            return

        ach_data = r.json()
        ach_list = ach_data.get("list", [])
        ready_achs = [a for a in ach_list if a.get("ready") is True]

        if ready_achs:
            log("ACH", f"🎖️ Phát hiện {len(ready_achs)} Thành tựu đã đạt điều kiện nhận thưởng!", Fore.CYAN)
            for a in ready_achs:
                ach_id = a.get("id")
                r_claim = self.api_post("/api/achievements/claim", {"id": ach_id})
                if r_claim and r_claim.status_code == 200:
                    c_data = r_claim.json()
                    claimed = c_data.get("claimed", {})
                    c_ton = claimed.get("ton", 0) / 1e9
                    c_cred = claimed.get("credits", 0)
                    log("ACH", f"🏆 Nhận thưởng thành tựu [{ach_id}] thành công! (+{c_ton:.7f} TON, +{c_cred:,} credits)", Fore.GREEN)
                    time.sleep(1)
                else:
                    log("ACH", f"Lỗi nhận thành tựu {ach_id}: {r_claim.text if r_claim else 'No response'}", Fore.RED)
        else:
            log("ACH", "Tất cả Thành tựu đang trong tiến độ hoàn thành.", Fore.WHITE)

    def auto_social(self):
        r = self.api_get("/api/social")
        if not r or r.status_code != 200:
            return

        soc_data = r.json()
        chats = soc_data.get("chats", [])
        unrewarded = [c for c in chats if not c.get("rewarded")]

        if unrewarded:
            log("SOCIAL", f"📢 Phát hiện {len(unrewarded)} nhiệm vụ mạng xã hội chưa nhận. Đang xác minh...", Fore.YELLOW)
            r_check = self.api_post("/api/social/check", {})
            if r_check and r_check.status_code == 200:
                res = r_check.json()
                log("SOCIAL", "Đã xác minh và cập nhật nhiệm vụ mạng xã hội thành công!", Fore.GREEN)
        else:
            log("SOCIAL", "Đã hoàn thành toàn bộ nhiệm vụ mạng xã hội.", Fore.WHITE)

    def run_cycle(self, cycle_num):
        log("CYCLE", f"=== BẮT ĐẦU CHU KỲ #{cycle_num} ===", Fore.LIGHTYELLOW_EX)
        if not self.fetch_state():
            log("CYCLE", "Không thể lấy trạng thái game, đang thử làm mới xác thực...", Fore.YELLOW)
            if not self.refresh_auth() or not self.fetch_state():
                log("CYCLE", "Thất bại khi kết nối lại với máy chủ.", Fore.RED)
                return 60

        if cycle_num == 1 or cycle_num % 10 == 0:
            self.print_dashboard()

        # 1. Thu hoạch kho quặng
        self.auto_collect()

        # 2. Canh và mở Rương kho báu
        self.auto_chest()

        # 3. Vòng quay may mắn
        self.auto_wheel()

        # 4. Nhận thành tựu
        self.auto_achievements()

        # 5. Nhiệm vụ mạng xã hội (chỉ chạy chu kỳ 1 hoặc mỗi 30 chu kỳ)
        if cycle_num == 1 or cycle_num % 30 == 0:
            self.auto_social()

        # Tính toán thời gian nghỉ thông minh
        now = self.server_now or int(time.time() * 1000)
        next_chest_at = self.state.get("nextChestAt", 0)
        time_to_chest = (next_chest_at - now) / 1000

        # Nếu rương sắp xuất hiện trong vòng 30s - 180s, ngủ đúng tới lúc rương ra để nhặt ngay
        if 20 <= time_to_chest <= 180:
            sleep_sec = int(time_to_chest) + 3
            log("SLEEP", f"Canh rương kho báu kế tiếp... Tự động hoạt động lại sau {sleep_sec} giây!", Fore.CYAN)
        else:
            sleep_sec = 120  # Chu kỳ chuẩn 2 phút để kho quặng luôn được thu hoạch và không bao giờ lỡ rương
            log("SLEEP", f"Hoàn tất chu kỳ #{cycle_num}. Đang cày quặng... Nghỉ {sleep_sec} giây trước chu kỳ tiếp theo.", Fore.WHITE)

        return sleep_sec

    def run(self):
        log("START", "Khởi động Bot Auto Ore Village 24/7 thành công!", Fore.GREEN)
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
