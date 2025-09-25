# 自动日报生成器

一个自动获取、处理并发送每日学习报告的Python工具。

## 功能特点

- **✨ 今日内容编辑器** - 只修改当日部分，优化编辑体验
- **🖥️ 命令行编辑** - 交互式命令行编辑界面
- **🌐 Web界面编辑** - 直观的浏览器编辑界面  
- 支持月度计划表格式，一次编辑整月内容
- 根据当天日期自动提取对应学习内容
- 智能日期选择：当找不到当天内容时，自动使用最近日期的内容
- 从GitHub获取每日学习内容
- 使用Gemini AI处理和格式化内容
- 自动发送格式化的HTML邮件
- 支持多个收件人
- 详细的日志记录
- 工作日自动执行（周一至周五）
- 使用北京时间（UTC+8）

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/zhaojinyang117/auto_daily_report.git
cd auto_daily_report
```

2. 安装依赖：
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装系统依赖（如果需要）
sudo apt-get update
sudo apt-get install -y at python3-dotenv
```

3. 配置环境变量：
   复制`.env.example`文件到`.env`并填写您自己的配置：
```bash
cp .env.example .env
# 然后编辑.env文件填写您的配置
```

`.env`文件内容示例：
```env
# Gemini API配置
GEMINI_API_KEY=your_api_key

# 个人信息配置
USER_NAME=你的姓名
EMAIL_SIGNATURE_NAME=Your English Name    # 邮件签名显示的英文名
EMAIL_SIGNATURE_PHONE=+86 123 4567 8901  # 邮件签名显示的电话

# 邮件配置
EMAIL_FROM=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_TO=recipient1@example.com,recipient2@example.com

# SMTP配置
SMTP_SERVER=your_smtp_server
SMTP_PORT=465

# 日志配置
LOG_LEVEL=INFO
```

> **安全提示**：`.env`文件包含敏感信息，不会被提交到Git仓库中。请确保不要意外提交该文件。

## 使用方法

### 基本用法

1. fork仓库,在GitHub上更新`study_today.txt`文件内容为月度计划表格式
   (修改`scraper.py`中的`url`变量，指向新的`study_today.txt`文件)

   月度计划表格式示例：
   ```
   <月度计划：2024-04>

   <2024-04-01>
   ## 今日学习内容
   - 学习了Python基础知识
   - 完成了项目设计
   </2024-04-01>

   <2024-04-02>
   ## 今日学习内容
   - 学习了数据库设计
   - 完成了API开发
   </2024-04-02>
   ```

2. 运行程序：
```bash
python main.py
```

### ✨ 新功能：今日内容编辑器

**问题**: 之前修改当日日报需要编辑整个月度计划文件，体验不够好。

**解决方案**: 现在提供专门的今日内容编辑功能，只修改当日部分！

#### 🖥️ 命令行编辑模式
```bash
# 交互式编辑今日内容
python main.py --edit

# 或者直接使用编辑脚本
python edit_today.py
```

特点：
- 只显示和编辑今天的内容
- 自动创建备份文件
- 支持内容预览
- 智能插入新日期条目

#### 🌐 Web界面编辑模式
```bash
# 启动Web编辑器（默认端口8000）
python main.py --web-edit

# 指定端口
python main.py --web-edit --port 8080
```

然后在浏览器中访问 `http://localhost:8000`

Web界面特点：
- 直观的图形界面
- 实时预览功能
- 自动保存草稿
- 响应式设计，支持移动设备

#### 📋 编辑功能优势

✅ **只修改当日部分** - 不需要编辑整个月度文件  
✅ **自动备份** - 编辑前自动创建备份文件  
✅ **安全可靠** - 支持预览，确认后再保存  
✅ **多种模式** - 命令行和Web界面两种选择  
✅ **智能处理** - 自动处理日期不存在的情况  

#### 🎯 使用场景

1. **日常更新**: 当天学习内容有变化时，快速编辑
2. **内容补充**: 发现遗漏内容时，及时添加
3. **错误修正**: 发现内容错误时，快速更正
4. **格式调整**: 优化内容格式和结构

### 📚 完整命令参考

```bash
# 显示帮助信息
python main.py --help

# 运行日报生成和发送（默认行为）
python main.py

# 编辑今日内容（命令行模式）
python main.py --edit

# 启动Web编辑器
python main.py --web-edit

# 启动Web编辑器并指定端口
python main.py --web-edit --port 8080
```

