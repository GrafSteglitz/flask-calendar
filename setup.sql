DROP TABLE IF EXISTS Events;
CREATE TABLE Events
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    start_time TEXT,
    end_time TEXT,
    location TEXT,
    participants TEXT,
    series_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


-- repeats INTEGER NOT NULL DEFAULT 0,
-- repeat_frequency INTEGER NOT NULL DEFAULT 0,

-- INSERT INTO Events (name, description, start_date) VALUES ('event1', 'no description','31-10-2025');
-- ALTER TABLE Events ADD user_id REFERENCES 
SELECT * FROM Events;

DROP TABLE IF EXISTS users;

CREATE TABLE users(
    user_id TEXT PRIMARY_KEY,
    password TEXT NOT NULL
);
SELECT * FROM users;

-- INSERT INTO TABLE Events