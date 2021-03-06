import sqlalchemy as sa

from aiohttp_security.abc import AbstractAuthorizationPolicy
from passlib.hash import sha256_crypt
import db.models as db


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, db_engine):
        self._db_engine = db_engine

    async def authorized_userid(self, identity):
        return identity

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False

        async with self._db_engine.acquire() as conn:

            if permission == 'admin':
                where = db.admin.c.email == identity
                query = db.admin.select().where(where)

            elif permission == 'company':
                where = sa.and_(db.company.c.email == identity,
                                sa.not_(db.company.c.disabled))
                query = db.company.select().where(where)

            else:
                where = sa.and_(db.employer.c.email == identity,
                                sa.not_(db.employer.c.disabled))
                query = db.employer.select().where(where)
            ret = await conn.execute(query)
            user = await ret.fetchone()
            if user is not None:
                return True

            return False


async def check_credentials(db_engine, username, password, permission):
    async with db_engine.acquire() as conn:

        if permission == 'admin':
            where = db.admin.c.email == username
            query = db.admin.select().where(where)

        elif permission == 'company':
            where = sa.and_(db.company.c.email == username,
                            sa.not_(db.company.c.disabled))
            query = db.company.select().where(where)

        elif permission == 'employer':
            where = sa.and_(db.employer.c.email == username,
                            sa.not_(db.employer.c.disabled))
            query = db.employer.select().where(where)

        ret = await conn.execute(query)
        user = await ret.fetchone()
        if user is not None:
            pass_hash = user[2]
            return sha256_crypt.verify(password, pass_hash)
    return False
