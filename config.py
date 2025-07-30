import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8253902772:AAFfrJIBuqbn8xibUp9vUZkJkrTq1I9FKa4")
ADMIN_ID = 5209458285
GROUP_ID = -1002751692154

# Database configuration
DATABASE_NAME = "onomatopoeia_bot.db"

# Welcome message
WELCOME_MESSAGE = """✒️Привітик!! Мене звати Ономатопейка. Я — база, що допоможе тобі з перекладом звуків.

1️⃣ Надішліть англійську ономатопею, а я відповім українською.
2️⃣ Ви можете доповнити базу. Просто напишіть англійську й українську версії. Я передам адміну, а він додасть.
3️⃣ Ви можете зв'язатися з адміністратором. Не лише з приводу доповнення бази, але й просто щоб побазікати."""
