import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# База данных
DB_PATH = 'fame_tg.db'

# Состояния для заявок
class ApplicationStates(StatesGroup):
    photo = State()
    name = State()
    username = State()
    category = State()
    channel = State()
    description = State()
    confirm = State()

# Создание таблиц
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица анкет
        await db.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                category_name TEXT NOT NULL,
                description TEXT,
                avatar TEXT,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                badges TEXT,
                links TEXT,
                pinned BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заявок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                photo TEXT,
                name TEXT NOT NULL,
                username TEXT NOT NULL,
                category TEXT NOT NULL,
                channel TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                admin_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

# Клавиатуры
def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки", callback_data="admin_apps")],
        [InlineKeyboardButton(text="👥 Анкеты", callback_data="admin_cards")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
    ])

def get_app_keyboard(app_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{app_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{app_id}")
        ],
        [InlineKeyboardButton(text="👁 Просмотр", callback_data=f"view_{app_id}")]
    ])

def get_badge_keyboard(card_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Verified", callback_data=f"badge_verified_{card_id}"),
            InlineKeyboardButton(text="⚠️ SCAM", callback_data=f"badge_scam_{card_id}")
        ],
        [
            InlineKeyboardButton(text="📌 Закреплён", callback_data=f"badge_pinned_{card_id}"),
            InlineKeyboardButton(text="📋 В скам базе", callback_data=f"badge_scamdb_{card_id}")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cards")]
    ])

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Сохраняем пользователя
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO users (id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name))
        await db.commit()
    
    # Проверяем, админ ли
    if user_id in ADMIN_IDS:
        await db.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user_id,))
        await db.commit()
        await message.answer(
            "👋 Привет, админ!\n\n"
            "Я бот Fame TG. Ты можешь управлять заявками и анкетами.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "👋 Привет! Я бот Fame TG.\n\n"
            "Ты можешь подать заявку на добавление в каталог медийных личностей.\n\n"
            "Для этого нажми /apply"
        )

# Команда /apply
@dp.message(Command("apply"))
async def cmd_apply(message: types.Message, state: FSMContext):
    await message.answer(
        "📝 Давай заполним заявку!\n\n"
        "Шаг 1 из 6: Отправь мне своё фото для аватара.\n"
        "(можно просто фото или файл)"
    )
    await state.set_state(ApplicationStates.photo)

