#!/usr/bin/env python3
"""
Shared Database Schema Module
Provides centralized schema definitions for all OpsConductor services
"""

from typing import Dict, List, Any

# Table names
class Tables:
    USERS = "users"
    CREDENTIALS = "credentials"
    TARGETS = "targets"
    JOBS = "jobs"
    JOB_RUNS = "job_runs"
    JOB_RUN_STEPS = "job_run_steps"
    SCHEDULES = "schedules"
    NOTIFICATIONS = "notifications"
    NOTIFICATION_PREFERENCES = "notification_preferences"
    NOTIFICATION_TEMPLATES = "notification_templates"
    DISCOVERY_JOBS = "discovery_jobs"
    DISCOVERED_TARGETS = "discovered_targets"
    DISCOVERY_TEMPLATES = "discovery_templates"

# Column definitions
class Columns:
    # Common columns
    ID = "id"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    
    # Users table
    class Users:
        ID = "id"
        EMAIL = "email"
        USERNAME = "username"
        PWD_HASH = "pwd_hash"
        ROLE = "role"
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        TELEPHONE = "telephone"
        TITLE = "title"
        CREATED_AT = "created_at"
        UPDATED_AT = "updated_at"
        TOKEN_VERSION = "token_version"
    
    # Credentials table
    class Credentials:
        ID = "id"
        NAME = "name"
        DESCRIPTION = "description"
        TYPE = "type"
        USERNAME = "username"
        PASSWORD_ENCRYPTED = "password_encrypted"
        PRIVATE_KEY_ENCRYPTED = "private_key_encrypted"
        PASSPHRASE_ENCRYPTED = "passphrase_encrypted"
        CREATED_AT = "created_at"
        UPDATED_AT = "updated_at"
        CREATED_BY = "created_by"
    
    # Targets table
    class Targets:
        ID = "id"
        NAME = "name"
        DESCRIPTION = "description"
        HOST = "host"
        PORT = "port"
        CONNECTION_TYPE = "connection_type"
        CREDENTIAL_ID = "credential_id"
        CREATED_AT = "created_at"
        UPDATED_AT = "updated_at"
        CREATED_BY = "created_by"
        LAST_CONNECTION_STATUS = "last_connection_status"
        LAST_CONNECTION_TIME = "last_connection_time"
    
    # Notifications table
    class Notifications:
        ID = "id"
        JOB_RUN_ID = "job_run_id"
        USER_ID = "user_id"
        CHANNEL = "channel"
        DEST = "dest"
        PAYLOAD = "payload"
        TEMPLATE_ID = "template_id"
        STATUS = "status"
        RETRIES = "retries"
        CREATED_AT = "created_at"
        UPDATED_AT = "updated_at"
        SENT_AT = "sent_at"
        ERROR = "error"

# Common query fragments
class QueryFragments:
    # User fields for SELECT statements
    USER_SELECT_FIELDS = f"""
        {Columns.Users.ID}, {Columns.Users.EMAIL}, {Columns.Users.USERNAME}, 
        {Columns.Users.ROLE}, {Columns.Users.FIRST_NAME}, {Columns.Users.LAST_NAME}, 
        {Columns.Users.TELEPHONE}, {Columns.Users.TITLE}, {Columns.Users.CREATED_AT}, 
        {Columns.Users.TOKEN_VERSION}
    """
    
    # Credential fields for SELECT statements
    CREDENTIAL_SELECT_FIELDS = f"""
        {Columns.Credentials.ID}, {Columns.Credentials.NAME}, {Columns.Credentials.DESCRIPTION}, 
        {Columns.Credentials.TYPE}, {Columns.Credentials.USERNAME}, {Columns.Credentials.CREATED_AT}, 
        {Columns.Credentials.UPDATED_AT}, {Columns.Credentials.CREATED_BY}
    """
    
    # Target fields for SELECT statements
    TARGET_SELECT_FIELDS = f"""
        {Columns.Targets.ID}, {Columns.Targets.NAME}, {Columns.Targets.DESCRIPTION}, 
        {Columns.Targets.HOST}, {Columns.Targets.PORT}, {Columns.Targets.CONNECTION_TYPE}, 
        {Columns.Targets.CREDENTIAL_ID}, {Columns.Targets.CREATED_AT}, {Columns.Targets.UPDATED_AT}, 
        {Columns.Targets.CREATED_BY}, {Columns.Targets.LAST_CONNECTION_STATUS}, 
        {Columns.Targets.LAST_CONNECTION_TIME}
    """
    
    # Notification fields for SELECT statements
    NOTIFICATION_SELECT_FIELDS = f"""
        {Columns.Notifications.ID}, {Columns.Notifications.JOB_RUN_ID}, {Columns.Notifications.USER_ID}, 
        {Columns.Notifications.CHANNEL}, {Columns.Notifications.DEST}, {Columns.Notifications.PAYLOAD}, 
        {Columns.Notifications.TEMPLATE_ID}, {Columns.Notifications.STATUS}, {Columns.Notifications.RETRIES}, 
        {Columns.Notifications.CREATED_AT}, {Columns.Notifications.UPDATED_AT}, {Columns.Notifications.SENT_AT}, 
        {Columns.Notifications.ERROR}
    """

# Query builders
def build_select_query(table: str, fields: str, where_clause: str = "", 
                       order_by: str = "", limit: int = 0, offset: int = 0) -> str:
    """Build a SELECT query with optional clauses"""
    query = f"SELECT {fields} FROM {table}"
    
    if where_clause:
        query += f" WHERE {where_clause}"
    
    if order_by:
        query += f" ORDER BY {order_by}"
    
    if limit > 0:
        query += f" LIMIT {limit}"
    
    if offset > 0:
        query += f" OFFSET {offset}"
    
    return query

def build_insert_query(table: str, columns: List[str]) -> str:
    """Build an INSERT query with returning clause"""
    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)
    
    return f"INSERT INTO {table} ({column_names}) VALUES ({placeholders}) RETURNING id"

def build_update_query(table: str, columns: List[str], where_clause: str) -> str:
    """Build an UPDATE query"""
    set_clause = ", ".join([f"{col} = %s" for col in columns])
    
    return f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

def build_delete_query(table: str, where_clause: str) -> str:
    """Build a DELETE query"""
    return f"DELETE FROM {table} WHERE {where_clause}"

def build_count_query(table: str, where_clause: str = "") -> str:
    """Build a COUNT query"""
    query = f"SELECT COUNT(*) FROM {table}"
    
    if where_clause:
        query += f" WHERE {where_clause}"
    
    return query

# Pagination query with total count
def build_paginated_query(table: str, fields: str, where_clause: str = "", 
                         order_by: str = "", limit: int = 100, offset: int = 0) -> str:
    """Build a paginated query that includes total count"""
    return f"""
        WITH data AS (
            SELECT {fields}, COUNT(*) OVER() as total_count
            FROM {table}
            {f"WHERE {where_clause}" if where_clause else ""}
            {f"ORDER BY {order_by}" if order_by else ""}
            LIMIT {limit} OFFSET {offset}
        )
        SELECT * FROM data
    """