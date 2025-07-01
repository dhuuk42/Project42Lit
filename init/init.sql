CREATE TABLE IF NOT EXISTS weight_entries (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    weight REAL NOT NULL
);
