from typing import List, Dict, Any, Optional

import requests

class ZeaburEmailClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = (api_key or '').strip()
        self.base_url = 'https://api.zeabur.com/api/v1/zsend'
        self.timeout = timeout
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        if not self.api_key:
            raise ValueError("请先在页面中输入 API Key")

    @staticmethod
    def _normalize_recipients(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [item for item in value if item]
        return [value]

    @staticmethod
    def _validate_required(value: str, field_name: str):
        if not value or not value.strip():
            raise ValueError(f"{field_name} 不能为空")

    @staticmethod
    def _compact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        compacted: Dict[str, Any] = {}
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, (list, tuple, dict)) and not value:
                continue
            compacted[key] = value
        return compacted

    def _request(self, method: str, endpoint: str, json=None, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                json=json,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            if not response.content:
                return {"status": "ok"}
            try:
                return response.json()
            except ValueError:
                return {"status": "ok", "message": response.text}
        except requests.exceptions.RequestException as e:
            response = getattr(e, "response", None)
            if response is not None:
                try:
                    return response.json()
                except ValueError:
                    return {"error": "Request Failed", "message": response.text or str(e)}
            return {"error": "Request Failed", "message": str(e)}

    # --- 1. 邮件发送接口 ---
    def send_email(self, sender: str, to: List[str], subject: str,
                   html: str = None, text: str = None, **kwargs):
        """发送单封邮件"""
        self._validate_required(sender, "sender")
        self._validate_required(subject, "subject")
        recipients = self._normalize_recipients(to)
        if not recipients:
            raise ValueError("to 不能为空")
        payload = self._compact_payload({
            "from": sender,
            "to": recipients,
            "subject": subject,
            "html": html,
            "text": text,
            **kwargs # 支持 cc, bcc, reply_to, attachments, headers, tags
        })
        return self._request('POST', '/emails', json=payload)

    # --- 2. 定时邮件接口 ---
    def schedule_email(self, sender: str, to: List[str], subject: str,
                       scheduled_at: str, html: str = None, text: str = None, **kwargs):
        """安排在指定时间发送邮件 (ISO 8601 格式)"""
        self._validate_required(sender, "sender")
        self._validate_required(subject, "subject")
        self._validate_required(scheduled_at, "scheduled_at")
        recipients = self._normalize_recipients(to)
        if not recipients:
            raise ValueError("to 不能为空")
        payload = self._compact_payload({
            "from": sender,
            "to": recipients,
            "subject": subject,
            "scheduled_at": scheduled_at,
            "html": html,
            "text": text,
            **kwargs
        })
        return self._request('POST', '/emails/schedule', json=payload)

    def list_scheduled_emails(self, page=1, limit=20, status: str = None):
        """查询定时邮件列表"""
        params = {"page": page, "limit": limit}
        if status: params["status"] = status
        return self._request('GET', '/emails/scheduled', params=params)

    def get_scheduled_email(self, email_id: str):
        """查询定时邮件详情"""
        return self._request('GET', f'/emails/scheduled/{email_id}')

    def cancel_scheduled_email(self, email_id: str):
        """取消定时邮件"""
        return self._request('DELETE', f'/emails/scheduled/{email_id}')

    # --- 3. 批量发送接口 ---
    def send_batch_emails(self, emails: List[Dict[str, Any]]):
        """批量发送邮件 (最多 100 封)"""
        if not isinstance(emails, list) or not emails:
            raise ValueError("emails 不能为空且必须是列表")
        return self._request('POST', '/emails/batch', json={"emails": emails})

    def list_batch_jobs(self, page=1, limit=20):
        """查询批量任务列表"""
        return self._request('GET', '/emails/batch', params={"page": page, "limit": limit})

    def get_batch_job_details(self, job_id: str):
        """查询批量任务详情"""
        return self._request('GET', f'/emails/batch/{job_id}')

    # --- 4. 邮件查询接口 ---
    def list_emails(self, page=1, page_size=20, status: str = None, job_type: str = None):
        """查询邮件列表"""
        params = {"page": page, "page_size": page_size}
        if status: params["status"] = status
        if job_type: params["job_type"] = job_type
        return self._request('GET', '/emails', params=params)

    def get_email_details(self, email_id: str):
        """查询单封邮件详情"""
        return self._request('GET', f'/emails/{email_id}')
