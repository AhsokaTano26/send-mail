from datetime import datetime
import json
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st

from zeabur_email import ZeaburEmailClient


SIGNATURE_HTML = """
<br><br>
<div style="font-family: sans-serif; border-top: 1px solid #eee; padding-top: 20px; display: flex; align-items: center;">
    <div style="margin-right: 15px;">
        <img src="https://cdn.v2ex.com/gravatar/a565d4366d88a05a5fbf4d9f64a2b63e42133b7fe218c40fa62eeccfa8d1216f?v=1765490201000&size=256&d=initials" alt="Tano" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover;">
    </div>
    <div>
        <div style="font-size: 18px; font-weight: bold; color: #000; margin-bottom: 4px;">Tano</div>
        <div style="font-size: 14px; color: #666; line-height: 1.4;">
            Student, Chong Qing University<br>
            Chong Qing, China
        </div>
        <div style="margin-top: 8px;">
            <a href="https://gravatar.com/ahsokatano26" style="font-size: 14px; color: #666; text-decoration: underline;">
                gravatar.com/ahsokatano26
            </a>
        </div>
    </div>
</div>
"""


st.set_page_config(page_title="Zeabur Email", page_icon="✉️", layout="wide")
st.title("Zeabur 邮件发送面板")
st.caption("使用 Streamlit 可视化发送、定时和查询邮件。")


def parse_list_field(value: str) -> List[str]:
    if not value:
        return []
    items: List[str] = []
    for line in value.replace("\n", ",").split(","):
        item = line.strip()
        if item:
            items.append(item)
    return items


def merge_signature(html: str, enabled: bool) -> str:
    base_html = html.strip()
    if not enabled:
        return base_html
    if base_html:
        return f"{base_html}{SIGNATURE_HTML}"
    return SIGNATURE_HTML


def display_result(result: Any) -> None:
    if isinstance(result, list):
        if result:
            st.dataframe(result, use_container_width=True)
        else:
            st.info("没有返回数据")
        return
    if isinstance(result, dict):
        st.json(result)
        return
    st.write(result)


def create_client() -> ZeaburEmailClient:
    api_key = st.session_state.get("api_key") or None
    timeout = int(st.session_state.get("timeout", 30))
    return ZeaburEmailClient(api_key=api_key, timeout=timeout)


def run_action(label: str, action) -> None:
    with st.spinner(label):
        result = action()
    st.success("操作完成")
    display_result(result)


with st.sidebar:
    st.header("连接配置")
    st.text_input("API Key", key="api_key", type="password", help="每次启动后都需要在这里输入")
    st.number_input("超时时间（秒）", key="timeout", min_value=5, max_value=120, value=30, step=5)
    st.divider()
    st.markdown("**签名预览**")
    st.markdown(SIGNATURE_HTML, unsafe_allow_html=True)


try:
    client = create_client()
    st.sidebar.success("已连接")
except ValueError as exc:
    client = None
    st.sidebar.error(str(exc))
    st.warning("先在侧边栏输入 API Key。")


tab_send, tab_schedule, tab_query, tab_batch = st.tabs(["发送邮件", "定时邮件", "查询邮件", "批量任务"])

with tab_send:
    st.subheader("发送邮件")
    with st.form("send_email_form"):
        sender = st.text_input("发件人", value="notice@mail.tano.asia")
        recipients = st.text_area("收件人", placeholder="每行或用逗号分隔")
        subject = st.text_input("主题")
        html = st.text_area("HTML 正文", height=180)
        text = st.text_area("纯文本正文", height=140)
        include_signature = st.checkbox("附加签名", value=True)
        cc = st.text_area("抄送", placeholder="每行或用逗号分隔")
        bcc = st.text_area("密送", placeholder="每行或用逗号分隔")
        reply_to = st.text_input("Reply-To")
        tags = st.text_input("标签", help="用逗号分隔")
        submit_send = st.form_submit_button("发送邮件")

    if submit_send:
        if not client:
            st.error("请先配置 API Key。")
        else:
            try:
                run_action(
                    "正在发送邮件",
                    lambda: client.send_email(
                        sender=sender,
                        to=parse_list_field(recipients),
                        subject=subject,
                        html=merge_signature(html, include_signature),
                        text=text,
                        cc=parse_list_field(cc),
                        bcc=parse_list_field(bcc),
                        reply_to=reply_to or None,
                        tags=parse_list_field(tags),
                    ),
                )
            except Exception as exc:
                st.error(str(exc))

with tab_schedule:
    st.subheader("定时发送")
    with st.form("schedule_email_form"):
        sender = st.text_input("发件人", value="notice@mail.tano.asia", key="schedule_sender")
        recipients = st.text_area("收件人", placeholder="每行或用逗号分隔", key="schedule_recipients")
        subject = st.text_input("主题", key="schedule_subject")
        scheduled_at = st.datetime_input("发送时间", value=datetime.now(), key="scheduled_at")
        html = st.text_area("HTML 正文", height=180, key="schedule_html")
        text = st.text_area("纯文本正文", height=140, key="schedule_text")
        include_signature = st.checkbox("附加签名", value=True, key="schedule_signature")
        cc = st.text_area("抄送", placeholder="每行或用逗号分隔", key="schedule_cc")
        bcc = st.text_area("密送", placeholder="每行或用逗号分隔", key="schedule_bcc")
        reply_to = st.text_input("Reply-To", key="schedule_reply_to")
        tags = st.text_input("标签", help="用逗号分隔", key="schedule_tags")
        submit_schedule = st.form_submit_button("创建定时任务")

    if submit_schedule:
        if not client:
            st.error("请先配置 API Key。")
        else:
            try:
                run_action(
                    "正在创建定时任务",
                    lambda: client.schedule_email(
                        sender=sender,
                        to=parse_list_field(recipients),
                        subject=subject,
                        scheduled_at=scheduled_at.isoformat(),
                        html=merge_signature(html, include_signature),
                        text=text,
                        cc=parse_list_field(cc),
                        bcc=parse_list_field(bcc),
                        reply_to=reply_to or None,
                        tags=parse_list_field(tags),
                    ),
                )
            except Exception as exc:
                st.error(str(exc))

