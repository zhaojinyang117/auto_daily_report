**目标：** 创建一个基于 Web 的自动报告工具网页版，支持多用户、独立配置、网页内容管理、可配置的任务调度和历史记录查看，并针对低资源（1C1G）服务器进行优化。

**核心技术栈：**

*   **后端：** Django
*   **包管理器：** uv
*   **数据库：** SQLite（设置简单，适合单服务器、低并发初期，但扩展性较差）。考虑到 1C1G 的限制和未来潜在需求
*   **前端：** Django 模板（标准），可选择性地使用少量 JavaScript（如 HTMX 或 Alpine.js）来增强动态性，避免引入重型框架。
*   **任务队列/调度：**
    *   **方案 A（更简单，适合 1C1G）：** 使用 `django-cron` 或自定义 Django 管理命令，并通过系统的 `cron` 来运行。这避免了额外的进程（如 Celery worker/broker）。
*   **Web 服务器/部署：** Gunicorn + Nginx（标准、高效）。

---

**开发计划（分步进行）**

**阶段一：项目设置与基础用户认证**

1.  √ **初始化 Django 项目：**
    *   √ 建立虚拟环境（例如使用 `venv` 或 `uv`）。
    *   √ 安装 Django：`pip install django python-dotenv`
    *   √ 创建 Django 项目：`django-admin startproject daily_reporter_project .`
    *   √ 创建核心应用：`python manage.py startapp reporter`
    *   √ 在 `settings.py` 的 `INSTALLED_APPS` 中添加 `reporter` 和必要的内置应用（如 `django.contrib.admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`）。
2.  √ **配置数据库：**
    *   √ 选择数据库（QLite）并在 `settings.py` 中进行相应配置。安装必要的驱动程序
3.  √ **基础模型（Models）：**
    *   √ 在 `reporter/models.py` 中定义初始模型。如果需要，可以定义一个自定义的用户 Profile 模型，但初期 Django 内置的 `User` 模型可能足够。
    *   √ 运行初始数据库迁移：`python manage.py makemigrations`, `python manage.py migrate`。
4.  √ **用户认证：**
    *   √ 使用 Django 内置的 `django.contrib.auth.views` 实现基本的登录/登出视图。
    *   √ 为登录 (`registration/login.html`)、登出创建简单的模板，如果后续需要注册功能，也创建相应模板。
    *   √ 在 `reporter/urls.py` 中设置 URL 模式，并将其包含在主 `daily_reporter_project/urls.py` 中。
    *   √ 使用 `@login_required` 装饰器或 `LoginRequiredMixin` 限制对主要应用视图的访问。
5.  √ **管理后台（Admin）：**
    *   √ 创建超级用户：`python manage.py createsuperuser`。
    *   √ 在 `reporter/admin.py` 中注册模型（初期只需注册 `User`）。
    *   √ 访问 `/admin/` 路径来管理用户。

**阶段二：用户特定配置**

1.  √ **用户设置模型：**
    *   √ 在 `reporter/models.py` 中创建 `UserSettings` 模型，并与 `User` 模型建立一对一关联（OneToOneField）。
    *   √ 字段：`gemini_api_key` (安全存储!), `email_signature_name`, `email_signature_phone`, `email_from`, `email_password` (安全存储!), `email_to` (CharField, 处理逗号分隔), `smtp_server`, `smtp_port`, `send_time` (TimeField, 用于调度), `USER_NAME`.env中的用户中文名，用于构建邮件标题的，`is_active` (BooleanField, 用于启用/禁用报告)。
    *   √ **安全提示：** 使用 `django-environ` 或类似库管理应用级密钥（如 Django 的 `SECRET_KEY`）。对于用户密钥（API Key, 密码），考虑在数据库中加密存储（例如使用 `django-cryptography` 或 Fernet 库），或者如果复杂度允许，使用专门的密钥管理服务。*初期可以简单处理，但要为后续增强安全性做计划*。
2.  √ **视图（Views）与表单（Forms）：**
    *   √ 为 `UserSettings` 创建一个 Django `ModelForm`。
    *   √ 创建一个视图 (`UserSettingsUpdateView`)，允许用户编辑自己的设置。确保只有登录用户能编辑自己的设置。可以使用 Django 的通用视图 `UpdateView` 或自定义基于函数的视图。
    *   √ 为设置表单创建一个模板 (`reporter/user_settings_form.html`)。
    *   √ 添加设置视图的 URL 模式。