3. 设置定时执行：

   本地执行：

   使用传统方式（crontab）：
   ```bash
   # 给脚本添加执行权限
   chmod +x schedule_tasks.sh

   # 运行定时任务设置脚本
   ./schedule_tasks.sh
   ```

   使用uv环境设置定时任务：
   
   Linux/macOS:
   ```bash
   # 给脚本添加执行权限
   chmod +x schedule_tasks_uv.sh

   # 运行定时任务设置脚本（使用uv虚拟环境）
   ./schedule_tasks_uv.sh
   ```
   
   Windows:
   ```bash
   # 运行Windows下的定时任务设置脚本
   schedule_tasks_uv.bat
   ```

   GitHub Actions执行（推荐）：

   1. 在GitHub仓库设置中添加以下Secrets:
      - `GEMINI_API_KEY`: 你的Gemini API密钥
      - `USER_NAME`: 你的姓名
      - `EMAIL_SIGNATURE_NAME`: 邮件签名中显示的英文名
      - `EMAIL_SIGNATURE_PHONE`: 邮件签名中显示的电话号码
      - `EMAIL_FROM`: 发件人邮箱
      - `EMAIL_PASSWORD`: 邮箱密码或应用专用密码
      - `EMAIL_TO`: 收件人邮箱（多个邮箱用逗号分隔）
      - `SMTP_SERVER`: SMTP服务器地址
      - `SMTP_PORT`: SMTP服务器端口

   2. GitHub Actions会自动按计划运行（工作日每晚8点），或者你可以手动触发工作流程

脚本会：
- 自动安装at命令（如果需要）
- 检查已有任务，避免重复设置
- 设置工作日（周一至周五）的执行计划
- 每天北京时间20:00自动运行程序
- 显示所有已设置的任务

## 文件结构

- `main.py`: 主程序入口
- `scraper.py`: 内容获取模块
- `gemini_processor.py`: AI内容处理模块
- `email_generator.py`: 邮件内容生成器
- `email_sender.py`: 邮件发送模块
- `logger.py`: 日志记录模块
- `config.py`: 配置加载模块
- `.env.example`: 环境变量配置模板（不包含敏感信息）
- `.env`: 实际环境变量配置（包含敏感信息，不提交到仓库）
- `schedule_tasks.sh`: 定时任务设置脚本（传统方式）
- `setup_uv.sh`: Linux/macOS下使用uv的安装脚本
- `setup_uv.bat`: Windows下使用uv的安装脚本
- `schedule_tasks_uv.sh`: Linux/macOS下基于uv环境的定时任务脚本
- `schedule_tasks_uv.bat`: Windows下基于uv环境的定时任务脚本
- `github_action_runner.py`: GitHub Actions运行脚本
- `.github/workflows/`: GitHub Actions工作流配置文件

## 月度计划表功能

本项目支持使用月度计划表格式来一次性编辑整月的日报内容，然后根据当天日期自动提取对应的内容。

### 月度计划表格式

```
<月度计划：YYYY-MM>

<YYYY-MM-DD>
这里是第一天的内容
</YYYY-MM-DD>

<YYYY-MM-DD>
这里是第二天的内容
</YYYY-MM-DD>

...以此类推
```

### 工作原理

1. 在`study_today.txt`文件中按月度计划表格式编辑整月内容
2. 系统根据当前北京时间（UTC+8）自动提取当天的内容
3. 如果找不到当天的内容，会智能查找距离当天最近的日期内容并使用
4. 提取的内容会自动添加正文标签并发送

### 智能日期选择

该功能可以智能处理缺失日期的情况：
- 当月度计划表中没有当天日期的内容时，系统不会返回默认内容
- 而是会查找所有可用日期，计算与当前日期的天数差值
- 自动选择距离当前日期最近的内容
- 在内容前标明使用了哪一天的内容（例如"[使用2024-04-03的内容]"）

这样即使您忘记设置某天的内容，系统也能选择最相关的内容发送，确保日报的连续性和相关性。

### 优势

- 一次编辑，整月使用
- 提前规划学习内容
- 减少每日修改文件的操作
- 支持跨时区自动获取北京时间的内容
- 智能处理缺失日期，确保始终有相关内容发送

## 注意事项

- 确保已正确配置所有必要的环境变量
- `USER_NAME`、`EMAIL_SIGNATURE_NAME`和`EMAIL_SIGNATURE_PHONE`为必填项，没有默认值
- 日志级别`LOG_LEVEL`有默认值`INFO`，可以不设置
- 检查SMTP服务器设置是否正确
- 确保有足够的权限访问日志文件
- 所有定时任务使用北京时间
- 只在工作日（周一至周五）执行
- 需要安装python-dotenv和google-generativeai包
- 不要将包含敏感信息的`.env`文件提交到公开仓库

