import os
import time
import re
import logging
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konfigurasi bot
BOT_TOKEN = 'gantibottekan'
CHANNEL_ID = '@gantichlu'  # Channel ID dengan format username
CHANNEL_NUMERIC_ID = None     # Akan diisi saat bot berjalan
GROUP_USERNAME = 'teman_random_grup'  # Username grup tanpa @
GROUP_ID = None       # Akan diisi saat bot berjalan
GROUP_LINK = f'https://t.me/{GROUP_USERNAME}'  # Group link
ADMIN_ID = 1780107438  # Admin ID for receiving logs
MAX_VIDEO_DURATION = 30  # Maximum video duration in seconds
COOLDOWN_TIME = 3 * 60  # 3 minutes in seconds

# Store last message time for each user
last_message_time = {}

# Path to blacklist file
BLACKLIST_FILE = 'blacklist.txt'

# Create blacklist file if it doesn't exist
if not os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, 'w') as f:
        pass

# Helper functions
async def send_log(context: ContextTypes.DEFAULT_TYPE, message: str, is_error: bool = False):
    """Send log messages to admin"""
    try:
        prefix = "❌ ERROR: " if is_error else "ℹ️ INFO: "
        await context.bot.send_message(ADMIN_ID, f"{prefix}{message}")
        if is_error:
            logger.error(message)
        else:
            logger.info(message)
    except Exception as e:
        logger.error(f"Failed to send log: {e}")

async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id, retry_with_username=False, chat_username=None) -> bool:
    """Check if user is a member of a chat with robust error handling"""
    try:
        # Coba dengan ID numerik terlebih dahulu
        try:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            status = chat_member.status
            is_member = status in ['creator', 'administrator', 'member']
            logger.info(f"Membership check for user {user_id} in {chat_id}: {is_member} (status: {status})")
            return is_member
        except Exception as e:
            # Jika gagal dengan ID numerik dan kita punya username, coba dengan username
            if retry_with_username and chat_username:
                logger.info(f"Retrying membership check with username @{chat_username}")
                try:
                    chat_member = await context.bot.get_chat_member(f"@{chat_username}", user_id)
                    status = chat_member.status
                    is_member = status in ['creator', 'administrator', 'member']
                    logger.info(f"Username-based membership check for user {user_id} in @{chat_username}: {is_member} (status: {status})")
                    return is_member
                except Exception as username_error:
                    # Jika kedua metode gagal, log error dan kembalikan False
                    logger.error(f"Both numeric ID and username checks failed: {username_error}")
                    return False
            else:
                # Tidak punya username atau tidak ingin retry, log error dan kembalikan False
                logger.error(f"Membership check failed and no retry attempted: {e}")
                return False
    except Exception as outer_e:
        # Catch any unexpected error in our logic
        logger.error(f"Unexpected error in check_membership: {outer_e}")
        return False

def is_user_blacklisted(user_id: int) -> bool:
    """Check if user is blacklisted"""
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            blacklist = [line.strip() for line in f.readlines() if line.strip()]
        return str(user_id) in blacklist
    except Exception as e:
        logger.error(f"Error checking blacklist: {e}")
        return False

