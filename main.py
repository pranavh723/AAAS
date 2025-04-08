import os
import random
import time
from pyrogram import Client, filters
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

# Improved Mafia game command
@pr0fess0r_99.on_message(filters.command(["mafia"]) & filters.group)
async def mafia_game(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Check if a game is already in progress
    if chat_id in mafia_games and mafia_games[chat_id]["active"]:
        await message.reply("A Mafia game is already in progress in this chat.")
        return
    
    # Initialize new game
    min_players = 5  # Minimum players required
    if len(message.command) > 1 and message.command[1].isdigit():
        min_players = max(5, int(message.command[1]))  # Ensure at least 5 players
    
    # Create join button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Game", callback_data="join_mafia")],
        [InlineKeyboardButton("Start Game", callback_data="start_mafia")]
    ])
    
    # Send invitation message
    invite_msg = await message.reply(
        f"🎮 **Mafia Game**\n\n"
        f"A new Mafia game is starting! Click the button below to join.\n\n"
        f"Minimum players needed: {min_players}\n"
        f"Players joined: 1/{min_players}\n\n"
        f"Game will start automatically in 60 seconds or when enough players join."
        f"Creator: {message.from_user.mention}",
        reply_markup=keyboard
    )
    
    # Initialize game data
    mafia_games[chat_id] = {
        "active": False,
        "players": {user_id: message.from_user.first_name},
        "min_players": min_players,
        "message_id": invite_msg.id,
        "end_time": time.time() + 60,  # 60 seconds to join
        "creator": user_id,
        "roles": {},
        "leaderboard": {}
    }
    
    # Schedule game start after timeout
    asyncio.create_task(start_mafia_game_after_timeout(client, chat_id))

# Handle mafia game join button
@pr0fess0r_99.on_callback_query(filters.regex("^join_mafia$"))
async def join_mafia_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    
    # Check if game exists
    if chat_id not in mafia_games:
        await callback_query.answer("This game no longer exists.", show_alert=True)
        return
    
    # Check if game is already active
    if mafia_games[chat_id]["active"]:
        await callback_query.answer("Game already started. Wait for the next one.", show_alert=True)
        return
    
    # Check if user already joined
    if user_id in mafia_games[chat_id]["players"]:
        await callback_query.answer("You already joined this game!", show_alert=True)
        return
    
    # Add user to players
    mafia_games[chat_id]["players"][user_id] = callback_query.from_user.first_name
    
    # Update message with new player count
    player_count = len(mafia_games[chat_id]["players"])
    min_players = mafia_games[chat_id]["min_players"]
    remaining_time = int(mafia_games[chat_id]["end_time"] - time.time())
    
    if remaining_time < 0:
        remaining_time = 0
    
    try:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=mafia_games[chat_id]["message_id"],
            text=f"🎮 **Mafia Game**\n\n"
                f"A new Mafia game is starting! Click the button below to join.\n\n"
                f"Minimum players needed: {min_players}\n"
                f"Players joined: {player_count}/{min_players}\n\n"
                f"Game will start automatically in {remaining_time} seconds or when enough players join."
                f"Creator: {(await client.get_users(mafia_games[chat_id]['creator'])).mention}",
            reply_markup=callback_query.message.reply_markup
        )
    except Exception as e:
        print(f"Error updating mafia message: {e}")
    
    await callback_query.answer("You joined the game!")
    
    # Auto-start if we have enough players
    if player_count >= min_players:
        asyncio.create_task(start_mafia_game(client, chat_id))

