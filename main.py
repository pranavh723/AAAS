import os
import random
import time
import json
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, User, ChatJoinRequest, ChatPermissions
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired, UsernameInvalid, PeerIdInvalid
import asyncio
from keepalive import keep_alive
keep_alive()

# Bot owners and sudo users lists
BOT_OWNERS = [6985505204, 7335254391]  # List of bot owner IDs
SUDO_USERS = set()  # Set of sudo users who have owner-like privileges

# Try to import TgCrypto for better performance
try:
    import tgcrypto
    print("TgCrypto is installed!")
except ImportError:
    print("TgCrypto is not installed. Installing recommended for better performance.")

# Set environment variables directly in the code
os.environ["BOT_TOKEN"] = "7399953040:AAGjsk0m1W5ymXq2KESrYsTf2-wMb2xLKVg"
os.environ["API_ID"] = "25056303"
os.environ["API_HASH"] = "423f1e11581ff494841681fc66e9c8e6"
os.environ["APPROVED_WELCOME_TEXT"] = "Hello {mention} Welcome to {title} Your request was approved!"

# Bot maintenance team configuration
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))  # Main bot owner
if os.environ.get("SUDO_USERS"):
    for user in os.environ.get("SUDO_USERS", "").split(","):
        try:
            SUDO_USERS.add(int(user.strip()))
        except ValueError:
            pass

# Add BOT_OWNERS to SUDO_USERS
for owner_id in BOT_OWNERS:
    SUDO_USERS.add(owner_id)

pr0fess0r_99 = Client(
    "Auto Approved Bot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"]
)

CHAT_ID = [int(chat) for chat in os.environ.get("CHAT_ID", "").split()] if os.environ.get("CHAT_ID") else None
TEXT = os.environ.get("APPROVED_WELCOME_TEXT", "Hello {mention} Welcome To {title} Your Auto Approved")
APPROVED = os.environ.get("APPROVED_WELCOME", "on").lower()

# Track bot start time
bot_start_time = time.time()

# Stats tracking
bot_stats = {
    "total_approved": 0,
    "total_messages_sent": 0,
    "start_time": time.time()
}

# Store settings for each chat
chat_settings = {}

# Store globally banned users
banned_users = set()

# Store globally muted users
muted_users = set()

# Store tagging state
tagging_in_progress = {}
tagged_users = {}

# Store mafia games
mafia_games = {}

# Store removed users for each chat
removed_users = {}

# Helper functions
async def is_maintenance_team(user_id):
    """Check if user is in the maintenance team (owner or sudo)"""
    return user_id in BOT_OWNERS or user_id == OWNER_ID or user_id in SUDO_USERS

async def is_admin_or_owner(client, chat_id, user_id):
    """Check if user is admin or owner of the chat"""
    # First check if user is in maintenance team
    if user_id in BOT_OWNERS or user_id in SUDO_USERS:
        return True

    try:
        # Get the chat member information directly
        member = await client.get_chat_member(chat_id, user_id)
        # Check if user is creator or administrator
        return member.status in ["creator", "administrator"] or "owner" in str(member.status).lower()
    except UserNotParticipant:
        # User is not a participant in the chat
        return False
    except Exception as e:
        print(f"Error in is_admin_or_owner: {e}")
        return False

async def is_group_owner(client, chat_id, user_id):
    """Check if user is the owner of the group"""
    # First check if user is in maintenance team
    if user_id in BOT_OWNERS or user_id in SUDO_USERS:
        return True

    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status == "creator" or "owner" in str(member.status).lower()
    except UserNotParticipant:
        # User is not a participant in the chat
        return False
    except Exception as e:
        print(f"Error in is_group_owner: {e}")
        return False

async def has_ban_rights(client, chat_id, user_id):
    """Check if user has ban rights"""
    # First check if user is in maintenance team (bot owners or sudo users)
    if user_id in BOT_OWNERS or user_id in SUDO_USERS:
        return True

    try:
        # Get the chat member information
        member = await client.get_chat_member(chat_id, user_id)
        # Return True if user is creator/owner or admin with restrict_members permission
        return (member.status == "creator" or 
               "owner" in str(member.status).lower() or
               (member.status == "administrator" and member.can_restrict_members))
    except UserNotParticipant:
        # User is not a participant in the chat
        return False
    except Exception as e:
        print(f"Error checking ban rights: {e}")
        return False

async def has_specific_rights(client, chat_id, user_id, right_type):
    """Check if user has specific rights (ban, invite, pin, etc.)"""
    # First check if user is in maintenance team (bot owners or sudo users)
    if user_id in BOT_OWNERS or user_id in SUDO_USERS:
        return True

    try:
        # Get the chat member information
        member = await client.get_chat_member(chat_id, user_id)
        
        # Check for creator/owner (they have all rights)
        if member.status == "creator" or "owner" in str(member.status).lower():
            return True
            
        # For administrators, check specific rights
        if member.status == "administrator":
            if right_type == "ban" and member.can_restrict_members:
                return True
            elif right_type == "pin" and member.can_pin_messages:
                return True
            elif right_type == "invite" and member.can_invite_users:
                return True
            elif right_type == "delete" and member.can_delete_messages:
                return True
            elif right_type == "change_info" and member.can_change_info:
                return True
            elif right_type == "promote" and member.can_promote_members:
                return True
            
        return False
    except UserNotParticipant:
        # User is not a participant in the chat
        return False
    except Exception as e:
        print(f"Error checking specific rights: {e}")
        return False

async def find_user_in_chat(client, chat_id, username_or_id):
    """Find a user in a chat by username or ID, with improved error handling"""
    target_user_id = None
    
    # If it's already a user ID
    if isinstance(username_or_id, int) or (isinstance(username_or_id, str) and username_or_id.isdigit()):
        target_user_id = int(username_or_id)
        return target_user_id
    
    # If it's a username
    if isinstance(username_or_id, str):
        username = username_or_id.replace("@", "")
        
        # Try multiple methods to find the user
        try:
            # Method 1: Direct get_users call
            user = await client.get_users(username)
            return user.id
        except (UsernameInvalid, PeerIdInvalid):
            # Method 2: Search in chat members
            try:
                async for member in client.get_chat_members(chat_id, query=username):
                    if member.user.username and member.user.username.lower() == username.lower():
                        return member.user.id
            except Exception as e:
                print(f"Error searching chat members: {e}")
                
            # Method 3: Try to find in recent messages
            try:
                async for message in client.get_chat_history(chat_id, limit=100):
                    if message.from_user and message.from_user.username and message.from_user.username.lower() == username.lower():
                        return message.from_user.id
            except Exception as e:
                print(f"Error searching chat history: {e}")
                
    return None

