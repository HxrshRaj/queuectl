from sqlalchemy import insert, select, update

from queuectl.database.db import engine
from queuectl.database.schema import config


class ConfigRepository:
    DEFAULTS = {
        "max-retries": "3",
        "backoff-base": "2",
        "recovery-timeout": "60",
        "poll-interval": "1",
    }

    def initialize(self):
        with engine.begin() as conn:
            for key, value in self.DEFAULTS.items():
                row = conn.execute(
                    select(config.c.key).where(config.c.key == key)
                ).first()

                if row is None:
                    conn.execute(
                        insert(config).values(
                            key=key,
                            value=value,
                        )
                    )

    def get(self, key: str):
        with engine.connect() as conn:
            row = conn.execute(
                select(config.c.value).where(config.c.key == key)
            ).first()

            return None if row is None else row[0]

    def get_int(self, key: str):
        value = self.get(key)
        return None if value is None else int(value)

    def set(self, key: str, value):
        value = str(value)

        with engine.begin() as conn:
            row = conn.execute(
                select(config.c.key).where(config.c.key == key)
            ).first()

            if row is None:
                conn.execute(
                    insert(config).values(
                        key=key,
                        value=value,
                    )
                )
            else:
                conn.execute(
                    update(config)
                    .where(config.c.key == key)
                    .values(value=value)
                )

    def all(self):
        with engine.connect() as conn:
            return conn.execute(select(config)).mappings().all()