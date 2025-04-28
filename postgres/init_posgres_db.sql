CREATE SCHEMA IF NOT EXISTS sins;

CREATE TABLE IF NOT EXISTS sins.users (
    id uuid PRIMARY KEY,
    chat_id INT NOT NULL UNIQUE,
    nickname TEXT NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS sins.sins (
    id uuid PRIMARY KEY,
    text TEXT NOT NULL,
    anon BOOLEAN NOT NULL,
    likes INT NOT NULL,
    dislikes INT NOT NULL,
    author_id uuid NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone,
    FOREIGN KEY (author_id) REFERENCES sins.users(id)
);

CREATE TABLE IF NOT EXISTS sins.votes (
    id uuid PRIMARY KEY,
    author_id uuid NOT NULL,
    sin_id uuid NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone,
    FOREIGN KEY (author_id) REFERENCES sins.users(id),
    FOREIGN KEY (sin_id) REFERENCES sins.sins(id)
);

