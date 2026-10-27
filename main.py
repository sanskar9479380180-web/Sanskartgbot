
import asyncio
import os
import sqlite3
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = os.getenv("DB_PATH", "bot_data.sqlite3")

if not TOKEN or TOKEN == "PASTE_YOUR_NEW_BOTFATHER_TOKEN_HERE":
    raise RuntimeError("BOT_TOKEN set nahi hai. Railway Variables mein set karein.")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                added_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_seen TEXT NOT NULL
            )
        """)


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Status", callback_data="status"),
            InlineKeyboardButton(text="🔗 Links", callback_data="links"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ Help", callback_data="help"),
        ],
    ])


def get_link_count():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]


def register_user(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, first_seen) VALUES (?, ?)",
            (user_id, datetime.now(timezone.utc).isoformat()),
        )


def get_user_count():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user:
        register_user(message.from_user.id)

    await message.answer(
        "👋 Welcome to SR7 Bot!\n\n"
        "Neeche menu se option select karein.",
        reply_markup=main_menu(),
    )


@dp.message(Command("menu"))
async def menu(message: Message):
    await message.answer("📌 Main Menu", reply_markup=main_menu())


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "🤖 SR7 Bot Help\n\n"
        "/start - Bot start karein\n"
        "/menu - Main menu kholein\n"
        "/status - Bot status dekhein\n"
        "/links - Saved links dekhein\n"
        "/addlink Title | https://example.com - Link add karein"
    )


@dp.message(Command("status"))
async def status_command(message: Message):
    await message.answer(
        "🟢 Bot Status: Online\n"
        f"👥 Registered users: {get_user_count()}\n"
        f"🔗 Saved links: {get_link_count()}"
    )


@dp.message(Command("links"))
async def links_command(message: Message):
    await send_links(message)


async def send_links(target):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT title, url FROM links ORDER BY id DESC LIMIT 20"
        ).fetchall()

    if not rows:
        text = "🔗 Abhi koi link save nahi hai.\n\n"
    else:
        text = "🔗 Saved Links:\n\n"
        for title, url in rows:
            text += f"• {title}\n{url}\n\n"

    await target.answer(text) if isinstance(target, Message) else await target.message.answer(text)


@dp.message(Command("addlink"))
async def add_link(message: Message):
    parts = (message.text or "").partition(" ")[2].split("|", 1)

    if len(parts) != 2:
        await message.answer(
            "Format:\n/addlink Title | https://example.com"
        )
        return

    title, url = (part.strip() for part in parts)

    if not title or not url.startswith(("https://", "http://")):
        await message.answer("❌ Valid title aur http/https URL dein.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO links (title, url, added_at) VALUES (?, ?, ?)",
            (title[:100], url[:500], datetime.now(timezone.utc).isoformat()),
        )

    await message.answer("✅ Link save ho gaya!")


@dp.callback_query(F.data == "status")
async def status_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🟢 Bot Status: Online\n"
        f"👥 Registered users: {get_user_count()}\n"
        f"🔗 Saved links: {get_link_count()}"
    )


@dp.callback_query(F.data == "links")
async def links_callback(callback: CallbackQuery):
    await callback.answer()
    await send_links(callback)


@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "/start - Start\n"
        "/menu - Menu\n"
        "/status - Status\n"
        "/links - Saved links\n"
        "/addlink Title | https://example.com - Add link"
    )


async def main():
    init_db()
    print("SR7 Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
