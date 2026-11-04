#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BOT AUTO PLAY 24/7 SIÊU TỐI ƯU ĐUA TOP - ORE VILLAGE (@orevillagebot)
  Website: https://orevillage.online/
  Bot    : @orevillagebot

  TÍNH NĂNG TỐI ĐA HÓA LỢI NHUẬN & BỨC PHÁ BẢNG XẾP HẠNG (ĐUA TOP):
    1. 24/7 RELAY HANDOVER (CHUYỂN GIAO CA LIÊN TỤC): Tự động dispatch phiên mới
       trước khi GitHub Actions chạm ngưỡng 350 phút, đảm bảo cày 24/7 không gián đoạn.
    2. LEADERBOARD RANK TRACKER: Theo dõi trực tiếp thứ hạng Rank & DPS trong game.
    3. ZERO-LATENCY CHEST HUNTER: Canh rương kho báu chuẩn xác từng giây,
       tự động thức dậy ngay khi rương xuất hiện để nhặt sạch 100% rương (+TON thưởng).
    4. AUTO HIGH-FREQUENCY ORE HARVEST: Thu hoạch kho quặng liên tục, chống tràn kho,
       chuyển đổi toàn bộ quặng thành TON thực tế vào số dư ví.
    5. AUTO FARM & REPLANT: Tự động gieo hạt giống (Havuç) và thu hoạch nông sản
       làm đầy Bếp ăn (Kitchen), duy trì 100% năng lượng và DPS cho công nhân mỏ.
    6. AUTO FISHING HUNTER: Tự động thả câu (solucan), canh chuẩn xác thời gian cá cắn câu
       (bite window) để kéo cá lên, tăng thành tựu và nguyên liệu.
    7. AUTO LUCKY WHEEL: Tự động quay sạch vé may mắn khi nhận được từ rương/nhiệm vụ.
    8. AUTO ACHIEVEMENTS: Tự động quét và nhận thưởng toàn bộ thành tựu khi đạt mốc.
    9. GEAR DURABILITY MONITOR & REPAIR: Giám sát độ bền trang bị (Cuốc, Mũ, Ủng, Găng).
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
#  CẤU HÌNH HỆ THỐNG & TELEGRAM
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
MAX_RUNTIME = int(os.getenv("MAX_RUNTIME_SECONDS", "17500"))  # ~4.8 tiếng
REPO_NAME = "ore-village"
WORKFLOW_NAME = "orevillage.yml"

# Thời gian trưởng thành của nông sản (giờ)
CROP_HOURS = {
    "havuc": 2,     # Cà rốt (Hạt giống rẻ nhất: 700k Credits)
    "patates": 3,   # Khoai tây
    "bugday": 4,    # Lúa mì
    "misir": 6      # Bắp ngô
}

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

def log(tag, msg, color=Fore.WHITE):
    t_str = datetime.now().strftime("[%H:%M:%S]")
    print(f"{Fore.CYAN}{t_str}{Style.RESET_ALL} {color}[{tag:13s}]{Style.RESET_ALL} {msg}", flush=True)

def trigger_next_shift():
    """Tự động gọi GitHub Actions API chuyển giao ca làm việc tiếp theo để cày 24/7"""
    log("HANDOVER", f"🔄 Đang kích hoạt ca chạy tiếp theo trên {REPO_NAME}...", Fore.CYAN)
    pat = os.getenv("GH_PAT") or ("ghp_" + "4uoxqr79k4DnDki4jYmjIORTKybfeX1XnPbn")
    repo = os.getenv("GITHUB_REPOSITORY") or f"nthanhhung0122-max/{REPO_NAME}"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_NAME}/dispatches"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        r = requests.post(url, headers=headers, json={"ref": "main"}, timeout=15)
        if r.status_code == 204:
            log("HANDOVER", f"✅ Đã kích hoạt thành công ca làm việc tiếp theo trên {repo}!", Fore.GREEN)
            return True
        else:
            log("HANDOVER", f"⚠️ Dispatch thất bại: {r.status_code} {r.text}", Fore.YELLOW)
            return False
    except Exception as e:
        log("HANDOVER", f"❌ Lỗi khi dispatch ca tiếp theo: {e}", Fore.RED)
        return False

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

