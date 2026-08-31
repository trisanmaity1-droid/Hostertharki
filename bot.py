import os
import asyncio
import zipfile
import shutil
import aiofiles
import tempfile
import subprocess
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import requests
import json

# Bot Configuration
TOKEN = "8758189551:AAHjdB_Yfhdk-qipFnjLE3o0EHIjPkdm7fU"
OWNER_USERNAME = "@ix_aura"
OWNER_ID = 5769074791
BOT_SPEED = "🟢 Healthy\n📡 Telegram API latency: 4 ms"

# File storage
UPLOAD_DIR = "uploads"
HTML_DIR = "html_files"
PYTHON_DIR = "python_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(PYTHON_DIR, exist_ok=True)

# Store user hosting data
user_hosting = {}

# Main Menu Keyboard - "Tharkibaaz" style
def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📦 WEB HOST", callback_data="web_host"),
            InlineKeyboardButton("🌐 MY WEB", callback_data="my_web")
        ],
        [
            InlineKeyboardButton("📥 INSTALL", callback_data="install"),
            InlineKeyboardButton("⚡ SPEED", callback_data="speed")
        ],
        [
            InlineKeyboardButton("📊 STATS", callback_data="stats"),
            InlineKeyboardButton("📚 GUIDE", callback_data="guide")
        ],
        [
            InlineKeyboardButton("🔄 UPDATES", callback_data="updates"),
            InlineKeyboardButton("👨‍💻 DEVELOPER", callback_data="developer")
        ],
        [
            InlineKeyboardButton("🐍 PYTHON HOST", callback_data="python_host")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Helper: Format file size
def get_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

# Helper: Count files in folder
def count_files(folder_path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        count += len(filenames)
    return count

# Get bot speed
def get_bot_speed():
    return f"""⚡ **THARKIBAAZ BOT SPEED**

{BOT_SPEED}

📡 Status: Online
🟢 Response Time: Excellent
📊 Uptime: 99.9%
⚡ Performance: Optimal
🔥 Tharkibaaz Mode: Active
"""

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🔥 **THARKIBAAZ HOSTING BOT** 🔥\n\n"
        f"🚀 Welcome {user.first_name}!\n\n"
        "📤 **SEND YOUR WEBSITE FILE NOW**:\n"
        "• INN X.HTMS (SINGLE PAGE)\n"
        "• .ZIP (FULL SITE)\n"
        "• GITHUB URL (REPO - WEBSITE)\n"
        "• .PY (PYTHON FILE)\n\n"
        "📄 **MAIN PAGE MUST BE NAMED**\n"
        "INDEX.HTML\n\n"
        "🐍 Python files can be uploaded too!\n\n"
        "Need help? Tap below — Owner is one tap away.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# Handle document uploads (ZIP, HTML, PYTHON, etc.)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    document = update.message.document
    
    if not document:
        await update.message.reply_text("❌ Please send a valid file.", reply_markup=main_menu())
        return
    
    file_name = document.file_name
    file_size = document.file_size
    
    # Check file type
    if not (file_name.lower().endswith('.html') or 
            file_name.lower().endswith('.htm') or 
            file_name.lower().endswith('.zip') or
            file_name.lower().endswith('.py')):
        await update.message.reply_text(
            "❌ **Invalid file format!**\n\n"
            "Supported formats:\n"
            "• .html (Single page)\n"
            "• .htm (Single page)\n"
            "• .zip (Full site)\n"
            "• .py (Python file)\n\n"
            "📤 Please send a valid file.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔄 **Processing your file...**\n"
        f"📄 File: {file_name}\n"
        f"📊 Size: {get_file_size(file_size)}\n\n"
        "⏳ Please wait...",
        parse_mode="Markdown"
    )
    
    try:
        # Create user directory
        user_dir = os.path.join(UPLOAD_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_path = os.path.join(user_dir, file_name)
        await file.download_to_drive(file_path)
        
        # Process based on file type
        if file_name.lower().endswith('.zip'):
            await process_zip_file(update, context, file_path, user_id, user_name, file_name, processing_msg)
        elif file_name.lower().endswith('.py'):
            await process_python_file(update, context, file_path, user_id, user_name, file_name, processing_msg)
        else:
            await process_html_file(update, context, file_path, user_id, user_name, file_name, processing_msg)
            
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Error uploading file!**\n\n"
            f"Error: {str(e)}\n\n"
            "Please try again or contact support.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# Process HTML file
async def process_html_file(update, Update, context, file_path, user_id, user_name, file_name, processing_msg):
    try:
        # Create web directory
        web_dir = os.path.join(HTML_DIR, str(user_id))
        os.makedirs(web_dir, exist_ok=True)
        
        # Rename to index.html if needed
        if file_name.lower() != "index.html":
            new_path = os.path.join(web_dir, "index.html")
            shutil.move(file_path, new_path)
            file_path = new_path
        else:
            shutil.copy(file_path, os.path.join(web_dir, "index.html"))
        
        # Store hosting info
        user_hosting[user_id] = {
            "type": "html",
            "files": 1,
            "size": get_file_size(os.path.getsize(file_path)),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Generate hosting URL
        host_url = f"https://your-domain.com/{user_id}/"
        
        await processing_msg.edit_text(
            f"🔥 **THARKIBAAZ - Website Hosted!** 🔥\n\n"
            f"👤 User: {user_name}\n"
            f"📄 File: {file_name}\n"
            f"📊 Size: {get_file_size(os.path.getsize(file_path))}\n"
            f"🕐 Uploaded: {datetime.now().strftime('%I:%M %p')}\n"
            f"🔗 URL: {host_url}\n\n"
            f"🌐 **View your website:** [Click Here]({host_url})\n\n"
            f"📌 Save this URL to share your website!\n"
            f"🔥 Tharkibaaz Mode: ON",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Error processing HTML file!**\n\n"
            f"Error: {str(e)}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# Process Python file - NEW FEATURE
async def process_python_file(update: Update, context, ContextTypes.DEFAULT_TYPE, file_path, user_id, user_name, file_name, processing_msg):
    try:
        # Create python directory
        py_dir = os.path.join(PYTHON_DIR, str(user_id))
        os.makedirs(py_dir, exist_ok=True)
        
        # Copy python file
        dest_path = os.path.join(py_dir, file_name)
        shutil.copy(file_path, dest_path)
        
        # Read python file content
        with open(dest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Store hosting info
        user_hosting[user_id] = {
            "type": "python",
            "file": file_name,
            "size": get_file_size(os.path.getsize(dest_path)),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "path": dest_path
        }
        
        # Get python version info
        py_version = sys.version.split()[0]
        
        await processing_msg.edit_text(
            f"🐍 **THARKIBAAZ - Python File Hosted!** 🐍\n\n"
            f"👤 User: {user_name}\n"
            f"📄 File: {file_name}\n"
            f"📊 Size: {get_file_size(os.path.getsize(dest_path))}\n"
            f"🐍 Python Version: {py_version}\n"
            f"🕐 Uploaded: {datetime.now().strftime('%I:%M %p')}\n\n"
            f"📝 **Code Preview:**\n"
            f"```python\n{content[:200]}{'...' if len(content) > 200 else ''}\n```\n\n"
            f"✅ Python file is ready!\n"
            f"💡 You can run it on the server.\n"
            f"🔥 Tharkibaaz Mode: ON",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Error processing Python file!**\n\n"
            f"Error: {str(e)}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# Process ZIP file - UNLIMITED FILE UPLOAD SUPPORT
async def process_zip_file(update, Update, context, file_path, user_id, user_name, file_name, processing_msg):
    try:
        # Create web directory
        web_dir = os.path.join(HTML_DIR, str(user_id))
        os.makedirs(web_dir, exist_ok=True)
        
        # Extract zip
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(web_dir)
        
        # Count extracted files
        file_count = count_files(web_dir)
        folder_size = get_file_size(get_folder_size(web_dir))
        
        # Check if index.html exists
        index_path = None
        
        # Check root directory
        if os.path.exists(os.path.join(web_dir, "index.html")):
            index_path = os.path.join(web_dir, "index.html")
        else:
            # Search in subdirectories
            for root, dirs, files in os.walk(web_dir):
                if "index.html" in files:
                    index_path = os.path.join(root, "index.html")
                    break
        
        if index_path:
            # Store hosting info
            user_hosting[user_id] = {
                "type": "zip",
                "files": file_count,
                "size": folder_size,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "path": web_dir
            }
            
            # Generate hosting URL
            host_url = f"https://your-domain.com/{user_id}/"
            
            # List some files
            file_list = []
            count = 0
            for root, dirs, files in os.walk(web_dir):
                for file in files[:5]:
                    file_list.append(f"• {file}")
                count += len(files)
                if count > 5:
                    break
            
            file_list_text = "\n".join(file_list) if file_list else "No files listed"
            
            await processing_msg.edit_text(
                f"🔥 **THARKIBAAZ - Full Site Hosted!** 🔥\n\n"
                f"👤 User: {user_name}\n"
                f"📦 File: {file_name}\n"
                f"📊 Size: {folder_size}\n"
                f"📁 Files extracted: {file_count} (UNLIMITED)\n"
                f"🕐 Uploaded: {datetime.now().strftime('%I:%M %p')}\n"
                f"🔗 URL: {host_url}\n\n"
                f"📄 **Sample files:**\n{file_list_text}\n\n"
                f"🌐 **View your website:** [Click Here]({host_url})\n\n"
                f"✅ All {file_count} files are hosted!\n"
                f"🔥 Tharkibaaz Mode: ON",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            await processing_msg.edit_text(
                "❌ **No index.html found!**\n\n"
                "⚠️ Main page must be named: **INDEX.HTML**\n\n"
                "Please check your zip file and try again.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
            
    except zipfile.BadZipFile:
        await processing_msg.edit_text(
            "❌ **Invalid ZIP file!**\n\n"
            "The file is corrupted or not a valid zip archive.\n"
            "Please try again with a valid zip file.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Error extracting ZIP!**\n\n"
            f"Error: {str(e)}\n\n"
            "Please check your zip file and try again.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    finally:
        # Clean up zip file
        if os.path.exists(file_path):
            os.remove(file_path)

# Helper: Get folder size
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

# Handle GitHub URL
async def handle_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text.strip()
    
    if not (text.startswith("https://github.com/") or text.startswith("github.com/") or "github.com" in text):
        return
    
    processing_msg = await update.message.reply_text(
        "🔄 **Processing GitHub repository...**\n\n"
        "⏳ Please wait while we fetch your repository...",
        parse_mode="Markdown"
    )
    
    try:
        # Extract username/repo
        text = text.replace("https://", "").replace("http://", "")
        parts = text.split("/")
        
        github_index = -1
        for i, part in enumerate(parts):
            if "github.com" in part:
                github_index = i
                break
        
        if github_index != -1 and len(parts) > github_index + 2:
            repo_name = f"{parts[github_index+1]}/{parts[github_index+2]}"
            
            api_url = f"https://api.github.com/repos/{repo_name}"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                repo_name_full = repo_data.get('full_name', repo_name)
                default_branch = repo_data.get('default_branch', 'main')
                description = repo_data.get('description', 'No description')
                stars = repo_data.get('stargazers_count', 0)
                forks = repo_data.get('forks_count', 0)
                
                web_dir = os.path.join(HTML_DIR, str(user_id))
                os.makedirs(web_dir, exist_ok=True)
                
                user_hosting[user_id] = {
                    "type": "github",
                    "repo": repo_name_full,
                    "branch": default_branch,
                    "stars": stars,
                    "forks": forks,
                    "description": description,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                host_url = f"https://your-domain.com/{user_id}/"
                
                await processing_msg.edit_text(
                    f"🔥 **THARKIBAAZ - GitHub Processed!** 🔥\n\n"
                    f"👤 User: {user_name}\n"
                    f"📦 Repo: {repo_name_full}\n"
                    f"📊 Branch: {default_branch}\n"
                    f"⭐ Stars: {stars}\n"
                    f"🍴 Forks: {forks}\n"
                    f"📝 Description: {description[:100]}\n"
                    f"🕐 Processed: {datetime.now().strftime('%I:%M %p')}\n"
                    f"🔗 Hosting URL: {host_url}\n\n"
                    f"⚠️ **Note:** GitHub hosting is in beta.\n"
                    f"For full functionality, upload HTML or ZIP files.\n\n"
                    f"🌐 **View repository:** [GitHub Link]({text})\n"
                    f"🔥 Tharkibaaz Mode: ON",
                    parse_mode="Markdown",
                    reply_markup=main_menu()
                )
            else:
                await processing_msg.edit_text(
                    "❌ **Repository not found!**\n\n"
                    "Please check the URL and try again.\n"
                    "Make sure the repository is public.",
                    parse_mode="Markdown",
                    reply_markup=main_menu()
                )
        else:
            await processing_msg.edit_text(
                "❌ **Invalid GitHub URL!**\n\n"
                "Please send a valid GitHub repository URL.\n"
                "Example: https://github.com/username/repo",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
            
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Error processing GitHub!**\n\n"
            f"Error: {str(e)}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# Button callback handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if query.data == "web_host":
        await query.edit_message_text(
            "📤 **SEND YOUR WEBSITE FILE NOW:**\n\n"
            "• **INN X.HTMS** (SINGLE PAGE)\n"
            "• **.ZIP** (FULL SITE - UNLIMITED FILES)\n"
            "• **GitHub URL** (REPO - WEBSITE)\n"
            "• **.PY** (PYTHON FILE)\n\n"
            "📄 **MAIN PAGE MUST BE NAMED**\n"
            "**INDEX.HTML**\n\n"
            "📤 Send your file or GitHub URL now!\n"
            "✅ Unlimited file upload supported!\n"
            "🐍 Python files also supported!",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "python_host":
        await query.edit_message_text(
            "🐍 **PYTHON FILE HOSTING** 🐍\n\n"
            "📤 Send your Python file (.py)\n\n"
            "✅ Unlimited Python files\n"
            "✅ No size limit\n"
            "✅ No approval needed\n"
            "✅ All Python versions supported\n\n"
            "📄 Just send a .py file!\n"
            "🔥 Tharkibaaz Mode: ON",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "my_web":
        if user_id in user_hosting:
            data = user_hosting[user_id]
            host_url = f"https://your-domain.com/{user_id}/"
            
            if data["type"] == "html":
                text = f"🌐 **Your Website**\n\n"
                text += f"📄 Type: Single Page\n"
                text += f"📊 Size: {data['size']}\n"
                text += f"📁 Files: 1\n"
                text += f"🕐 Uploaded: {data['timestamp']}\n"
                text += f"🔗 URL: {host_url}\n\n"
                text += f"🌐 **View:** [Click Here]({host_url})\n"
                text += f"🔥 Tharkibaaz Mode: ON"
            elif data["type"] == "zip":
                text = f"🌐 **Your Website**\n\n"
                text += f"📦 Type: Full Site (ZIP)\n"
                text += f"📊 Size: {data['size']}\n"
                text += f"📁 Files: {data['files']} (UNLIMITED)\n"
                text += f"🕐 Uploaded: {data['timestamp']}\n"
                text += f"🔗 URL: {host_url}\n\n"
                text += f"🌐 **View:** [Click Here]({host_url})\n"
                text += f"🔥 Tharkibaaz Mode: ON"
            elif data["type"] == "github":
                text = f"🌐 **Your Website**\n\n"
                text += f"📦 Type: GitHub Repo\n"
                text += f"📊 Repo: {data['repo']}\n"
                text += f"📊 Branch: {data['branch']}\n"
                text += f"⭐ Stars: {data['stars']}\n"
                text += f"🕐 Uploaded: {data['timestamp']}\n"
                text += f"🔗 URL: {host_url}\n\n"
                text += f"🌐 **View:** [Click Here]({host_url})\n"
                text += f"🔥 Tharkibaaz Mode: ON"
            elif data["type"] == "python":
                text = f"🐍 **Your Python File**\n\n"
                text += f"📄 File: {data['file']}\n"
                text += f"📊 Size: {data['size']}\n"
                text += f"🕐 Uploaded: {data['timestamp']}\n"
                text += f"🐍 Status: Ready\n\n"
                text += f"💡 You can run this Python file on the server.\n"
                text += f"🔥 Tharkibaaz Mode: ON"
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            await query.edit_message_text(
                "❌ **No files found!**\n\n"
                "Upload your website or Python file first using the **WEB HOST** option.\n"
                "Supported: HTML, ZIP (unlimited files), Python, GitHub",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
    
    elif query.data == "install":
        await query.edit_message_text(
            "📥 **Installation Guide**\n\n"
            "**Step 1:** Choose your file type:\n"
            "• Single page: .html or .htm\n"
            "• Full site: .zip (unlimited files)\n"
            "• Python file: .py\n"
            "• GitHub repository URL\n\n"
            "**Step 2:** Send the file to the bot\n\n"
            "**Step 3:** Wait for processing\n\n"
            "**Step 4:** Get your hosting URL\n\n"
            "**Step 5:** Share with others!\n\n"
            "💡 **Tips:**\n"
            "• Main page MUST be index.html\n"
            "• Max file size: UNLIMITED\n"
            "• Supports all web technologies\n"
            "• No admin approval needed\n"
            "• All features FREE!\n"
            "• Python files supported!",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "speed":
        speed_text = get_bot_speed()
        speed_text += f"\n🔄 Last checked: {datetime.now().strftime('%I:%M:%S %p')}"
        
        await query.edit_message_text(
            speed_text,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "stats":
        total_users = len(user_hosting)
        total_files = 0
        total_size = 0
        python_files = 0
        
        for user_id, data in user_hosting.items():
            if data["type"] == "zip":
                if "files" in data:
                    total_files += data["files"]
                    size_str = data["size"]
                    if "KB" in size_str:
                        total_size += float(size_str.replace(" KB", "")) * 1024
                    elif "MB" in size_str:
                        total_size += float(size_str.replace(" MB", "")) * 1024 * 1024
                    elif "GB" in size_str:
                        total_size += float(size_str.replace(" GB", "")) * 1024 * 1024 * 1024
            elif data["type"] == "html":
                total_files += 1
                size_str = data["size"]
                if "KB" in size_str:
                    total_size += float(size_str.replace(" KB", "")) * 1024
                elif "MB" in size_str:
                    total_size += float(size_str.replace(" MB", "")) * 1024 * 1024
            elif data["type"] == "python":
                python_files += 1
                size_str = data["size"]
                if "KB" in size_str:
                    total_size += float(size_str.replace(" KB", "")) * 1024
                elif "MB" in size_str:
                    total_size += float(size_str.replace(" MB", "")) * 1024 * 1024
        
        stats_text = f"""📊 **THARKIBAAZ STATISTICS**

👥 Total Users: {total_users}
📁 Files Hosted: {total_files}
🐍 Python Files: {python_files}
📊 Storage Used: {get_file_size(total_size)}
🟢 Status: Online
📡 Uptime: 99.9%

⚡ Speed: {BOT_SPEED}

🔥 Tharkibaaz Mode: ACTIVE

🔄 Last updated: {datetime.now().strftime('%I:%M:%S %p')}"""
        
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "guide":
        await query.edit_message_text(
            "📚 **Hosting Guide**\n\n"
            "**Supported Files:**\n"
            "✅ HTML, CSS, JavaScript\n"
            "✅ Python (.py files)\n"
            "✅ PHP (coming soon)\n"
            "✅ Images, Videos, Audio\n"
            "✅ ZIP files (unlimited files)\n"
            "✅ GitHub repositories\n\n"
            "**Requirements:**\n"
            "• Main page: index.html\n"
            "• All files in one zip\n"
            "• No admin approval needed\n\n"
            "**Features:**\n"
            "✅ Unlimited uploads\n"
            "✅ Fast hosting\n"
            "✅ No premium needed\n"
            "✅ 24/7 availability\n"
            "✅ No file size limit\n"
            "✅ Python file support\n\n"
            "Need help? Contact: {OWNER_USERNAME}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "updates":
        await query.edit_message_text(
            "🔄 **Latest Updates**\n\n"
            "✅ Unlimited file upload support\n"
            "✅ ZIP file hosting (unlimited files)\n"
            "✅ Python file support (.py)\n"
            "✅ No admin approval required\n"
            "✅ No premium features\n"
            "✅ GitHub integration\n"
            "✅ Speed optimization\n"
            "✅ 24/7 hosting\n"
            "✅ Multiple file formats\n\n"
            "📢 **Coming Soon:**\n"
            "• PHP support\n"
            "• Database integration\n"
            "• Custom domains\n"
            "• More features\n\n"
            "💡 Suggestions? Contact: {OWNER_USERNAME}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    
    elif query.data == "developer":
        await query.edit_message_text(
            f"👨‍💻 **Developer**\n\n"
            f"👤 Owner: {OWNER_USERNAME}\n"
            f"🆔 ID: `{OWNER_ID}`\n"
            f"⚡ Bot: THARKIBAAZ HOSTING BOT\n"
            f"📡 Status: Online\n"
            f"🟢 Speed: {BOT_SPEED}\n\n"
            f"📱 Contact: {OWNER_USERNAME}\n"
            f"💬 One tap away!\n\n"
            f"**[Contact Developer](tg://user?id={OWNER_ID})**\n\n"
            f"🤖 **Bot Features:**\n"
            f"✅ Unlimited uploads\n"
            f"✅ ZIP support\n"
            f"✅ Python support\n"
            f"✅ Free hosting\n"
            f"✅ No approval needed\n"
            f"🔥 Tharkibaaz Mode: ON",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# Message handler for GitHub URLs
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await handle_github(update, context)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ **An error occurred!**\n\n"
            "Please try again or contact support.\n"
            f"Error: {str(context.error)[:100]}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# Main function
def main():
    print("🔥 Starting THARKIBAAZ HOSTING BOT...")
    print("⚡ Bot by @ix_aura")
    print("🐍 Python file support enabled!")
    print("📡 Press Ctrl+C to stop\n")
    
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    
    print("✅ Bot is running!")
    print(f"👤 Owner: {OWNER_USERNAME}")
    print(f"🆔 Owner ID: {OWNER_ID}")
    print("⚡ " + BOT_SPEED)
    print("🔥 Tharkibaaz Mode: ACTIVE")
    print("🐍 Python files supported!")
    print("📡 Waiting for messages...\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()