# Handle mafia game start button
@pr0fess0r_99.on_callback_query(filters.regex("^start_mafia$"))
async def start_mafia_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    
    # Check if game exists
    if chat_id not in mafia_games:
        await callback_query.answer("This game no longer exists.", show_alert=True)
        return
    
    # Check if game is already active
    if mafia_games[chat_id]["active"]:
        await callback_query.answer("Game already started.", show_alert=True)
        return
    
    # Only creator or admin can force start
    if user_id != mafia_games[chat_id]["creator"] and not await is_admin_or_owner(client, chat_id, user_id):
        await callback_query.answer("Only the game creator or an admin can start the game.", show_alert=True)
        return
    
    # Check if we have minimum players
    if len(mafia_games[chat_id]["players"]) < 5:
        await callback_query.answer("Need at least 5 players to start the game.", show_alert=True)
        return
    
    await callback_query.answer("Starting the game!")
    asyncio.create_task(start_mafia_game(client, chat_id))

# Helper function to start mafia game after timeout
async def start_mafia_game_after_timeout(client, chat_id):
    await asyncio.sleep(60)  # Wait 60 seconds
    
    # Check if game exists and hasn't started yet
    if chat_id in mafia_games and not mafia_games[chat_id]["active"]:
        await start_mafia_game(client, chat_id)

