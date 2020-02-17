# Copyright 2020 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from alembic import op
from oslo_utils import uuidutils
import sqlalchemy as sa


"""add_rbac_support_for_address_scope

Revision ID: 46fb0c07e8cd
Revises: 2217c4222de6
Create Date: 2020-02-14 16:05:25.492685

"""

# revision identifiers, used by Alembic.
revision = '46fb0c07e8cd'
down_revision = '2217c4222de6'


def upgrade():
    address_scope_rbacs = op.create_table(
        'addressscoperbacs', sa.MetaData(),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('target_tenant', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('object_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['object_id'], ['address_scopes.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('target_tenant', 'object_id', 'action',
                            name='uniq_address_scopes_rbacs0'
                            'target_tenant0object_id0action')
    )
    op.bulk_insert(address_scope_rbacs,
                   get_rbac_policies_for_shared_address_scopes())

    op.create_index(op.f('ix_address_scopes_rbacs_project_id'),
                    'addressscoperbacs', ['project_id'], unique=False)

    op.drop_column('address_scopes', 'shared')


def get_rbac_policies_for_shared_address_scopes():
    # A simple model of the address_scopes table with only the fields needed
    # for the migration.
    address_scope = sa.Table(
        'address_scopes', sa.MetaData(),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255)),
        sa.Column('shared', sa.Boolean(), nullable=False)
    )

    session = sa.orm.Session(bind=op.get_bind())
    shared_address_scopes = session.query(address_scope).filter(
        address_scope.c.shared).all()
    values = []

    for row in shared_address_scopes:
        values.append({'id': uuidutils.generate_uuid(), 'object_id': row[0],
                       'project_id': row[1], 'target_tenant': '*',
                       'action': 'access_as_shared'})
    # this commit appears to be necessary to allow further operations
    session.commit()
    return values
