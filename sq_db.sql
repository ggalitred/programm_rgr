
CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY AUTOINCREMENT,
    surname text NOT NULL,
    name text NOT NULL,
    patronymic text,
    email text NOT NULL,
    pass text NOT NULL,
    role text NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
    id integer PRIMARY KEY AUTOINCREMENT,
    description text NOT NULL
);
CREATE TABLE IF NOT EXISTS applications (
    id integer PRIMARY KEY AUTOINCREMENT,
    user_id integer NOT NULL,
    case_id integer NOT NULL,
    app_status TEXT NOT NULL,
    app_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);