# Helper function to start the mafia game
async def start_mafia_game(client, chat_id):
    # Check if game exists
    if chat_id not in mafia_games:
        return
    
    # Check if game already started
    if mafia_games[chat_id]["active"]:
        return
    
    # Get players
    players = mafia_games[chat_id]["players"]
    min_players = mafia_games[chat_id]["min_players"]
    
    # Check if we have enough players
    if len(players) < 5:  # Minimum 5 players required
        try:
            await client.send_message(
                chat_id=chat_id,
                text=f"❌ Not enough players joined the Mafia game. Needed at least 5, but only {len(players)} joined."
            )
        except Exception as e:
            print(f"Error sending mafia game cancellation: {e}")
        
        # Clean up
        del mafia_games[chat_id]
        return
    
    # Mark game as active
    mafia_games[chat_id]["active"] = True
    
    # Assign roles
    player_ids = list(players.keys())
    num_players = len(player_ids)
    
    # Calculate role counts
    mafia_count = max(1, num_players // 5)  # 20% are mafia
    detective_count = 1
    doctor_count = 1
    civilian_count = num_players - mafia_count - detective_count - doctor_count
    
    # Create role list and shuffle
    roles = ["Mafia"] * mafia_count + ["Detective"] * detective_count + ["Doctor"] * doctor_count + ["Civilian"] * civilian_count
    random.shuffle(roles)
    
    # Assign roles to players
    role_assignments = {}
    for i, player_id in enumerate(player_ids):
        role_assignments[player_id] = roles[i]
    
    mafia_games[chat_id]["roles"] = role_assignments
    
    # Send game start message
    game_msg = "🎭 **Mafia Game Started**\n\n"
    game_msg += f"**Total Players:** {num_players}\n"
    game_msg += f"**Mafia:** {mafia_count}\n"
    game_msg += f"**Detective:** {detective_count}\n"
    game_msg += f"**Doctor:** {doctor_count}\n"
    game_msg += f"**Civilians:** {civilian_count}\n\n"
    game_msg += "**Players:**\n"
    
    # List all players
    for player_id, player_name in players.items():
        try:
            user = await client.get_users(player_id)
            game_msg += f"• {user.mention}\n"
        except:
            game_msg += f"• {player_name}\n"
    
    game_msg += "\nRoles have been sent to each player via private message. The game will be managed manually by the players."
    
    await client.send_message(chat_id=chat_id, text=game_msg)
    
    # Send private messages to each player with their role
    for player_id, role in role_assignments.items():
        try:
            # Create role-specific instructions
            if role == "Mafia":
                role_msg = "🔪 You are a **Mafia**!\n\nYour goal is to eliminate all civilians without being caught."
                # List other mafia members if there are multiple
                if mafia_count > 1:
                    role_msg += "\n\n**Other Mafia members:**\n"
                    for p_id, p_role in role_assignments.items():
                        if p_id != player_id and p_role == "Mafia":
                            try:
                                p_user = await client.get_users(p_id)
                                role_msg += f"• {p_user.first_name} ({p_user.id})\n"
                            except:
                                role_msg += f"• {players[p_id]}\n"
            elif role == "Detective":
                role_msg = "🔍 You are a **Detective**!\n\nYour goal is to find all mafia members. You can investigate one player each night."
            elif role == "Doctor":
                role_msg = "💉 You are a **Doctor**!\n\nYour goal is to protect civilians. You can save one player each night."
            else:  # Civilian
                role_msg = "👨‍💼 You are a **Civilian**!\n\nYour goal is to find and eliminate all mafia members through discussion and voting."
            
            # Send private message with role
            await client.send_message(
                chat_id=player_id,
                text=f"**Mafia Game in {(await client.get_chat(chat_id)).title}**\n\n{role_msg}"
            )
        except Exception as e:
            print(f"Error sending role to player {player_id}: {e}")
    
    # Update leaderboard
    if "mafia_leaderboard" not in bot_stats:
        bot_stats["mafia_leaderboard"] = {}
    
    # Game will be managed manually by players
    # We'll keep the game data for leaderboard purposes
    
    # Schedule cleanup after 2 hours
    asyncio.create_task(cleanup_mafia_game(client, chat_id))

# Helper function to clean up mafia game after it's done
async def cleanup_mafia_game(client, chat_id):
    await asyncio.sleep(7200)  # 2 hours
    
    if chat_id in mafia_games:
        # Send game end message
        try:
            await client.send_message(
                chat_id=chat_id,
                text="🎮 The Mafia game session has ended. Start a new game with /mafia command!"
            )
        except:
            pass
        
        # Clean up
        del mafia_games[chat_id]

# Mafia leaderboard command
@pr0fess0r_99.on_message(filters.command(["mafialeaderboard", "mafiascore"]) & filters.group)
async def mafia_leaderboard(client, message):
    if "mafia_leaderboard" not in bot_stats or not bot_stats["mafia_leaderboard"]:
        await message.reply("No Mafia games have been played yet.")
        return
    
    leaderboard_text = "🎮 **Mafia Game Leaderboard**\n\n"
    
    # Sort players by wins
    sorted_players = sorted(bot_stats["mafia_leaderboard"].items(), key=lambda x: x[1]["wins"], reverse=True)
    
    # Show top 10
    for i, (player_id, stats) in enumerate(sorted_players[:10], 1):
        try:
            user = await client.get_users(player_id)
            player_name = user.first_name
        except:
            player_name = f"User {player_id}"
        
        wins = stats.get("wins", 0)
        games = stats.get("games", 0)
        win_rate = (wins / games * 100) if games > 0 else 0
        
        leaderboard_text += f"{i}. {player_name} - **{wins}** wins ({games} games, {win_rate:.1f}% win rate)\n"
    
    await message.reply(leaderboard_text)

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
        # First argument could be user_id or username
        if message.command[1].isdigit():
            target_user_id = int(message.command[1])
        else:
            # Try to get user from username
            target_user_id = await find_user_in_chat(client, chat_id, message.command[1])
            if not target_user_id:
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
                can_add_web_page_previews=True
            )
        )
        
        # Send notification in the group
        unmute_message = f"🔊 {user_mention} has been unmuted."
        await message.reply(unmute_message)
    except Exception as e:
        await message.reply(f"Error unmuting user: {e}")

# Global ban command
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

# Global unban command
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

# Global mute command
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

    # Don't allow muting self
    if target_user_id == user_id:
        await message.reply("You cannot mute yourself.")
        return

    # Don't allow muting bot owners or sudo users
    if target_user_id in BOT_OWNERS or target_user_id in SUDO_USERS:
        await message.reply("Cannot mute bot maintenance team members.")
        return

    # Add user to global mute list
    muted_users.add(target_user_id)

    # Get user info for the message
    try:
        muted_user = await client.get_users(target_user_id)
        mute_message = f"🌐 {muted_user.mention} has been globally muted.\n**Reason:** {reason}"
    except:
        mute_message = f"🌐 User with ID {target_user_id} has been globally muted.\n**Reason:** {reason}"

    await message.reply(mute_message)

