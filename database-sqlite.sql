CREATE TABLE quotes (
    quoteId INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    broadcaster VARCHAR NOT NULL,
    quote VARCHAR NOT NULL
);
CREATE INDEX quotes_broadcaster ON quotes (broadcaster);

CREATE TABLE quotes_tags (
    quoteId INTEGER NOT NULL,
    tag VARCHAR NOT NULL,
    PRIMARY KEY (quoteId, tag),
    FOREIGN KEY (quoteId) REFERENCES quotes(quoteId)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX quotes_tags_id ON quotes_tags (quoteId);

CREATE TABLE quotes_history (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    quoteId INTEGER NOT NULL,
    createdTime TIMESTAMP NOT NULL,
    broadcaster VARCHAR NOT NULL,
    quote VARCHAR NOT NULL,
    editor VARCHAR NOT NULL
);
CREATE INDEX quotes_history_broadcaster ON quotes_history (broadcaster);
