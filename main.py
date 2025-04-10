import os
import random
import time
import json
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, User, ChatJoinRequest, ChatPermissions
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired, UsernameInvalid, PeerIdInvalid
import asyncio
from datetime import datetime
import re
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from typing import Optional
from pyrogram.enums import ChatType
from keepalive import keep_alive
keep_alive()

# Bot Configuration
BOT_TOKEN = "7399953040:AAEYa0H41TKOAH5DWO-sU8rFutByKk777NM"
API_ID = "25056303"
API_HASH = "423f1e11581ff494841681fc66e9c8e6"

# Initialize bot with proper parameters
pr0fess0r_99 = Client(
    "Auto Approved Bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True
)

# Bot Owners and Teams
BOT_OWNERS = [6985505204]
MAINTENANCE_TEAM = set(BOT_OWNERS)

# Support Information
SUPPORT_CHANNEL = "https://t.me/Bot_SOURCEC"
UPDATES_CHANNEL = "https://t.me/Bot_SOURCEC"

# Messages
PROMOTION_MESSAGE = """
🎉 Congratulations! Your request has been approved!

Join our amazing community and enjoy exclusive benefits!

💫 Special Offer: Get premium access to all features!
"""

# Data Storage
DATA_FILE = "bot_data.json"

# Initialize Data Structure
DEFAULT_BOT_DATA = {
    "auto_approve_chats": set(),
    "chat_settings": {},
    "tagging_in_progress": {},
    "tagged_users": {},
    "banned_users": set(),
    "muted_users": set(),
    "welcome_settings": {},
    "welcome_media": {},
    "spam_protection": {},
    "custom_filters": {},
    "quiz_games": {},
    "mafia_games": {},
    "sudo_users": set(),
    "maintenance_team": set(),
    "bot_stats": {
        "start_time": datetime.now().timestamp(),
        "total_approved": 0,
        "total_messages_sent": 0
    }
}

# Feature Flags
AUTO_APPROVE = True
WELCOME_ENABLED = True
FORCE_SUB_CHANNEL = None

# Initialize data storage
bot_data = DEFAULT_BOT_DATA.copy()

# Add START_TIME at the top of the file with other constants
START_TIME = datetime.now()

# Add these constants at the top with other constants
PROMOTION_MESSAGE = "🎉 Congratulations! Your request has been approved!\n\n" \
                   "Join our amazing community and enjoy exclusive benefits!\n\n" \
                   "💫 Special Offer: Get premium access to all features!"

# Update support channels
SUPPORT_CHANNEL = "https://t.me/Bot_SOURCEC"
UPDATES_CHANNEL = "https://t.me/Bot_SOURCEC"

# Add a simple ping command to test if bot is responding
@pr0fess0r_99.on_message(filters.command("ping"))
async def ping_command(client, message):
    try:
        start_time = time.time()
        m = await message.reply_text("Pinging...")
        end_time = time.time()
        
        await m.edit_text(
            f"🏓 Pong!\n"
            f"⏱️ Response Time: {round((end_time - start_time) * 1000)}ms"
        )
    except Exception as e:
        print(f"Error in ping command: {e}")
        await message.reply("❌ Error in ping command")

# Add start command for all users
@pr0fess0r_99.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        
        # Common buttons for all users
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Add me to your group",
                    url=f"https://t.me/{(await client.get_me()).username}?startgroup=true"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Support",
                    url=SUPPORT_CHANNEL
                ),
                InlineKeyboardButton(
                    "❓ Help",
                    callback_data="help_command"
                )
            ]
        ]
        
        # Add owner panel button for bot owners
        if user_id in BOT_OWNERS:
            keyboard.append([InlineKeyboardButton("👑 Owner Panel", callback_data="owner_panel")])
            welcome_text = f"""Hello {first_name} 👋

👑 Welcome back, Bot Owner!

I can help you manage your group by:
• Auto-approving join requests
• Managing group members
• Providing admin tools
• And much more!"""
        else:
            welcome_text = f"""Hello {first_name}!

👋 Welcome to Auto Approve Bot!

I can help you manage your group by:
• Auto-approving join requests
• Managing group members
• Providing admin tools
• And much more!"""
        
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Error in start command: {e}")
        await message.reply("❌ An error occurred while processing the start command.")

# Add help command for all users
@pr0fess0r_99.on_message(filters.command("help"))
async def help_command(client, message):
    """Handle the help command"""
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Commands List", callback_data="help_command")]
        ])
        
        await message.reply_text(
            "Click the button below to see the list of commands:",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in help command: {e}")
        await message.reply("❌ An error occurred while showing help.")

@pr0fess0r_99.on_callback_query(filters.regex("^help_command$"))
async def help_command_callback(client, callback_query):
    help_text = """**🤖 Bot Commands List**

**👥 Basic Commands:**
• /start - Start the bot
• /help - Show this help message
• /ping - Check bot's response time
• /stats - View bot statistics

**🎯 Tagging Commands:**
• /tag [message] [count] - Tag members with emoji buttons
  Example: `/tag Hello everyone 10`
• /stoptag - Stop ongoing tagging process
• /toptag - Show top tagged users
• /resettag - Reset tag statistics

**👮 Admin Commands:**
• /ban - Ban a user from the group
• /unban - Unban a user
• /mute - Mute a user
• /unmute - Unmute a user
• /kick - Kick a user
• /pin - Pin a message
• /unpin - Unpin a message
• /purge - Delete messages in bulk
• /del - Delete a specific message

**⚙️ Group Settings:**
• /approveon - Enable auto-approval
• /approveoff - Disable auto-approval
• /setwelcome - Set custom welcome message
• /refresh - Refresh bot settings
• /checkadmin - Check your admin rights

**🎮 Game Commands:**
• /mafia - Start a Mafia game
• /quiz - Start a Quiz game

**👑 Owner Commands:**
• /broadcast - Send broadcast message
• /addsudo - Add a sudo user
• /delsudo - Remove a sudo user
• /sudolist - List all sudo users

**🛡️ Maintenance Commands:**
• /gban - Global ban a user
• /ungban - Remove global ban
• /gmute - Global mute a user
• /ungmute - Remove global mute

**💡 Welcome Message Variables:**
You can use these in welcome messages:
• {mention} - Mentions the user
• {title} - Group/Channel title
• {first} - User's first name
• {last} - User's last name
• {id} - User ID

**📝 Note:** 
• Some commands require specific admin rights
• Maintenance commands are for authorized users only
• Join @Bot_SOURCEC for updates and support"""

    await callback_query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )

# File storage functions
def save_data():
    """Save bot data to JSON file"""
    try:
        # Convert sets to lists for JSON serialization
        data_to_save = {
            "auto_approve_chats": list(bot_data["auto_approve_chats"]),
            "chat_settings": bot_data["chat_settings"],
            "tagging_in_progress": bot_data["tagging_in_progress"],
            "tagged_users": bot_data["tagged_users"],
            "banned_users": list(bot_data["banned_users"]),
            "muted_users": list(bot_data["muted_users"]),
            "welcome_settings": bot_data["welcome_settings"],
            "welcome_media": bot_data["welcome_media"],
            "spam_protection": bot_data["spam_protection"],
            "custom_filters": bot_data["custom_filters"],
            "quiz_games": bot_data["quiz_games"],
            "mafia_games": bot_data["mafia_games"],
            "sudo_users": list(bot_data["sudo_users"]),
            "maintenance_team": list(bot_data["maintenance_team"]),
            "bot_stats": bot_data["bot_stats"]
        }

        # Save to temporary file first
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(data_to_save, f, indent=4)

        # Replace original file with temporary file
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        os.rename(temp_file, DATA_FILE)

    except Exception as e:
        print(f"Error saving data: {e}")

def load_data():
    """Load bot data from JSON file"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)

                # Convert lists back to sets
                bot_data["auto_approve_chats"] = set(data.get("auto_approve_chats", []))
                bot_data["chat_settings"] = data.get("chat_settings", {})
                bot_data["tagging_in_progress"] = data.get("tagging_in_progress", {})
                bot_data["tagged_users"] = data.get("tagged_users", {})
                bot_data["banned_users"] = set(data.get("banned_users", []))
                bot_data["muted_users"] = set(data.get("muted_users", []))
                bot_data["welcome_settings"] = data.get("welcome_settings", {})
                bot_data["welcome_media"] = data.get("welcome_media", {})
                bot_data["spam_protection"] = data.get("spam_protection", {})
                bot_data["custom_filters"] = data.get("custom_filters", {})
                bot_data["quiz_games"] = data.get("quiz_games", {})
                bot_data["mafia_games"] = data.get("mafia_games", {})
                bot_data["sudo_users"] = set(data.get("sudo_users", []))
                bot_data["maintenance_team"] = set(data.get("maintenance_team", []))
                bot_data["bot_stats"] = data.get("bot_stats", {
                    "start_time": time.time(),
                    "total_approved": 0,
                    "total_messages_sent": 0
                })

                # Update maintenance team with bot owners and sudo users
                bot_data["maintenance_team"].update(BOT_OWNERS)
                bot_data["maintenance_team"].update(bot_data["sudo_users"])
    except Exception as e:
        print(f"Error loading data: {e}")
        # Initialize maintenance team with bot owners if loading fails
        bot_data["maintenance_team"] = set(BOT_OWNERS)

# Utility functions
async def is_maintenance_team(user_id):
    """Check if user is in the maintenance team (owner or sudo)"""
    try:
        # First check if user is a bot owner
        if user_id in BOT_OWNERS:
            return True
            
        # Then check if user is in maintenance team or sudo users
        return (user_id in bot_data.get("maintenance_team", set()) or 
                user_id in bot_data.get("sudo_users", set()))
    except Exception as e:
        print(f"Error in is_maintenance_team: {e}")
        return user_id in BOT_OWNERS

async def check_command_permission(client, message, command_type):
    """Check if user has permission to use a specific command type"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id

        # Map command types to required rights
        command_rights = {
            "ban": "can_restrict_members",
            "mute": "can_restrict_members",
            "pin": "can_pin_messages",
            "delete": "can_delete_messages",
            "invite": "can_invite_users",
            "manage": "can_manage_chat",
            "promote": "can_promote_members",
            "change_info": "can_change_info",
            "manage_video": "can_manage_video_chats",
            "post": "can_post_messages",
            "edit": "can_edit_messages"
        }

        # Check if command type requires specific rights
        if command_type in command_rights:
            return await has_specific_rights(client, chat_id, user_id, command_rights[command_type])

        # Check other permission types
        if command_type == "admin":
            return await is_admin_or_owner(client, chat_id, user_id)
        elif command_type == "owner":
            return user_id in BOT_OWNERS
        elif command_type == "maintenance":
            return await is_maintenance_team(user_id)
        elif command_type == "user":
            return True

        return False
    except Exception as e:
        print(f"Error in check_command_permission: {e}")
        return False

