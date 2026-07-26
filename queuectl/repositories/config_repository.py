from sqlalchemy import insert, select, update

from queuectl.database.db import engine
from queuectl.database.schema import config


class ConfigRepository:

    DEFAULTS = {
        "max-retries": "3",
        "backoff-base": "2",
    }

    def initialize(self):
        with engine.begin() as conn:
            for key, value in self.DEFAULTS.items():
                exists = conn.execute(
                    select(config.c.key)
                    .where(config.c.key == key)
                ).first()

                if exists is None:
                    conn.execute(
                        insert(config).values(
                            key=key,
                            value=value,
                        )
                    )

    def get(self, key: str):
        with engine.connect() as conn:
            row = conn.execute(
                select(config.c.value)
                .where(config.c.key == key)
            ).first()

            if row is None:
                return None

            return row[0]

    def set(self, key: str, value: str):
        with engine.begin() as conn:
            exists = conn.execute(
                select(config.c.key)
                .where(config.c.key == key)
            ).first()

            if exists is None:
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
                    .values(
                        value=value,
                    )
                )

    def all(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(config)
            )

            return result.mappings().all()