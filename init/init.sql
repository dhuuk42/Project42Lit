-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Weight entries per user
CREATE TABLE IF NOT EXISTS weight_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    weight REAL NOT NULL
);

-- Challenge completion log
CREATE TABLE IF NOT EXISTS challenge_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, date)
);