async def is_admin_or_owner(client, chat_id, user_id):
    """Check if user is admin or owner of the chat"""
    try:
        # First check if user is in maintenance team
        if await is_maintenance_team(user_id):
            return True

        # Get the chat member information
        member = await client.get_chat_member(chat_id, user_id)
        status = str(member.status)

        # Check if user is creator or administrator
        is_admin = status in ["ChatMemberStatus.OWNER", "ChatMemberStatus.ADMINISTRATOR", "creator", "administrator"]
        return is_admin
    except Exception as e:
        print(f"Error in is_admin_or_owner: {e}")
        return False

async def is_group_owner(client, chat_id, user_id):
    """Check if user is the owner of the group"""
    try:
        # First check if user is in maintenance team
        if await is_maintenance_team(user_id):
            return True

        # Get the chat member information
        member = await client.get_chat_member(chat_id, user_id)
        status = str(member.status)

        # Check if user is owner
        is_owner = status in ["ChatMemberStatus.OWNER", "creator"]
        return is_owner
    except Exception as e:
        print(f"Error in is_group_owner: {e}")
        return False

async def has_specific_rights(client, chat_id, user_id, right_type):
    """Check if user has specific rights in the chat"""
    try:
        # First check if user is in maintenance team or is bot owner
        if await is_maintenance_team(user_id) or user_id in BOT_OWNERS:
            return True

        # Get the chat member information
        member = await client.get_chat_member(chat_id, user_id)
        status = str(member.status)

        # Check if user is owner (has all rights)
        if status in ["ChatMemberStatus.OWNER", "creator"]:
            return True

        # Check if user is administrator
        if status in ["ChatMemberStatus.ADMINISTRATOR", "administrator"]:
            # Get admin privileges
            privileges = member.privileges

            # Map right types to privilege checks
            right_mapping = {
                "can_restrict_members": privileges.can_restrict_members,
                "can_pin_messages": privileges.can_pin_messages,
                "can_delete_messages": privileges.can_delete_messages,
                "can_invite_users": privileges.can_invite_users,
                "can_manage_chat": privileges.can_manage_chat,
                "can_promote_members": privileges.can_promote_members,
                "can_change_info": privileges.can_change_info,
                "can_manage_video_chats": privileges.can_manage_video_chats,
                "can_post_messages": privileges.can_post_messages,
                "can_edit_messages": privileges.can_edit_messages
            }

            # Check if the requested right exists in the mapping
            if right_type in right_mapping:
                return right_mapping[right_type]

        return False
    except Exception as e:
        print(f"Error in has_specific_rights: {e}")
        return False

async def get_user_info(client, chat_id, user_input, message=None):
    """Get user information from username, user ID, mention, or reply
    
    Args:
        client: The Pyrogram client
        chat_id: The chat ID where the command was issued
        user_input: The user input string to parse
        message: Optional message object containing entities
        
    Returns:
        User object if found, None otherwise
    """
    try:
        # If input is None or empty, return None
        if not user_input:
            return None

        # Handle mentions in the format @username
        if isinstance(user_input, str) and user_input.startswith("@"):
            try:
                return await client.get_users(user_input[1:])
            except Exception as e:
                print(f"Error getting user by username: {e}")

        # Handle text mentions from message entities
        if message and message.entities:
            for entity in message.entities:
                if entity.type == "text_mention":
                    return entity.user

        # Handle mentions that include the full name with ID
        if isinstance(user_input, str):
            mention_pattern = re.compile(r'\[(.*?)\]\(tg://user\?id=(\d+)\)')
            mention_match = mention_pattern.search(user_input)
            if mention_match:
                try:
                    user_id = int(mention_match.group(2))
                    return await client.get_users(user_id)
                except Exception as e:
                    print(f"Error getting user from mention: {e}")

        # Try to get user by ID (extract numbers only)
        if isinstance(user_input, (int, str)):
            try:
                user_id = int(re.sub(r'[^\d]', '', str(user_input)))
                return await client.get_users(user_id)
            except Exception as e:
                print(f"Error getting user by ID: {e}")

        # Try to get user from chat members
        if isinstance(user_input, str):
            clean_input = user_input.lower().strip('@')
            try:
                async for member in client.get_chat_members(chat_id):
                    if member.user.username and member.user.username.lower() == clean_input:
                        return member.user
                    if member.user.first_name and member.user.first_name.lower() == clean_input:
                        return member.user
                    if member.user.id and str(member.user.id) == clean_input:
                        return member.user
            except Exception as e:
                print(f"Error searching chat members: {e}")

        return None
    except Exception as e:
        print(f"Error in get_user_info: {e}")
        return None

async def is_protected_user(user_id):
    """Check if user is protected (maintenance team or bot owner)"""
    try:
        return user_id in bot_data["maintenance_team"] or user_id in BOT_OWNERS
    except Exception as e:
        print(f"Error in is_protected_user: {e}")
        return False

# Update database functions to use file storage
async def save_chat_settings(chat_id):
    """Save chat settings to file storage"""
    try:
        bot_data["chat_settings"][chat_id] = {
            "approve": chat_id in bot_data["auto_approve_chats"],
            "welcome": chat_id in bot_data["welcome_settings"],
            "welcome_media": chat_id in bot_data["welcome_media"],
            "tag_stats": chat_id in bot_data["tagged_users"]
        }
        save_data()
    except Exception as e:
        print(f"Error saving chat settings: {e}")

# Auto-approve and welcome message handlers
@pr0fess0r_99.on_chat_join_request(filters.group | filters.channel)
async def auto_approve(client, message: ChatJoinRequest):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        user = message.from_user

        # Check if auto-approve is enabled
        if chat_id in bot_data["auto_approve_chats"]:
            # Approve the request
            await client.approve_chat_join_request(chat_id, user_id)

            # Get chat info
            chat = await client.get_chat(chat_id)
            chat_title = chat.title

            try:
                # Send welcome and promotion message to user
                welcome_text = f"Hello {user.first_name},\n\nYour Request to Join {chat_title} has been Approved.\n\nSend /start to know more."
                
                # Create keyboard with support channels
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📢 Updates Channel", url=UPDATES_CHANNEL),
                        InlineKeyboardButton("💬 Support Group", url=SUPPORT_CHANNEL)
                    ]
                ])

                # Try to send message with keyboard
                try:
                    await client.send_message(
                        chat_id=user_id,
                        text=welcome_text,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    if "PEER_ID_INVALID" in str(e):
                        # Log the error but don't fail the auto-approve
                        print(f"Could not send DM to user {user_id}: User hasn't started a conversation with the bot")
                    else:
                        # Log other errors
                        print(f"Could not send DM to user {user_id}: {e}")

            except Exception as e:
                print(f"Error in welcome message handling: {e}")

            # Update stats
            bot_data["bot_stats"]["total_approved"] += 1
            bot_data["bot_stats"]["total_messages_sent"] += 1
            save_data()

    except Exception as e:
        print(f"Error in auto-approve: {e}")

@pr0fess0r_99.on_message(filters.command(["setwelcome"]) & filters.group)
async def set_welcome(client, message):
    try:
        # Check if user has change info rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_change_info"):
            await message.reply("❌ You don't have the 'Change Group Info' right to use this command.")
            return

        # Check if message has text or media
        if not message.reply_to_message:
            await message.reply("""❌ Please reply to a message containing the welcome text or media.

✨ **Available Variables:**
• {mention} - Mentions the user
• {title} - Group/Channel title
• {first} - User's first name
• {last} - User's last name
• {id} - User ID

Example: Welcome {mention} to {title}!""")
            return

        reply = message.reply_to_message

        # Initialize welcome settings if not exists
        if message.chat.id not in bot_data["welcome_settings"]:
            bot_data["welcome_settings"][message.chat.id] = {
                "text": "",
                "has_media": False,
                "media_type": None,
                "media_file_id": None
            }

        # Handle text message
        if reply.text or reply.caption:
            bot_data["welcome_settings"][message.chat.id]["text"] = reply.text or reply.caption
            await message.reply("✅ Welcome message has been set! Variables will be replaced when sending welcome messages.")

        # Handle media message
        if reply.photo:
            bot_data["welcome_settings"][message.chat.id]["has_media"] = True
            bot_data["welcome_settings"][message.chat.id]["media_type"] = "photo"
            bot_data["welcome_settings"][message.chat.id]["media_file_id"] = reply.photo.file_id
            await message.reply("✅ Welcome photo has been set!")
        elif reply.video:
            bot_data["welcome_settings"][message.chat.id]["has_media"] = True
            bot_data["welcome_settings"][message.chat.id]["media_type"] = "video"
            bot_data["welcome_settings"][message.chat.id]["media_file_id"] = reply.video.file_id
            await message.reply("✅ Welcome video has been set!")
        elif reply.animation:
            bot_data["welcome_settings"][message.chat.id]["has_media"] = True
            bot_data["welcome_settings"][message.chat.id]["media_type"] = "animation"
            bot_data["welcome_settings"][message.chat.id]["media_file_id"] = reply.animation.file_id
            await message.reply("✅ Welcome animation has been set!")

        # Save settings to file storage
        save_data()
    except Exception as e:
        print(f"Error in setwelcome command: {e}")
        await message.reply("❌ An error occurred while setting welcome message.")

@pr0fess0r_99.on_message(filters.command(["approveon"]) & filters.group)
async def approve_on(client, message):
    try:
        # Check if user has invite users rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_invite_users"):
            await message.reply("❌ You don't have the 'Invite Users' right to use this command.")
            return

        # Update in-memory state
        if message.chat.id not in bot_data["chat_settings"]:
            bot_data["chat_settings"][message.chat.id] = {}
        bot_data["chat_settings"][message.chat.id]["approve"] = True
        bot_data["auto_approve_chats"].add(message.chat.id)

        # Update file storage
        save_data()

        await message.reply("✅ Auto-approval has been enabled for this chat.")
    except Exception as e:
        print(f"Error in approveon command: {e}")

@pr0fess0r_99.on_message(filters.command(["approveoff"]) & (filters.group | filters.channel))
async def approve_off(client, message):
    try:
        # Check if user has remove users rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_invite_users"):
            await message.reply("❌ You don't have the 'Remove Users' right to use this command.")
            return

        # Update in-memory state
        if message.chat.id not in bot_data["chat_settings"]:
            bot_data["chat_settings"][message.chat.id] = {}
        bot_data["chat_settings"][message.chat.id]["approve"] = False
        bot_data["auto_approve_chats"].discard(message.chat.id)

        # Update file storage
        save_data()

        await message.reply("✅ Auto-approval has been disabled for this chat.")
    except Exception as e:
        print(f"Error in approveoff command: {e}")
        await message.reply("❌ Error saving settings. Please try again.")

# Admin command handlers
@pr0fess0r_99.on_message(filters.command(["ban"]) & (filters.group | filters.private))
async def ban_user(client, message):
    try:
        # Check if user has ban rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_restrict_members"):
            await message.reply("❌ You don't have the 'Ban Users' right to use this command.")
            return

        # Get target user info
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            # Get the full text after the command
            user_input = " ".join(message.command[1:])
            target_user = await get_user_info(client, message.chat.id, user_input)
            
            # If not found, try to get from entities
            if not target_user and message.entities:
                for entity in message.entities:
                    if entity.type in ["text_mention", "mention"]:
                        if entity.type == "text_mention":
                            target_user = entity.user
                            break
                        elif entity.type == "mention":
                            username = message.text[entity.offset:entity.offset + entity.length]
                            try:
                                target_user = await client.get_users(username.strip("@"))
                                break
                            except:
                                continue

        if not target_user:
            await message.reply(
                "❌ User not found. Please use one of these methods:\n"
                "1. Reply to the user's message with /ban\n"
                "2. Use /ban @username\n"
                "3. Use /ban followed by the user's ID\n"
                "4. Tag/mention the user with /ban"
            )
            return

        # Check if target is protected
        if await is_protected_user(target_user.id):
            await message.reply("❌ You cannot ban a maintenance team member or bot owner.")
            return

        try:
            # Check if bot has admin rights
            bot_member = await client.get_chat_member(message.chat.id, "me")
            if not bot_member.privileges.can_restrict_members:
                await message.reply("❌ I don't have permission to ban users in this chat. Please make me an admin with ban rights.")
                return

            # Ban the user
            await client.ban_chat_member(message.chat.id, target_user.id)
            bot_data["banned_users"].add(target_user.id)
            
            # Send ban confirmation with user details
            ban_msg = f"✅ User has been banned successfully!\n\n"
            ban_msg += f"👤 Banned User: {target_user.mention}\n"
            ban_msg += f"🆔 User ID: `{target_user.id}`\n"
            ban_msg += f"👮 Banned By: {message.from_user.mention}"
            
            await message.reply(ban_msg)
            save_data()
        except Exception as e:
            if "CHAT_ADMIN_REQUIRED" in str(e):
                await message.reply("❌ I don't have permission to ban users in this chat. Please make me an admin with ban rights.")
            else:
                print(f"Error in ban command: {e}")
                await message.reply("❌ An error occurred while processing the ban command.")
    except Exception as e:
        print(f"Error in ban command: {e}")
        await message.reply("❌ An error occurred while processing the ban command.")

@pr0fess0r_99.on_message(filters.command(["unban"]) & (filters.group | filters.private))
async def unban_user(client, message):
    try:
        # Check if user has ban rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_restrict_members"):
            await message.reply("❌ You don't have the 'Ban Users' right to use this command.")
            return

        # Get target user info
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            # Get the full text after the command
            user_input = " ".join(message.command[1:])
            target_user = await get_user_info(client, message.chat.id, user_input)
            
            # If not found, try to get from entities
            if not target_user and message.entities:
                for entity in message.entities:
                    if entity.type in ["text_mention", "mention"]:
                        if entity.type == "text_mention":
                            target_user = entity.user
                            break
                        elif entity.type == "mention":
                            username = message.text[entity.offset:entity.offset + entity.length]
                            try:
                                target_user = await client.get_users(username.strip("@"))
                                break
                            except:
                                continue

        if not target_user:
            await message.reply(
                "❌ User not found. Please use one of these methods:\n"
                "1. Reply to the user's message with /unban\n"
                "2. Use /unban @username\n"
                "3. Use /unban followed by the user's ID\n"
                "4. Tag/mention the user with /unban"
            )
            return

        # Unban the user
        try:
            await client.unban_chat_member(
                message.chat.id, 
                target_user.id
            )
            
            # Remove from banned users list
            bot_data["banned_users"].discard(target_user.id)
            save_data()

            # Send unban confirmation with user details
            unban_msg = f"✅ User has been unbanned successfully!\n\n"
            unban_msg += f"👤 Unbanned User: {target_user.mention}\n"
            unban_msg += f"🆔 User ID: `{target_user.id}`\n"
            unban_msg += f"👮 Unbanned By: {message.from_user.mention}"
            
            await message.reply(unban_msg)

            # Try to notify the user
            try:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✨ Join Group", url=f"https://t.me/{message.chat.username}")]
                ])
                
                await client.send_message(
                    target_user.id,
                    f"✅ You have been unbanned from {message.chat.title}!\n"
                    f"You can now join the group again.",
                    reply_markup=keyboard
                )
            except:
                pass  # Don't worry if we can't message the user

        except Exception as e:
            print(f"Error unbanning user: {e}")
            await message.reply("❌ Failed to unban the user. Please make sure I have the necessary permissions.")
            
    except Exception as e:
        print(f"Error in unban command: {e}")
        await message.reply("❌ An error occurred while processing the unban command.")

