# send-email

Zeabur 邮件发送的 Streamlit 可视化面板。

## 安装

```bash
pip3 install -r requirements.txt
```

在项目根目录创建 `.env`：

```bash
ZEABUR_API_KEY=your_api_key
```

## 启动

```bash
streamlit run main.py
```

## 功能

- 发送邮件
- 定时发送
- 查询邮件/定时任务
- 取消定时任务
- 批量发送与批量任务查询
- 默认附加你之前的签名，也可以在发送时关闭

## 签名

页面侧边栏会显示并应用你之前的 HTML 签名，发信时默认附加到 HTML 正文末尾。