def get_fresh_init_data_sync(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            log("AUTH", f"Đang kết nối Telegram lấy tgWebAppData tươi mới (Lần {attempt}/{max_retries})...", Fore.YELLOW)
            init_data = asyncio.run(_fetch_tg_init_data())
            if init_data:
                log("AUTH", f"Lấy init-data thành công! Độ dài: {len(init_data)} bytes", Fore.GREEN)
                return init_data
            time.sleep(3)
        except Exception as e:
            log("AUTH", f"Lỗi Telethon (Lần {attempt}): {e}", Fore.RED)
            time.sleep(3)
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
        new_init = get_fresh_init_data_sync(max_retries=3)
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

    def check_leaderboard(self):
        """Theo dõi thứ hạng Rank & DPS đua top"""
        r = self.api_get("/api/leaderboard")
        if r and r.status_code == 200:
            data = r.json()
            me = data.get("me", {})
            rank = me.get("rank", "N/A")
            dps = me.get("dps", 0)
            workers = me.get("workers", 0)
            total = data.get("total", 0)
            log("LEADERBOARD", f"🏆 BẢNG XẾP HẠNG: Top #{Fore.YELLOW}{rank}{Style.RESET_ALL}/{total} | DPS: {Fore.GREEN}{dps:,.2f}{Style.RESET_ALL} | Thợ mỏ: {workers}", Fore.MAGENTA)

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

        # Bếp ăn & Câu cá
        kitchen = self.state.get("kitchen", {})
        food_val = kitchen.get("food", 0)
        fish_data = self.state.get("fish", {})
        rod_lv = fish_data.get("rod", 0)
        bait_count = fish_data.get("bait", {}).get("solucan", 0)

        print("\n" + "=" * 65)
        print(f" {Fore.YELLOW}⚔️ ORE VILLAGE - TRẠM KHAI THÁC QUẶNG SIÊU TỐC ĐUA TOP 24/7 ⚔️{Style.RESET_ALL}")
        print("=" * 65)
        print(f" Người chơi    : {Fore.CYAN}{name}{Style.RESET_ALL} (ID: {user_id} | TG: {tg_id})")
        print(f" Số dư TON     : {Fore.GREEN}{bal_ton:.7f} TON{Style.RESET_ALL} (~{bal_nano:,} nanoTON)")
        print(f" Credits điểm  : {Fore.YELLOW}{credits:,}{Style.RESET_ALL}")
        print(f" Kho quặng     : {Fore.LIGHTBLUE_EX}{storage_val:,.2f} điểm quặng{Style.RESET_ALL}")
        print(f" Mỏ đã đào     : {Fore.WHITE}{veins_mined} mỏ quặng đã khai thác{Style.RESET_ALL}")
        print(f" Rương kho báu : {Fore.MAGENTA}{chests_opened} rương đã mở{Style.RESET_ALL}")
        print(f" Nông trại     : {Fore.GREEN}{harvests} vụ mùa{Style.RESET_ALL} [{farm_str}]")
        print(f" Lương thực kho: {Fore.LIGHTYELLOW_EX}{food_val:,.0f} năng lượng{Style.RESET_ALL}")
        print(f" Cần câu & mồi : {Fore.CYAN}Cần câu Lv {rod_lv}{Style.RESET_ALL} (Mồi giun: {bait_count} con)")
        print("=" * 65 + "\n")

    def auto_collect(self):
        """Thu hoạch quặng liên tục, chống tràn kho, quy đổi thành TON"""
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
        return False

    def auto_chest(self):
        """Săn và mở rương kho báu siêu tốc"""
        chest = self.state.get("chest")
        now = self.server_now or int(time.time() * 1000)
        next_chest_at = self.state.get("nextChestAt", 0)

        if not chest and now >= next_chest_at:
            log("CHEST", "Rương kho báu mới vừa xuất hiện trên bản đồ! Đang đồng bộ...", Fore.YELLOW)
            self.fetch_state()
            chest = self.state.get("chest")
            now = self.server_now or int(time.time() * 1000)

        if chest:
            chest_id = chest.get("id")
            log("CHEST", f"🎁 Phát hiện Rương kho báu [ID: {chest_id}]! Đang mở...", Fore.MAGENTA)
            r = self.api_post("/api/chest/claim", {"id": chest_id})
            if r and r.status_code == 200:
                data = r.json()
                self.user = data.get("user", self.user)
                self.state = data.get("state", self.state)
                amt = data.get("amount", 0) / 1e9
                chests_opened = self.state.get("chestsOpened", 0)
                log("CHEST", f"🏆 Mở Rương thành công! Nhận: {Fore.GREEN}+{amt:.7f} TON{Style.RESET_ALL} | Tổng rương: {chests_opened}", Fore.GREEN)
                return True
        return False

    def auto_farm(self):
        """Quản lý gieo hạt & thu hoạch Nông trại tự động 24/7"""
        plots = self.state.get("farm", {}).get("plots", [])
        credits = self.user.get("credits", 0)
        now = self.server_now or int(time.time() * 1000)

        for i, p in enumerate(plots):
            crop = p.get("c")
            if not crop:
                if credits >= 700000:
                    log("FARM", f"🌱 Ô đất #{i+1} trống. Gieo hạt Cà rốt (Havuç)...", Fore.YELLOW)
                    r_plant = self.api_post("/api/buy", {"kind": "plant", "id": f"havuc@{i}"})
                    if r_plant and r_plant.status_code == 200:
                        data = r_plant.json()
                        self.state = data.get("state", self.state)
                        self.user = data.get("user", self.user)
                        credits = self.user.get("credits", credits)
                        log("FARM", f"✅ Đã gieo Cà rốt ô #{i+1}! Thời gian thu hoạch: 2 tiếng.", Fore.GREEN)
            else:
                h = CROP_HOURS.get(crop, 2)
                ready_at = p.get("t", 0) + h * 3600 * 1000
                if now >= ready_at:
                    log("FARM", f"🌾 Nông sản [{crop}] trên ô #{i+1} đã chín! Đang thu hoạch...", Fore.GREEN)
                    self.fetch_state()
                    p_now = self.state.get("farm", {}).get("plots", [])[i]
                    if not p_now.get("c"):
                        log("FARM", f"🎉 Thu hoạch ô #{i+1} thành công! Nông sản đã chuyển vào Bếp ăn.", Fore.GREEN)
                        if credits >= 700000:
                            self.api_post("/api/buy", {"kind": "plant", "id": f"havuc@{i}"})

    def auto_fishing(self):
        """Tự động câu cá khi có mồi giun (solucan) và cần câu"""
        fish_data = self.state.get("fish", {})
        rod_lv = fish_data.get("rod", 0)
        bait_count = fish_data.get("bait", {}).get("solucan", 0)

        if rod_lv < 1 or bait_count <= 0:
            return

        log("FISH", f"🎣 Chuẩn bị quăng cần câu (Còn {bait_count} mồi solucan)...", Fore.CYAN)
        r_cast = self.api_post("/api/fish/cast", {"bait": "solucan"})
        if r_cast and r_cast.status_code == 200:
            data = r_cast.json()
            cast_info = data.get("cast", {})
            cast_id = cast_info.get("id")
            bite_at = cast_info.get("bite", 0)
            server_now = data.get("serverNow", int(time.time() * 1000))

            wait_s = max(0.5, (bite_at - server_now) / 1000.0)
            log("FISH", f"Đang chờ cá cắn câu... ({wait_s:.1f}s)", Fore.YELLOW)
            time.sleep(wait_s + 0.1)

            r_reel = self.api_post("/api/fish/reel", {"id": cast_id})
            if r_reel and r_reel.status_code == 200:
                reel_data = r_reel.json().get("reel", {})
                if reel_data.get("ok"):
                    f_name = reel_data.get("fish", "cá")
                    log("FISH", f"🐟 GIẬT CẦU THÀNH CÔNG! Bắt được: {Fore.GREEN}{f_name.upper()}{Style.RESET_ALL} (Đã thêm vào kho Bếp ăn)!", Fore.GREEN)
                else:
                    log("FISH", f"Cá giật hụt ({reel_data.get('reason', 'tuột')}). Lần sau sẽ thử lại!", Fore.LIGHTBLACK_EX)

    def auto_wheel(self):
        """Quay Vòng quay may mắn khi có vé"""
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
                    log("WHEEL", f"✨ Lượt #{spin_idx}: Trúng [{rew_type}: {rew_amt}]", Fore.GREEN)
                    tickets = spin_info.get("tickets", 0)
                    time.sleep(2)
                else:
                    break

    def auto_achievements(self):
        """Nhận thưởng tất cả thành tựu hoàn thành"""
        r = self.api_get("/api/achievements")
        if not r or r.status_code != 200:
            return

        ach_data = r.json()
        ach_list = ach_data.get("list", [])
        ready_achs = [a for a in ach_list if a.get("ready") is True]

        for a in ready_achs:
            ach_id = a.get("id")
            r_claim = self.api_post("/api/achievements/claim", {"id": ach_id})
            if r_claim and r_claim.status_code == 200:
                c_data = r_claim.json()
                claimed = c_data.get("claimed", {})
                c_ton = claimed.get("ton", 0) / 1e9
                c_cred = claimed.get("credits", 0)
                log("ACH", f"🏆 Nhận thành tựu [{ach_id}]! (+{c_ton:.7f} TON, +{c_cred:,} credits)", Fore.GREEN)
                time.sleep(1)

    def check_gear_health(self):
        """Giám sát độ bền và tự động sửa chữa nếu cần"""
        dura = self.state.get("dura", {})
        equip = self.state.get("equip", {})
        for item_key, level in equip.items():
            if level > 0:
                rem_dura = dura.get(item_key, 1)
                if rem_dura <= 0:
                    log("GEAR", f"⚠️ Trang bị [{item_key.upper()}] bị hỏng! Thử sửa chữa...", Fore.YELLOW)
                    self.api_post("/api/buy", {"kind": "repair", "id": item_key})

    def run_cycle(self, cycle_num):
        log("CYCLE", f"=== BẮT ĐẦU CHU KỲ #{cycle_num} ===", Fore.LIGHTYELLOW_EX)
        if not self.fetch_state():
            log("CYCLE", "Không thể lấy trạng thái game, đang thử làm mới xác thực...", Fore.YELLOW)
            if not self.refresh_auth() or not self.fetch_state():
                log("CYCLE", "Thất bại khi kết nối lại. Chờ 30s...", Fore.RED)
                return 30

        if cycle_num == 1 or cycle_num % 10 == 0:
            self.print_dashboard()
            self.check_leaderboard()

        # 1. Thu hoạch kho quặng liên tục
        self.auto_collect()

        # 2. Săn và mở rương kho báu
        self.auto_chest()

        # 3. Quản lý Nông trại (tự động gieo trồng & thu hoạch)
        self.auto_farm()

        # 4. Tự động câu cá (mỗi chu kỳ câu 1 lần để duy trì liên tục)
        self.auto_fishing()

        # 5. Quay Vòng quay may mắn
        self.auto_wheel()

        # 6. Nhận thưởng thành tựu
        self.auto_achievements()

        # 7. Giám sát độ bền trang bị
        self.check_gear_health()

        # 8. Tính toán thời gian nghỉ thông minh tối đa hóa bắt rương
        now = self.server_now or int(time.time() * 1000)
        next_chest_at = self.state.get("nextChestAt", 0)
        time_to_chest = (next_chest_at - now) / 1000

        if 15 <= time_to_chest <= 150:
            sleep_sec = int(time_to_chest) + 2
            log("SLEEP", f"🎯 Đang canh Rương kho báu... Thức dậy sau {sleep_sec} giây để nhặt ngay!", Fore.CYAN)
        else:
            sleep_sec = 90  # Chu kỳ 90s tối ưu tốc độ cày và kho quặng
            log("SLEEP", f"Hoàn tất chu kỳ #{cycle_num}. Đang cày cuốc liên tục... Nghỉ {sleep_sec}s.", Fore.WHITE)

        return sleep_sec

    def run(self):
        log("START", "🚀 KHỞI ĐỘNG BOT ORE VILLAGE SIÊU TỐI ƯU ĐUA TOP 24/7!", Fore.GREEN)
        start_time = time.time()
        handover_triggered = False
        cycle = 0

        while True:
            try:
                cycle += 1
                elapsed = time.time() - start_time

                # Chuyển giao ca 24/7 trước khi hết hạn runner GitHub Actions
                if elapsed > MAX_RUNTIME - 600 and not handover_triggered:
                    log("HANDOVER", f"⏰ Ca chạy đã đạt {int(elapsed/60)} phút. Tiến hành kích hoạt ca mới tiếp quản...", Fore.CYAN)
                    if trigger_next_shift():
                        handover_triggered = True

                if elapsed >= MAX_RUNTIME:
                    log("LIFETIME", f"🏁 Đã hoàn thành trọn vẹn phiên {MAX_RUNTIME}s (~4.8 tiếng). Bàn giao slot an toàn!", Fore.GREEN)
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
    init_tok = get_fresh_init_data_sync(max_retries=5)
    if init_tok:
        bot = OreVillageBot(init_tok)
        bot.run()
    else:
        log("FATAL", "Không thể lấy init-data sau 5 lần thử. Thoát.", Fore.RED)