with tab_query:
    st.subheader("邮件查询")
    query_mode = st.radio(
        "选择查询类型",
        ["邮件列表", "邮件详情", "定时列表", "定时详情", "取消定时"],
        horizontal=True,
    )

    if query_mode == "邮件列表":
        with st.form("list_emails_form"):
            page = st.number_input("页码", min_value=1, value=1, step=1)
            page_size = st.number_input("每页数量", min_value=1, value=20, step=1)
            status = st.text_input("状态")
            job_type = st.text_input("任务类型")
            submit = st.form_submit_button("查询邮件列表")
        if submit:
            if not client:
                st.error("请先配置 API Key。")
            else:
                try:
                    run_action(
                        "正在查询邮件列表",
                        lambda: client.list_emails(page=page, page_size=page_size, status=status or None, job_type=job_type or None),
                    )
                except Exception as exc:
                    st.error(str(exc))

    elif query_mode == "邮件详情":
        with st.form("email_detail_form"):
            email_id = st.text_input("邮件 ID")
            submit = st.form_submit_button("查询详情")
        if submit:
            if not client:
                st.error("请先配置 API Key。")
            else:
                try:
                    run_action("正在查询邮件详情", lambda: client.get_email_details(email_id))
                except Exception as exc:
                    st.error(str(exc))

    elif query_mode == "定时列表":
        with st.form("scheduled_list_form"):
            page = st.number_input("页码", min_value=1, value=1, step=1, key="scheduled_page")
            limit = st.number_input("每页数量", min_value=1, value=20, step=1)
            status = st.text_input("状态", key="scheduled_status")
            submit = st.form_submit_button("查询定时列表")
        if submit:
            if not client:
                st.error("请先配置 API Key。")
            else:
                try:
                    run_action("正在查询定时列表", lambda: client.list_scheduled_emails(page=page, limit=limit, status=status or None))
                except Exception as exc:
                    st.error(str(exc))

    elif query_mode == "定时详情":
        with st.form("scheduled_detail_form"):
            email_id = st.text_input("定时任务 ID")
            submit = st.form_submit_button("查询详情")
        if submit:
            if not client:
                st.error("请先配置 API Key。")
            else:
                try:
                    run_action("正在查询定时详情", lambda: client.get_scheduled_email(email_id))
                except Exception as exc:
                    st.error(str(exc))

    else:
        with st.form("cancel_scheduled_form"):
            email_id = st.text_input("定时任务 ID", key="cancel_scheduled_id")
            submit = st.form_submit_button("取消任务")
        if submit:
            if not client:
                st.error("请先配置 API Key。")
            else:
                try:
                    run_action("正在取消定时任务", lambda: client.cancel_scheduled_email(email_id))
                except Exception as exc:
                    st.error(str(exc))

with tab_batch:
    st.subheader("批量任务")
    batch_mode = st.radio("批量输入方式", ["JSON 文本", "上传 JSON 文件"], horizontal=True)
    with st.form("batch_form"):
        if batch_mode == "JSON 文本":
            batch_json = st.text_area("批量邮件 JSON", height=240, value='[\n  {\n    "from": "notice@mail.tano.asia",\n    "to": ["a@example.com"],\n    "subject": "Hello",\n    "text": "Test"\n  }\n]')
        else:
            batch_file = st.file_uploader("选择 JSON 文件", type=["json"])
            batch_json = None
        submit = st.form_submit_button("提交批量任务")

    if submit:
        if not client:
            st.error("请先配置 API Key。")
        else:
            try:
                if batch_mode == "JSON 文本":
                    emails = json.loads(batch_json or "")
                else:
                    if batch_file is None:
                        raise ValueError("请先上传 JSON 文件")
                    emails = json.loads(batch_file.read().decode("utf-8"))
                run_action("正在提交批量任务", lambda: client.send_batch_emails(emails))
            except Exception as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("批量任务查询")
    with st.form("batch_query_form"):
        query_mode = st.radio("查询方式", ["任务列表", "任务详情"], horizontal=True, key="batch_query_mode")
        if query_mode == "任务列表":
            page = st.number_input("页码", min_value=1, value=1, step=1, key="batch_page")
            limit = st.number_input("每页数量", min_value=1, value=20, step=1, key="batch_limit")
        else:
            job_id = st.text_input("任务 ID", key="batch_job_id")
        submit = st.form_submit_button("查询")
    if submit:
        if not client:
            st.error("请先配置 API Key。")
        else:
            try:
                if query_mode == "任务列表":
                    run_action("正在查询批量任务列表", lambda: client.list_batch_jobs(page=page, limit=limit))
                else:
                    run_action("正在查询批量任务详情", lambda: client.get_batch_job_details(job_id))
            except Exception as exc:
                st.error(str(exc))
