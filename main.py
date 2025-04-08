import os
import random
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, User, ChatJoinRequest, ChatPermissions
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired
import asyncio
from keepalive import keep_alive
keep_alive()

# Bot owners and sudo users lists
BOT_OWNERS = [6985505204,7335254391]  # List of bot owner IDs
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
BOT_OWNERS = [6985505204] 
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

# Store tagging state
tagging_in_progress = {}
tagged_users = {}

# Helper functions
# Remove the duplicate functions and keep only the fixed versions
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
        # Print debug info
        print(f"Admin check for {user_id} in {chat_id}: status={member.status}")
        # Check if user is creator or administrator
        return member.status in ["creator", "administrator"] or "owner" in str(member.status).lower()
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
    except Exception as e:
        print(f"Error checking ban rights: {e}")
        return False

# Auto-approve join requests
@pr0fess0r_99.on_chat_join_request(filters.group)
async def auto_approve(client, message: ChatJoinRequest):
    # ... existing code ...
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
            InlineKeyboardButton("Help", callback_data="help")
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

**👥 Advanced Users Commands**
• `/toptag` - Tag leaderboard (for all advanced users)
• `/checkadmin` - Check admin status of a user

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
        await message.reply("No tag data available for this chat yet.")
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

# New Mafia game command - Can be used by anyone
@pr0fess0r_99.on_message(filters.command(["mafia"]) & filters.group)
async def mafia_game(client, message):
    chat_id = message.chat.id

    # Get number of players (default to 10)
    num_players = 10
    if len(message.command) > 1 and message.command[1].isdigit():
        num_players = int(message.command[1])
        if num_players < 4:
            await message.reply("You need at least 4 players for a Mafia game.")
            return
        if num_players > 20:
            num_players = 20  # Limit to 20 players max

    # Get members
    status_message = await message.reply("🎮 Setting up Mafia game...")

    try:
        # Get all members
        all_members = []
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot and not member.user.is_deleted:
                all_members.append(member.user)

        if len(all_members) < num_players:
            await status_message.edit_text(f"Not enough members in the group. Need {num_players} players but only found {len(all_members)}.")
            return

        # Select random players
        players = random.sample(all_members, num_players)

        # Assign roles
        mafia_count = max(1, num_players // 5)  # 20% are mafia
        detective_count = 1
        doctor_count = 1

        roles = ["Mafia"] * mafia_count + ["Detective"] * detective_count + ["Doctor"] * doctor_count
        roles += ["Civilian"] * (num_players - len(roles))
        random.shuffle(roles)

        # Create game message
        game_msg = "🎭 **Mafia Game Setup**\n\n"
        game_msg += f"**Total Players:** {num_players}\n"
        game_msg += f"**Mafia:** {mafia_count}\n"
        game_msg += f"**Detective:** {detective_count}\n"
        game_msg += f"**Doctor:** {doctor_count}\n"
        game_msg += f"**Civilians:** {num_players - mafia_count - detective_count - doctor_count}\n\n"

        # Send roles to each player privately
        for i, player in enumerate(players):
            role = roles[i]
            try:
                await client.send_message(
                    player.id,
                    f"🎮 **Mafia Game in {message.chat.title}**\n\nYour role is: **{role}**\n\n"
                    f"{'🔪 You are a Mafia. Kill civilians at night and blend in during the day.' if role == 'Mafia' else ''}"
                    f"{'🔍 You are a Detective. You can investigate one player each night to determine if they are Mafia.' if role == 'Detective' else ''}"
                    f"{'💉 You are a Doctor. You can save one player each night from being killed.' if role == 'Doctor' else ''}"
                    f"{'👨‍👩‍👧‍👦 You are a Civilian. Find the Mafia before they kill everyone!' if role == 'Civilian' else ''}"
                )
                game_msg += f"• {player.mention} has received their role.\n"
            except Exception as e:
                game_msg += f"• {player.mention} could not receive their role (make sure they've started the bot).\n"
                print(f"Error sending role to {player.id}: {e}")

        # Send final game setup message
        await status_message.edit_text(game_msg)

        # Send game instructions
        instructions = """
**🎲 How to Play Mafia:**

1. The game alternates between "day" and "night" phases.
2. During the night, the Mafia chooses someone to kill, the Detective investigates a player, and the Doctor saves someone.
3. During the day, all players discuss who they think is Mafia and vote to eliminate one person.
4. The game continues until either all Mafia are eliminated (Town wins) or the Mafia outnumbers the Town (Mafia wins).

This is just a role assignment - continue the game through discussion in the group!
"""
        await client.send_message(chat_id, instructions)

    except Exception as e:
        await status_message.edit_text(f"Error setting up Mafia game: {e}")

# Add a debug command to check admin status
@pr0fess0r_99.on_message(filters.command(["checkadmin"]) & filters.group)
async def check_admin_status(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # If replying to someone, check their admin status
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user
    else:
        target_user_id = user_id
        target_user = message.from_user

    try:
        # Get detailed member info
        member = await client.get_chat_member(chat_id, target_user_id)

        # Create detailed status message
        status_text = f"👤 **Admin Status Check for {target_user.mention}**\n\n"
        status_text += f"**User ID:** `{target_user_id}`\n"
        status_text += f"**Status:** {member.status}\n\n"

        if member.status == "administrator":
            status_text += "**Admin Permissions:**\n"
            status_text += f"- Can change info: {member.can_change_info}\n"
            status_text += f"- Can delete messages: {member.can_delete_messages}\n"
            status_text += f"- Can restrict members: {member.can_restrict_members}\n"
            status_text += f"- Can invite users: {member.can_invite_users}\n"
            status_text += f"- Can pin messages: {member.can_pin_messages}\n"
            status_text += f"- Can promote members: {member.can_promote_members}\n"

        # Check using our functions
        is_admin = await is_admin_or_owner(client, chat_id, target_user_id)
        has_ban = await has_ban_rights(client, chat_id, target_user_id)

        status_text += f"\n**Function Checks:**\n"
        status_text += f"- is_admin_or_owner: {is_admin}\n"
        status_text += f"- has_ban_rights: {has_ban}\n"

        await message.reply(status_text)
    except Exception as e:
        await message.reply(f"Error checking admin status: {e}")

# Enable/disable auto-approve commands
@pr0fess0r_99.on_message(filters.command(["approveon"]) & filters.group)
async def approve_on(client, message):
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

    # Enable auto-approve for this chat
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {}

    chat_settings[chat_id]["approve"] = True

    await message.reply("✅ Auto-approve has been enabled for this chat.")

@pr0fess0r_99.on_message(filters.command(["approveoff"]) & filters.group)
async def approve_off(client, message):
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

    # Disable auto-approve for this chat
    if chat_id not in chat_settings:
        chat_settings[chat_id] = {}

    chat_settings[chat_id]["approve"] = False

    await message.reply("❌ Auto-approve has been disabled for this chat.")

# Ban command
@pr0fess0r_99.on_message(filters.command(["ban"]) & filters.group)
async def ban_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has ban rights
    if not await has_ban_rights(client, chat_id, user_id):
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
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Ban the user
    try:
        await client.ban_chat_member(chat_id, target_user_id)

        # Get user info for the message
        try:
            banned_user = await client.get_users(target_user_id)
            ban_message = f"🚫 {banned_user.mention} has been banned.\n**Reason:** {reason}"
        except:
            ban_message = f"🚫 User with ID {target_user_id} has been banned.\n**Reason:** {reason}"

        await message.reply(ban_message)
    except Exception as e:
        await message.reply(f"Error banning user: {e}")

# Unban command
@pr0fess0r_99.on_message(filters.command(["unban"]) & filters.group)
async def unban_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has ban rights
    if not await has_ban_rights(client, chat_id, user_id):
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
        await message.reply("Please specify a user to unban by replying to their message or providing their ID/username.")
        return

    # Unban the user
    try:
        await client.unban_chat_member(chat_id, target_user_id)

        # Get user info for the message
        try:
            unbanned_user = await client.get_users(target_user_id)
            unban_message = f"✅ {unbanned_user.mention} has been unbanned."
        except:
            unban_message = f"✅ User with ID {target_user_id} has been unbanned."

        await message.reply(unban_message)
    except Exception as e:
        await message.reply(f"Error unbanning user: {e}")

# Mute command
@pr0fess0r_99.on_message(filters.command(["mute"]) & filters.group)
async def mute_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has restrict rights
    if not await has_ban_rights(client, chat_id, user_id):
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
    except Exception as e:
        await message.reply(f"Error checking target user status: {e}")
        return

    # Mute the user
    try:
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

        # Get user info for the message
        try:
            muted_user = await client.get_users(target_user_id)
            mute_message = f"🔇 {muted_user.mention} has been muted.\n**Reason:** {reason}"
        except:
            mute_message = f"🔇 User with ID {target_user_id} has been muted.\n**Reason:** {reason}"

        await message.reply(mute_message)
    except Exception as e:
        await message.reply(f"Error muting user: {e}")

# Unmute command
@pr0fess0r_99.on_message(filters.command(["unmute"]) & filters.group)
async def unmute_user(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if user has restrict rights
    if not await has_ban_rights(client, chat_id, user_id):
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
        await message.reply("Please specify a user to unmute by replying to their message or providing their ID/username.")
        return

    # Unmute the user
    try:
        await client.restrict_chat_member(
            chat_id, 
            target_user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )

        # Get user info for the message
        try:
            unmuted_user = await client.get_users(target_user_id)
            unmute_message = f"🔊 {unmuted_user.mention} has been unmuted."
        except:
            unmute_message = f"🔊 User with ID {target_user_id} has been unmuted."

        await message.reply(unmute_message)
    except Exception as e:
        await message.reply(f"Error unmuting user: {e}")
# ... existing code ...

# Broadcast command - Restricted to maintenance team
@pr0fess0r_99.on_message(filters.command(["broadcast"]))
async def broadcast_message(client, message):
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
    
    # Check if there's a message to broadcast
    if len(message.text.split("\n", 1)) < 2 and not message.reply_to_message:
        await message.reply(
            "Please provide a message to broadcast.\n\nExample:\n`/broadcast\nHello everyone! This is an announcement.`\n\n"
            "Or reply to a message with `/broadcast`"
        )
        return
    
    # Get the message to broadcast
    if message.reply_to_message:
        broadcast_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        # If replying to media
        media = None
        if message.reply_to_message.photo:
            media = message.reply_to_message.photo.file_id
            media_type = "photo"
        elif message.reply_to_message.video:
            media = message.reply_to_message.video.file_id
            media_type = "video"
        elif message.reply_to_message.document:
            media = message.reply_to_message.document.file_id
            media_type = "document"
        elif message.reply_to_message.audio:
            media = message.reply_to_message.audio.file_id
            media_type = "audio"
        elif message.reply_to_message.voice:
            media = message.reply_to_message.voice.file_id
            media_type = "voice"
    else:
        broadcast_text = message.text.split("\n", 1)[1]
        media = None
        media_type = None
    
    # Start broadcasting
    status_message = await message.reply("🔄 Starting broadcast...")
    
    # Get all chats where the bot is present
    all_chats = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in ["group", "supergroup", "channel"]:
            all_chats.append(dialog.chat.id)
    
    if not all_chats:
        await status_message.edit_text("No chats found to broadcast to.")
        return
    
    # Initialize counters
    success_count = 0
    failed_count = 0
    
    # Update status message
    await status_message.edit_text(f"🔄 Broadcasting to {len(all_chats)} chats...")
    
    # Send message to each chat
    for i, chat_id in enumerate(all_chats):
        try:
            if media:
                if media_type == "photo":
                    await client.send_photo(chat_id, media, caption=broadcast_text)
                elif media_type == "video":
                    await client.send_video(chat_id, media, caption=broadcast_text)
                elif media_type == "document":
                    await client.send_document(chat_id, media, caption=broadcast_text)
                elif media_type == "audio":
                    await client.send_audio(chat_id, media, caption=broadcast_text)
                elif media_type == "voice":
                    await client.send_voice(chat_id, media, caption=broadcast_text)
            else:
                await client.send_message(chat_id, broadcast_text)
            
            success_count += 1
            
            # Update status every 10 chats
            if i % 10 == 0:
                await status_message.edit_text(
                    f"🔄 Broadcasting: {i+1}/{len(all_chats)} chats\n"
                    f"✅ Success: {success_count}\n"
                    f"❌ Failed: {failed_count}"
                )
            
            # Add a small delay to avoid flood limits
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await status_message.edit_text(f"Hit rate limit. Waiting for {e.x} seconds...")
            await asyncio.sleep(e.x)
            # Try again
            try:
                if media:
                    if media_type == "photo":
                        await client.send_photo(chat_id, media, caption=broadcast_text)
                    elif media_type == "video":
                        await client.send_video(chat_id, media, caption=broadcast_text)
                    elif media_type == "document":
                        await client.send_document(chat_id, media, caption=broadcast_text)
                    elif media_type == "audio":
                        await client.send_audio(chat_id, media, caption=broadcast_text)
                    elif media_type == "voice":
                        await client.send_voice(chat_id, media, caption=broadcast_text)
                else:
                    await client.send_message(chat_id, broadcast_text)
                success_count += 1
            except Exception:
                failed_count += 1
        except Exception as e:
            print(f"Error broadcasting to {chat_id}: {e}")
            failed_count += 1
    
    # Final status update
    await status_message.edit_text(
        f"✅ Broadcast completed!\n\n"
        f"📊 **Statistics:**\n"
        f"• Total chats: {len(all_chats)}\n"
        f"• Successful: {success_count}\n"
        f"• Failed: {failed_count}"
    )

# ... rest of your code ...
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

    # Don't allow banning self
    if target_user_id == user_id:
        await message.reply("You cannot ban yourself.")
        return

    # Don't allow banning bot owners or sudo users
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot ban bot maintenance team members.")
        return

    # Add user to global ban list
    banned_users.add(target_user_id)

    # Get user info for the message
    try:
        banned_user = await client.get_users(target_user_id)
        ban_message = f"🌐 {banned_user.mention} has been globally banned.\n**Reason:** {reason}"
    except:
        ban_message = f"🌐 User with ID {target_user_id} has been globally banned.\n**Reason:** {reason}"

    await message.reply(ban_message)

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
        await message.reply("Please specify a user to globally unban by replying to their message or providing their ID/username.")
        return

    # Remove user from global ban list
    if target_user_id in banned_users:
        banned_users.remove(target_user_id)

        # Get user info for the message
        try:
            unbanned_user = await client.get_users(target_user_id)
            unban_message = f"🌐 {unbanned_user.mention} has been globally unbanned."
        except:
            unban_message = f"🌐 User with ID {target_user_id} has been globally unbanned."

        await message.reply(unban_message)
    else:
        await message.reply("This user is not globally banned.")

# Refresh command - Can be used by anyone in a group
@pr0fess0r_99.on_message(filters.command(["refresh"]) & filters.group)
async def refresh_settings(client, message):
    chat_id = message.chat.id

    # Reset chat settings for this chat
    if chat_id in chat_settings:
        # Keep welcome text if it exists
        welcome_text = chat_settings[chat_id].get("welcome_text", None)
        chat_settings[chat_id] = {}
        if welcome_text:
            chat_settings[chat_id]["welcome_text"] = welcome_text

    await message.reply("✅ Bot settings have been refreshed for this chat.")

# Run the bot
print("Bot is starting...")

# --- Keep Alive Server ---

pr0fess0r_99.run()
