# Чат с тектом
## Авторы:
- Волков Матвей (М8О-109М)
- Федоров Антон (М8О-114М)

## Полезные ссылки
<img src="./docs/imgs/MongoDB_Logo.svg" width="200"/>

- [Особенности MongoDB](https://mcs.mail.ru/blog/osobennosti-mongodb-kogda-baza-dannyh-vam-podhodit#)
- [MongoDB github actions](https://github.com/marketplace/actions/mongodb-in-github-actions)


<img src="./docs/imgs/keydb-seeklogo.com.svg" width="200"/>

- [Key-db](https://docs.keydb.dev/) - fork redis базы данных
- [Key-db](https://habr.com/ru/companies/flant/articles/478404/) - habr статья сравнения с redis

<img src="./docs/imgs/elasticsearch-seeklogo.com.svg" width="50"/>

- [ElasticSearch doc](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [ElasticSearch habr](https://habr.com/ru/articles/489924/) - "С чего начинается Elasticsearch"

# Документация
## Диаграмма взаимодействий

### Отправка сообщений

```mermaid
sequenceDiagram
    actor client


    box MediumSlateBlue API
        participant SendMsg
        participant GetMsg
        participant Search
    end

    box OliveDrab DB
        participant Elastic 
        participant MongoDB
    end

    client ->> SendMsg: JSON с сообщением
    Note over client,SendMsg: JSON содержит<br/>различные характеристики<br/>сообщений
    activate SendMsg
        SendMsg ->> MongoDB: Сохранить JSON
    deactivate SendMsg

    MongoDB --) Elastic: фоновая обработка 
    Note over Elastic,MongoDB: Возможна обработка<br/>индексов
```
При отправке сообщений, пользователь отправляет JSON файл, который содержит все нужные характеристики сообщения такие, как:
- UUID сообщения
- Само сообщение
- Файл в бинарном представлении
- ID чата
- UUID отправителя
- Timestamp время

JSON сообщения сохраняется напрямую в `MongoDB` и `Elasticsearch` используется для сохранения индексов сообщений для последующего удобного поиска.

### Получение сообщений
```mermaid
sequenceDiagram
    actor client

    box MediumSlateBlue API
        participant SendMsg
        participant GetMsg
        participant Search
    end

    box Olive DB-cache
        participant Key-db
    end

    box OliveDrab DB
        participant Elastic 
        participant MongoDB
    end

    client ->> GetMsg: Запрос с пагинацией
    Note over client,GetMsg: Пагинация будет по простому лимиту<br/>сообщений
    opt Websocket
        client -) GetMsg: Websocket in
        
    end

    activate GetMsg

    GetMsg -> GetMsg: Обработка пагинации
    opt Websocket
        alt db cache 
            GetMsg ->> Key-db: Проверка новых сообщений
        else no cache
            GetMsg -) GetMsg: Проверка новых сообщений
        end
        GetMsg -) client: Websocket out
        
    end
    GetMsg ->> MongoDB: Запрос сообщений

    deactivate GetMsg

    activate  MongoDB

    MongoDB --> MongoDB: 1. Поиск сообщений
    MongoDB --> MongoDB: 2. Сортировка по дате
    MongoDB --> MongoDB: 3. Учет пагинации

    deactivate MongoDB

    MongoDB ->> GetMsg: Получение сообщений

    GetMsg ->> client: Отдача сообщений
    opt Websocket
       GetMsg -) client: Websocket out
    end

```

Получение сообщений сообщений будет происходить по API ручке. (Опционально добавление websocket соединения).

Получение сообщений будет происходит с пагинацией на лимит сообщений (*например 30 сообщений*), которые будут отсортированы по дате отправления сообщений: первое сообщение будет последнее отправленное.

При использовании Websocket полезно использовать какой-нибудь кэш, чтобы возможно было смотреть на изменения сообщений.
Если будет использоваться кэш на базе данных, то будет использоваться key-db.

### Поиск сообщений в чате

```mermaid
sequenceDiagram
    actor client

    box MediumSlateBlue API
        participant SendMsg
        participant GetMsg
        participant Search
    end

    box OliveDrab DB
        participant Elastic 
        participant MongoDB
    end

    client ->> Search: Паттерн поиска
    Search ->> Elastic: Передача паттерна

    activate Elastic
        Elastic --> Elastic: Обработка
        Elastic ->> MongoDB: Запрос сообщений 
        MongoDB ->> Elastic: Возврат сообщений
    deactivate Elastic

    Elastic ->> Search: Отдача сообщений
    Search ->> client: Отдача сообщений

```
Поиск сообщений предполагается осуществлять при помощи `ElasticSearch`.
Elastic, после обработки паттерна и нахождения нужных индексов в MongoDB, пойдет в базу данных MongoDB за самими сообщениями.

ElasticSearch в данном случае служит прослойкой для упрощения поиска по базе MongoDB.

Клиент в данном случае будет получать массив сообщений, паттерн который соответствует телу сообщения.


# Как запустить
Выполнить в терминале:
```bash
docker compose up
```
Потом зайти на `http://127.0.0.1:8000/docs` и дергать ручки.