3.  √ **管理后台集成：**
    *   √ （可选）允许管理员通过 Django Admin 查看/编辑 `UserSettings`。在 `reporter/admin.py` 中注册 `UserSettings` 模型。

**阶段三：基于 Web 的内容管理（替换 Git 获取）**

1.  √ **内容模型：**
    *   √ 在 `reporter/models.py` 中创建 `MonthlyPlan` 模型。
    *   √ 字段：`user` (ForeignKey 关联到 User), `year` (IntegerField), `month` (IntegerField), `content` (TextField)。添加 `unique_together = ('user', 'year', 'month')` 约束，确保每个用户每月只有一个计划。这种方式更接近原始工作流，用户粘贴整个带有 `<YYYY-MM-DD>` 标签结构的文本。
2.  √ **视图与表单：**
    *   √ 为 `MonthlyPlan` 创建一个 `ModelForm`。
    *   √ 创建视图用于：
        *   √ 列出用户的所有月度计划。
        *   √ 创建新的月度计划。
        *   √ 更新已有的月度计划。
    *   √ 使用 Django 的通用视图 (`ListView`, `CreateView`, `UpdateView`) 或自定义视图。
    *   √ 创建模板用于列表展示 (`monthlyplan_list.html`) 和使用 `<textarea>` 编辑内容 (`monthlyplan_form.html`)。
    *   √ 添加相应的 URL 模式。
3.  √ **调整内容提取逻辑：**
    *   √ 将 `scraper.py` 中的 `extract_content_for_date` 逻辑修改为一个工具函数或 `MonthlyPlan` 模型内的方法。它现在将从数据库模型实例的 `content` 字段获取内容，而不是从 Git/URL 获取。

**阶段四：集成核心逻辑（处理与发送）**

1.  √ **重构现有模块：**
    *   √ 将 `gemini_processor.py`, `email_generator.py`, `email_sender.py` 中的核心逻辑移入 `reporter` 应用内的工具函数或类中（例如放在 `reporter/services.py` 或 `reporter/utils.py`）。
    *   √ 修改这些函数，使其接受用户特定的配置（从 `UserSettings` 模型获取）和内容（从 `MonthlyPlan` 模型获取/提取）作为参数，而不是依赖全局 `CONFIG` 或 `.env` 文件。
    *   √ 确保在需要时，使用用户特定的设置来实例化 `GeminiProcessor` 和 `EmailSender` 类。
2.  √ **创建核心报告发送服务：**
    *   √ 在 `reporter/services.py` 中创建一个函数 `send_user_report(user: User, specific_date: date = None)`。
    *   √ 此函数将：
        *   √ 获取目标日期（用户时区的今天日期，或指定的日期）。
        *   √ 获取用户的 `UserSettings`。检查 `is_active` 是否为 True。
        *   √ 获取用户对应目标年月 `MonthlyPlan`。
        *   √ 调用调整后的 `extract_content_for_date` 逻辑，传入计划内容和目标日期。
        *   √ 如果找到内容：
            *   √ 实例化 `GeminiProcessor`（如果 API key 存在）并处理内容。
            *   √ 使用用户设置和处理后的内容实例化 `EmailGenerator`，获取邮件主题和正文。
            *   √ 使用用户设置实例化 `EmailSender` 并发送邮件。
            *   √ 返回成功状态/消息。
        *   √ 如果未找到内容/设置或发生错误，返回错误状态/消息。

**阶段五：调度与后台任务**

1.  √ **选择调度方法：** 在方案 A (cron + manage.py) 。
2.  √ **创建管理命令：**
    *   √ 创建 `reporter/management/commands/send_daily_reports.py`。
    *   √ 该命令将：
        *   √ 遍历所有拥有活动 `UserSettings` (`is_active=True`) 的 `User` 对象。
        *   √ 确定当前时间。
        *   √ 对每个用户，检查其配置的 `send_time` 是否与当前小时匹配（或落在当前执行窗口内）。
        *   √ 如果匹配，调用阶段四创建的 `send_user_report(user)` 服务函数。
        *   √ 记录每个用户的执行结果（成功/失败）（日志记录将在阶段六详述）。
        *   √ **排队（简化处理）：** 按顺序处理用户。如果一个用户失败，记录日志并继续处理下一个。对于 1C1G 服务器，在一个每 5-15 分钟运行一次的 cron 任务中顺序处理 1-5 个用户应该是可行的。初期避免复杂的队列系统。
