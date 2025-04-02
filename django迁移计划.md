好的，这是一个将上述开发计划翻译成中文的版本：

**目标：** 创建一个 Django Web 应用程序，允许多个用户管理、生成并自动发送个性化的每日报告，基于他们的输入，并使用 Gemini 进行处理。

**核心技术：**

*   **后端：** Django, Python
*   **数据库：** PostgreSQL (推荐用于 Django 生产环境) 或 SQLite (用于开发环境)
*   **后台任务/调度：** Celery，使用 Redis 或 RabbitMQ 作为消息中间件
*   **前端：** Django 模板, HTML, CSS (可以选择使用 Bootstrap 或 Tailwind CSS 这样的框架来加速样式开发)
*   **AI 处理：** Google Generative AI SDK (和现在使用的相同)
*   **邮件：** Django 的邮件后端或 `smtplib` (和现在使用的相同，封装在 Celery 任务中)

---

**开发计划：**

**第一阶段：项目设置和用户认证**

1.  **初始化 Django 项目：**
    *   设置一个虚拟环境 (例如，使用  `uv init && uv venv`)。
    *   安装 Django: `uv add django`
    *   创建 Django 项目: `django-admin startproject daily_reporter_project`
    *   创建核心应用: `cd daily_reporter_project && python manage.py startapp reporter`
    *   将 `reporter` 添加到 `settings.py` 中的 `INSTALLED_APPS`。
    *   在 `settings.py` 中配置数据库。

2.  **用户模型和认证：**
    *   Django 内置的 `User` 模型最初对于 1-5 个用户是合适的。
    *   实现基本的认证视图 (登录, 登出)。 你可以使用 Django 内置的视图 (`django.contrib.auth.urls`)。
    *   创建登录模板 (`templates/registration/login.html`)。
    *   *可选：* 如果需要，实现用户注册，或者计划最初通过管理界面创建用户。
    *   使用环境变量或 `.env` 文件（使用 `python-dotenv`）安全地存储敏感密钥（例如 Django 的 `SECRET_KEY`）。

3.  **用户设置模型：**
    *   **目标：** 存储用户特定的配置，而不是全局的 `.env` 文件。
    *   在 `reporter/models.py` 中，创建 `UserSettings` 模型：
        *   `user`: `OneToOneField`，连接到 Django 的 `User` 模型。
        *   `gemini_api_key`: `CharField` (安全存储，如果需要，稍后考虑加密)。
        *   `email_signature_name`: `CharField`。
        *   `email_signature_phone`: `CharField`。
        *   `email_from`: `EmailField`。
        *   `email_password`: `CharField` (安全存储，例如，使用 `django-fernet-fields` 或类似方法)。
        *   `email_to`: `TextField` (用于存储逗号分隔的邮件地址)。
        *   `smtp_server`: `CharField`。
        *   `smtp_port`: `IntegerField`。
        *   `schedule_time`: `TimeField` (用于用户首选的发送时间)。
        *   `timezone`: `CharField` (存储用户的时区，例如 'Asia/Shanghai', 默认为 'UTC+8')。
        *   `is_active`: `BooleanField` (用于启用/禁用用户的自动发送)。
    *   运行 `python manage.py makemigrations reporter` 和 `python manage.py migrate`。
    *   将 `UserSettings` 注册到 Django 管理界面 (`reporter/admin.py`) 以方便管理。

4.  **用户资料/设置视图：**
    *   创建一个视图 (`reporter/views.py`)，用 `@login_required` 保护。
    *   创建一个基于 `UserSettings` 模型的 Django 表单 (`reporter/forms.py`)。
    *   创建一个模板 (`templates/reporter/settings.html`)，让用户查看和更新他们的设置。
    *   在视图中处理表单提交，以保存设置。 确保在用户首次访问或注册时为用户创建一个 `UserSettings` 实例。

**第二阶段：核心逻辑集成和手动触发**