# Auto-approve join requests
@pr0fess0r_99.on_chat_join_request(filters.group)
async def auto_approve(client, message: ChatJoinRequest):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user is globally banned
    if user_id in banned_users:
        print(f"Rejected join request from banned user {user_id}")
        return

    # Check if auto-approve is enabled for this chat
    if chat_id in chat_settings and "approve" in chat_settings[chat_id]:
        if not chat_settings[chat_id]["approve"]:
            print(f"Auto-approve is disabled for chat {chat_id}")
            return
    elif APPROVED != "on":
        print(f"Auto-approve is disabled globally")
        return

    try:
        # Approve the join request
        await client.approve_chat_join_request(chat_id, user_id)
        bot_stats["total_approved"] += 1
        print(f"Approved {user_id} in {chat_id}")

        # Get custom welcome text for this chat, or use default
        welcome_text = TEXT
        if chat_id in chat_settings and "welcome_text" in chat_settings[chat_id]:
            welcome_text = chat_settings[chat_id]["welcome_text"]

        # Format the welcome message
        formatted_text = welcome_text.format(
            mention=message.from_user.mention,
            title=message.chat.title,
            first=message.from_user.first_name,
            last=message.from_user.last_name or "",
            id=message.from_user.id
        )

        # Send welcome message
        await client.send_message(chat_id, formatted_text)
        bot_stats["total_messages_sent"] += 1
    except Exception as e:
        print(f"Error in auto_approve: {e}")