def add_user_to_blacklist(user_id: int) -> bool:
    """Add user to blacklist"""
    try:
        if is_user_blacklisted(user_id):
            return False
        
        with open(BLACKLIST_FILE, 'a') as f:
            f.write(f"{user_id}\n")
        return True
    except Exception as e:
        logger.error(f"Error adding user to blacklist: {e}")
        return False

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    try:
        # Cek apakah pesan diterima di chat privat (bukan grup)
        if update.effective_chat.type != 'private':
            # Abaikan pesan dari grup
            return
            
        user_id = update.effective_user.id
        username = update.effective_user.username or "no username"
        
        # Check if user is blacklisted
        if is_user_blacklisted(user_id):
            await update.message.reply_text("❌ Anda telah dibanned dari menggunakan bot ini.")
            return
        
        # Create channel name without @ if it exists
        channel_name = CHANNEL_ID[1:] if CHANNEL_ID.startswith('@') else CHANNEL_ID
        
        # Create inline keyboard buttons
        keyboard = [
            [InlineKeyboardButton("📢 Bergabung dengan Channel", url=f"https://t.me/{channel_name}")],
            [InlineKeyboardButton("👥 Bergabung dengan Grup", url=GROUP_LINK)],
            [InlineKeyboardButton("✅ Sudah Bergabung - Cek Kembali", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(
            f"👋 <b>Selamat datang di Menfes Video Bot {CHANNEL_ID}!</b>\n\n"
            f"Bot ini akan mengirimkan video Anda ke <b>{CHANNEL_ID}</b>.\n\n"
            "<b>Untuk menggunakan bot ini, Anda harus:</b>\n"
            "1. Bergabung dengan channel dan grup kami\n"
            "2. Memiliki username Telegram\n"
            "3. Kirim video beserta caption ke bot ini (maksimal 30 detik)\n"
            "4. Pastikan konten tidak melanggar aturan komunitas\n\n"
            "Klik tombol di bawah ini untuk bergabung, lalu tekan \"Sudah Bergabung\" setelah selesai.",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        await send_log(context, f"User {user_id} (@{username}) memulai bot")
    except Exception as e:
        await send_log(context, f"Error saat mengirim pesan start: {e}", True)
        try:
            await update.message.reply_text(
                "Selamat datang di Menfes Video Bot! Terjadi kesalahan saat menampilkan pesan selamat datang. "
                "Silakan coba lagi nanti."
            )
        except Exception as reply_err:
            await send_log(context, f"Error saat mengirim pesan fallback: {reply_err}", True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    try:
        # Cek apakah pesan diterima di chat privat (bukan grup)
        if update.effective_chat.type != 'private':
            # Abaikan pesan dari grup
            return
            
        user_id = update.effective_user.id
        username = update.effective_user.username or "no username"
        
        # Check if user is blacklisted
        if is_user_blacklisted(user_id):
            await update.message.reply_text("❌ Anda telah dibanned dari menggunakan bot ini.")
            return
        
        await update.message.reply_html(
            f"ℹ️ <b>Bantuan Penggunaan Menfes Video Bot</b>\n\n"
            f"Bot ini memungkinkan Anda mengirim video ke channel {CHANNEL_ID}.\n\n"
            "<b>Cara penggunaan:</b>\n"
            "1. Kirim video dengan durasi maksimal 30 detik\n"
            "2. Pastikan video memiliki caption/pesan (wajib)\n"
            "3. Anda harus memiliki username Telegram\n"
            "4. Bot akan mengirimkan video Anda ke channel\n\n"
            "<b>Aturan:</b>\n"
            f"• Maksimal durasi video {MAX_VIDEO_DURATION} detik\n"
            "• Video harus memiliki caption\n"
            "• Interval pengiriman 3 menit\n"
            "• Konten tidak boleh melanggar aturan komunitas\n\n"
            "Jika mengalami masalah, silakan hubungi admin grup."
        )
        
        await send_log(context, f"User {user_id} (@{username}) melihat bantuan")
    except Exception as e:
        await send_log(context, f"Error saat mengirim pesan bantuan: {e}", True)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /ban command (admin only)"""
    try:
        # Cek apakah pesan diterima di chat privat (bukan grup)
        if update.effective_chat.type != 'private':
            # Abaikan pesan dari grup
            return
            
        user_id = update.effective_user.id
        
        # Check if sender is admin
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return
        
        # Check if command has parameters
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("⚠️ Format yang benar: /ban [user_id] [alasan]")
            return
        
        user_id_to_ban = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Tidak ada alasan yang diberikan"
        
        # Validate user ID
        if not user_id_to_ban.isdigit():
            await update.message.reply_text("⚠️ User ID harus berupa angka.")
            return
        
        # Add user to blacklist
        success = add_user_to_blacklist(int(user_id_to_ban))
        
        if success:
            await update.message.reply_text(f"✅ User dengan ID {user_id_to_ban} berhasil dibanned.\nAlasan: {reason}")
            await send_log(context, f"Admin {user_id} memban user {user_id_to_ban}. Alasan: {reason}")
        else:
            await update.message.reply_text(f"ℹ️ User dengan ID {user_id_to_ban} sudah ada dalam daftar blacklist.")
    except Exception as e:
        await send_log(context, f"Error saat proses ban user: {e}", True)
        await update.message.reply_text("❌ Terjadi kesalahan saat mencoba memban user.")

# Callback handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Handle different callback data
        if query.data == "check_membership":
            await handle_check_membership(update, context)
        elif query.data == "create_menfes":
            await handle_create_menfes(update, context)
        elif query.data.startswith("like_"):
            await handle_like(update, context)
        elif query.data.startswith("dislike_"):
            await handle_dislike(update, context)
    except Exception as e:
        await send_log(context, f"Error handling callback: {e}", True)
        try:
            await query.answer("❌ Terjadi kesalahan saat memproses permintaan")
        except Exception:
            pass

async def handle_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the check_membership callback"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Check if user is blacklisted
    if is_user_blacklisted(user_id):
        await query.answer("❌ Anda telah dibanned dari menggunakan bot ini.")
        await query.edit_message_text(
            "❌ <b>AKSES DITOLAK</b>\n\n"
            "Anda telah dibanned dari menggunakan bot ini.\n"
            "Silakan hubungi admin untuk informasi lebih lanjut.",
            parse_mode='HTML'
        )
        return
    
    # Check membership - mengkonversi GROUP_ID ke string jika diperlukan
    is_group_member = await check_membership(context, user_id, GROUP_ID)
    is_channel_member = await check_membership(context, user_id, CHANNEL_ID)
    
    await send_log(context, f"Callback check_membership for user {user_id}: Group={is_group_member}, Channel={is_channel_member}")
    
    # If user is member of both
    if is_group_member and is_channel_member:
        keyboard = [[InlineKeyboardButton("📹 Kirim Video Menfes Sekarang", callback_data="create_menfes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.answer("✅ Verifikasi keanggotaan berhasil!")
        await query.edit_message_text(
            "✅ <b>VERIFIKASI BERHASIL</b>\n\n"
            "Anda telah bergabung dengan grup dan channel kami.\n"
            "Sekarang Anda dapat mengirim video menfes.",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        await send_log(context, f"User {user_id} berhasil memverifikasi keanggotaan grup dan channel")
    else:
        # Create buttons for groups/channels that user hasn't joined
        buttons = []
        channel_name = CHANNEL_ID[1:] if CHANNEL_ID.startswith('@') else CHANNEL_ID
        
        if not is_group_member:
            buttons.append([InlineKeyboardButton("👥 Bergabung dengan Grup", url=GROUP_LINK)])
        
        if not is_channel_member:
            buttons.append([InlineKeyboardButton("📢 Bergabung dengan Channel", url=f"https://t.me/{channel_name}")])
        
        buttons.append([InlineKeyboardButton("🔄 Cek Kembali", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await query.answer("⚠️ Anda belum bergabung dengan semua grup/channel yang diperlukan")
        await query.edit_message_text(
            "⚠️ <b>VERIFIKASI GAGAL</b>\n\n"
            "Untuk mengirim menfes, Anda harus bergabung dengan:\n"
            f"{'' if is_group_member else '• Grup kami\n'}"
            f"{'' if is_channel_member else '• Channel kami\n'}\n"
            "Silakan bergabung terlebih dahulu dengan mengklik tombol di bawah ini.\n"
            "Setelah bergabung, klik tombol <b>Cek Kembali</b> untuk verifikasi.",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        await send_log(
            context, 
            f"User {user_id} gagal memverifikasi keanggotaan - masih belum bergabung dengan "
            f"{'' if is_group_member else 'grup'} {'' if is_channel_member else 'channel'}"
        )

async def handle_create_menfes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the create_menfes callback"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.message.reply_html(
        "📹 <b>KIRIM VIDEO MENFES ANDA</b>\n\n"
        "Silakan kirim video yang ingin Anda sampaikan.\n"
        "<b>Perhatian:</b> Video HARUS memiliki caption/pesan.\n\n"
        "<b>Aturan pengiriman:</b>\n"
        f"• Maksimal durasi video {MAX_VIDEO_DURATION} detik\n"
        "• Harus memiliki caption/pesan\n"
        "• Harus memiliki username Telegram\n"
        "• Interval pengiriman 3 menit\n"
        "• Konten tidak boleh melanggar aturan komunitas"
    )
    
    await send_log(context, f"User {user_id} memulai proses pengiriman video menfes")

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the like button callback"""
    query = update.callback_query
    user_id = query.from_user.id
    message_id = query.message.message_id
    
    # Extract original sender ID from callback data
    original_sender_id = query.data.split('_')[1]
    
    # Extract current caption
    current_caption = query.message.caption or ""
    
    # Extract current like/dislike counts
    like_dislike_match = re.search(r'👍 (\d+) \| 👎 (\d+)', current_caption)
    if not like_dislike_match:
        await query.answer("❌ Error: Format caption tidak valid")
        return
    
    likes = int(like_dislike_match.group(1))
    dislikes = int(like_dislike_match.group(2))
    
    # Increment likes
    likes += 1
    
    # Update caption
    new_caption = re.sub(r'👍 \d+ \| 👎 \d+', f'👍 {likes} | 👎 {dislikes}', current_caption)
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("👍 Like", callback_data=f"like_{original_sender_id}"),
            InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{original_sender_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await context.bot.edit_message_caption(
        chat_id=query.message.chat.id,
        message_id=message_id,
        caption=new_caption,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    await query.answer("👍 Anda menyukai video ini!")
    await send_log(context, f"User {user_id} menyukai video dari user {original_sender_id} (Message ID: {message_id})")

async def handle_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the dislike button callback"""
    query = update.callback_query
    user_id = query.from_user.id
    message_id = query.message.message_id
    
    # Extract original sender ID from callback data
    original_sender_id = query.data.split('_')[1]
    
    # Extract current caption
    current_caption = query.message.caption or ""
    
    # Extract current like/dislike counts
    like_dislike_match = re.search(r'👍 (\d+) \| 👎 (\d+)', current_caption)
    if not like_dislike_match:
        await query.answer("❌ Error: Format caption tidak valid")
        return
    
    likes = int(like_dislike_match.group(1))
    dislikes = int(like_dislike_match.group(2))
    
    # Increment dislikes
    dislikes += 1
    
    # Update caption
    new_caption = re.sub(r'👍 \d+ \| 👎 \d+', f'👍 {likes} | 👎 {dislikes}', current_caption)
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("👍 Like", callback_data=f"like_{original_sender_id}"),
            InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{original_sender_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await context.bot.edit_message_caption(
        chat_id=query.message.chat.id,
        message_id=message_id,
        caption=new_caption,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    await query.answer("👎 Anda tidak menyukai video ini")
    await send_log(context, f"User {user_id} tidak menyukai video dari user {original_sender_id} (Message ID: {message_id})")

# Message handlers
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video messages"""
    try:
        # Cek apakah pesan diterima di chat privat (bukan grup)
        if update.effective_chat.type != 'private':
            # Abaikan pesan dari grup
            return
            
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Cek apakah user memiliki username
        if not username:
            await update.message.reply_html(
                "⚠️ <b>USERNAME DIPERLUKAN</b>\n\n"
                "Untuk mengirim menfes, Anda harus memiliki username Telegram.\n"
                "Silakan atur username di pengaturan profil Telegram Anda terlebih dahulu."
            )
            await send_log(context, f"User {user_id} mencoba mengirim video tanpa username")
            return
            
        # Cek apakah ada caption
        caption = update.message.caption
        if not caption or caption.strip() == "":
            await update.message.reply_html(
                "⚠️ <b>CAPTION DIPERLUKAN</b>\n\n"
                "Untuk mengirim menfes, video Anda harus memiliki caption/pesan.\n"
                "Silakan kirim ulang video dengan menambahkan caption."
            )
            await send_log(context, f"User {user_id} (@{username}) mencoba mengirim video tanpa caption")
            return
            
        first_name = update.effective_user.first_name or ""
        last_name = update.effective_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        
        # Check if user is blacklisted
        if is_user_blacklisted(user_id):
            await update.message.reply_text("❌ Anda telah dibanned dari menggunakan bot ini.")
            return
        
        # Cek keanggotaan grup dengan metode yang lebih robust
        is_group_member = await check_membership(
            context, 
            user_id, 
            GROUP_ID, 
            retry_with_username=True, 
            chat_username=GROUP_USERNAME
        )
        
        # Cek keanggotaan channel dengan metode yang lebih robust
        is_channel_member = await check_membership(
            context, 
            user_id, 
            CHANNEL_NUMERIC_ID if CHANNEL_NUMERIC_ID else CHANNEL_ID, 
            retry_with_username=True, 
            chat_username=CHANNEL_ID.replace('@', '') if CHANNEL_ID.startswith('@') else CHANNEL_ID
        )
        
        if not is_group_member or not is_channel_member:
            message_text = "⚠️ <b>AKSES DITOLAK</b>\n\n"
            message_text += "Untuk mengirim menfes, Anda harus bergabung dengan:\n"
            
            if not is_group_member:
                message_text += "• Grup kami\n"
            
            if not is_channel_member:
                message_text += "• Channel kami\n"
            
            message_text += "\nSilakan gunakan perintah /start untuk memulai proses verifikasi."
            
            await update.message.reply_html(message_text)
            return
            
        # Check cooldown
        now = time.time()
        if user_id in last_message_time and (now - last_message_time[user_id] < COOLDOWN_TIME):
            remaining_time = int(COOLDOWN_TIME - (now - last_message_time[user_id]))
            await update.message.reply_html(
                "⏳ <b>MOHON TUNGGU</b>\n\n"
                f"Anda harus menunggu {remaining_time} detik lagi sebelum dapat mengirim video berikutnya."
            )
            return
        
        # Check video duration
        video_duration = update.message.video.duration
        if video_duration > MAX_VIDEO_DURATION:
            await update.message.reply_html(
                "⚠️ <b>DURASI TERLALU PANJANG</b>\n\n"
                f"Durasi video Anda adalah {video_duration} detik.\n"
                f"Maksimal durasi video yang diperbolehkan adalah {MAX_VIDEO_DURATION} detik."
            )
            return
        
        # Format caption baru dengan username dan informasi bot
        formatted_caption = f"📨 <b>MENFES VIDEO</b>\n\n"
        
        if caption:
            formatted_caption += f"<b>Pesan:</b>\n{caption}\n\n"
            
        formatted_caption += f"<i>Dikirim oleh: @{username}</i>\n"
        formatted_caption += f"<i>Via: @TemanRandomMenfes_bot</i>"
        
        # Send video to channel
        sent_message = await context.bot.send_video(
            CHANNEL_ID,
            update.message.video.file_id,
            caption=formatted_caption,
            parse_mode='HTML'
        )
        
        # Update last message time
        last_message_time[user_id] = now
        
        # Send confirmation to sender
        await update.message.reply_html(
            "✅ <b>VIDEO BERHASIL DIKIRIM!</b>\n\n"
            "Video Anda telah berhasil dikirim ke channel.\n"
            "Terima kasih telah menggunakan Menfes Video Bot!"
        )
        
        # Send detailed log to admin
        await context.bot.send_message(
            ADMIN_ID,
            f"📤 <b>VIDEO MENFES TERKIRIM</b>\n\n"
            f"<b>Pengirim:</b>\n"
            f"• ID: {user_id}\n"
            f"• Username: @{username}\n"
            f"• Nama: {full_name}\n\n"
            f"<b>Detail Video:</b>\n"
            f"• Durasi: {video_duration} detik\n"
            f"• Caption: {caption}\n"
            f"• Message ID: {sent_message.message_id}\n"
            f"• Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode='HTML'
        )
        
        await send_log(context, f"User {user_id} (@{username}) mengirim video menfes dengan durasi {video_duration} detik")
    except Exception as e:
        await send_log(context, f"Error saat memproses video: {e}", True)
        await update.message.reply_text("❌ Terjadi kesalahan saat mengirim video Anda. Silakan coba lagi nanti.")
        
        # Check cooldown
        now = time.time()
        if user_id in last_message_time and (now - last_message_time[user_id] < COOLDOWN_TIME):
            remaining_time = int(COOLDOWN_TIME - (now - last_message_time[user_id]))
            await update.message.reply_html(
                "⏳ <b>MOHON TUNGGU</b>\n\n"
                f"Anda harus menunggu {remaining_time} detik lagi sebelum dapat mengirim video berikutnya."
            )
            return
        
        # Check video duration
        video_duration = update.message.video.duration
        if video_duration > MAX_VIDEO_DURATION:
            await update.message.reply_html(
                "⚠️ <b>DURASI TERLALU PANJANG</b>\n\n"
                f"Durasi video Anda adalah {video_duration} detik.\n"
                f"Maksimal durasi video yang diperbolehkan adalah {MAX_VIDEO_DURATION} detik."
            )
            return
        
        # Get caption if any
        caption = update.message.caption or ""
        
        # Create keyboard for like/dislike buttons
        keyboard = [
            [
                InlineKeyboardButton("👍 Like", callback_data=f"like_{user_id}"),
                InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send video to channel
        sent_message = await context.bot.send_video(
            CHANNEL_ID,
            update.message.video.file_id,
            caption=f"{caption}\n\n<i>👍 0 | 👎 0</i>" if caption else "<i>👍 0 | 👎 0</i>",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        # Update last message time
        last_message_time[user_id] = now
        
        # Send confirmation to sender
        await update.message.reply_html(
            "✅ <b>VIDEO BERHASIL DIKIRIM!</b>\n\n"
            "Video Anda telah berhasil dikirim ke channel secara anonim.\n"
            "Terima kasih telah menggunakan Menfes Video Bot!"
        )
        
        # Send detailed log to admin
        await context.bot.send_message(
            ADMIN_ID,
            f"📤 <b>VIDEO MENFES TERKIRIM</b>\n\n"
            f"<b>Pengirim:</b>\n"
            f"• ID: {user_id}\n"
            f"• Username: @{username}\n"
            f"• Nama: {full_name}\n\n"
            f"<b>Detail Video:</b>\n"
            f"• Durasi: {video_duration} detik\n"
            f"• Caption: {caption if caption else '(Tidak ada caption)'}\n"
            f"• Message ID: {sent_message.message_id}\n"
            f"• Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode='HTML'
        )
        
        await send_log(context, f"User {user_id} (@{username}) mengirim video menfes dengan durasi {video_duration} detik")
    except Exception as e:
        await send_log(context, f"Error saat memproses video: {e}", True)
        await update.message.reply_text("❌ Terjadi kesalahan saat mengirim video Anda. Silakan coba lagi nanti.")

async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-video messages"""
    # Cek apakah pesan diterima di chat privat (bukan grup)
    if update.effective_chat.type != 'private':
        # Abaikan pesan dari grup
        return
        
    # Skip if message is a command or video (already handled)
    if update.message.video or (update.message.text and update.message.text.startswith('/')):
        return
        
    try:
        user_id = update.effective_user.id
        
        # Check if user is blacklisted
        if is_user_blacklisted(user_id):
            await update.message.reply_text("❌ Anda telah dibanned dari menggunakan bot ini.")
            return
            
        await update.message.reply_html(
            "📹 <b>PERHATIAN</b>\n\n"
            "Bot ini hanya menerima video menfes.\n"
            f"Silakan kirim video dengan durasi maksimal {MAX_VIDEO_DURATION} detik untuk diteruskan ke channel.\n\n"
            "Gunakan perintah /help untuk informasi lebih lanjut."
        )
    except Exception as e:
        await send_log(context, f"Error saat memproses pesan non-video: {e}", True)

async def set_bot_description(application: Application) -> None:
    """Set bot description and commands on startup"""
    try:
        await application.bot.set_my_description(
            "✨ Menfes Video Bot ✨\n\n"
            "Kirim video ke channel. Aturan:\n"
            f"• Maksimal {MAX_VIDEO_DURATION} detik\n"
            "• Wajib memiliki caption/pesan\n"
            "• Wajib memiliki username Telegram\n"
            "• Interval pengiriman 3 menit\n"
            "• Tidak mengandung konten sensitif\n\n"
            "Cara penggunaan: Kirim video beserta caption sebagai pesan."
        )
        
        await application.bot.set_my_commands([
            ("start", "Mulai bot dan verifikasi keanggotaan"),
            ("help", "Bantuan penggunaan bot"),
            ("ban", "Ban user dari menggunakan bot (admin only)")
        ])
        
        # Dapatkan ID numeric dari channel dan grup yang digunakan
        global CHANNEL_NUMERIC_ID, GROUP_ID
        
        try:
            # Ambil info channel
            channel_info = await application.bot.get_chat(CHANNEL_ID)
            CHANNEL_NUMERIC_ID = channel_info.id
            logger.info(f"Channel ID resolved: {CHANNEL_ID} -> {CHANNEL_NUMERIC_ID}")
            
            # Ambil info grup berdasarkan username
            group_info = await application.bot.get_chat(f"@{GROUP_USERNAME}")
            GROUP_ID = group_info.id
            logger.info(f"Group ID resolved: @{GROUP_USERNAME} -> {GROUP_ID}")
        except Exception as e:
            logger.error(f"Failed to resolve chat IDs: {e}")
        
        logger.info("Bot description and commands set successfully")
    except Exception as e:
        logger.error(f"Error setting bot description and commands: {e}")

def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.ALL, handle_other_messages))
    
    # Set bot description and commands on startup
    application.post_init = set_bot_description
    
    # Start the bot
    logger.info("Starting Menfes Video Bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