1.  **重构现有逻辑：**
    *   将核心逻辑从 `gemini_processor.py`, `email_generator.py` 和 `email_sender.py` 移动到 `reporter` 应用中的可重用函数或类（例如，在 `reporter/services.py` 或单独的文件中）。
    *   修改这些函数/类，使其接受用户特定的设置（作为参数传递或通过 `user` 对象获取），而不是依赖于全局 `CONFIG` 或 `.env`。
    *   调整 `EmailGenerator` 以使用 `UserSettings` 中的签名信息。
    *   调整 `GeminiProcessor` 以使用 `UserSettings` 中的 `gemini_api_key`。
    *   调整 `EmailSender` 以使用 `UserSettings` 中的所有邮件/SMTP 详细信息。

2.  **内容输入：**
    *   向 `UserSettings` 模型添加 `monthly_plan_content`: `TextField`。 运行迁移。
    *   更新 `UserSettings` 表单和模板，包含一个大型文本区域，供用户粘贴/编辑他们的月度计划内容（类似于 `study_today.txt` 中的格式）。
    *   将内容提取逻辑从 `scraper.py` (`extract_content_for_date`) 重构为 `reporter/utils.py` 中的一个实用函数。 这个函数现在将接受*用户存储的文本*和目标日期作为输入。

3.  **报告历史模型：**
    *   **目标：** 跟踪已生成/发送的报告。
    *   在 `reporter/models.py` 中，创建 `ReportHistory` 模型：
        *   `user`: `ForeignKey`，连接到 `User`。
        *   `generation_time`: `DateTimeField` (触发生成的时间)。
        *   `send_time`: `DateTimeField` (null=True, blank=True，实际发送邮件的时间)。
        *   `status`: `CharField` (例如, 'Pending', 'Processing', 'Success', 'Failed')。
        *   `subject`: `CharField`。
        *   `raw_content_used`: `TextField` (提取的特定日期内容)。
        *   `processed_content`: `TextField` (经过 Gemini 处理的内容)。
        *   `email_html`: `TextField` (最终生成的邮件正文)。
        *   `error_message`: `TextField` (null=True, blank=True)。
    *   运行迁移。 注册到管理界面。

4.  **手动触发视图：**
    *   创建一个视图 (例如, `generate_today_report`)，用 `@login_required` 保护。
    *   在用户仪表盘页面 (`templates/reporter/dashboard.html`) 上添加一个按钮，向这个视图发送 POST 请求。
    *   在这个视图中：
        *   获取已登录用户的 `UserSettings` 和 `monthly_plan_content`。
        *   调用重构后的 `extract_content_for_date` 函数，获取今天的日期内容（考虑用户的时区）。
        *   创建一个 `ReportHistory` 记录，状态为 'Processing'。
        *   调用重构后的 `GeminiProcessor`。
        *   调用重构后的 `EmailGenerator`。
        *   调用重构后的 `EmailSender`。
        *   使用结果更新 `ReportHistory` 记录（Success/Failed、内容、错误信息、发送时间）。
        *   使用 Django 的消息框架向用户提供反馈 (例如, "报告已成功生成并发送!" 或 "发送报告失败: [错误]")。
        *   重定向回仪表盘。

5.  **历史显示视图：**
    *   创建一个视图 (`reporter/views.py`, 例如 `report_history`)，用 `@login_required` 保护。
    *   获取已登录用户的 `ReportHistory` 记录，获取最近 7 天的，按 `generation_time` 降序排列。
    *   创建一个模板 (`templates/reporter/history.html`)，在一个表格中显示历史记录（日期、主题、状态、也许可以链接/弹窗查看内容/错误）。

**第三阶段：使用 Celery 进行调度和后台任务**

1.  **设置 Celery 和消息中间件：**
    *   安装 Celery 和一个消息中间件: `pip install celery redis` (或者 `librabbitmq` 用于 RabbitMQ)。
    *   在你的 Django 项目中配置 Celery (创建 `celery.py`，更新 `__init__.py`，在 `settings.py` 中配置消息中间件 URL)。 遵循官方的 Django Celery 集成指南。
    *   确保 Redis (或 RabbitMQ) 服务器正在运行。

2.  **创建 Celery 任务：**
    *   在 `reporter/tasks.py` 中，定义一个 Celery 任务 (例如, `generate_and_send_report_task`)。
    *   这个任务应该接受一个 `user_id` 作为参数。
    *   在任务内部：
        *   使用 `user_id` 获取 `User` 和 `UserSettings`。
        *   执行*整个*报告生成和发送逻辑（提取内容、使用 Gemini 处理、生成邮件、发送邮件），之前在手动触发视图中完成。
        *   至关重要的是，将核心逻辑封装在 `try...except` 代码块中。
        *   在各个阶段创建/更新 `ReportHistory` 记录（Pending -> Processing -> Success/Failed），包含相关的详细信息和错误消息。

