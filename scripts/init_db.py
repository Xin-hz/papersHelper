"""在 PostgreSQL 中创建 pgvector 扩展（需先创建数据库）"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("请先安装: pip install psycopg2-binary")
    sys.exit(1)

database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/papers_helper",
)


def main():
    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.OperationalError as e:
        print("无法连接 PostgreSQL，请检查：")
        print("  1. 若用 Docker：在项目根目录执行  docker compose up -d")
        print("  2. 若用本机 Postgres：确认服务已启动（Postgres.app: https://postgresapp.com）")
        print("  3. 若用远程数据库：在 .env 中设置 DATABASE_URL")
        print()
        print(f"错误信息: {e}")
        sys.exit(1)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("pgvector 扩展已就绪")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
