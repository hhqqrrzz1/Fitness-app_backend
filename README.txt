Проект(асинхронный) для создания тренировок пользователя. Реализование различные эндпоинты по добавлению, удалению, изменению и получению тренировок,упражнений, подходов.
Так же реализована авторизация по JWT, БД - PostgreSQL, фреймворк - FastAPI, миграции с alembic, логирование с loguru

Проверить работоспособность проекта:
1. склонируем к себе проект (git clone https://github.com/hhqqrrzz1/Fitness-app_backend.git)

2. Создаем виртуальное окружение и устанавливаем все зависимости из файла requirements.txt

3. создадим файл /app/.env со следующим содержимым:
```
DB_USER=*
DB_PASSWORD=*
DB_HOST=*
DB_PORT=*
DB_NAME=*

SECRET_KEY=(если у вас установлен OpenSSL, можно воспользоваться командой в терминале - `openssl rand -hex 32`)
ALGORITHM=HS256
FULL_RIGHTS=admin,nikita
```
* - заменить на свои данные
FULL_RIGHTS - админы, у которых будут абсолютные права

4. Удалим директорию с миграциями и создадим новую командой - `alembic init -t async app/migrations`

5. в файле /app/migrations/env.py находим строку "target_metadata = None", заменим её на:
```
from app.config import settings
from app.backend.db import Base
from app.models import all_models

target_metadata = Base.metadata
```

6. В файле alembic.ini укажем наш url sqlalchemy.url = postgresql+asyncpg://user*:password*@host*:port*/db_name*
все знач. с * заменить на свои

7. Создадим первую миграцию `alembic revision --autogenerate -m "Описание изменений"` -> `alembic upgrade head`

8. Запускаем файл main.py и переходим в документацию (в случае локального запуска http://127.0.0.1:8000/docs#/)