3.  **实现调度 (Celery Beat)：**
    *   在你的 `settings.py` 中配置 Celery Beat。
    *   创建一个周期性的 Celery 任务 (例如, `schedule_daily_reports`)，频繁运行 (例如，每 5-10 分钟)。
    *   在 `schedule_daily_reports` 内部：
        *   查询所有活跃的 `UserSettings` (`is_active=True`)。
        *   对于每个用户：
            *   获取他们的首选 `schedule_time` 和 `timezone`。
            *   计算当前时间在用户时区中的时间。
            *   检查当前时间是否与他们的 `schedule_time` 匹配。
            *   **重要：** 检查*今天*是否已为该用户成功处理或正在处理报告（查询 `ReportHistory`）。 这可以防止重复发送。
            *   如果是时间，并且今天没有报告存在/正在处理，则为该 `user_id` 入队 `generate_and_send_report_task`。 使用 `apply_async`，`eta` 略微在将来，或者立即入队。 如果多个任务同时准备就绪，Celery 的工作池将处理排队。

4.  **运行 Worker 和 Beat：**
    *   你需要运行 Celery worker (`celery -A daily_reporter_project worker -l info`) 和 Celery Beat 调度器 (`celery -A daily_reporter_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`)，同时运行你的 Django 开发服务器。 对于生产环境，这些将由 supervisor 或 systemd 管理。

**第四阶段：UI/UX 优化和错误处理**

1.  **改进前端：**
    *   使用 CSS 框架 (Bootstrap, Tailwind) 实现现代的外观。 将它应用到登录、设置、仪表盘和历史记录页面。
    *   使历史记录视图更丰富 (例如，显示内容片段、清晰的错误消息)。
    *   为任务状态添加视觉提示 (例如，为 Success/Failed 添加标记)。

2.  **增强反馈：**
    *   当用户手动触发报告时，考虑使用 AJAX，这样页面就不会完全重新加载，从而提供更快的反馈。
    *   对于计划任务，历史记录页面是主要的反馈机制。 确保它更新得足够快（用户可能需要刷新）。

3.  **强大的错误处理：**
    *   确保所有外部调用（Gemini、SMTP）在 Celery 任务中都有适当的 `try...except` 代码块。
    *   在 `ReportHistory` 模型中清楚地记录错误。
    *   配置 Django 的日志记录以捕获详细的日志以进行调试。

4.  **安全性：**
    *   查看敏感密钥的存储（`gemini_api_key`、`email_password`）。 考虑使用 `django-environ` 进行设置管理，并可能使用 `django-fernet-fields` 或 Django 的密钥管理来加密数据库中的敏感字段。
    *   确保所有需要登录的视图都使用 `@login_required` 或 `LoginRequiredMixin`。
    *   防止常见的 Web 漏洞（CSRF 由 Django 表单处理，如果显示用户生成的内容，请注意 XSS）。

**第五阶段：测试和部署**

1.  **测试：**
    *   为实用函数（内容提取）、服务（邮件生成逻辑）和 Celery 任务编写单元测试（模拟外部 API/SMTP）。
    *   为视图和表单编写集成测试。
2.  **部署：**
    *   选择一个托管服务提供商（例如，Heroku、PythonAnywhere、AWS、DigitalOcean）。
    *   配置一个生产就绪的数据库 (PostgreSQL)。
    *   为 Celery 设置 Redis/RabbitMQ。
    *   使用进程管理器（例如 `supervisor` 或 `systemd`）来运行 Django（通过 Gunicorn/uWSGI）、Celery workers 和 Celery Beat。
    *   在服务器上安全地配置环境变量。
    *   设置静态文件服务（例如，使用 WhiteNoise 或 Nginx）。

---

这个计划提供了一个结构化的方法。 你可以根据优先级调整各个阶段。 记住经常提交你的代码，并彻底测试每个步骤。 祝你好运!