# Start command
@pr0fess0r_99.on_message(filters.command(["start"]) & filters.private)
async def start_command(client, message):
    # Create inline keyboard with buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Add me to your group", url="https://t.me/AUTOAPPROVEPRO_BOT?startgroup=true"),
            InlineKeyboardButton("Support", url="https://t.me/Bot_SOURCEC")
        ],
        [
            InlineKeyboardButton("Help", callback_data="help"),
            InlineKeyboardButton("Refresh", callback_data="refresh")
        ]
    ])

    # Send welcome message with keyboard
    await message.reply(
        f"Hello {message.from_user.mention}!\n\n"
        f"I'm an Auto Approve Bot. I can approve new join requests in groups/channels automatically.\n\n"
        f"Add me to your group/channel and make me admin with 'Add Members' permission.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# Help command and callback
@pr0fess0r_99.on_message(filters.command(["help"]))
async def help_command(client, message):
    # Show maintenance team commands only to maintenance team
    is_maint = await is_maintenance_team(message.from_user.id)
    await send_help_message(client, message.chat.id, is_maint)

@pr0fess0r_99.on_callback_query(filters.regex("^help$"))
async def help_callback(client, callback_query):
    # Show maintenance team commands only to maintenance team
    is_maint = await is_maintenance_team(callback_query.from_user.id)
    await send_help_message(client, callback_query.message.chat.id, is_maint)
    await callback_query.answer()

# Refresh callback
@pr0fess0r_99.on_callback_query(filters.regex("^refresh$"))
async def refresh_callback(client, callback_query):
    await callback_query.answer("Settings refreshed!")
    
    # If in a group, refresh group settings
    if callback_query.message.chat.type in ["group", "supergroup"]:
        chat_id = callback_query.message.chat.id
        if chat_id in chat_settings:
            await callback_query.message.reply("Group settings have been refreshed.")
    else:
        # In private chat, just acknowledge
        await callback_query.message.reply("Bot settings have been refreshed.")

# Refresh command
@pr0fess0r_99.on_message(filters.command(["refresh"]))
async def refresh_command(client, message):
    chat_id = message.chat.id
    
    # If in a group, refresh group settings
    if message.chat.type in ["group", "supergroup"]:
        if chat_id in chat_settings:
            await message.reply("Group settings have been refreshed.")
        else:
            chat_settings[chat_id] = {"approve": True}
            await message.reply("Group settings have been initialized.")
    else:
        # In private chat, just acknowledge
        await message.reply("Bot settings have been refreshed.")

async def send_help_message(client, chat_id, show_admin_commands=False):
    # Regular help text for all users
    help_text = """
**🤖 Bot Commands**
• `/start` - Start the bot
• `/help` - Show this help message
• `/stats` - Show bot statistics
• `/mafia` - Start a Mafia game in the group (Public)
• `/refresh` - Refresh bot settings in a group (Public)

**🔧 Setup Commands**
• `/setwelcome` - Set a custom welcome message (Group Owner Only)
• `/addsudo` - Add a sudo user (Bot Owner Only)
• `/delsudo` - Remove a sudo user (Bot Owner Only)

**🔐 Auto-Approval Settings (Admins with "Add Users" Right Only)**
• `/approveon` - Enable auto-approval
• `/approveoff` - Disable auto-approval

**🛠️ Admin Commands (Group Only, With Specific Rights)**
• `/tag <message> <number>` - Tag members in the group
  Example: `/tag Hello everyone 10`
• `/stoptag` - Stop ongoing tagging process
• `/ban` - Ban a user (admin must have ban rights)
• `/unban` - Unban a user (admin must have unban rights)
• `/mute` - Mute a user (admin must have mute rights)
• `/unmute` - Unmute a user (admin must have unmute rights)
• `/checkadmin` - Check admin status and permissions of a user

**👥 Advanced Users Commands**
• `/toptag` - Tag leaderboard (for all advanced users)

**✨ Welcome Message Variables**
You can use these placeholders in your custom welcome messages:
• `{mention}` - Mentions the user
• `{title}` - Group/Channel title
• `{first}` - User's first name
• `{last}` - User's last name
• `{id}` - User ID
"""

    # Additional maintenance team commands
    if show_admin_commands:
        maint_text = """
**⚙️ Maintenance Team Commands (Full Access)**
• `/sudolist` - List all sudo users
• `/broadcast` - Send message to all chats
• `/gban` - Ban user globally
• `/ungban` - Unban user globally
• `/gmute` - Mute user globally
• `/ungmute` - Unmute user globally
• `/banall` - Ban all members in a group
• `/unbanall` - Unban all banned members
• `/muteall` - Mute all members in a group
• `/unmuteall` - Unmute all muted members
"""
        help_text += maint_text

    await client.send_message(chat_id=chat_id, text=help_text)

# Stats command
@pr0fess0r_99.on_message(filters.command(["stats"]))
async def show_stats(client, message):
    uptime = time.time() - bot_stats["start_time"]
    uptime_str = format_time(uptime)

    stats_text = f"""
**📊 Bot Statistics**

• **Total Approved:** {bot_stats["total_approved"]}
• **Welcome Messages Sent:** {bot_stats["total_messages_sent"]}
• **Uptime:** {uptime_str}
"""
    await message.reply(stats_text)

def format_time(seconds):
    days = int(seconds / 86400)
    seconds %= 86400
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60
    return f"{days}d {hours}h {minutes}m {int(seconds)}s"

# Custom welcome message - Updated to be restricted to group owners only
@pr0fess0r_99.on_message(filters.command(["setwelcome"]))
async def set_welcome(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user is group owner in group or channel
    if message.chat.type != "private":
        if not await is_group_owner(client, chat_id, user_id):
            # Delete command if user is not group owner
            try:
                await message.delete()
            except Exception:
                pass
            await message.reply("This command is restricted to group owners only.")
            return
    # In private chat, only maintenance team can set global welcome
    elif not await is_maintenance_team(user_id):
        await message.reply("Only maintenance team members can set global welcome messages.")
        return

    if len(message.text.split("\n", 1)) < 2:
        await message.reply(
            "Please provide a welcome message.\n\nExample:\n`/setwelcome\nHello {mention}, welcome to {title}!`\n\n"
            "Available variables: {mention}, {title}, {first}, {last}, {id}"
        )
        return

    welcome_text = message.text.split("\n", 1)[1]

    # Set welcome message for this specific chat
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {}

    chat_settings[chat_id]["welcome_text"] = welcome_text

    # If in private chat, set global welcome message
    if message.chat.type == "private":
        global TEXT
        TEXT = welcome_text
        await message.reply("Global welcome message updated!")
    else:
        await message.reply(f"Welcome message updated for this chat! Preview:\n\n{welcome_text.format(mention='@user', title='Group Name', first='John', last='Doe', id='123456')}")

# Add sudo user command - Restricted to bot owners only
@pr0fess0r_99.on_message(filters.command(["addsudo"]))
async def add_sudo(client, message):
    user_id = message.from_user.id

    # Check if user is a bot owner
    if user_id not in BOT_OWNERS:
        # Delete command if user is not a bot owner
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to bot owners only.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # Try to get user_id from command
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return

    if not target_user_id:
        await message.reply("Please specify a user to add as sudo by replying to their message or providing their ID/username.")
        return

    # Don't allow adding self as sudo (they're already a bot owner)
    if target_user_id in BOT_OWNERS:
        await message.reply("This user is already a bot owner.")
        return

    # Add user to sudo users
    if target_user_id in SUDO_USERS:
        await message.reply("This user is already a sudo user.")
        return

    SUDO_USERS.add(target_user_id)

    # Get user info for the message
    try:
        sudo_user = await client.get_users(target_user_id)
        sudo_message = f"✅ Added {sudo_user.mention} as a sudo user."
    except:
        sudo_message = f"✅ Added user with ID {target_user_id} as a sudo user."

    await message.reply(sudo_message)

# Remove sudo user command - Restricted to bot owners only
@pr0fess0r_99.on_message(filters.command(["delsudo"]))
async def del_sudo(client, message):
    user_id = message.from_user.id

    # Check if user is a bot owner
    if user_id not in BOT_OWNERS:
        # Delete command if user is not a bot owner
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to bot owners only.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # Try to get user_id from command
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return

    if not target_user_id:
        await message.reply("Please specify a sudo user to remove by replying to their message or providing their ID/username.")
        return

    # Don't allow removing bot owners from sudo
    if target_user_id in BOT_OWNERS:
        await message.reply("Cannot remove a bot owner from sudo users.")
        return

    # Remove user from sudo users
    if target_user_id not in SUDO_USERS:
        await message.reply("This user is not a sudo user.")
        return

    SUDO_USERS.remove(target_user_id)

    # Get user info for the message
    try:
        sudo_user = await client.get_users(target_user_id)
        sudo_message = f"❌ Removed {sudo_user.mention} from sudo users."
    except:
        sudo_message = f"❌ Removed user with ID {target_user_id} from sudo users."

    await message.reply(sudo_message)

# List sudo users command - Restricted to bot owners only
@pr0fess0r_99.on_message(filters.command(["sudolist"]))
async def sudo_list(client, message):
    user_id = message.from_user.id

    # Check if user is a bot owner or sudo user
    if not await is_maintenance_team(user_id):
        # Delete command if user is not authorized
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to maintenance team only.")
        return

    if not SUDO_USERS:
        await message.reply("No sudo users have been added.")
        return

    sudo_list_text = "**📋 Sudo Users List**\n\n"

    for i, sudo_id in enumerate(SUDO_USERS, 1):
        try:
            sudo_user = await client.get_users(sudo_id)
            sudo_list_text += f"{i}. {sudo_user.mention} - `{sudo_id}`\n"
        except:
            sudo_list_text += f"{i}. Unknown User - `{sudo_id}`\n"

    await message.reply(sudo_list_text)

# Tag members command
@pr0fess0r_99.on_message(filters.command(["tag", "tagall"]) & filters.group)
async def tag_members(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user is admin
    if not await is_admin_or_owner(client, chat_id, user_id):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You need to be an admin to use this command.")
        return

    # Check if tagging is already in progress
    if chat_id in tagging_in_progress and tagging_in_progress[chat_id]:
        await message.reply("Tagging is already in progress. Use `/stoptag` to stop it.")
        return

    # Parse command: /tag message [number]
    command_parts = message.text.split(" ", 1)

    if len(command_parts) < 2:
        await message.reply("Please provide a message to tag members with.\nFormat: `/tag Your message [number]`")
        return

    # Extract message and optional number
    tag_parts = command_parts[1].rsplit(" ", 1)
    tag_message = tag_parts[0]

    # Get number of members to tag (default to all if not specified or not a number)
    num_members = None  # None means tag all members
    if len(tag_parts) > 1 and tag_parts[1].isdigit():
        num_members = int(tag_parts[1])

    # Initialize tagged users for this chat if not already done
    if chat_id not in tagged_users:
        tagged_users[chat_id] = {}

    # Set tagging in progress
    tagging_in_progress[chat_id] = True

    # Get members
    status_message = await message.reply("Fetching members...")

    try:
        # Get all members
        all_members = []
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                all_members.append(member.user)

        if not all_members:
            await status_message.edit_text("No members to tag.")
            tagging_in_progress[chat_id] = False
            return

        total_members = len(all_members)

        # If number specified, limit to that many members
        members_to_tag = all_members
        if num_members is not None:
            if num_members < total_members:
                members_to_tag = random.sample(all_members, num_members)
            else:
                members_to_tag = all_members

        # Tag in groups of 5
        chunk_size = 5
        member_chunks = [members_to_tag[i:i + chunk_size] for i in range(0, len(members_to_tag), chunk_size)]

        total_chunks = len(member_chunks)
        await status_message.edit_text(f"Tagging {len(members_to_tag)} members in {total_chunks} messages...")

        for i, chunk in enumerate(member_chunks):
            # Check if tagging was stopped
            if not tagging_in_progress.get(chat_id, True):
                await status_message.edit_text("Tagging process stopped.")
                return

            mentions = ""
            for user in chunk:
                mentions += f"[{user.first_name}](tg://user?id={user.id}) "
                # Update tag count for this user
                if user.id not in tagged_users[chat_id]:
                    tagged_users[chat_id][user.id] = 0
                tagged_users[chat_id][user.id] += 1

            try:
                await client.send_message(
                    chat_id=chat_id,
                    text=f"{tag_message}\n\n{mentions}",
                    disable_web_page_preview=True
                )
                # Update status every 5 chunks
                if i % 5 == 0:
                    await status_message.edit_text(f"Tagging in progress: {i+1}/{total_chunks} messages sent")

                # Add a small delay to avoid flood limits
                await asyncio.sleep(2)
            except FloodWait as e:
                await status_message.edit_text(f"Hit rate limit. Waiting for {e.x} seconds...")
                await asyncio.sleep(e.x)
            except Exception as e:
                await message.reply(f"Error tagging members: {e}")
                tagging_in_progress[chat_id] = False
                return

        tagging_in_progress[chat_id] = False
        await status_message.edit_text(f"✅ Successfully tagged {len(members_to_tag)} members in {total_chunks} messages.")

    except Exception as e:
        tagging_in_progress[chat_id] = False
        await status_message.edit_text(f"Error fetching members: {e}")

# Stop tagging command
@pr0fess0r_99.on_message(filters.command(["stoptag"]) & filters.group)
async def stop_tag(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user is admin
    if not await is_admin_or_owner(client, chat_id, user_id):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You need to be an admin to use this command.")
        return

    if chat_id in tagging_in_progress and tagging_in_progress[chat_id]:
        tagging_in_progress[chat_id] = False
        await message.reply("✅ Tagging process stopped.")
    else:
        await message.reply("No tagging process is currently running.")

# Top tag command
@pr0fess0r_99.on_message(filters.command(["toptag"]) & filters.group)
async def top_tag(client, message):
    chat_id = message.chat.id

    # Check if there's any tag data for this chat
    if chat_id not in tagged_users or not tagged_users[chat_id]:
        await message.reply(f"No tag data available for this chat yet.")
        return

    # Sort users by tag count
    sorted_users = sorted(tagged_users[chat_id].items(), key=lambda x: x[1], reverse=True)

    # Limit to top 10
    top_users = sorted_users[:10]

    # Create message
    top_tag_text = "**👥 Top Tagged Users**\n\n"

    for i, (user_id, count) in enumerate(top_users, 1):
        try:
            user = await client.get_users(user_id)
            top_tag_text += f"{i}. {user.mention} - **{count}** tags\n"
        except:
            top_tag_text += f"{i}. User {user_id} - **{count}** tags\n"

    await message.reply(top_tag_text)

# Reset tag data command - Restricted to admins
@pr0fess0r_99.on_message(filters.command(["resettag"]) & filters.group)
async def reset_tag(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user is admin
    if not await is_admin_or_owner(client, chat_id, user_id):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You need to be an admin to use this command.")
        return

    # Reset tag data for this chat
    if chat_id in tagged_users:
        tagged_users[chat_id] = {}
        await message.reply("✅ Tag data has been reset for this chat.")
    else:
        await message.reply("No tag data exists for this chat.")

# Check admin command - Shows admin status and permissions
@pr0fess0r_99.on_message(filters.command(["checkadmin"]) & filters.group)
async def check_admin(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_user_id = None
    
    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # Try to get user_id from command
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return
    
    # If no target specified, check the command sender
    if not target_user_id:
        target_user_id = user_id
    
    try:
        # Get chat member info
        member = await client.get_chat_member(chat_id, target_user_id)
        user = member.user
        
        # Get user mention
        user_mention = user.mention
        
        # Check status
        if member.status == "creator":
            status = "👑 Owner"
        elif member.status == "administrator":
            status = "⚜️ Administrator"
        elif member.status == "member":
            status = "👤 Member"
        elif member.status == "restricted":
            status = "🔒 Restricted"
        elif member.status == "left":
            status = "🚶‍♂️ Left the chat"
        elif member.status == "banned":
            status = "🚫 Banned"
        else:
            status = f"Unknown ({member.status})"
        
        # Create permissions text for admins
        permissions = ""
        if member.status == "administrator":
            permissions += "\n\n**Admin Permissions:**\n"
            permissions += f"• Can change info: {'✅' if member.can_change_info else '❌'}\n"
            permissions += f"• Can delete messages: {'✅' if member.can_delete_messages else '❌'}\n"
            permissions += f"• Can restrict members: {'✅' if member.can_restrict_members else '❌'}\n"
            permissions += f"• Can invite users: {'✅' if member.can_invite_users else '❌'}\n"
            permissions += f"• Can pin messages: {'✅' if member.can_pin_messages else '❌'}\n"
            permissions += f"• Can promote members: {'✅' if member.can_promote_members else '❌'}\n"
            permissions += f"• Can manage voice chats: {'✅' if getattr(member, 'can_manage_voice_chats', False) else '❌'}\n"
            permissions += f"• Is anonymous: {'✅' if getattr(member, 'is_anonymous', False) else '❌'}\n"
        
        # Create message
        admin_text = f"**User Information**\n\n"
        admin_text += f"**User:** {user_mention}\n"
        admin_text += f"**ID:** `{user.id}`\n"
        admin_text += f"**Status:** {status}"
        admin_text += permissions
        
        await message.reply(admin_text)
    
    except UserNotParticipant:
        await message.reply("This user is not a member of this chat.")
    except Exception as e:
        await message.reply(f"Error checking admin status: {e}")

# Ban command
@pr0fess0r_99.on_message(filters.command(["ban"]) & filters.group)
async def ban_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has ban rights
    if not await has_specific_rights(client, chat_id, user_id, "ban"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to ban users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None
    reason = "No reason provided"

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        # Check if there's a reason provided
        if len(message.text.split(" ", 1)) > 1:
            reason = message.text.split(" ", 1)[1]
    # If command has arguments (user_id/username and optional reason)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
                await message.reply("User not found in this chat.")
                return
                
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]

    if not target_user_id:
        await message.reply("Please specify a user to ban by replying to their message or providing their ID/username.")
        return

    # Don't allow banning self
    if target_user_id == user_id:
        await message.reply("You cannot ban yourself.")
        return

    # Don't allow banning bot owners or sudo users
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot ban bot maintenance team members.")
        return

    # Check if target user is an admin
    try:
        target_member = await client.get_chat_member(chat_id, target_user_id)
        if target_member.status in ["creator", "administrator"]:
            await message.reply("Cannot ban an admin.")
            return
    except UserNotParticipant:
        # User is not in the chat, can still be banned
        pass
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Ban the user
    try:
        # Get user info for the message
        try:
            banned_user = await client.get_users(target_user_id)
            user_mention = banned_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Ban the user from the chat
        await client.ban_chat_member(chat_id, target_user_id)
        
        # Add to removed users list for this chat
        if chat_id not in removed_users:
            removed_users[chat_id] = {}
        removed_users[chat_id][target_user_id] = {
            "reason": reason,
            "type": "ban",
            "time": time.time(),
            "by": user_id
        }
        
        # Send notification in the group
        ban_message = f"🚫 {user_mention} has been banned.\n**Reason:** {reason}"
        await message.reply(ban_message)
        
        # Send notification to the banned user
        try:
            chat = await client.get_chat(chat_id)
            await client.send_message(
                target_user_id,
                f"You have been banned from {chat.title}.\n**Reason:** {reason}"
            )
        except:
            pass  # User might have blocked the bot
    except Exception as e:
        await message.reply(f"Error banning user: {e}")

# Unban command
@pr0fess0r_99.on_message(filters.command(["unban"]) & filters.group)
async def unban_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has ban rights
    if not await has_specific_rights(client, chat_id, user_id, "ban"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to unban users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
            except:
                await message.reply("User not found.")
                return

    if not target_user_id:
        await message.reply("Please specify a user to unban by replying to their message or providing their ID/username.")
        return

    # Unban the user
    try:
        # Get user info for the message
        try:
            unbanned_user = await client.get_users(target_user_id)
            user_mention = unbanned_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Unban the user from the chat
        await client.unban_chat_member(chat_id, target_user_id)
        
        # Remove from removed users list if present
        if chat_id in removed_users and target_user_id in removed_users[chat_id]:
            del removed_users[chat_id][target_user_id]
        
        # Send notification in the group
        unban_message = f"✅ {user_mention} has been unbanned."
        await message.reply(unban_message)
    except Exception as e:
        await message.reply(f"Error unbanning user: {e}")

# Mute command
@pr0fess0r_99.on_message(filters.command(["mute"]) & filters.group)
async def mute_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has restrict rights
    if not await has_specific_rights(client, chat_id, user_id, "ban"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to mute users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None
    reason = "No reason provided"

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        # Check if there's a reason provided
        if len(message.text.split(" ", 1)) > 1:
            reason = message.text.split(" ", 1)[1]
    # If command has arguments (user_id/username and optional reason)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
                await message.reply("User not found in this chat.")
                return
                
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]

    if not target_user_id:
        await message.reply("Please specify a user to mute by replying to their message or providing their ID/username.")
        return

    # Don't allow muting self
    if target_user_id == user_id:
        await message.reply("You cannot mute yourself.")
        return

    # Don't allow muting bot owners or sudo users
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot mute bot maintenance team members.")
        return

    # Check if target user is an admin
    try:
        target_member = await client.get_chat_member(chat_id, target_user_id)
        if target_member.status in ["creator", "administrator"]:
            await message.reply("Cannot mute an admin.")
            return
    except UserNotParticipant:
        await message.reply("This user is not a member of this chat.")
        return
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Mute the user
    try:
        # Get user info for the message
        try:
            muted_user = await client.get_users(target_user_id)
            user_mention = muted_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Mute the user in the chat
        await client.restrict_chat_member(
            chat_id,
            target_user_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        
        # Add to removed users list for this chat
        if chat_id not in removed_users:
            removed_users[chat_id] = {}
        removed_users[chat_id][target_user_id] = {
            "reason": reason,
            "type": "mute",
            "time": time.time(),
            "by": user_id
        }
        
        # Send notification in the group
        mute_message = f"🔇 {user_mention} has been muted.\n**Reason:** {reason}"
        await message.reply(mute_message)
        
        # Send notification to the muted user
        try:
            chat = await client.get_chat(chat_id)
            await client.send_message(
                target_user_id,
                f"You have been muted in {chat.title}.\n**Reason:** {reason}"
            )
        except:
            pass  # User might have blocked the bot
    except Exception as e:
        await message.reply(f"Error muting user: {e}")

# Unmute command
@pr0fess0r_99.on_message(filters.command(["unmute"]) & filters.group)
async def unmute_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has restrict rights
    if not await has_specific_rights(client, chat_id, user_id, "ban"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to unmute users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
                await message.reply("User not found in this chat.")
                return

    if not target_user_id:
        await message.reply("Please specify a user to unmute by replying to their message or providing their ID/username.")
        return

    # Unmute the user
    try:
        # Get user info for the message
        try:
            unmuted_user = await client.get_users(target_user_id)
            user_mention = unmuted_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Unmute the user in the chat
        await client.restrict_chat_member(
            chat_id,
            target_user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_invite_users=True,
                can_pin_messages=False,
                can_change_info=False
            )
        )
        
        # Remove from removed users list if present
        if chat_id in removed_users and target_user_id in removed_users[chat_id]:
            del removed_users[chat_id][target_user_id]
        
        # Send notification in the group
        unmute_message = f"🔊 {user_mention} has been unmuted."
        await message.reply(unmute_message)
    except Exception as e:
        await message.reply(f"Error unmuting user: {e}")

# Global ban command - Restricted to maintenance team
@pr0fess0r_99.on_message(filters.command(["gban"]))
async def global_ban(client, message):
    user_id = message.from_user.id
    
    # Check if user is in maintenance team
    if not await is_maintenance_team(user_id):
        # Delete command if user is not authorized
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to maintenance team only.")
        return
    
    # Check if the command has a reply or a user mention
    target_user_id = None
    reason = "No reason provided"
    
    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        # Check if there's a reason provided
        if len(message.text.split(" ", 1)) > 1:
            reason = message.text.split(" ", 1)[1]
    # If command has arguments (user_id/username and optional reason)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
                # Check if there's a reason provided
                if len(message.text.split(" ", 2)) > 2:
                    reason = message.text.split(" ", 2)[2]
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return
    
    if not target_user_id:
        await message.reply("Please specify a user to globally ban by replying to their message or providing their ID/username.")
        return
    
    # Don't allow banning maintenance team members
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot globally ban maintenance team members.")
        return
    
    # Add user to global ban list
    banned_users.add(target_user_id)
    
    # Get user info for the message
    try:
        banned_user = await client.get_users(target_user_id)
        user_mention = banned_user.mention
    except:
        user_mention = f"User {target_user_id}"
    
    # Send confirmation message
    gban_message = f"🌐 {user_mention} has been globally banned.\n**Reason:** {reason}"
    await message.reply(gban_message)

# Global unban command - Restricted to maintenance team
@pr0fess0r_99.on_message(filters.command(["ungban"]))
async def global_unban(client, message):
    user_id = message.from_user.id
    
    # Check if user is in maintenance team
    if not await is_maintenance_team(user_id):
        # Delete command if user is not authorized
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to maintenance team only.")
        return
    
    # Check if the command has a reply or a user mention
    target_user_id = None
    
    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return
    
    if not target_user_id:
        await message.reply("Please specify a user to globally unban by replying to their message or providing their ID/username.")
        return
    
    # Remove user from global ban list
    if target_user_id in banned_users:
        banned_users.remove(target_user_id)
        
        # Get user info for the message
        try:
            unbanned_user = await client.get_users(target_user_id)
            user_mention = unbanned_user.mention
        except:
            user_mention = f"User {target_user_id}"
        
        # Send confirmation message
        gunban_message = f"🌐 {user_mention} has been globally unbanned."
        await message.reply(gunban_message)
    else:
        await message.reply("This user is not globally banned.")

# Global mute command - Restricted to maintenance team
@pr0fess0r_99.on_message(filters.command(["gmute"]))
async def global_mute(client, message):
    user_id = message.from_user.id
    
    # Check if user is in maintenance team
    if not await is_maintenance_team(user_id):
        # Delete command if user is not authorized
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to maintenance team only.")
        return
    
    # Check if the command has a reply or a user mention
    target_user_id = None
    reason = "No reason provided"
    
    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        # Check if there's a reason provided
        if len(message.text.split(" ", 1)) > 1:
            reason = message.text.split(" ", 1)[1]
    # If command has arguments (user_id/username and optional reason)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
                # Check if there's a reason provided
                if len(message.text.split(" ", 2)) > 2:
                    reason = message.text.split(" ", 2)[2]
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return
    
    if not target_user_id:
        await message.reply("Please specify a user to globally mute by replying to their message or providing their ID/username.")
        return
    
    # Don't allow muting maintenance team members
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot globally mute maintenance team members.")
        return
    
    # Add user to global mute list
    muted_users.add(target_user_id)
    
    # Get user info for the message
    try:
        muted_user = await client.get_users(target_user_id)
        user_mention = muted_user.mention
    except:
        user_mention = f"User {target_user_id}"
    
    # Send confirmation message
    gmute_message = f"🌐 {user_mention} has been globally muted.\n**Reason:** {reason}"
    await message.reply(gmute_message)

# Global unmute command - Restricted to maintenance team
@pr0fess0r_99.on_message(filters.command(["ungmute"]))
async def global_unmute(client, message):
    user_id = message.from_user.id
    
    # Check if user is in maintenance team
    if not await is_maintenance_team(user_id):
        # Delete command if user is not authorized
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to maintenance team only.")
        return
    
    # Check if the command has a reply or a user mention
    target_user_id = None
    
    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            try:
                target_user = await client.get_users(message.command[1].replace("@", ""))
                target_user_id = target_user.id
            except Exception as e:
                await message.reply(f"Error finding user: {e}")
                return
    
    if not target_user_id:
        await message.reply("Please specify a user to globally unmute by replying to their message or providing their ID/username.")
        return
    
    # Remove user from global mute list
    if target_user_id in muted_users:
        muted_users.remove(target_user_id)
        
        # Get user info for the message
        try:
            unmuted_user = await client.get_users(target_user_id)
            user_mention = unmuted_user.mention
        except:
            user_mention = f"User {target_user_id}"
        
        # Send confirmation message
        gunmute_message = f"🌐 {user_mention} has been globally unmuted."
        await message.reply(gunmute_message)
    else:
        await message.reply("This user is not globally muted.")

# Ban all command - Restricted to maintenance team
@pr0fess0r_99.on_message(filters.command(["banall"]) & filters.group)
async def ban_all(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if user is in maintenance team
    if not await is_maintenance_team(user_id):
        # Delete command if user is not authorized
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("This command is restricted to maintenance team only.")
        return
    
    # Confirm action
    confirm_msg = await message.reply("⚠️ **WARNING**: This will ban all members in the group. Are you sure?\n\nReply with `confirm` within 30 seconds to proceed.")
    
    # Wait for confirmation
    try:
        response = await client.wait_for_message(
            filters.chat(chat_id) & 
            filters.user(user_id) & 
            filters.text & 
            filters.reply(confirm_msg.id),
            timeout=30
        )
        
        if response.text.lower() != "confirm":
             await confirm_msg.edit_text("Operation cancelled.")
            return
        
        # Start banning all members
        status_msg = await message.reply("Starting mass ban operation...")
        
        # Get all members
        members_count = 0
        banned_count = 0
        
        try:
            async for member in client.get_chat_members(chat_id):
                # Skip bots, deleted accounts, and the user executing the command
                if member.user.is_bot or member.user.is_deleted or member.user.id == user_id:
                    continue
                    
                # Skip bot owners and sudo users
                if member.user.id in BOT_OWNERS or member.user.id in SUDO_USERS:
                    continue
                    
                # Skip chat owner
                if member.status == "creator":
                    continue
                
                members_count += 1
                
                # Ban the member
                try:
                    await client.ban_chat_member(chat_id, member.user.id)
                    banned_count += 1
                    
                    # Update status every 10 bans
                    if banned_count % 10 == 0:
                        await status_msg.edit_text(f"Banning in progress... {banned_count}/{members_count} members banned.")
                    
                    # Add a small delay to avoid flood limits
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    await status_msg.edit_text(f"Hit rate limit. Waiting for {e.x} seconds...")
                    await asyncio.sleep(e.x)
                except Exception as e:
                    logger.error(f"Error banning user {member.user.id}: {e}")
            
            await status_msg.edit_text(f"✅ Operation completed. {banned_count}/{members_count} members were banned.")
        
        except Exception as e:
            await status_msg.edit_text(f"Error during mass ban operation: {e}")
    
    except asyncio.TimeoutError:
        await confirm_msg.edit_text("Confirmation timeout. Operation cancelled.")

# Kick command
@pr0fess0r_99.on_message(filters.command(["kick"]) & filters.group)
async def kick_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has ban rights
    if not await has_specific_rights(client, chat_id, user_id, "ban"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to kick users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None
    reason = "No reason provided"

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        # Check if there's a reason provided
        if len(message.text.split(" ", 1)) > 1:
            reason = message.text.split(" ", 1)[1]
    # If command has arguments (user_id/username and optional reason)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
                await message.reply("User not found in this chat.")
                return
                
            # Check if there's a reason provided
            if len(message.text.split(" ", 2)) > 2:
                reason = message.text.split(" ", 2)[2]

    if not target_user_id:
        await message.reply("Please specify a user to kick by replying to their message or providing their ID/username.")
        return

    # Don't allow kicking self
    if target_user_id == user_id:
        await message.reply("You cannot kick yourself.")
        return

    # Don't allow kicking bot owners or sudo users
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot kick bot maintenance team members.")
        return

    # Check if target user is an admin
    try:
        target_member = await client.get_chat_member(chat_id, target_user_id)
        if target_member.status in ["creator", "administrator"]:
            await message.reply("Cannot kick an admin.")
            return
    except UserNotParticipant:
        await message.reply("This user is not a member of this chat.")
        return
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Kick the user
    try:
        # Get user info for the message
        try:
            kicked_user = await client.get_users(target_user_id)
            user_mention = kicked_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Kick the user from the chat (ban and then unban)
        await client.ban_chat_member(chat_id, target_user_id)
        await client.unban_chat_member(chat_id, target_user_id)
        
        # Add to removed users list for this chat
        if chat_id not in removed_users:
            removed_users[chat_id] = {}
        removed_users[chat_id][target_user_id] = {
            "reason": reason,
            "type": "kick",
            "time": time.time(),
            "by": user_id
        }
        
        # Send notification in the group
        kick_message = f"👢 {user_mention} has been kicked.\n**Reason:** {reason}"
        await message.reply(kick_message)
        
        # Send notification to the kicked user
        try:
            chat = await client.get_chat(chat_id)
            await client.send_message(
                target_user_id,
                f"You have been kicked from {chat.title}.\n**Reason:** {reason}"
            )
        except:
            pass  # User might have blocked the bot
    except Exception as e:
        await message.reply(f"Error kicking user: {e}")

# Pin message command
@pr0fess0r_99.on_message(filters.command(["pin"]) & filters.group)
async def pin_message(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has pin rights
    if not await has_specific_rights(client, chat_id, user_id, "pin"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to pin messages.")
        return

    # Check if the command is a reply to a message
    if not message.reply_to_message:
        await message.reply("Please reply to a message to pin it.")
        return

    # Check for silent pin option
    silent = False
    if len(message.command) > 1 and message.command[1].lower() in ["silent", "quiet"]:
        silent = True

    # Pin the message
    try:
        await client.pin_chat_message(
            chat_id=chat_id,
            message_id=message.reply_to_message.id,
            disable_notification=silent
        )
        
        if silent:
            # Delete the command message to keep it clean
            try:
                await message.delete()
            except:
                pass
        else:
            await message.reply("📌 Message pinned successfully.")
    except Exception as e:
        await message.reply(f"Error pinning message: {e}")

# Unpin message command
@pr0fess0r_99.on_message(filters.command(["unpin"]) & filters.group)
async def unpin_message(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has pin rights
    if not await has_specific_rights(client, chat_id, user_id, "pin"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to unpin messages.")
        return

    # Check if the command is a reply to a message
    if message.reply_to_message:
        # Unpin specific message
        try:
            await client.unpin_chat_message(
                chat_id=chat_id,
                message_id=message.reply_to_message.id
            )
            await message.reply("📌 Message unpinned successfully.")
        except Exception as e:
            await message.reply(f"Error unpinning message: {e}")
    else:
        # Unpin the most recent pinned message
        try:
            await client.unpin_chat_message(chat_id=chat_id)
            await message.reply("📌 Most recent pinned message unpinned successfully.")
        except Exception as e:
            await message.reply(f"Error unpinning message: {e}")

# Unpin all messages command
@pr0fess0r_99.on_message(filters.command(["unpinall"]) & filters.group)
async def unpin_all_messages(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has pin rights
    if not await has_specific_rights(client, chat_id, user_id, "pin"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to unpin messages.")
        return

    # Confirm action
    confirm_msg = await message.reply("⚠️ This will unpin all pinned messages in this chat. Are you sure?\n\nReply with `confirm` within 30 seconds to proceed.")
    
    # Wait for confirmation
    try:
        response = await client.wait_for_message(
            filters.chat(chat_id) & 
            filters.user(user_id) & 
            filters.text & 
            filters.reply(confirm_msg.id),
            timeout=30
        )
        
        if response.text.lower() != "confirm":
            await confirm_msg.edit_text("Operation cancelled.")
            return
        
        # Unpin all messages
        try:
            await client.unpin_all_chat_messages(chat_id)
            await confirm_msg.edit_text("📌 All pinned messages have been unpinned.")
        except Exception as e:
            await confirm_msg.edit_text(f"Error unpinning all messages: {e}")
    
    except asyncio.TimeoutError:
        await confirm_msg.edit_text("Confirmation timeout. Operation cancelled.")

# Purge command - Delete messages in bulk
@pr0fess0r_99.on_message(filters.command(["purge"]) & filters.group)
async def purge_messages(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has delete messages rights
    if not await has_specific_rights(client, chat_id, user_id, "delete"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to delete messages.")
        return

    # Check if the command is a reply to a message
    if not message.reply_to_message:
        await message.reply("Please reply to a message to start purging from.")
        return

    # Get the message IDs to delete
    start_message_id = message.reply_to_message.id
    end_message_id = message.id

    # Count of messages to delete
    count = end_message_id - start_message_id + 1

    # Confirm if more than 50 messages
    if count > 50:
        confirm_msg = await message.reply(f"⚠️ You are about to delete {count} messages. Are you sure?\n\nReply with `confirm` within 30 seconds to proceed.")
        
        # Wait for confirmation
        try:
            response = await client.wait_for_message(
                filters.chat(chat_id) & 
                filters.user(user_id) & 
                filters.text & 
                filters.reply(confirm_msg.id),
                timeout=30
            )
            
            if response.text.lower() != "confirm":
                await confirm_msg.edit_text("Purge operation cancelled.")
                return
            
            # Delete the confirmation messages too
            await confirm_msg.delete()
            try:
                await response.delete()
            except:
                pass
        
        except asyncio.TimeoutError:
            await confirm_msg.edit_text("Confirmation timeout. Purge operation cancelled.")
            return

    # Delete messages
    deleted_count = 0
    status_message = None

    # For large purges, show a status message
    if count > 100:
        status_message = await client.send_message(chat_id, "Purging messages...")

    try:
        # Delete messages in chunks to avoid API limitations
        message_ids = list(range(start_message_id, end_message_id + 1))
        chunks = [message_ids[i:i + 100] for i in range(0, len(message_ids), 100)]
        
        for chunk in chunks:
            try:
                await client.delete_messages(chat_id, chunk)
                deleted_count += len(chunk)
                
                # Update status for large purges
                if status_message and deleted_count % 200 == 0:
                    await status_message.edit_text(f"Purged {deleted_count}/{count} messages...")
                
                # Add a small delay to avoid flood limits
                await asyncio.sleep(0.5)
            except FloodWait as e:
                if status_message:
                    await status_message.edit_text(f"Hit rate limit. Waiting for {e.x} seconds...")
                await asyncio.sleep(e.x)
            except Exception as e:
                logger.error(f"Error deleting message chunk: {e}")
        
        # Send completion message
        completion_message = await client.send_message(
            chat_id=chat_id,
            text=f"✅ Successfully purged {deleted_count} messages."
        )
        
        # Delete status message if it exists
        if status_message:
            try:
                await status_message.delete()
            except:
                pass
        
        # Auto-delete completion message after 5 seconds
        await asyncio.sleep(5)
        try:
            await completion_message.delete()
        except:
            pass
    
    except Exception as e:
        if status_message:
            await status_message.edit_text(f"Error during purge operation: {e}")
        else:
            error_message = await client.send_message(
                chat_id=chat_id,
                text=f"Error during purge operation: {e}"
            )
            # Auto-delete error message after 5 seconds
            await asyncio.sleep(5)
            try:
                await error_message.delete()
            except:
                pass

# Delete command - Delete a specific message
@pr0fess0r_99.on_message(filters.command(["del", "delete"]) & filters.group)
async def delete_message(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has delete messages rights
    if not await has_specific_rights(client, chat_id, user_id, "delete"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to delete messages.")
        return

    # Check if the command is a reply to a message
    if not message.reply_to_message:
        await message.reply("Please reply to a message to delete it.")
        return

    # Delete the replied message
    try:
        await message.reply_to_message.delete()
        
        # Delete the command message too
        try:
            await message.delete()
        except:
            pass
    except Exception as e:
        await message.reply(f"Error deleting message: {e}")

# Promote command
@pr0fess0r_99.on_message(filters.command(["promote"]) & filters.group)
async def promote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has promote rights
    if not await has_specific_rights(client, chat_id, user_id, "promote"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to promote users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
                await message.reply("User not found in this chat.")
                return

    if not target_user_id:
        await message.reply("Please specify a user to promote by replying to their message or providing their ID/username.")
        return

    # Don't allow promoting self
    if target_user_id == user_id:
        await message.reply("You cannot promote yourself.")
        return

    # Check if target user is already an admin
    try:
        target_member = await client.get_chat_member(chat_id, target_user_id)
        if target_member.status in ["creator", "administrator"]:
            await message.reply("This user is already an admin.")
            return
    except UserNotParticipant:
        await message.reply("This user is not a member of this chat.")
        return
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Parse custom title if provided
    custom_title = None
    if len(message.command) > 2:
        custom_title = " ".join(message.command[2:])
        # Limit title to 16 characters as per Telegram's limit
        if len(custom_title) > 16:
            custom_title = custom_title[:16]

    # Promote the user
    try:
        # Get user info for the message
        try:
            promoted_user = await client.get_users(target_user_id)
            user_mention = promoted_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Promote the user in the chat
        await client.promote_chat_member(
            chat_id=chat_id,
            user_id=target_user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_promote_members=False,
            can_manage_chat=True,
            can_manage_voice_chats=True
        )
        
        # Set custom title if provided
        if custom_title:
            await client.set_administrator_title(chat_id, target_user_id, custom_title)
            promote_message = f"🔰 {user_mention} has been promoted with title: **{custom_title}**"
        else:
            promote_message = f"🔰 {user_mention} has been promoted to admin."
        
        await message.reply(promote_message)
    except Exception as e:
        await message.reply(f"Error promoting user: {e}")

# Demote command
@pr0fess0r_99.on_message(filters.command(["demote"]) & filters.group)
async def demote_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has promote rights
    if not await has_specific_rights(client, chat_id, user_id, "promote"):
        # Delete command if user doesn't have rights
        try:
            await message.delete()
        except Exception:
            pass
        await message.reply("You don't have permission to demote users.")
        return

    # Check if the command has a reply or a user mention
    target_user_id = None

    # If command is a reply to a message
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    # If command has arguments (user_id or username)
    elif len(message.command) > 1:
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
                await message.reply("User not found in this chat.")
                return

    if not target_user_id:
        await message.reply("Please specify a user to demote by replying to their message or providing their ID/username.")
        return

    # Don't allow demoting self
    if target_user_id == user_id:
        await message.reply("You cannot demote yourself.")
        return

    # Don't allow demoting bot owners or sudo users
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot demote bot maintenance team members.")
        return

    # Check if target user is an admin
    try:
        target_member = await client.get_chat_member(chat_id, target_user_id)
        if target_member.status == "creator":
            await message.reply("Cannot demote the chat creator.")
            return
        elif target_member.status != "administrator":
            await message.reply("This user is not an admin.")
            return
    except UserNotParticipant:
        await message.reply("This user is not a member of this chat.")
        return
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Demote the user
    try:
        # Get user info for the message
        try:
            demoted_user = await client.get_users(target_user_id)
            user_mention = demoted_user.mention
        except:
            user_mention = f"User {target_user_id}"

        # Demote the user in the chat
        await client.promote_chat_member(
            chat_id=chat_id,
            user_id=target_user_id,
            can_change_info=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_chat=False,
            can_manage_voice_chats=False
        )
        
        demote_message = f"⬇️ {user_mention} has been demoted."
        await message.reply(demote_message)
    except Exception as e:
        await message.reply(f"Error demoting user: {e}")

# Start the bot
pr0fess0r_99.run()