3.  √ **发送日期设置功能：**
    *   √ 添加 `send_days` 字段到 `UserSettings` 模型，用于存储每月需要发送报告的日期。
    *   √ 在设置界面添加日历选择器，允许用户自定义选择每月的发送日期。
    *   √ 提供快捷按钮（全选、清空、选择工作日）以便于用户快速设置。
    *   √ 在 `send_user_report` 服务中添加验证，确保只在用户选择的日期发送报告。
4.  **系统 Cron Job：**
    *   设置一个系统 `cron` 任务来定期运行该管理命令（例如，每 15 分钟或每小时）。
    *   示例 crontab 条目：
        ```bash
        */15 * * * * /path/to/your/venv/bin/python /path/to/your/project/manage.py send_daily_reports >> /path/to/your/project/logs/cron.log 2>&1
        ```
    *   确保 cron 任务运行时设置了正确的环境变量（特别是如果使用 `.env` 文件管理 Django 设置）。

**阶段六：历史记录、日志与反馈**

1.  **历史/日志模型：**
    *   在 `reporter/models.py` 中创建 `EmailLog` 模型。
    *   字段：`user` (ForeignKey 关联到 User), `send_timestamp` (DateTimeField, auto_now_add=True), `status` (CharField - 例如 'Success', 'Failed', 'No Content'), `subject` (CharField), `content_preview` (TextField, 可选 - 存储生成的部分邮件正文), `error_message` (TextField, nullable=True)。
2.  **更新发送服务：**
    *   修改 `send_user_report` 服务和管理命令，在每次尝试发送后创建 `EmailLog` 条目，记录状态、主题和任何错误信息。
3.  **历史记录视图与模板：**
    *   创建一个视图 (`EmailHistoryListView`) 来显示当前登录用户的 `EmailLog` 条目，按时间戳降序排列。
    *   创建一个模板 (`reporter/email_log_list.html`) 来渲染历史记录表格（时间戳、状态、主题、错误详情）。初期为了性能，可以限制只显示最近一周或一个月的数据。
4.  **用户反馈：**
    *   使用 Django 的消息框架 (`django.contrib.messages`) 在用户执行操作（如保存设置）后提供反馈（例如 `messages.success(request, '设置已成功保存！')`）。
    *   在基础模板中显示这些消息。

**阶段七：完善、优化与部署**

1.  **UI/UX 打磨：** 改进模板，添加导航，确保响应式设计。
2.  **错误处理：** 在整个应用程序中添加更健壮的错误处理和日志记录。
3.  **1C1G 优化：**
    *   **数据库：** 在视图/查询中使用 `select_related` 和 `prefetch_related` 减少数据库查询次数（尤其是在管理命令和历史记录视图中）。为常用查询字段（`user`, `date`, `timestamp`）添加数据库索引。
    *   **模板：** 保持模板简洁，避免在模板中进行过多计算。
    *   **静态文件：** 在生产环境中使用 `whitenoise` 来简化静态文件服务，或者使用 Nginx 处理。
    *   **缓存：** 如果必要，为频繁访问的非关键数据实施缓存（例如 Django 的缓存框架），但初期可以不加。
4.  **安全加固：** 复查安全实践（CSRF、XSS、SQL 注入 - Django 已处理大部分，但仍需注意），确保用户密钥得到妥善处理，生产环境中设置 `DEBUG=False`。
5.  **测试：** 为模型、服务、视图和管理命令编写单元测试和集成测试。
6.  **部署：**
    *   设置 Gunicorn 来运行 Django 应用。
    *   设置 Nginx 作为 Gunicorn 前面的反向代理，处理静态文件和 SSL 终止。
    *   配置生产数据库。
    *   在服务器上设置 cron 任务。
    *   安全地管理环境变量（例如，使用系统环境变量或 git 仓库之外的 `.env` 文件）。