# Обработка фото
@dp.message(ApplicationStates.photo, F.photo | F.document)
async def process_photo(message: types.Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
    else:
        await message.answer("Пожалуйста, отправь фото.")
        return
    
    # Скачиваем фото
    file = await bot.get_file(file_id)
    file_path = f"avatars/{file_id}.jpg"
    os.makedirs("avatars", exist_ok=True)
    await bot.download_file(file.file_path, file_path)
    
    await state.update_data(photo=file_path)
    await message.answer("✅ Фото сохранено!\n\nШаг 2 из 6: Введи своё имя:")
    await state.set_state(ApplicationStates.name)

# Обработка имени
@dp.message(ApplicationStates.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("✅ Имя сохранено!\n\nШаг 3 из 6: Введи свой username (без @):")
    await state.set_state(ApplicationStates.username)

# Обработка username
@dp.message(ApplicationStates.username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.replace('@', '')
    await state.update_data(username=username)
    
    # Клавиатура с категориями
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Медийки", callback_data="cat_medijki")],
        [InlineKeyboardButton(text="Фейм", callback_data="cat_fame")],
        [InlineKeyboardButton(text="Средний", callback_data="cat_middle")],
        [InlineKeyboardButton(text="Малый", callback_data="cat_small")],
        [InlineKeyboardButton(text="Кодеры", callback_data="cat_coders")],
        [InlineKeyboardButton(text="Товары", callback_data="cat_goods")],
        [InlineKeyboardButton(text="Каналы", callback_data="cat_channels")],
        [InlineKeyboardButton(text="Скам", callback_data="cat_scam")],
        [InlineKeyboardButton(text="Дизайнеры", callback_data="cat_designers")],
        [InlineKeyboardButton(text="Эдиторы", callback_data="cat_editors")]
    ])
    
    await message.answer("✅ Username сохранён!\n\nШаг 4 из 6: Выбери категорию:", reply_markup=kb)
    await state.set_state(ApplicationStates.category)

# Обработка категории
@dp.callback_query(ApplicationStates.category, F.data.startswith('cat_'))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace('cat_', '')
    await state.update_data(category=category)
    await callback.message.edit_text(
        f"✅ Категория выбрана!\n\n"
        f"Шаг 5 из 6: Если у тебя есть канал, отправь ссылку (или отправь 'пропустить'):"
    )
    await state.set_state(ApplicationStates.channel)
    await callback.answer()

# Обработка канала
@dp.message(ApplicationStates.channel)
async def process_channel(message: types.Message, state: FSMContext):
    if message.text.lower() == 'пропустить':
        channel = None
    else:
        channel = message.text
    
    await state.update_data(channel=channel)
    await message.answer(
        "✅ Канал сохранён!\n\n"
        "Шаг 6 из 6: Напиши подробное описание о себе:\n"
        "(проекты, достижения, узнаваемость)"
    )
    await state.set_state(ApplicationStates.description)

# Обработка описания
@dp.message(ApplicationStates.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Показываем предпросмотр
    preview = (
        f"📋 **Предпросмотр заявки**\n\n"
        f"**Имя:** {data['name']}\n"
        f"**Username:** @{data['username']}\n"
        f"**Категория:** {data['category']}\n"
        f"**Канал:** {data.get('channel', 'Не указан')}\n"
        f"**Описание:** {data['description'][:100]}...\n\n"
        f"Всё верно?"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")
        ]
    ])
    
    await message.answer(preview, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(ApplicationStates.confirm)

# Подтверждение заявки
@dp.callback_query(ApplicationStates.confirm, F.data == "confirm_yes")
async def confirm_application(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем заявку в БД
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO applications (user_id, user_name, photo, name, username, category, channel, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            callback.from_user.id,
            callback.from_user.full_name,
            data['photo'],
            data['name'],
            data['username'],
            data['category'],
            data.get('channel'),
            data['description']
        ))
        app_id = cursor.lastrowid
        await db.commit()
    
    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"📨 **Новая заявка!**\n\n"
                f"**От:** {callback.from_user.full_name} (@{callback.from_user.username})\n"
                f"**Имя:** {data['name']}\n"
                f"**Username:** @{data['username']}\n"
                f"**Категория:** {data['category']}\n\n"
                f"Заявка #{app_id}",
                reply_markup=get_app_keyboard(app_id),
                parse_mode="Markdown"
            )
        except:
            pass
    
    await callback.message.edit_text(
        "✅ Заявка отправлена!\n\n"
        "Администратор рассмотрит её в ближайшее время.\n"
        "Статус заявки можно отследить через /status"
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(ApplicationStates.confirm, F.data == "confirm_no")
async def cancel_application(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Заявка отменена. Начни заново через /apply")
    await state.clear()
    await callback.answer()

# Админка: просмотр заявок
@dp.callback_query(F.data == "admin_apps")
async def admin_show_apps(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT * FROM applications WHERE status = 'pending' ORDER BY created_at DESC
        ''')
        apps = await cursor.fetchall()
    
    if not apps:
        await callback.message.edit_text("📭 Новых заявок нет")
        return
    
    for app in apps[:5]:  # Показываем последние 5
        text = (
            f"📋 Заявка #{app['id']}\n"
            f"От: {app['user_name']}\n"
            f"Имя: {app['name']}\n"
            f"Username: @{app['username']}\n"
            f"Категория: {app['category']}\n"
            f"Дата: {app['created_at']}"
        )
        await callback.message.answer(text, reply_markup=get_app_keyboard(app['id']))
    
    await callback.answer()

# Принятие заявки
@dp.callback_query(F.data.startswith('approve_'))
async def approve_application(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    app_id = int(callback.data.split('_')[1])
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
        app = await cursor.fetchone()
        
        if not app:
            await callback.answer("Заявка не найдена")
            return
        
        # Добавляем в карточки
        await db.execute('''
            INSERT INTO cards (name, username, category, category_name, description, avatar, links)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            app['name'],
            app['username'],
            app['category'],
            app['category'].capitalize(),
            app['description'],
            app['photo'],
            app['channel']
        ))
        
        # Обновляем статус заявки
        await db.execute('UPDATE applications SET status = ? WHERE id = ?', ('approved', app_id))
        await db.commit()
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            app['user_id'],
            "✅ **Поздравляю!**\n\n"
            "Твоя заявка принята! Теперь ты в каталоге Fame TG.\n"
            f"https://bksaa01.github.io/fame-tg/#{app['username']}"
        )
    except:
        pass
    
    await callback.message.edit_text(f"✅ Заявка #{app_id} принята!")
    await callback.answer()

# Отклонение заявки
@dp.callback_query(F.data.startswith('reject_'))
async def reject_application(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    app_id = int(callback.data.split('_')[1])
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT user_id FROM applications WHERE id = ?', (app_id,))
        user_id = await cursor.fetchone()
        
        await db.execute('UPDATE applications SET status = ? WHERE id = ?', ('rejected', app_id))
        await db.commit()
    
    if user_id:
        try:
            await bot.send_message(
                user_id[0],
                "❌ К сожалению, твоя заявка отклонена.\n\n"
                "Попробуй подать заявку снова, улучшив описание."
            )
        except:
            pass
    
    await callback.message.edit_text(f"❌ Заявка #{app_id} отклонена")
    await callback.answer()

# Управление метками
@dp.callback_query(F.data.startswith('badge_'))
async def manage_badge(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа")
        return
    
    parts = callback.data.split('_')
    badge_type = parts[1]
    card_id = int(parts[2])
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT badges FROM cards WHERE id = ?', (card_id,))
        row = await cursor.fetchone()
        
        if row:
            badges = row[0].split(',') if row[0] else []
            if badge_type in badges:
                badges.remove(badge_type)
            else:
                badges.append(badge_type)
            
            await db.execute('UPDATE cards SET badges = ? WHERE id = ?', (','.join(badges), card_id))
            await db.commit()
    
    await callback.answer(f"Метка {'добавлена' if badge_type in badges else 'удалена'}")
    await callback.message.edit_reply_markup(reply_markup=get_badge_keyboard(card_id))

# Запуск бота
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