# Global unmute command
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
        await message.reply("Please specify a user to globally unmute by replying to their message or providing their ID/username.")
        return

    # Remove user from global mute list
    if target_user_id in muted_users:
        muted_users.remove(target_user_id)

        # Get user info for the message
        try:
            unmuted_user = await client.get_users(target_user_id)
            unmute_message = f"🌐 {unmuted_user.mention} has been globally unmuted."
        except:
            unmute_message = f"🌐 User with ID {target_user_id} has been globally unmuted."

        await message.reply(unmute_message)
    else:
        await message.reply("This user is not globally muted.")

# Helper function to check if user is in maintenance team (bot owners or sudo users)
async def is_maintenance_team(user_id):
    return user_id in BOT_OWNERS or user_id in SUDO_USERS

# Helper function to check if user has ban rights
async def has_ban_rights(client, chat_id, user_id):
    # Bot owners and sudo users always have ban rights
    if await is_maintenance_team(user_id):
        return True
    
    # Check if user is admin with ban rights
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status == "creator":
            return True
        if member.status == "administrator" and member.can_restrict_members:
            return True
    except Exception:
        pass
    
    return False

# Helper function to check if user is admin or owner
async def is_admin_or_owner(client, chat_id, user_id):
    # Bot owners and sudo users are always considered admins
    if await is_maintenance_team(user_id):
        return True
    
    # Check if user is admin
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return True
    except Exception:
        pass
    
    return False

# Helper function to find a user in a chat by username
async def find_user_in_chat(client, chat_id, username):
    username = username.replace("@", "")
    
    try:
        # Try to get user directly by username
        user = await client.get_users(username)
        if user:
            return user.id
    except:
        pass
    
    # If direct lookup fails, search through chat members
    try:
        async for member in client.get_chat_members(chat_id):
            if member.user.username and member.user.username.lower() == username.lower():
                return member.user.id
    except Exception:
        pass
    
    return None

# Save bot stats periodically
async def save_stats_periodically():
    while True:
        await asyncio.sleep(300)  # Save every 5 minutes
        save_stats()

# Save stats to file
def save_stats():
    try:
        with open("bot_stats.json", "w") as f:
            json.dump(bot_stats, f)
    except Exception as e:
        print(f"Error saving stats: {e}")

# Load stats from file
def load_stats():
    global bot_stats
    try:
        if os.path.exists("bot_stats.json"):
            with open("bot_stats.json", "r") as f:
                bot_stats = json.load(f)
    except Exception as e:
        print(f"Error loading stats: {e}")

# Save chat settings periodically
async def save_settings_periodically():
    while True:
        await asyncio.sleep(300)  # Save every 5 minutes
        save_settings()

# Save settings to file
def save_settings():
    try:
        with open("chat_settings.json", "w") as f:
            json.dump(chat_settings, f)
    except Exception as e:
        print(f"Error saving settings: {e}")

# Load settings from file
def load_settings():
    global chat_settings
    try:
        if os.path.exists("chat_settings.json"):
            with open("chat_settings.json", "r") as f:
                chat_settings = json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")

# Main function to start the bot
async def main():
    # Load stats and settings
    load_stats()
    load_settings()
    
    # Start periodic saving tasks
    asyncio.create_task(save_stats_periodically())
    asyncio.create_task(save_settings_periodically())
    
    # Start the bot
    await pr0fess0r_99.start()
    
    # Get bot info
    bot_info = await pr0fess0r_99.get_me()
    print(f"Bot started as @{bot_info.username}")
    
    # Keep the bot running
    await idle()
    
    # Save stats and settings before stopping
    save_stats()
    save_settings()
    
    # Stop the bot
    await pr0fess0r_99.stop()

# Run the bot
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
