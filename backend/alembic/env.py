# File cấu hình Alembic (quản lý phiên bản database).
# Nếu chưa muốn dùng Alembic cũng được: main.py đã tự tạo bảng bằng create_all.
from alembic import context
from app.database import Base, engine
from app import models

target_metadata = Base.metadata

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
