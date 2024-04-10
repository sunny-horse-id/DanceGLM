# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from typing import Optional

import streamlit as st
import sqlite3
import hashlib
from utils import dir_init

DATABASE = "/home/cq/code/2024/ChatGLM3/composite_demo/config/database/user.db"
database = DATABASE


# 连接到SQLite数据库（如果不存在则创建）
def database_init(database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()


def conn_get(database):
    conn = sqlite3.connect(database)
    return conn


# 注册函数
# def register(username: Optional[str], password: Optional[str]):
def register():
    database_init(database)
    conn = conn_get(database)
    username = st.text_input('用户名[4-16]位')
    password = st.text_input('密码含有大小写', type='password')
    reg = st.button("注册")
    if reg:
        # 连接数据库，插入新用户信息
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        conn.close()
        st.success('注册成功！')


# 登录函数
# def login(username: Optional[str], password: Optional[str]) -> int:
def login() -> int:
    database_init(database)
    conn = conn_get(database)
    username = st.text_input('用户名')
    password = st.text_input('密码', type='password')
    log = st.button("登录")
    if log:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        user = cursor.fetchone()
        conn.row_factory = None
        conn.close()
        if user and check_password(password, user[2]):
            st.session_state.user_id = user[0]
            print("User", user)
            st.success('登录成功！')
            # 替换变量的值
            new_value = st.session_state.user_id
            dir_init(new_value)
            return st.session_state.user_id
        else:
            st.error('登录失败，用户名或密码错误。')

    return st.session_state.user_id


# 密码哈希函数
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


# 密码验证函数
def check_password(password, hashed_password):
    return hash_password(password) == hashed_password


# Streamlit应用程序主逻辑
def main():
    # st.set_page_config(page_title="用户注册登录")
    placeholder = st.container()
    st.session_state.user_id = None
    database_init(database)
    conn = conn_get(database)
    if 'user_id' not in st.session_state:
        choice = placeholder.radio('还没有账号？注册', ['是', '否'])
        if choice == '是':
            register(conn)
        else:
            logged_in = login(conn)
            if logged_in:
                st.write('登录成功，欢迎用户！')
