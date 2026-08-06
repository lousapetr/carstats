"""currency support, price per liter, car name

Revision ID: 86aacad3c569
Revises: 440887b3f096
Create Date: 2026-08-06 02:12:08.891394

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '86aacad3c569'
down_revision: str | Sequence[str] | None = '440887b3f096'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CURRENCY_ENUM = sa.Enum(
    'CZK', 'EUR', 'PLN', 'HUF', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'RON', name='currency'
)


def upgrade() -> None:
    op.create_table(
        'currencyrate',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency', _CURRENCY_ENUM, nullable=False),
        sa.Column('rate_to_czk', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('currency'),
    )

    with op.batch_alter_table('carprofile') as batch_op:
        batch_op.add_column(
            sa.Column(
                'name', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=''
            )
        )

    with op.batch_alter_table('fuelentry') as batch_op:
        batch_op.add_column(sa.Column('price_per_liter', sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column(
                'currency',
                sa.Enum(
                    'CZK', 'EUR', 'PLN', 'HUF', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'RON',
                    name='currency', create_constraint=False,
                ),
                nullable=False,
                server_default='CZK',
            )
        )
        batch_op.add_column(
            sa.Column('exchange_rate', sa.Float(), nullable=False, server_default='1.0')
        )

    # Backfill price_per_liter from the previously-stored total for existing rows.
    op.execute("UPDATE fuelentry SET price_per_liter = price_total / liters WHERE liters != 0")
    op.execute("UPDATE fuelentry SET price_per_liter = 0 WHERE price_per_liter IS NULL")

    with op.batch_alter_table('fuelentry') as batch_op:
        batch_op.alter_column('price_per_liter', nullable=False)
        batch_op.drop_column('price_total')

    with op.batch_alter_table('serviceentry') as batch_op:
        batch_op.add_column(
            sa.Column(
                'currency',
                sa.Enum(
                    'CZK', 'EUR', 'PLN', 'HUF', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'RON',
                    name='currency', create_constraint=False,
                ),
                nullable=False,
                server_default='CZK',
            )
        )
        batch_op.add_column(
            sa.Column('exchange_rate', sa.Float(), nullable=False, server_default='1.0')
        )


def downgrade() -> None:
    with op.batch_alter_table('serviceentry') as batch_op:
        batch_op.drop_column('exchange_rate')
        batch_op.drop_column('currency')

    with op.batch_alter_table('fuelentry') as batch_op:
        batch_op.add_column(sa.Column('price_total', sa.Float(), nullable=True))
    op.execute("UPDATE fuelentry SET price_total = price_per_liter * liters")
    with op.batch_alter_table('fuelentry') as batch_op:
        batch_op.alter_column('price_total', nullable=False)
        batch_op.drop_column('exchange_rate')
        batch_op.drop_column('currency')
        batch_op.drop_column('price_per_liter')

    with op.batch_alter_table('carprofile') as batch_op:
        batch_op.drop_column('name')

    op.drop_table('currencyrate')