@pr0fess0r_99.on_message(filters.command(["mute"]) & (filters.group | filters.private))
async def mute_user(client, message):
    try:
        # Check if user has restrict rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_restrict_members"):
            await message.reply("❌ You don't have the 'Restrict Users' right to use this command.")
            return

        # Get target user info
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            # Get the full text after the command
            user_input = " ".join(message.command[1:])
            target_user = await get_user_info(client, message.chat.id, user_input)
            
            # If not found, try to get from entities
            if not target_user and message.entities:
                for entity in message.entities:
                    if entity.type in ["text_mention", "mention"]:
                        if entity.type == "text_mention":
                            target_user = entity.user
                            break
                        elif entity.type == "mention":
                            username = message.text[entity.offset:entity.offset + entity.length]
                            try:
                                target_user = await client.get_users(username.strip("@"))
                                break
                            except:
                                continue

        if not target_user:
            await message.reply(
                "❌ User not found. Please use one of these methods:\n"
                "1. Reply to the user's message with /mute\n"
                "2. Use /mute @username\n"
                "3. Use /mute followed by the user's ID\n"
                "4. Tag/mention the user with /mute"
            )
            return

        # Check if target is protected
        if await is_protected_user(target_user.id):
            await message.reply("❌ You cannot mute a maintenance team member or bot owner.")
            return

        # Mute the user
        await client.restrict_chat_member(
            message.chat.id,
            target_user.id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        
        # Send mute confirmation with user details
        mute_msg = f"✅ User has been muted successfully!\n\n"
        mute_msg += f"👤 Muted User: {target_user.mention}\n"
        mute_msg += f"🆔 User ID: `{target_user.id}`\n"
        mute_msg += f"👮 Muted By: {message.from_user.mention}"
        
        await message.reply(mute_msg)
    except Exception as e:
        print(f"Error in mute command: {e}")
        await message.reply("❌ An error occurred while processing the mute command.")

@pr0fess0r_99.on_message(filters.command(["unmute"]) & (filters.group | filters.private))
async def unmute_user(client, message):
    try:
        # Check if user has restrict rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_restrict_members"):
            await message.reply("❌ You don't have the 'Restrict Users' right to use this command.")
            return

        # Get target user info
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            # Get the full text after the command
            user_input = " ".join(message.command[1:])
            target_user = await get_user_info(client, message.chat.id, user_input)
            
            # If not found, try to get from entities
            if not target_user and message.entities:
                for entity in message.entities:
                    if entity.type in ["text_mention", "mention"]:
                        if entity.type == "text_mention":
                            target_user = entity.user
                            break
                        elif entity.type == "mention":
                            username = message.text[entity.offset:entity.offset + entity.length]
                            try:
                                target_user = await client.get_users(username.strip("@"))
                                break
                            except:
                                continue

        if not target_user:
            await message.reply(
                "❌ User not found. Please use one of these methods:\n"
                "1. Reply to the user's message with /unmute\n"
                "2. Use /unmute @username\n"
                "3. Use /unmute followed by the user's ID\n"
                "4. Tag/mention the user with /unmute"
            )
            return

        # Check if target is protected
        if await is_protected_user(target_user.id):
            await message.reply("❌ You cannot unmute a maintenance team member or bot owner.")
            return

        try:
            # First try to get chat member to check if they're muted
            member = await client.get_chat_member(message.chat.id, target_user.id)
            if member.permissions.can_send_messages:
                await message.reply("❌ This user is not muted.")
                return
        except Exception:
            pass  # Continue with unmute attempt

        # Unmute the user
        try:
            await client.restrict_chat_member(
                message.chat.id,
                target_user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            
            # Remove from muted users list if globally muted
            bot_data["muted_users"].discard(target_user.id)
            save_data()

            # Send unmute confirmation with user details
            unmute_msg = f"✅ User has been unmuted successfully!\n\n"
            unmute_msg += f"👤 Unmuted User: {target_user.mention}\n"
            unmute_msg += f"🆔 User ID: `{target_user.id}`\n"
            unmute_msg += f"👮 Unmuted By: {message.from_user.mention}"
            
            await message.reply(unmute_msg)

            # Try to notify the user
            try:
                await client.send_message(
                    target_user.id,
                    f"✅ You have been unmuted in {message.chat.title}!"
                )
            except:
                pass  # Don't worry if we can't message the user

        except Exception as e:
            print(f"Error unmuting user: {e}")
            await message.reply("❌ Failed to unmute the user. Please make sure I have the necessary permissions.")
            
    except Exception as e:
        print(f"Error in unmute command: {e}")
        await message.reply("❌ An error occurred while processing the unmute command.")

@pr0fess0r_99.on_message(filters.command(["kick"]) & (filters.group | filters.private))
async def kick_user(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "admin"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get chat_id from message or callback data
        chat_id = message.chat.id
        if message.chat.type == "private":
            if hasattr(message, "callback_data") and "_" in message.callback_data:
                chat_id = int(message.callback_data.split("_")[-1])
            else:
                await message.reply("❌ Please select a chat to manage first.")
                return

        # Get target user info
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user_input = message.command[1]
            target_user = await get_user_info(client, chat_id, user_input)

        if not target_user:
            await message.reply("❌ User not found. Please provide a valid username, user ID, or reply to a message.")
            return

        # Check if target is protected
        if await is_protected_user(target_user.id):
            await message.reply("❌ You cannot kick a maintenance team member or bot owner.")
            return

        # Kick the user
        await client.ban_chat_member(chat_id, target_user.id)
        await client.unban_chat_member(chat_id, target_user.id)
        await message.reply(f"✅ {target_user.mention} has been kicked.")
    except Exception as e:
        print(f"Error in kick command: {e}")
        await message.reply("❌ An error occurred while processing the kick command.")

@pr0fess0r_99.on_message(filters.command(["pin"]) & (filters.group | filters.private))
async def pin_message(client, message):
    try:
        # Check if user has pin rights
        if not await has_specific_rights(client, message.chat.id, message.from_user.id, "can_pin_messages"):
            await message.reply("❌ You don't have the 'Pin Messages' right to use this command.")
            return

        if not message.reply_to_message:
            await message.reply("❌ Please reply to the message you want to pin.")
            return

        # Pin the message
        await client.pin_chat_message(message.chat.id, message.reply_to_message.id)
        await message.reply("✅ Message has been pinned.")
    except Exception as e:
        print(f"Error in pin command: {e}")
        await message.reply("❌ An error occurred while processing the pin command.")

@pr0fess0r_99.on_message(filters.command(["unpin"]) & (filters.group | filters.private))
async def unpin_message(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "admin"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get chat_id from message or callback data
        chat_id = message.chat.id
        if message.chat.type == "private":
            if hasattr(message, "callback_data") and "_" in message.callback_data:
                chat_id = int(message.callback_data.split("_")[-1])
            else:
                await message.reply("❌ Please select a chat to manage first.")
                return

        # Unpin the message
        await client.unpin_chat_message(chat_id)
        await message.reply("✅ Message has been unpinned.")
    except Exception as e:
        print(f"Error in unpin command: {e}")
        await message.reply("❌ An error occurred while processing the unpin command.")

@pr0fess0r_99.on_message(filters.command(["purge"]) & (filters.group | filters.private))
async def purge_messages(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "admin"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get chat_id from message or callback data
        chat_id = message.chat.id
        if message.chat.type == "private":
            if hasattr(message, "callback_data") and "_" in message.callback_data:
                chat_id = int(message.callback_data.split("_")[-1])
            else:
                await message.reply("❌ Please select a chat to manage first.")
                return

        if not message.reply_to_message:
            await message.reply("❌ Please reply to the first message of the range you want to delete.")
            return

        # Delete messages
        messages_to_delete = []
        async for msg in client.get_chat_history(chat_id, limit=100):
            if msg.id <= message.reply_to_message.id:
                messages_to_delete.append(msg.id)
            if msg.id == message.id:
                break

        await client.delete_messages(chat_id, messages_to_delete)
        await message.reply(f"✅ Deleted {len(messages_to_delete)} messages.")
    except Exception as e:
        print(f"Error in purge command: {e}")
        await message.reply("❌ An error occurred while processing the purge command.")

@pr0fess0r_99.on_message(filters.command(["del"]) & (filters.group | filters.private))
async def delete_message(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "admin"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get chat_id from message or callback data
        chat_id = message.chat.id
        if message.chat.type == "private":
            if hasattr(message, "callback_data") and "_" in message.callback_data:
                chat_id = int(message.callback_data.split("_")[-1])
            else:
                await message.reply("❌ Please select a chat to manage first.")
                return

        if not message.reply_to_message:
            await message.reply("❌ Please reply to the message you want to delete.")
            return

        # Delete the message
        await client.delete_messages(chat_id, message.reply_to_message.id)
        await message.delete()
    except Exception as e:
        print(f"Error in del command: {e}")
        await message.reply("❌ An error occurred while processing the delete command.")

# Maintenance team command handlers
@pr0fess0r_99.on_message(filters.command(["gban"]) & filters.private)
async def global_ban(client, message):
    try:
        user_id = message.from_user.id
        
        # Check if user is maintenance team
        if not await is_maintenance_team(user_id):
            await message.reply("❌ Only maintenance team members can use this command!")
            return

        # Get target user and reason
        target_user = None
        reason = "No reason provided"

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else reason
        elif len(message.command) > 1:
            user_input = message.command[1]
            try:
                target_user = await client.get_users(user_input)
                reason = " ".join(message.command[2:]) if len(message.command) > 2 else reason
            except:
                pass

        if not target_user:
            await message.reply(
                "❌ Please specify the user:\n"
                "1. Reply to their message with /gban [reason]\n"
                "2. Use /gban @username [reason]\n"
                "3. Use /gban user_id [reason]"
            )
            return

        # Check if user is protected
        if await is_maintenance_team(target_user.id):
            await message.reply("❌ Cannot ban protected users (Bot owners/Maintenance team)!")
            return

        # Check if already banned
        if target_user.id in bot_data.get("banned_users", set()):
            await message.reply("❌ This user is already globally banned!")
            return

        # Initialize banned_users if not exists
        if "banned_users" not in bot_data:
            bot_data["banned_users"] = set()

        # Send initial status
        status_msg = await message.reply(
            f"🚫 Starting global ban process for {target_user.mention}...\n"
            f"• Reason: {reason}\n"
            "• Status: Processing..."
        )

        # Add to banned users
        bot_data["banned_users"].add(target_user.id)
        
        # Store ban info
        if "gban_info" not in bot_data:
            bot_data["gban_info"] = {}
        
        bot_data["gban_info"][target_user.id] = {
            "banned_by": message.from_user.id,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Ban from all chats
        success = 0
        failed = 0
        
        for chat_id in bot_data.get("auto_approve_chats", set()):
            try:
                await client.ban_chat_member(chat_id, target_user.id)
                success += 1
            except Exception as e:
                print(f"Failed to ban in {chat_id}: {e}")
                failed += 1

        # Save to database
        save_data()

        # Send final status
        await status_msg.edit_text(
            f"✅ Global Ban Successfully Applied!\n\n"
            f"👤 Banned User: {target_user.mention}\n"
            f"🆔 User ID: `{target_user.id}`\n"
            f"📝 Reason: {reason}\n"
            f"👮 Banned By: {message.from_user.mention}\n\n"
            f"📊 Ban Status:\n"
            f"• Success: {success} chats\n"
            f"• Failed: {failed} chats"
        )

    except Exception as e:
        print(f"Error in gban: {e}")
        await message.reply("❌ An error occurred while processing the global ban.")

@pr0fess0r_99.on_message(filters.command(["ungban"]) & filters.private)
async def global_unban(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "maintenance"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get target user info and reason
        target_user = None
        reason = "No reason provided"
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else reason
        elif len(message.command) > 1:
            user_input = message.command[1]
            target_user = await get_user_info(client, message.chat.id, user_input)
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else reason

        if not target_user:
            await message.reply("❌ User not found. Please provide a valid username, user ID, or reply to a message.")
            return

        # Check if user was banned
        if target_user.id not in bot_data.get("banned_users", set()):
            await message.reply("❌ This user is not globally banned.")
            return

        # Remove from banned users
        bot_data["banned_users"].discard(target_user.id)
        if "gban_info" in bot_data and target_user.id in bot_data["gban_info"]:
            del bot_data["gban_info"][target_user.id]

        # Unban from all chats
        success = 0
        failed = 0
        for chat_id in bot_data.get("auto_approve_chats", set()):
            try:
                await client.unban_chat_member(chat_id, target_user.id)
                success += 1
            except:
                failed += 1

        # Save to database
        save_data()

        # Send confirmation message
        await message.reply(
            f"✅ Global Unban Successfully Applied!\n\n"
            f"👤 User: {target_user.mention}\n"
            f"🆔 User ID: `{target_user.id}`\n"
            f"📝 Reason: {reason}\n\n"
            f"📊 Unban Status:\n"
            f"• Success: {success} chats\n"
            f"• Failed: {failed} chats"
        )

        # Notify other maintenance team members
        for admin_id in bot_data.get("maintenance_team", set()):
            if admin_id != message.from_user.id:
                try:
                    await client.send_message(
                        admin_id,
                        f"✅ Global Unban Alert!\n\n"
                        f"User: {target_user.mention}\n"
                        f"Unbanned by: {message.from_user.mention}\n"
                        f"Reason: {reason}"
                    )
                except:
                    continue

    except Exception as e:
        print(f"Error in ungban command: {e}")
        await message.reply("❌ An error occurred while processing the global unban command.")

@pr0fess0r_99.on_message(filters.command(["gmute"]) & filters.private)
async def global_mute(client, message):
    try:
        user_id = message.from_user.id
        
        # Check if user is maintenance team
        if not await is_maintenance_team(user_id):
            await message.reply("❌ Only maintenance team members can use this command!")
            return

        # Get target user and reason
        target_user = None
        reason = "No reason provided"

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else reason
        elif len(message.command) > 1:
            user_input = message.command[1]
            try:
                target_user = await client.get_users(user_input)
                reason = " ".join(message.command[2:]) if len(message.command) > 2 else reason
            except:
                pass

        if not target_user:
            await message.reply(
                "❌ Please specify the user:\n"
                "1. Reply to their message with /gmute [reason]\n"
                "2. Use /gmute @username [reason]\n"
                "3. Use /gmute user_id [reason]"
            )
            return

        # Check if user is protected
        if await is_maintenance_team(target_user.id):
            await message.reply("❌ Cannot mute protected users (Bot owners/Maintenance team)!")
            return

        # Check if already muted
        if target_user.id in bot_data.get("muted_users", set()):
            await message.reply("❌ This user is already globally muted!")
            return

        # Send initial status
        status_msg = await message.reply(
            f"🔇 Starting global mute process for {target_user.mention}...\n"
            f"• Reason: {reason}\n"
            "• Status: Processing..."
        )

        # Add to muted users
        bot_data["muted_users"].add(target_user.id)
        
        # Store mute info
        if "gmute_info" not in bot_data:
            bot_data["gmute_info"] = {}
        
        bot_data["gmute_info"][target_user.id] = {
            "muted_by": message.from_user.id,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Mute in all chats
        success = 0
        failed = 0
        
        for chat_id in bot_data.get("auto_approve_chats", set()):
            try:
                await client.restrict_chat_member(
                    chat_id,
                    target_user.id,
                    ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False
                    )
                )
                success += 1
            except Exception as e:
                print(f"Failed to mute in {chat_id}: {e}")
                failed += 1

        # Save to database
        save_data()

        # Send final status
        await status_msg.edit_text(
            f"✅ Global Mute Successfully Applied!\n\n"
            f"👤 Muted User: {target_user.mention}\n"
            f"🆔 User ID: `{target_user.id}`\n"
            f"📝 Reason: {reason}\n"
            f"👮 Muted By: {message.from_user.mention}\n\n"
            f"📊 Mute Status:\n"
            f"• Success: {success} chats\n"
            f"• Failed: {failed} chats"
        )

        # Notify maintenance team
        for admin_id in bot_data.get("maintenance_team", set()):
            if admin_id != message.from_user.id:
                try:
                    await client.send_message(
                        admin_id,
                        f"🔇 Global Mute Alert!\n\n"
                        f"• User: {target_user.mention}\n"
                        f"• ID: `{target_user.id}`\n"
                        f"• Muted By: {message.from_user.mention}\n"
                        f"• Reason: {reason}\n"
                        f"• Success: {success} chats\n"
                        f"• Failed: {failed} chats"
                    )
                except:
                    continue

    except Exception as e:
        print(f"Error in gmute: {e}")
        await message.reply("❌ An error occurred while processing the global mute.")

@pr0fess0r_99.on_message(filters.command(["ungmute"]) & filters.private)
async def global_unmute(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "maintenance"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get target user info and reason
        target_user = None
        reason = "No reason provided"
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else reason
        elif len(message.command) > 1:
            user_input = message.command[1]
            target_user = await get_user_info(client, message.chat.id, user_input)
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else reason

        if not target_user:
            await message.reply("❌ User not found. Please provide a valid username, user ID, or reply to a message.")
            return

        # Check if user was muted
        if target_user.id not in bot_data.get("muted_users", set()):
            await message.reply("❌ This user is not globally muted.")
            return

        # Remove from muted users
        bot_data["muted_users"].discard(target_user.id)
        if "gmute_info" in bot_data and target_user.id in bot_data["gmute_info"]:
            del bot_data["gmute_info"][target_user.id]

        # Unmute in all chats
        success = 0
        failed = 0
        for chat_id in bot_data.get("auto_approve_chats", set()):
            try:
                await client.restrict_chat_member(
                    chat_id,
                    target_user.id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
                success += 1
            except:
                failed += 1

        # Save to database
        save_data()

        # Send confirmation message
        await message.reply(
            f"✅ Global Unmute Successfully Applied!\n\n"
            f"👤 User: {target_user.mention}\n"
            f"🆔 User ID: `{target_user.id}`\n"
            f"📝 Reason: {reason}\n\n"
            f"📊 Unmute Status:\n"
            f"• Success: {success} chats\n"
            f"• Failed: {failed} chats"
        )

        # Notify other maintenance team members
        for admin_id in bot_data.get("maintenance_team", set()):
            if admin_id != message.from_user.id:
                try:
                    await client.send_message(
                        admin_id,
                        f"🔊 Global Unmute Alert!\n\n"
                        f"User: {target_user.mention}\n"
                        f"Unmuted by: {message.from_user.mention}\n"
                        f"Reason: {reason}"
                    )
                except:
                    continue

    except Exception as e:
        print(f"Error in ungmute command: {e}")
        await message.reply("❌ An error occurred while processing the global unmute command.")

@pr0fess0r_99.on_message(filters.command(["sudolist"]))
async def sudo_list(client, message):
    try:
        # Check permissions
        if not await check_command_permission(client, message, "maintenance"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Get sudo users
        sudo_users = []
        for user_id in bot_data["sudo_users"]:
            try:
                user = await client.get_users(user_id)
                sudo_users.append(f"• {user.mention} (ID: {user.id})")
            except:
                continue

        if not sudo_users:
            await message.reply("❌ No sudo users found.")
            return

        # Send sudo list
        sudo_text = "**👑 Sudo Users List**\n\n" + "\n".join(sudo_users)
        await message.reply(sudo_text)
    except Exception as e:
        print(f"Error in sudolist command: {e}")
        await message.reply("❌ An error occurred while processing the sudo list command.")

@pr0fess0r_99.on_message(filters.command(["broadcast"]) & filters.private)
async def broadcast_message(client, message):
    try:
        user_id = message.from_user.id
        
        # Check if user is bot owner
        if user_id not in BOT_OWNERS:
            await message.reply("❌ Only bot owners can use the broadcast command!")
            return

        if not message.reply_to_message:
            await message.reply(
                "❌ Please reply to the message you want to broadcast.\n\n"
                "This can be text, photo, video, or any other media."
            )
            return

        # Check if specific chat ID is provided
        args = message.command[1:]
        target_chat = None
        if args:
            try:
                target_chat = int(args[0])
            except ValueError:
                await message.reply("❌ Invalid chat ID. Please provide a valid numeric chat ID.")
                return

        # Get chats to broadcast to
        if target_chat:
            chats = [target_chat]
            broadcast_type = "specific chat"
        else:
            chats = list(bot_data["auto_approve_chats"])
            broadcast_type = "all chats"
        
        if not chats:
            await message.reply("❌ No chats found for broadcasting.")
            return

        # Send initial status
        status_msg = await message.reply(
            f"🚀 Starting broadcast to {len(chats)} {broadcast_type}...\n\n"
            "• Success: 0\n"
            "• Failed: 0\n"
            "• Progress: 0%"
        )

        success = 0
        failed = 0
        
        # Process in batches of 5 to avoid flood wait
        batch_size = 5
        total_batches = (len(chats) + batch_size - 1) // batch_size

        for i in range(0, len(chats), batch_size):
            batch = chats[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            for chat_id in batch:
                try:
                    await message.reply_to_message.copy(chat_id)
                    success += 1
                except Exception as e:
                    print(f"Failed to send to {chat_id}: {e}")
                    failed += 1

                # Update status every 5 chats
                if (success + failed) % 5 == 0:
                    progress = (success + failed) * 100 // len(chats)
                    await status_msg.edit_text(
                        f"🚀 Broadcasting to {broadcast_type}...\n\n"
                        f"• Success: {success}\n"
                        f"• Failed: {failed}\n"
                        f"• Progress: {progress}%\n"
                        f"• Batch: {batch_num}/{total_batches}"
                    )

            # Add delay between batches
            await asyncio.sleep(2)

        # Send final status
        await status_msg.edit_text(
            f"✅ Broadcast completed!\n\n"
            f"• Target: {broadcast_type}\n"
            f"• Total chats: {len(chats)}\n"
            f"• Success: {success}\n"
            f"• Failed: {failed}"
        )

    except Exception as e:
        print(f"Error in broadcast: {e}")
        await message.reply("❌ An error occurred during broadcast.")

# Bot owner command handlers
@pr0fess0r_99.on_message(filters.command(["addsudo"]) & filters.private)
async def add_sudo(client, message):
    try:
        user_id = message.from_user.id
        
        # Check if user is bot owner
        if user_id not in BOT_OWNERS:
            await message.reply("❌ Only bot owners can add sudo users!")
            return

        # Get target user
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user_input = message.command[1]
            try:
                target_user = await client.get_users(user_input)
            except:
                pass

        if not target_user:
            await message.reply(
                "❌ Please specify the user:\n"
                "1. Reply to their message with /addsudo\n"
                "2. Use /addsudo with their username/ID"
            )
            return

        # Check if already sudo
        if target_user.id in bot_data["sudo_users"]:
            await message.reply("❌ This user is already a sudo user!")
            return

        # Add to sudo users
        bot_data["sudo_users"].add(target_user.id)
        bot_data["maintenance_team"].add(target_user.id)
        save_data()

        # Send confirmation
        await message.reply(
            f"✅ Successfully added {target_user.mention} as sudo user!\n\n"
            f"• Name: {target_user.first_name}\n"
            f"• User ID: `{target_user.id}`"
        )

        # Notify the user
        try:
            await client.send_message(
                target_user.id,
                "🎉 Congratulations! You have been promoted to sudo user!"
            )
        except:
            pass

    except Exception as e:
        print(f"Error in addsudo: {e}")
        await message.reply("❌ An error occurred while adding sudo user.")

@pr0fess0r_99.on_message(filters.command(["delsudo"]) & filters.private)
async def del_sudo(client, message):
    try:
        user_id = message.from_user.id
        
        # Check if user is bot owner
        if user_id not in BOT_OWNERS:
            await message.reply("❌ Only bot owners can remove sudo users!")
            return

        # Get target user
        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user_input = message.command[1]
            try:
                target_user = await client.get_users(user_input)
            except:
                pass

        if not target_user:
            await message.reply(
                "❌ Please specify the user:\n"
                "1. Reply to their message with /delsudo\n"
                "2. Use /delsudo with their username/ID"
            )
            return

        # Check if not sudo
        if target_user.id not in bot_data["sudo_users"]:
            await message.reply("❌ This user is not a sudo user!")
            return

        # Remove from sudo users
        bot_data["sudo_users"].discard(target_user.id)
        bot_data["maintenance_team"].discard(target_user.id)
        save_data()

        # Send confirmation
        await message.reply(
            f"✅ Successfully removed {target_user.mention} from sudo users!\n\n"
            f"• Name: {target_user.first_name}\n"
            f"• User ID: `{target_user.id}`"
        )

        # Notify the user
        try:
            await client.send_message(
                target_user.id,
                "ℹ️ Your sudo user access has been removed."
            )
        except:
            pass

    except Exception as e:
        print(f"Error in delsudo: {e}")
        await message.reply("❌ An error occurred while removing sudo user.")

# Game command handlers
@pr0fess0r_99.on_message(filters.command(["mafia"]) & filters.group)
async def start_mafia(client, message):
    try:
        chat_id = message.chat.id

        # Check if game is already running
        if chat_id in bot_data["mafia_games"]:
            await message.reply("❌ A mafia game is already running in this chat.")
            return

        # Initialize game in bot_data if not exists
        if "mafia_games" not in bot_data:
            bot_data["mafia_games"] = {}

        # Initialize game
        bot_data["mafia_games"][chat_id] = {
            "players": [],
            "roles": {},
            "phase": "waiting",  # waiting, night, day
            "votes": {},
            "alive": set(),
            "mafia": set(),
            "doctor": None,
            "detective": None
        }

        # Create join button
        keyboard = [[InlineKeyboardButton("Join Game", callback_data="mafia_join")]]
        await message.reply(
            "🎮 A new Mafia game is starting!\n\n"
            "Click the button below to join the game.\n"
            "The game will start when there are at least 5 players.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Error in mafia command: {e}")
        await message.reply("❌ An error occurred while starting the mafia game.")

@pr0fess0r_99.on_callback_query(filters.regex("^mafia_join$"))
async def join_mafia(client, callback_query):
    try:
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        # Check if game exists
        if chat_id not in mafia_games:
            await callback_query.answer("❌ No game is currently running.")
            return

        # Check if game is in waiting phase
        if mafia_games[chat_id]["phase"] != "waiting":
            await callback_query.answer("❌ The game has already started.")
            return

        # Check if user is already in the game
        if user_id in mafia_games[chat_id]["players"]:
            await callback_query.answer("❌ You are already in the game.")
            return

        # Add player to game
        mafia_games[chat_id]["players"].append(user_id)
        mafia_games[chat_id]["alive"].add(user_id)

        # Update message
        player_count = len(mafia_games[chat_id]["players"])
        await callback_query.message.edit_text(
            f"🎮 Mafia Game\n\n"
            f"Players: {player_count}/10\n"
            f"Click the button below to join the game.\n"
            f"The game will start when there are at least 5 players.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Game", callback_data="mafia_join")]])
        )

        # Start game if enough players
        if player_count >= 5:
            await start_mafia_game(client, chat_id)

        await callback_query.answer("✅ You have joined the game!")
    except Exception as e:
        print(f"Error in mafia join: {e}")
        await callback_query.answer("❌ An error occurred while joining the game.")

async def start_mafia_game(client, chat_id):
    try:
        game = mafia_games[chat_id]
        players = game["players"]
        player_count = len(players)

        # Assign roles
        mafia_count = max(1, player_count // 4)
        roles = ["mafia"] * mafia_count + ["civilian"] * (player_count - mafia_count - 2) + ["doctor", "detective"]
        random.shuffle(roles)

        for i, player_id in enumerate(players):
            role = roles[i]
            game["roles"][player_id] = role
            if role == "mafia":
                game["mafia"].add(player_id)

        # Send role messages
        for player_id in players:
            try:
                role = game["roles"][player_id]
                role_text = f"Your role is: {role.capitalize()}"
                if role == "mafia":
                    other_mafia = [p for p in game["mafia"] if p != player_id]
                    if other_mafia:
                        role_text += f"\nOther mafia members: {', '.join([f'@{p}' for p in other_mafia])}"
                await client.send_message(player_id, role_text)
            except:
                continue

        # Start night phase
        game["phase"] = "night"
        await client.send_message(
            chat_id,
            "🌙 Night has fallen. Mafia members, please choose your target."
        )
    except Exception as e:
        print(f"Error in start_mafia_game: {e}")
        await client.send_message(chat_id, "❌ An error occurred while starting the game.")

@pr0fess0r_99.on_message(filters.command(["quiz"]) & filters.group)
async def start_quiz(client, message):
    try:
        chat_id = message.chat.id

        # Check if game is already running
        if chat_id in quiz_games:
            await message.reply("❌ A quiz game is already running in this chat.")
            return

        # Initialize game
        quiz_games[chat_id] = {
            "players": {},
            "current_question": None,
            "question_number": 0,
            "total_questions": 10,
            "questions": [
                {
                    "question": "What is the capital of France?",
                    "options": ["London", "Paris", "Berlin", "Madrid"],
                    "correct": 1
                },
                # Add more questions here
            ]
        }

        # Create join button
        keyboard = [[InlineKeyboardButton("Join Quiz", callback_data="quiz_join")]]
        await message.reply(
            "📚 A new Quiz game is starting!\n\n"
            "Click the button below to join the game.\n"
            "The game will start in 30 seconds.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Start game after 30 seconds
        await asyncio.sleep(30)
        if chat_id in quiz_games:
            await start_quiz_game(client, chat_id)
    except Exception as e:
        print(f"Error in quiz command: {e}")
        await message.reply("❌ An error occurred while starting the quiz game.")

@pr0fess0r_99.on_callback_query(filters.regex("^quiz_join$"))
async def join_quiz(client, callback_query):
    try:
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        # Check if game exists
        if chat_id not in quiz_games:
            await callback_query.answer("❌ No game is currently running.")
            return

        # Check if user is already in the game
        if user_id in quiz_games[chat_id]["players"]:
            await callback_query.answer("❌ You are already in the game.")
            return

        # Add player to game
        quiz_games[chat_id]["players"][user_id] = 0

        # Update message
        player_count = len(quiz_games[chat_id]["players"])
        await callback_query.message.edit_text(
            f"📚 Quiz Game\n\n"
            f"Players: {player_count}\n"
            f"Click the button below to join the game.\n"
            f"The game will start in 30 seconds.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Quiz", callback_data="quiz_join")]])
        )

        await callback_query.answer("✅ You have joined the game!")
    except Exception as e:
        print(f"Error in quiz join: {e}")
        await callback_query.answer("❌ An error occurred while joining the game.")

async def start_quiz_game(client, chat_id):
    try:
        game = quiz_games[chat_id]
        if not game["players"]:
            await client.send_message(chat_id, "❌ No players joined the game.")
            del quiz_games[chat_id]
            return

        # Start asking questions
        while game["question_number"] < game["total_questions"]:
            question = game["questions"][game["question_number"]]
            game["current_question"] = question

            # Create options keyboard
            keyboard = []
            for i, option in enumerate(question["options"]):
                keyboard.append([InlineKeyboardButton(option, callback_data=f"quiz_answer_{i}")])

            # Send question
            await client.send_message(
                chat_id,
                f"Question {game['question_number'] + 1}/{game['total_questions']}:\n\n"
                f"{question['question']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # Wait for answers
            await asyncio.sleep(30)

            # Show correct answer
            correct_option = question["options"][question["correct"]]
            await client.send_message(
                chat_id,
                f"✅ The correct answer was: {correct_option}\n\n"
                f"Current scores:\n" + "\n".join([
                    f"• {await client.get_users(user_id).first_name}: {score}"
                    for user_id, score in game["players"].items()
                ])
            )

            game["question_number"] += 1
            await asyncio.sleep(5)

        # End game
        winner = max(game["players"].items(), key=lambda x: x[1])
        await client.send_message(
            chat_id,
            f"🏆 Quiz Game Over!\n\n"
            f"Winner: {await client.get_users(winner[0]).first_name} with {winner[1]} points!"
        )
        del quiz_games[chat_id]
    except Exception as e:
        print(f"Error in start_quiz_game: {e}")
        await client.send_message(chat_id, "❌ An error occurred while running the quiz game.")

@pr0fess0r_99.on_callback_query(filters.regex("^quiz_answer_"))
async def quiz_answer(client, callback_query):
    try:
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        answer = int(callback_query.data.split("_")[-1])

        # Check if game exists and is active
        if chat_id not in quiz_games or user_id not in quiz_games[chat_id]["players"]:
            await callback_query.answer("❌ No active game found.")
            return

        game = quiz_games[chat_id]
        question = game["current_question"]

        # Check if answer is correct
        if answer == question["correct"]:
            game["players"][user_id] += 1
            await callback_query.answer("✅ Correct answer!")
        else:
            await callback_query.answer("❌ Wrong answer!")
    except Exception as e:
        print(f"Error in quiz answer: {e}")
        await callback_query.answer("❌ An error occurred while processing your answer.")

# Tagging functionality
@pr0fess0r_99.on_message(filters.command(["tag"]) & filters.group)
async def start_tagging(client, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check if user has admin rights
        if not await has_specific_rights(client, chat_id, user_id, "can_invite_users"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Parse command arguments
        if len(message.command) < 2:
            await message.reply(
                "❌ Please use the correct format:\n"
                "/tag message [number_of_users]\n\n"
                "Example:\n"
                "• /tag Hello everyone - Tags all members\n"
                "• /tag Hello 15 - Tags 15 members"
            )
            return

        # Extract user count if provided
        command_text = " ".join(message.command[1:])
        user_count = None
        tag_message = command_text

        # Check if last word is a number
        words = command_text.split()
        if words and words[-1].isdigit():
            user_count = int(words[-1])
            tag_message = " ".join(words[:-1])

        # Get all members
        members = []
        try:
            async for member in client.get_chat_members(chat_id):
                if not member.user.is_bot and member.user.id != user_id:
                    members.append(member.user)
        except Exception as e:
            print(f"Error getting chat members: {e}")
            await message.reply("❌ Failed to get chat members. Please try again.")
            return

        # Shuffle members to randomize tagging
        random.shuffle(members)

        # Limit members if user_count is specified
        if user_count and user_count < len(members):
            members = members[:user_count]

        # Emoji list for tagging (using fun and varied emojis)
        emojis = ["👻", "🎯", "🎲", "🎮", "🎪", "🎨", "🎭", "🎪", "🎫", "🎪", 
                 "🌟", "✨", "💫", "⭐", "🌙", "☀️", "🌈", "🌸", "🎭", "🎪",
                 "🦁", "🐯", "🐱", "🐶", "🐼", "🐨", "🐮", "🐷", "🐸", "🐙"]
        
        # Create batches of 5 users
        total_members = len(members)
        batches = [members[i:i + 5] for i in range(0, total_members, 5)]

        # Store tagging progress
        bot_data["tagging_in_progress"][chat_id] = {
            "started_by": user_id,
            "total_members": total_members,
            "tagged_members": 0
        }
        save_data()

        for batch in batches:
            # Create message with emojis and hidden mentions
            batch_message = tag_message + "\n\n"
            for member in batch:
                emoji = random.choice(emojis)
                batch_message += f"[{emoji}](tg://user?id={member.id}) "

            try:
                await client.send_message(chat_id, batch_message)
                bot_data["tagging_in_progress"][chat_id]["tagged_members"] += len(batch)
                save_data()
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except Exception as e:
                print(f"Error sending tag message: {e}")
                continue
            
            # Add delay between batches
            await asyncio.sleep(2)

        # Remove tagging progress after completion
        if chat_id in bot_data["tagging_in_progress"]:
            del bot_data["tagging_in_progress"][chat_id]
            save_data()

    except Exception as e:
        print(f"Error in tag command: {e}")
        await message.reply("❌ An error occurred while processing the tag command.")

@pr0fess0r_99.on_callback_query(filters.regex("^tag_"))
async def tag_callback(client, callback_query):
    """Handle tag button clicks"""
    try:
        # Extract user ID from callback data
        user_id = int(callback_query.data.split("_")[1])
        
        try:
            user = await client.get_users(user_id)
            # Send the mention as a reply
            await callback_query.message.reply(user.mention, quote=True)
            await callback_query.answer()
        except Exception as e:
            print(f"Error getting user info: {e}")
            await callback_query.answer("User not found!", show_alert=True)
            
    except Exception as e:
        print(f"Error in tag callback: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_message(filters.command(["stoptag"]) & filters.group)
async def stop_tagging(client, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check if user has admin rights
        if not await has_specific_rights(client, chat_id, user_id, "can_invite_users"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Check if tagging is in progress
        if chat_id not in bot_data.get("tagging_in_progress", {}):
            await message.reply("❌ No tagging process is currently running.")
            return

        # Stop tagging process
        del bot_data["tagging_in_progress"][chat_id]
        save_data()
        await message.reply("✅ Tagging process stopped!")
    except Exception as e:
        print(f"Error in stoptag command: {e}")
        await message.reply("❌ An error occurred while processing the stoptag command.")

@pr0fess0r_99.on_message(filters.command(["toptag"]) & filters.group)
async def top_tagged(client, message):
    try:
        chat_id = message.chat.id

        # Check if there are any tag statistics
        if "tagged_users" not in bot_data or chat_id not in bot_data["tagged_users"] or not bot_data["tagged_users"][chat_id]:
            await message.reply("❌ No tag statistics available for this chat.")
            return

        # Get top 10 tagged users
        top_users = sorted(
            bot_data["tagged_users"][chat_id].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Create top list message
        top_list = "🏆 **Top 10 Most Tagged Users:**\n\n"
        for i, (user_id, count) in enumerate(top_users, 1):
            try:
                user = await client.get_users(user_id)
                top_list += f"{i}. {user.mention} - {count} times\n"
            except Exception as e:
                print(f"Error getting user {user_id}: {e}")
                top_list += f"{i}. User {user_id} - {count} times\n"

        await message.reply(top_list)
    except Exception as e:
        print(f"Error in toptag command: {e}")
        await message.reply("❌ An error occurred while processing the toptag command.")

@pr0fess0r_99.on_message(filters.command(["resettag"]) & filters.group)
async def reset_tag_stats(client, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check if user has admin rights
        if not await has_specific_rights(client, chat_id, user_id, "can_invite_users"):
            await message.reply("❌ You don't have permission to use this command.")
            return

        # Reset tag statistics
        if chat_id in bot_data["tagged_users"]:
            bot_data["tagged_users"][chat_id] = {}

        # Delete statistics from database
        await db.tag_statistics.delete_many({"chat_id": chat_id})

        await message.reply("✅ Tag statistics have been reset!")
    except Exception as e:
        print(f"Error in resettag command: {e}")
        await message.reply("❌ An error occurred while processing the resettag command.")

# Refresh command and error handling
@pr0fess0r_99.on_message(filters.command(["refresh"]) & filters.group)
async def refresh_settings(client, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Check if user is a member of the chat
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                await message.reply("❌ You need to be a member of this chat to use this command.")
                return
        except Exception as e:
            print(f"Error checking member status: {e}")
            await message.reply("❌ Could not verify your membership in this chat.")
            return

        # Reload settings from database
        await load_data()

        # Update chat settings
        chat_settings[chat_id] = {
            "approve": chat_id in bot_data["auto_approve_chats"],
            "welcome": chat_id in bot_data["welcome_settings"],
            "welcome_media": chat_id in bot_data["welcome_media"],
            "tag_stats": chat_id in bot_data["tagged_users"]
        }

        # Save updated settings
        await save_chat_settings(chat_id)

        await message.reply("✅ Bot settings have been refreshed!")
    except Exception as e:
        print(f"Error in refresh command: {e}")
        await message.reply("❌ An error occurred while refreshing settings.")

@pr0fess0r_99.on_message(filters.command(["checkadmin"]) & filters.group)
async def check_admin(client, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Get user's admin status
        is_admin = await is_admin_or_owner(client, chat_id, user_id)
        is_owner = await is_group_owner(client, chat_id, user_id)
        is_maint = await is_maintenance_team(user_id)

        # Get user's rights
        rights = []
        for right in [
            "can_restrict_members",
            "can_pin_messages",
            "can_delete_messages",
            "can_invite_users",
            "can_manage_chat",
            "can_promote_members",
            "can_change_info",
            "can_manage_video_chats",
            "can_post_messages",
            "can_edit_messages"
        ]:
            if await has_specific_rights(client, chat_id, user_id, right):
                rights.append(right.replace("can_", "").replace("_", " ").title())

        # Create status message
        status = f"""
**👤 Admin Status for {message.from_user.mention}**

• Is Admin: {'Yes' if is_admin else 'No'}
• Is Owner: {'Yes' if is_owner else 'No'}
• Is Maintenance: {'Yes' if is_maint else 'No'}

**🔑 Rights:**
{chr(10).join([f"• {right}" for right in rights]) if rights else "• No special rights"}
"""

        await message.reply(status)
    except Exception as e:
        print(f"Error in checkadmin command: {e}")
        await message.reply("❌ An error occurred while checking admin status.")

# Update the error handler to use the correct method
@pr0fess0r_99.on_message(filters.command(["error"]) & filters.private)
async def error_handler(client, message):
    """Handle errors and provide feedback"""
    try:
        # Get the error message from the command
        error_msg = " ".join(message.command[1:]) if len(message.command) > 1 else "No error message provided"

        # Log the error
        print(f"Error occurred: {error_msg}")

        # Send error report to bot owner
        for owner_id in BOT_OWNERS:
            try:
                await client.send_message(
                    owner_id,
                    f"⚠️ Error Report:\n\n{error_msg}\n\nFrom: {message.from_user.mention}"
                )
            except Exception as e:
                print(f"Failed to send error report to owner {owner_id}: {e}")

        # Acknowledge the error report
        await message.reply("✅ Error has been reported to the bot owner.")
    except Exception as e:
        print(f"Error in error handler: {e}")

# Add stats command
@pr0fess0r_99.on_message(filters.command("stats"))
async def stats_command(client, message):
    try:
        # Calculate uptime
        uptime = time.time() - bot_data["bot_stats"]["start_time"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        # Get chat counts
        total_chats = len(bot_data["auto_approve_chats"])
        
        # Create stats message
        stats_text = f"""
📊 **Bot Statistics**

⏱️ **Uptime:**
• {hours}h {minutes}m {seconds}s

👥 **Users & Chats:**
• Auto-approve Chats: {total_chats}
• Total Approved: {bot_data["bot_stats"]["total_approved"]}
• Total Messages: {bot_data["bot_stats"]["total_messages_sent"]}

🛡️ **Moderation:**
• Banned Users: {len(bot_data["banned_users"])}
• Muted Users: {len(bot_data["muted_users"])}
• Sudo Users: {len(bot_data["sudo_users"])}

🎮 **Games:**
• Mafia Games: {len(bot_data["mafia_games"])}
• Quiz Games: {len(bot_data["quiz_games"])}

⚙️ **Settings:**
• Welcome Messages: {len(bot_data["welcome_settings"])}
• Custom Filters: {len(bot_data["custom_filters"])}
"""
        await message.reply(stats_text)
    except Exception as e:
        print(f"Error in stats command: {e}")
        await message.reply("❌ Error getting bot statistics")

async def main():
    await pr0fess0r_99.start()
    print("Bot started successfully!")
    await idle()
    await pr0fess0r_99.stop()

if __name__ == "__main__":
    pr0fess0r_99.run(main())

# Remove all the event loop handling code since we're using client.run()

@pr0fess0r_99.on_callback_query(filters.regex("^owner_.*"))
async def owner_panel_callback(client, callback_query):
    """Handle owner panel button callbacks"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized to use this panel!", show_alert=True)
            return
            
        callback_data = callback_query.data
        
        if callback_data == "owner_stats":
            # Calculate uptime
            uptime = datetime.now() - START_TIME
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            stats_text = f"""
📊 **Bot Statistics**

⏱️ **Uptime:** {hours}h {minutes}m

👥 **Users & Chats:**
• Auto-approve Chats: {len(bot_data["auto_approve_chats"])}
• Total Approved: {bot_data["bot_stats"]["total_approved"]}
• Messages Sent: {bot_data["bot_stats"]["total_messages_sent"]}

🛡️ **Moderation:**
• Banned Users: {len(bot_data["banned_users"])}
• Muted Users: {len(bot_data["muted_users"])}
• Sudo Users: {len(bot_data["sudo_users"])}

⚙️ **Settings:**
• Welcome Messages: {len(bot_data["welcome_settings"])}
• Custom Filters: {len(bot_data.get("custom_filters", {}))}
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="owner_stats"),
                 InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
            ])
            
            await callback_query.edit_message_text(stats_text, reply_markup=keyboard)
            
        elif callback_data == "owner_sudolist":
            sudo_text = "👑 **Sudo Users List**\n\n"
            if not bot_data["sudo_users"]:
                sudo_text += "No sudo users added yet."
            else:
                for sudo_id in bot_data["sudo_users"]:
                    try:
                        user = await client.get_users(sudo_id)
                        sudo_text += f"• {user.mention} (`{user.id}`)\n"
                    except:
                        sudo_text += f"• Unknown User (`{sudo_id}`)\n"
                
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Sudo", callback_data="owner_addsudo"),
                 InlineKeyboardButton("➖ Remove Sudo", callback_data="owner_remsudo")],
                [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
            ])
            
            await callback_query.edit_message_text(sudo_text, reply_markup=keyboard)
            
        elif callback_data == "owner_broadcast":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 All Chats", callback_data="broadcast_all"),
                 InlineKeyboardButton("👥 Users Only", callback_data="broadcast_users")],
                [InlineKeyboardButton("💭 Groups Only", callback_data="broadcast_groups")],
                [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
            ])
            
            await callback_query.edit_message_text(
                "**📢 Broadcast Menu**\n\nSelect where you want to broadcast your message:",
                reply_markup=keyboard
            )
            
        elif callback_data == "owner_settings":
            settings_text = f"""
⚙️ **Bot Settings**

🤖 **Current Status:**
• Auto-Approve: {'✅ Enabled' if AUTO_APPROVE else '❌ Disabled'}
• Welcome Messages: {'✅ Enabled' if WELCOME_ENABLED else '❌ Disabled'}
• Force Subscribe: {'✅ Enabled' if FORCE_SUB_CHANNEL else '❌ Disabled'}

📊 **Quick Stats:**
• Total Chats: {len(bot_data["auto_approve_chats"])}
• Active Settings: {len(bot_data["chat_settings"])}
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Toggle Auto-Approve", callback_data="toggle_autoapprove")],
                [InlineKeyboardButton("💬 Toggle Welcome", callback_data="toggle_welcome")],
                [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
            ])
            
            await callback_query.edit_message_text(settings_text, reply_markup=keyboard)
            
        elif callback_data == "owner_panel":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Statistics", callback_data="owner_stats"),
                 InlineKeyboardButton("👑 Sudo Users", callback_data="owner_sudolist")],
                [InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast"),
                 InlineKeyboardButton("⚙️ Settings", callback_data="owner_settings")]
            ])
            
            await callback_query.edit_message_text(
                "**🤖 Owner Control Panel**\n\nSelect an option from below:",
                reply_markup=keyboard
            )
        
        await callback_query.answer()
        
    except Exception as e:
        print(f"Error in owner panel callback: {e}")
        await callback_query.answer("❌ An error occurred!", show_alert=True)

@Client.on_callback_query(filters.regex("^help_command$"))
async def help_command_callback(client, callback_query):
    help_text = """**🤖 Bot Commands List**

**👥 Basic Commands:**
• /start - Start the bot
• /help - Show this help message
• /ping - Check bot's response time
• /stats - View bot statistics

**🎯 Tagging Commands:**
• /tag [message] [count] - Tag members with emoji buttons
  Example: `/tag Hello everyone 10`
• /stoptag - Stop ongoing tagging process
• /toptag - Show top tagged users
• /resettag - Reset tag statistics

**👮 Admin Commands:**
• /ban - Ban a user from the group
• /unban - Unban a user
• /mute - Mute a user
• /unmute - Unmute a user
• /kick - Kick a user
• /pin - Pin a message
• /unpin - Unpin a message
• /purge - Delete messages in bulk
• /del - Delete a specific message

**⚙️ Group Settings:**
• /approveon - Enable auto-approval
• /approveoff - Disable auto-approval
• /setwelcome - Set custom welcome message
• /refresh - Refresh bot settings
• /checkadmin - Check your admin rights

**🎮 Game Commands:**
• /mafia - Start a Mafia game
• /quiz - Start a Quiz game

**👑 Owner Commands:**
• /broadcast - Send broadcast message
• /addsudo - Add a sudo user
• /delsudo - Remove a sudo user
• /sudolist - List all sudo users

**🛡️ Maintenance Commands:**
• /gban - Global ban a user
• /ungban - Remove global ban
• /gmute - Global mute a user
• /ungmute - Remove global mute

**💡 Welcome Message Variables:**
You can use these in welcome messages:
• {mention} - Mentions the user
• {title} - Group/Channel title
• {first} - User's first name
• {last} - User's last name
• {id} - User ID

**📝 Note:** 
• Some commands require specific admin rights
• Maintenance commands are for authorized users only
• Join @Bot_SOURCEC for updates and support"""

    await callback_query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )

@Client.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_callback(client, callback_query):
    # Reuse the start command logic
    await start_command(client, callback_query.message)

@pr0fess0r_99.on_callback_query(filters.regex("^owner_panel$"))
async def owner_panel_handler(client, callback_query):
    """Handle the owner panel main menu"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized to use this panel!", show_alert=True)
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Statistics", callback_data="owner_stats"),
             InlineKeyboardButton("👑 Sudo Users", callback_data="owner_sudolist")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast"),
             InlineKeyboardButton("⚙️ Settings", callback_data="owner_settings")]
        ])
        
        await callback_query.message.edit_text(
            "**🤖 Owner Control Panel**\n\nSelect an option from below:",
            reply_markup=keyboard
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in owner panel: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_callback_query(filters.regex("^owner_stats$"))
async def owner_stats_callback(client, callback_query):
    """Show bot statistics"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return

        # Calculate uptime
        uptime = datetime.now() - START_TIME
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        seconds = int(uptime.total_seconds() % 60)
        
        stats_text = f"""
📊 **Bot Statistics**

⏱️ **Uptime:**
• {hours}h {minutes}m {seconds}s

👥 **Users & Chats:**
• Auto-approve Chats: {len(bot_data["auto_approve_chats"])}
• Total Approved: {bot_data["bot_stats"]["total_approved"]}
• Total Messages: {bot_data["bot_stats"]["total_messages_sent"]}

⚙️ **Settings:**
• Welcome Messages: {len(bot_data["welcome_settings"])}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
        ])
        
        await callback_query.message.edit_text(stats_text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        print(f"Error in owner stats: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_callback_query(filters.regex("^owner_sudolist$"))
async def owner_sudolist_callback(client, callback_query):
    """Show list of sudo users"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return
            
        sudo_text = "👑 **Sudo Users List**\n\n"
        if not bot_data["sudo_users"]:
            sudo_text += "No sudo users added yet."
        else:
            for sudo_id in bot_data["sudo_users"]:
                try:
                    user = await client.get_users(sudo_id)
                    sudo_text += f"• {user.mention} (`{user.id}`)\n"
                except:
                    sudo_text += f"• Unknown User (`{sudo_id}`)\n"
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
        ])
        
        await callback_query.message.edit_text(sudo_text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        print(f"Error in sudo list: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_callback_query(filters.regex("^owner_broadcast$"))
async def owner_broadcast_callback(client, callback_query):
    """Show broadcast options"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 All Chats", callback_data="broadcast_all")],
            [InlineKeyboardButton("👥 Users Only", callback_data="broadcast_users"),
             InlineKeyboardButton("💭 Groups Only", callback_data="broadcast_groups")],
            [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
        ])
        
        await callback_query.message.edit_text(
            "**📢 Broadcast Menu**\n\nSelect where you want to broadcast your message:",
            reply_markup=keyboard
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in broadcast menu: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_callback_query(filters.regex("^owner_settings$"))
async def owner_settings_callback(client, callback_query):
    """Show bot settings"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return
            
        settings_text = f"""
⚙️ **Bot Settings**

🤖 **Current Status:**
• Auto-Approve: {'✅ Enabled' if AUTO_APPROVE else '❌ Disabled'}
• Welcome Messages: {'✅ Enabled' if WELCOME_ENABLED else '❌ Disabled'}
• Force Subscribe: {'✅ Enabled' if FORCE_SUB_CHANNEL else '❌ Disabled'}

📊 **Quick Stats:**
• Total Chats: {len(bot_data["auto_approve_chats"])}
• Active Settings: {len(bot_data["chat_settings"])}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Toggle Auto-Approve", callback_data="toggle_autoapprove")],
            [InlineKeyboardButton("💬 Toggle Welcome", callback_data="toggle_welcome")],
            [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
        ])
        
        await callback_query.message.edit_text(settings_text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        print(f"Error in settings menu: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

# Settings toggle handlers
@pr0fess0r_99.on_callback_query(filters.regex("^toggle_autoapprove$"))
async def toggle_autoapprove(client, callback_query):
    """Toggle auto-approve setting"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return
            
        global AUTO_APPROVE
        AUTO_APPROVE = not AUTO_APPROVE
        await callback_query.answer(f"Auto-approve {'enabled' if AUTO_APPROVE else 'disabled'}!", show_alert=True)
        await owner_settings_callback(client, callback_query)
    except Exception as e:
        print(f"Error toggling auto-approve: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_callback_query(filters.regex("^toggle_welcome$"))
async def toggle_welcome(client, callback_query):
    """Toggle welcome messages setting"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return
            
        global WELCOME_ENABLED
        WELCOME_ENABLED = not WELCOME_ENABLED
        await callback_query.answer(f"Welcome messages {'enabled' if WELCOME_ENABLED else 'disabled'}!", show_alert=True)
        await owner_settings_callback(client, callback_query)
    except Exception as e:
        print(f"Error toggling welcome: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_message(filters.command("owner") & filters.private)
async def owner_command(client, message):
    """Show owner panel when /owner command is used"""
    try:
        user_id = message.from_user.id
        
        if user_id not in BOT_OWNERS:
            await message.reply("❌ You are not authorized to use this command!")
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Statistics", callback_data="owner_stats"),
             InlineKeyboardButton("👑 Sudo Users", callback_data="owner_sudolist")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast"),
             InlineKeyboardButton("⚙️ Settings", callback_data="owner_settings")]
        ])
        
        await message.reply(
            "**🤖 Owner Control Panel**\n\nSelect an option from below:",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in owner command: {e}")
        await message.reply("❌ An error occurred!")

@pr0fess0r_99.on_message(filters.command(["chats"]) & filters.private)
async def list_chats(client, message):
    try:
        user_id = message.from_user.id
        
        # Check if user is bot owner
        if user_id not in BOT_OWNERS:
            await message.reply("❌ Only bot owners can use this command!")
            return

        # Get all chats where bot is added
        chats = list(bot_data["auto_approve_chats"])
        
        if not chats:
            await message.reply("❌ Bot is not added to any chats yet.")
            return

        # Send initial status
        status_msg = await message.reply("📊 Fetching chat information...")

        # Process chats in batches
        chat_info = []
        batch_size = 5  # Reduced batch size due to additional API calls
        total_batches = (len(chats) + batch_size - 1) // batch_size

        for i in range(0, len(chats), batch_size):
            batch = chats[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            for chat_id in batch:
                try:
                    chat = await client.get_chat(chat_id)
                    chat_type = "Group" if chat.type == ChatType.GROUP else "Channel"
                    
                    # Get invite link if available
                    invite_link = "No link available"
                    try:
                        if chat.username:
                            invite_link = f"https://t.me/{chat.username}"
                        else:
                            invite_link = await client.export_chat_invite_link(chat_id)
                    except:
                        pass

                    # Determine if chat is private or public
                    privacy = "🔒 Private" if not chat.username else "🔓 Public"
                    
                    chat_info.append(
                        f"• {chat_type}: {chat.title}\n"
                        f"  ID: {chat.id}\n"
                        f"  Status: {privacy}\n"
                        f"  Link: {invite_link}\n"
                    )
                except Exception as e:
                    print(f"Error getting chat info for {chat_id}: {e}")
                    chat_info.append(f"• Unknown Chat (ID: {chat_id})\n")

            # Update status
            progress = (i + len(batch)) * 100 // len(chats)
            await status_msg.edit_text(
                f"📊 Fetching chat information...\n\n"
                f"• Progress: {progress}%\n"
                f"• Batch: {batch_num}/{total_batches}"
            )

            # Add delay between batches
            await asyncio.sleep(2)

        # Create final message
        total_chats = len(chat_info)
        message_text = f"📊 **Chats List**\n\n"
        message_text += f"Total Chats: {total_chats}\n\n"
        message_text += "\n".join(chat_info)

        # Send final message with pagination if needed
        if len(message_text) > 4000:
            # Split into multiple messages
            parts = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
            for part in parts:
                await message.reply(part)
        else:
            await status_msg.edit_text(message_text)

    except Exception as e:
        print(f"Error in list_chats command: {e}")
        await message.reply("❌ An error occurred while fetching chat list.")

@pr0fess0r_99.on_callback_query(filters.regex("^owner_chats$"))
async def owner_chats_callback(client, callback_query):
    """Show list of chats in owner panel"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return

        # Get all chats where bot is added
        chats = list(bot_data["auto_approve_chats"])
        
        if not chats:
            await callback_query.message.edit_text(
                "❌ Bot is not added to any chats yet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
                ])
            )
            return

        # Create chat list message
        chat_list = "📊 **Chats List**\n\n"
        chat_list += f"Total Chats: {len(chats)}\n\n"
        
        # Add first 5 chats (reduced due to additional API calls)
        for i, chat_id in enumerate(chats[:5], 1):
            try:
                chat = await client.get_chat(chat_id)
                chat_type = "Group" if chat.type == ChatType.GROUP else "Channel"
                
                # Get invite link if available
                invite_link = "No link available"
                try:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                    else:
                        invite_link = await client.export_chat_invite_link(chat_id)
                except:
                    pass

                # Determine if chat is private or public
                privacy = "🔒 Private" if not chat.username else "🔓 Public"
                
                chat_list += (
                    f"{i}. {chat_type}: {chat.title}\n"
                    f"   ID: {chat.id}\n"
                    f"   Status: {privacy}\n"
                    f"   Link: {invite_link}\n\n"
                )
            except:
                chat_list += f"{i}. Unknown Chat (ID: {chat_id})\n\n"

        # Add pagination if needed
        keyboard = []
        if len(chats) > 5:
            keyboard.append([
                InlineKeyboardButton("Next Page ➡️", callback_data="chats_page_2")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])

        await callback_query.message.edit_text(
            chat_list,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in owner chats callback: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

@pr0fess0r_99.on_callback_query(filters.regex("^chats_page_"))
async def chats_page_callback(client, callback_query):
    """Handle pagination for chats list"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized!", show_alert=True)
            return

        page = int(callback_query.data.split("_")[-1])
        chats = list(bot_data["auto_approve_chats"])
        items_per_page = 5  # Reduced due to additional API calls
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        chat_list = "📊 **Chats List**\n\n"
        chat_list += f"Total Chats: {len(chats)}\n\n"
        
        # Add chats for current page
        for i, chat_id in enumerate(chats[start_idx:end_idx], start_idx + 1):
            try:
                chat = await client.get_chat(chat_id)
                chat_type = "Group" if chat.type == ChatType.GROUP else "Channel"
                
                # Get invite link if available
                invite_link = "No link available"
                try:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                    else:
                        invite_link = await client.export_chat_invite_link(chat_id)
                except:
                    pass

                # Determine if chat is private or public
                privacy = "🔒 Private" if not chat.username else "🔓 Public"
                
                chat_list += (
                    f"{i}. {chat_type}: {chat.title}\n"
                    f"   ID: {chat.id}\n"
                    f"   Status: {privacy}\n"
                    f"   Link: {invite_link}\n\n"
                )
            except:
                chat_list += f"{i}. Unknown Chat (ID: {chat_id})\n\n"

        # Add pagination buttons
        keyboard = []
        if page > 1:
            keyboard.append([
                InlineKeyboardButton("⬅️ Previous Page", callback_data=f"chats_page_{page-1}")
            ])
        if end_idx < len(chats):
            keyboard.append([
                InlineKeyboardButton("Next Page ➡️", callback_data=f"chats_page_{page+1}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])

        await callback_query.message.edit_text(
            chat_list,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in chats page callback: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

# Update owner panel to include chats list button
@pr0fess0r_99.on_callback_query(filters.regex("^owner_panel$"))
async def owner_panel_handler(client, callback_query):
    """Handle the owner panel main menu"""
    try:
        user_id = callback_query.from_user.id
        
        if user_id not in BOT_OWNERS:
            await callback_query.answer("You are not authorized to use this panel!", show_alert=True)
            return
            
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Statistics", callback_data="owner_stats"),
             InlineKeyboardButton("👑 Sudo Users", callback_data="owner_sudolist")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast"),
             InlineKeyboardButton("⚙️ Settings", callback_data="owner_settings")],
            [InlineKeyboardButton("💬 Chats List", callback_data="owner_chats")]
        ])
        
        await callback_query.message.edit_text(
            "**🤖 Owner Control Panel**\n\nSelect an option from below:",
            reply_markup=keyboard
        )
        await callback_query.answer()
    except Exception as e:
        print(f"Error in owner panel: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)
