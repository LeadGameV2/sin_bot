from loguru import logger
import psycopg2

from bot import settings


def db_request(query: str, fetch: bool = False):
    try:
        connection = psycopg2.connect(
            database=settings.postgres.db_name,
            host=settings.postgres.host,
            user=settings.postgres.user,
            password=settings.postgres.password,
            port=settings.postgres.port)
        cursor = connection.cursor()
        cursor.execute(query)
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = True
        
    except (Exception, psycopg2.Error) as error:
        logger.warning(f"Error while fetching data from PostgreSQL {error}")
        result = False

    finally:
        if connection:
            cursor.close()
            connection.close()

    return result