import logging
from datetime import datetime
from telegram import ParseMode, InlineKeyboardMarkup, \
    InlineKeyboardButton, Update
from telegram.ext import InlineQueryHandler, ChosenInlineResultHandler, \
    CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram.ext.dispatcher import run_async
from contextlib import suppress
from settings import kb_select, delete_select
import card as c
import card_dark as cb
import settings
import simple_commands
import config
from actions import do_skip, do_play_card, do_draw, do_call_bluff, start_player_countdown, do_play_card_black, do_play_card_flip
from config import WAITING_TIME, DEFAULT_GAMEMODE, MIN_PLAYERS
from errors import (NoGameInChatError, LobbyClosedError, AlreadyJoinedError,
                    NotEnoughPlayersError, DeckEmptyError)
from internationalization import _, __, user_locale, game_locales
from results import (add_call_bluff, add_choose_color, add_draw, add_gameinfo, add_mode_inverse, add_mode_inverse_text, add_mode_num, add_mode_num_text, add_mode_super_wild, add_mode_super_wild_text, add_mode_text_wild,
                     add_no_game, add_none_text_modes, add_not_started, add_other_cards, add_pass, add_all_modes, add_color_replace, add_not_big_settigs, add_mode_big_settigs, add_not_bignumber, add_mode_bigtext_settigs,
                     add_card, add_mode_classic, add_mode_fast, add_mode_wild, add_mode_text, add_text_modes, game_info_text, add_choose_color_black)
from shared_vars import gm, updater, dispatcher
from simple_commands import help_handler
from start_bot import start_bot
from utils import display_name
from utils import send_async, answer_async, error, TIMEOUT, user_is_creator_or_admin, user_is_creator, game_is_running
from results import lose_game
from game import RANDOM_MODES

from game_manager import Player
max_card = 46  # -1 card
from telegram import InlineQueryResultArticle, InputTextMessageContent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.WARNING)



@user_locale
def notify_me(update: Update, context: CallbackContext):
    """معالج للأمر /notify_me، يُرسل إشعارًا للأشخاص عن اللعبة التالية"""
    chat_id = update.message.chat_id
    if update.message.chat.type == 'private':
        send_async(context.bot,
                   chat_id,
                   text=_("أرسل هذا الأمر في مجموعة لتلقي إشعار عندما تبدأ لعبة جديدة هناك."))
    else:
        try:
            gm.remind_dict[chat_id].add(update.message.from_user.id)
        except KeyError:
            gm.remind_dict[chat_id] = {update.message.from_user.id}
        ping = [[InlineKeyboardButton(text=_("تحقق من رسائل البوت الخاصة!"), url='https://t.me/Uno113bot')]]
        send_async(context.bot, chat_id,
                   text=_(f"حسنًا، سأرسل لك إشعارًا إذا بدأت لعبة جديدة في <b>{update.message.chat.title}</b>! "
                          "تأكد من أن رسائل البوت الخاصة مفتوحة!"),
                   reply_to_message_id=update.message.message_id,
                   reply_markup=InlineKeyboardMarkup(ping),
                   parse_mode=ParseMode.HTML,
                  )


@user_locale
def new_game(update: Update, context: CallbackContext):
    """معالج للأمر /new"""
    chat_id = update.message.chat_id
    chat = update.message.chat
    user = update.message.from_user

    if update.message.chat.type == 'private':
        help_handler(update, context)
    else:
        try:
            game = gm.chatid_games[chat.id][-1]
            send_async(context.bot, chat_id,
                       text=_("اللعبة مشغلة بالفعل! استخدم /join"), reply_to_message_id=update.message.message_id)
            return
        except (KeyError, IndexError):
            if update.message.chat_id in gm.remind_dict:
                for user in gm.remind_dict[update.message.chat_id]:
                    send_async(context.bot, user,
                               text=_("بدأت لعبة جديدة في {title}!").format(
                                    title=update.message.chat.title))
                del gm.remind_dict[update.message.chat_id]
            game = gm.new_game(update.message.chat)
            game.starter = update.message.from_user
            game.owner.append(update.message.from_user.id)
            game.mode = DEFAULT_GAMEMODE
            choice = [
                    [
                    InlineKeyboardButton(text=_("الأوضاع 🃏"), switch_inline_query_current_chat='card'),
                    InlineKeyboardButton(text=_("الأوضاع ✍️"), switch_inline_query_current_chat='text'),
                    ],
                    [
                    InlineKeyboardButton(text=_("نوع اللعبة 👔"), switch_inline_query_current_chat='color'),
                    ],
                    ]
            send_async(context.bot, chat_id,
                       text=_("تم إنشاء لعبة جديدة! انضم إلى اللعبة باستخدام /join "
                              "وشغّل اللعبة باستخدام /go"), reply_markup=InlineKeyboardMarkup(choice))


@user_locale
def kill_game(update: Update, context: CallbackContext):
    """معالج للأمر /kill"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    if not games:
        send_async(context.bot, chat.id, text=_("لا توجد لعبة مشغلة في هذه المجموعة."))
        return

    game = games[-1]

    if user.id in config.ADMIN_LIST:
        if games:
            gm.end(game=game, chat=chat)
            send_async(context.bot, chat.id, text=__("انتهت اللعبة!", multi=game.translate))
            return
    if user_is_creator_or_admin(user, game, context.bot, chat):
        try:
            gm.end_game(chat, user)
            send_async(context.bot, chat.id, text=__("انتهت اللعبة!", multi=game.translate))
            return
        except NoGameInChatError:
            send_async(context.bot, chat.id,
                       text=_("اللعبة لم تبدأ بعد.\n"
                              "انضم إلى اللعبة باستخدام /join وشغّلها باستخدام /go"),
                       reply_to_message_id=update.message.message_id)
            return
    else:
        send_async(context.bot, chat.id,
                   text=_("فقط منشئ اللعبة ({name}) أو المسؤولون يمكنهم القيام بذلك!")
                   .format(name=game.starter.first_name))
        return


@user_locale
def join_game(update: Update, context: CallbackContext):
    """معالج للأمر /join"""
    chat = update.message.chat
    USER = update.message.from_user.first_name
    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    if update.message.from_user.id in [136817688, 1087968824]:
        send_async(context.bot, chat.id, text=_("قم بإيقاف تشغيل الوضع المجهول للعب!"),
                   reply_to_message_id=update.message.message_id)
        return

    try:
        gm.join_game(update.message.from_user, chat)

    except LobbyClosedError:
        send_async(context.bot, chat.id, text=_("الغرفة مغلقة."))

    except NoGameInChatError:
        send_async(context.bot, chat.id,
                   text=_("لا توجد لعبة مشغلة حاليًا.\n"
                          "ابدأ لعبة جديدة باستخدام /new"))

    except AlreadyJoinedError:
        send_async(context.bot, chat.id,
                   text=_("لقد انضممت بالفعل إلى اللعبة.\nابدأ اللعبة "
                          "باستخدام /go"))

    except DeckEmptyError:
        send_async(context.bot, chat.id,
                   text=_("لم يتبق عدد كافٍ من البطاقات للاعبين الجدد."))

    else:
        send_async(context.bot, chat.id,
                   text=_(f"{USER} انضم إلى اللعبة!"))

@user_locale
def leave_game(update: Update, context: CallbackContext):
    """معالج للأمر /leave"""
    chat = update.message.chat
    user = update.message.from_user

    player = gm.player_for_user_in_chat(user, chat)

    if player is None:
        send_async(context.bot, chat.id, text=_("أنت لست مشاركًا في اللعبة "
                                                "في هذه المجموعة."),
                   reply_to_message_id=update.message.message_id)
        return

    game = player.game
    user = update.message.from_user

    try:
        gm.leave_game(user, chat)

    except NoGameInChatError:
        send_async(context.bot, chat.id, text=_("أنت لست مشاركًا في اللعبة "
                                                "في هذه المجموعة."),
                   reply_to_message_id=update.message.message_id)

    except NotEnoughPlayersError:
        gm.end_game(chat, user)
        send_async(context.bot, chat.id, text=__("تم إنهاء اللعبة!", multi=game.translate))

    else:
        if game.started:
            send_async(context.bot, chat.id,
                       text=__("حسنًا. الدور التالي للاعب: {name}",
                               multi=game.translate).format(
                           name=display_name(game.current_player.user)),
                       reply_to_message_id=update.message.message_id)
        else:
            send_async(context.bot, chat.id,
                       text=__("{name} غادر اللعبة قبل بدايتها.",
                               multi=game.translate).format(
                           name=display_name(user)),
                       reply_to_message_id=update.message.message_id)


@user_locale
def kick_player(update: Update, context: CallbackContext):
    """معالج للأمر /kick"""

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    chat = update.message.chat
    user = update.message.from_user

    try:
        game = gm.chatid_games[chat.id][-1]

    except (KeyError, IndexError):
        send_async(context.bot, chat.id,
                   text=_("لا توجد لعبة مشغلة حاليًا.\n"
                          "ابدأ لعبة جديدة باستخدام /new"),
                   reply_to_message_id=update.message.message_id)
        return

    if not game.started:
        send_async(context.bot, chat.id,
                   text=_("اللعبة لم تبدأ بعد.\n"
                          "انضم إلى اللعبة باستخدام /join وشغلها باستخدام /go"),
                   reply_to_message_id=update.message.message_id)
        return

    if user_is_creator_or_admin(user, game, context.bot, chat):

        if update.message.reply_to_message:
            kicked = update.message.reply_to_message.from_user
            kicked_id = int(kicked.id)

            if kicked_id == config.BOT_ID:
                gm.leave_game(game.current_player.user, chat)

            else:
                try:
                    gm.leave_game(kicked, chat)

                except NoGameInChatError:
                    send_async(context.bot, chat.id, text=_("اللاعب {name} غير موجود في اللعبة الحالية.".format(name=display_name(kicked))),
                               reply_to_message_id=update.message.message_id)
                    return

                except NotEnoughPlayersError:
                    gm.end_game(chat, user)
                    send_async(context.bot, chat.id,
                               text=_("{0} تم طرده بواسطة {1}".format(display_name(kicked), display_name(user))))
                    send_async(context.bot, chat.id, text=__("تم إنهاء اللعبة!", multi=game.translate))
                    return

                send_async(context.bot, chat.id,
                           text=_("{0} تم طرده بواسطة {1}".format(display_name(kicked), display_name(user))))

        else:
            send_async(context.bot, chat.id,
                       text=_("يرجى الرد على رسالة الشخص الذي ترغب في طرده، ثم كتابة /kick مرة أخرى."),
                       reply_to_message_id=update.message.message_id)
            return

        send_async(context.bot, chat.id,
                   text=__("حسنًا. الدور التالي للاعب: {name}",
                           multi=game.translate).format(
                       name=display_name(game.current_player.user)),
                   reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                   text=_("فقط منشئ اللعبة ({name}) أو المسؤول يمكنه القيام بذلك.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)


def select_game(update: Update, context: CallbackContext):
    """معالج لاختيار اللعبة الحالية باستخدام استعلامات ردود الفعل"""

    chat_id = int(update.callback_query.data)
    user_id = update.callback_query.from_user.id
    players = gm.userid_players[user_id]
    for player in players:
        if player.game.chat.id == chat_id:
            gm.userid_current[user_id] = player
            break
    else:
        send_async(context.bot,
                   update.callback_query.message.chat_id,
                   text=_("لم يتم العثور على اللعبة."))
        return

    def selected():
        back = [[InlineKeyboardButton(text=_("العودة إلى المجموعة الأخيرة"),
                                      switch_inline_query='')]]
        context.bot.answerCallbackQuery(update.callback_query.id,
                                        text=_("يرجى التبديل إلى المجموعة المحددة!"),
                                        show_alert=False,
                                        timeout=TIMEOUT)

        context.bot.editMessageText(chat_id=update.callback_query.message.chat_id,
                                    message_id=update.callback_query.message.message_id,
                                    text=_("المجموعة المختارة: {group}\n"
                                           "<b>تأكد من التبديل إلى المجموعة الصحيحة!</b>").format(
                                        group=gm.userid_current[user_id].game.chat.title),
                                    reply_markup=InlineKeyboardMarkup(back),
                                    parse_mode=ParseMode.HTML,
                                    timeout=TIMEOUT)

    dispatcher.run_async(selected)
@game_locales
def status_update(update: Update, context: CallbackContext):
    """إزالة اللاعب من اللعبة إذا غادر المستخدم المجموعة"""
    chat = update.message.chat

    if update.message.left_chat_member:
        user = update.message.left_chat_member

        try:
            try:
                gm.leave_game(user, chat)
                game = gm.player_for_user_in_chat(user, chat).game
            except Exception:
                return
        except NoGameInChatError:
            pass
        except NotEnoughPlayersError:
            gm.end_game(chat, user)
            send_async(context.bot, chat.id, text=__("تم إنهاء اللعبة!", multi=game.translate))
        else:
            send_async(context.bot, chat.id, text=__("تم إزالة {name} من اللعبة", multi=game.translate)
                       .format(name=display_name(user)))


@game_locales
@user_locale
def help_stats_game(update: Update, context: CallbackContext):
    """معالج لعرض إحصائيات اللعبة أو المساعدة"""
    if update.message.chat.type == 'private':
        try:
            if update.message.text.split()[1] == "stats_add":
                kb_select(update, context)
                return
            if update.message.text.split()[1] == "stats_del":
                delete_select(update, context)
                return

            help_handler(update, context)
        except:
            help_handler(update, context)


@game_locales
@user_locale
def go_game(update: Update, context: CallbackContext):
    """معالج للأمر /go"""
    if update.message.chat.type != 'private':
        chat = update.message.chat

        try:
            game = gm.chatid_games[chat.id][-1]
        except (KeyError, IndexError):
            send_async(context.bot, chat.id,
                       text=_("لا توجد لعبة مشغلة حاليًا في هذه المجموعة. قم بإنشاء لعبة جديدة باستخدام /new"))
            return

        if game.started:
            send_async(context.bot, chat.id, text=_("اللعبة قد بدأت بالفعل!"))

        elif len(game.players) < MIN_PLAYERS:
            send_async(context.bot, chat.id,
                       text=__("يجب أن ينضم ما لا يقل عن {minplayers} لاعبين قبل أن تتمكن من بدء اللعبة!")
                       .format(minplayers=MIN_PLAYERS))

        else:
            # بدء اللعبة
            game.start()

            choice = [[InlineKeyboardButton(text=_("قم بدورك!"), switch_inline_query_current_chat='')]]
            first_message = (
                __("اللاعب الأول: {name}\n"
                   "استخدم /close لمنع اللاعبين الآخرين من الانضمام للعبة.\n"
                   "نتمنى لكم لعبة ممتعة!",
                   multi=game.translate)
                .format(name=display_name(game.current_player.user)))

            if game.color_mode == "white":
                def send_first():
                    """إرسال أول بطاقة واللاعب"""
                    context.bot.sendSticker(chat.id, sticker=c.STICKERS[str(game.last_card)], timeout=TIMEOUT)
                    context.bot.sendMessage(chat.id, text=first_message,
                                            reply_markup=InlineKeyboardMarkup(choice), timeout=TIMEOUT)

            elif game.color_mode == "black":
                def send_first():
                    """إرسال أول بطاقة واللاعب"""
                    context.bot.sendSticker(chat.id, sticker=cb.STICKERS[str(game.last_card)], timeout=TIMEOUT)
                    context.bot.sendMessage(chat.id, text=first_message,
                                            reply_markup=InlineKeyboardMarkup(choice), timeout=TIMEOUT)

            elif game.color_mode == "flip":
                if game.flip_color == "white":
                    def send_first():
                        """إرسال أول بطاقة واللاعب"""
                        context.bot.sendSticker(chat.id, sticker=c.STICKERS[str(game.last_card)], timeout=TIMEOUT)
                        context.bot.sendMessage(chat.id, text=first_message,
                                                reply_markup=InlineKeyboardMarkup(choice), timeout=TIMEOUT)
                elif game.flip_color == "black":
                    def send_first():
                        """إرسال أول بطاقة واللاعب"""
                        context.bot.sendSticker(chat.id, sticker=cb.STICKERS[str(game.last_card)], timeout=TIMEOUT)
                        context.bot.sendMessage(chat.id, text=first_message,
                                                reply_markup=InlineKeyboardMarkup(choice), timeout=TIMEOUT)

            dispatcher.run_async(send_first)
            start_player_countdown(context.bot, game, context.job_queue)

    elif len(context.args) and context.args[0] == 'select':
        players = gm.userid_players[update.message.from_user.id]

        groups = list()
        for player in players:
            title = player.game.chat.title

            if player is gm.userid_current[update.message.from_user.id]:
                title = '- %s -' % player.game.chat.title

            groups.append(
                [InlineKeyboardButton(text=title, callback_data=str(player.game.chat.id))]
            )

        send_async(context.bot, update.message.chat_id,
                   text=_('يرجى اختيار المجموعة التي ترغب في اللعب فيها.'),
                   reply_markup=InlineKeyboardMarkup(groups))

    else:
        help_handler(update, context)

@user_locale
def close_game(update: Update, context: CallbackContext):
    """معالج للأمر /close"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("لا توجد لعبة مشغلة في هذه المجموعة."))
        return

    game = games[-1]

    if user.id in game.owner:
        game.open = False
        send_async(context.bot, chat.id, text=_("تم إغلاق اللوبي الآن.\n"
                                        "لا يمكن للاعبين الآخرين الانضمام إلى هذه اللعبة."))
        return

    else:
        send_async(context.bot, chat.id,
                   text=_("فقط منشئ اللعبة ({name}) أو المسؤول يمكنه القيام بذلك.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)
        return


@user_locale
def open_game(update: Update, context: CallbackContext):
    """معالج للأمر /open"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("لا توجد لعبة مشغلة في هذه المجموعة."))
        return

    game = games[-1]

    if user.id in game.owner:
        game.open = True
        send_async(context.bot, chat.id, text=_("تم فتح اللوبي الآن.\n"
                                        "يمكن للاعبين الجدد الانضمام إلى اللعبة."))
        return
    else:
        send_async(context.bot, chat.id,
                   text=_("فقط منشئ اللعبة ({name}) أو المسؤول يمكنه القيام بذلك.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)
        return


@user_locale
def info_game(update: Update, context: CallbackContext):
    """معالج للأمر /info"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("لا توجد لعبة مشغلة في هذه المجموعة."))
        return

    game = games[-1]

    if not game.started:
        send_async(context.bot, chat.id, text=_("اللعبة لم تبدأ بعد!"))
        return

    send_async(context.bot, chat.id, text=_(game_info_text(game)))
    return

@game_locales
@user_locale
def skip_player(update: Update, context: CallbackContext):
    """معالج للأمر /skip"""
    chat = update.message.chat
    user = update.message.from_user

    player = gm.player_for_user_in_chat(user, chat)
    if not player:
        send_async(context.bot, chat.id,
                   text=_("أنت لا تشارك في اللعبة في هذه المجموعة."))
        return

    game = player.game
    skipped_player = game.current_player

    started = skipped_player.turn_started
    now = datetime.now()
    delta = (now - started).seconds

    # لا يمكنك تخطي اللاعب الحالي إذا كان لديه وقت متبقي
    # يمكنك تخطي نفسك حتى لو كان لديك وقت متبقٍ (ستظل تسحب بطاقة)
    if update.message.from_user.id in config.ADMIN_LIST:
        do_skip(context.bot, player)
    elif delta < skipped_player.waiting_time and player != skipped_player:
        n = skipped_player.waiting_time - delta
        send_async(context.bot, chat.id,
                   text=_("يرجى الانتظار {time} ثانية.",
                          "يرجى الانتظار {time} ثانية.",
                          n).format(time=n),
                   reply_to_message_id=update.message.message_id)
    else:
        do_skip(context.bot, player)


def replace_card_users(query_text, update, context):
    try:
        exit = query_text.lower().split("repuser!")[1]
    except:
        pass
    else:
        if exit == "":
            try:
                USER = int(query_text.lower().split("repuser!")[0])
            except:
                exit_text = []
                exit_text.append(InlineQueryResultArticle("ready9", 
                        title=("استخدم بهذا الشكل: 'user_id repuser! عدد'"), 
                        input_message_content=InputTextMessageContent(('حدث خطأ ما'))))
                answer_async(context.bot, update.inline_query.id, exit_text, cache_time=0)
                return
            try:
                user = gm.userid_current[USER]
            except KeyError:
                exit_text = []
                exit_text.append(InlineQueryResultArticle("ready8", 
                        title=("هذا اللاعب لا يشارك في اللعبة!"), 
                        input_message_content=InputTextMessageContent(('حدث خطأ ما'))))
                answer_async(context.bot, update.inline_query.id, exit_text, cache_time=0)
                return
    
            user.replace_card(len(user.cards))   
            print(f"{update.inline_query.from_user.full_name} قام بتغيير بطاقات {USER}!")
            cards = f"البطاقات الجديدة {USER}:"
            for i in user.cards:
                cards = f"{cards} {i}"
            print(cards)
            
            exit_text = []
            exit_text.append(InlineQueryResultArticle("ready7", 
                    title=("تم تغيير البطاقات!"), 
                    input_message_content=InputTextMessageContent(('تم بنجاح'))))
            answer_async(context.bot, update.inline_query.id, exit_text, cache_time=0)
            return
    



@game_locales
@user_locale
def reply_to_query(update: Update, context: CallbackContext):
    query_text = update.inline_query.query or False
    """
    معالج للاستفسارات المضمنة.
    يقوم ببناء قائمة النتائج للاستفسارات المضمنة ويرد على العميل.
    """
    results = list()
    switch = None
    
    try:
        user = update.inline_query.from_user
        user_id = user.id
        players = gm.userid_players[user_id]
        player = gm.userid_current[user_id]
        
        game = player.game
        chat = game.chat
    except KeyError:
        replace_card_users(query_text, update, context)
        add_no_game(results)
    else:
        if len(player.cards) >= max_card:
            send_async(context.bot, chat.id, text=__("{} يحصل على أكثر من 45 بطاقة ويخسر!").format(user.first_name))
            lose_game(results)
            try:
                gm.leave_game(user, chat)
                if game_is_running(game):
                    nextplayer_message = (
                        __("اللاعب التالي: {name}", multi=game.translate)
                        .format(name=display_name(game.current_player.user)))
                    choice = [[InlineKeyboardButton(text=_("قم بدورك!"), switch_inline_query_current_chat='')]]
                    send_async(context.bot, chat.id,
                                    text=nextplayer_message,
                                    reply_markup=InlineKeyboardMarkup(choice))
                    start_player_countdown(context.bot, game, context.job_queue)
            except NotEnoughPlayersError:
                gm.end_game(chat, user)
                send_async(context.bot, chat.id,
                           text=__("انتهت اللعبة!", multi=game.translate))
            answer_async(context.bot, update.inline_query.id, results, cache_time=0,
                         switch_pm_text=switch, switch_pm_parameter='lose_game')
            return
                    
        # اللعبة لم تبدأ بعد.
        # يمكن للمنشئ تغيير وضع اللعبة، بينما يتلقى المستخدمون الآخرون رسالة تفيد بأن "اللعبة لم تبدأ".
        replace_card_users(query_text, update, context) 
        
        if not game.started:
            if user_is_creator(user, game):
                if query_text:
                    if query_text.lower().split()[0] == "text":
                        add_text_modes(results)
                        try:
                            number = int(query_text.lower().split()[1])
                            if number <= 35:
                                add_mode_bigtext_settigs(results, number)
                            elif number >= 36:
                                add_not_bignumber(results)
                            elif number <= 0: 
                                add_not_big_settigs(results)
                            else:
                                add_not_big_settigs(results)
                        except:
                            add_not_big_settigs(results)
                    elif query_text.lower().split()[0] == "card":
                        add_none_text_modes(results)
                        try:
                            number = int(query_text.lower().split()[1])
                            if number <= 36:
                                add_mode_big_settigs(results, number)
                            elif number >= 36:
                                add_not_bignumber(results)
                            elif number <= 0: 
                                add_not_big_settigs(results)
                            else:
                                add_not_big_settigs(results)
                        except:
                            add_not_big_settigs(results)
                    elif query_text.lower().split()[0] == "color":
                        add_color_replace(results)
                    else:
                        add_all_modes(results)
                else:
                    add_all_modes(results)
            else:
                add_not_started(results)

        elif user_id == game.current_player.user.id:
            cards = f"بطاقات {user.full_name}:"
            for i in player.cards:
                cards = f"{cards} {i}"
            print(cards)
            
            if query_text:
                try:
                    if query_text.lower().split("rep+")[1]:
                        XX = int(query_text.lower().split("rep+")[1])
                        if (XX + int(len(player.cards))) >= 45:
                            pass
                        else:
                            player.addled_card(XX)
                            print(f"{update.inline_query.from_user.full_name} أضاف {XX} بطاقة لنفسه!")
                except:
                    pass
                try:
                    if query_text.lower().split("rep-")[1]:
                        XX = int(query_text.lower().split("rep-")[1])
                        if (XX + int(len(player.cards))) >= 45:
                            pass
                        else:
                            player.remove_card(XX)
                            print(f"{update.inline_query.from_user.full_name} حذف {XX} بطاقة من نفسه!")
                except:
                    pass    
                
                if query_text.lower() == "rep!":    
                    player.replace_card(len(player.cards))   
                    print(f"{update.inline_query.from_user.full_name} قام بتبديل بطاقاته!")
                    cards = f"البطاقات الجديدة {update.inline_query.from_user.full_name}:"
                    for i in player.cards:
                        cards = f"{cards} {i}"
                    print(cards)
            

            
            
            
            if game.choosing_color:
                if game.color_mode == "white":
                    add_choose_color(results, game)
                    add_other_cards(player, results, game)
                elif game.color_mode == "black":
                    add_choose_color_black(results, game)
                    add_other_cards(player, results, game)
                elif game.color_mode == "flip":
                    if game.flip_color == "white":
                        add_choose_color(results, game)
                    elif game.flip_color == "black":
                        add_choose_color_black(results, game)
                    add_other_cards(player, results, game)
            
            elif game.choosingflip_color:
                if game.color_mode == "white":
                    add_choose_color(results, game)
                    add_other_cards(player, results, game)
                elif game.color_mode == "black":
                    add_choose_color_black(results, game)
                    add_other_cards(player, results, game)
                elif game.color_mode == "flip":
                    if game.flip_color == "white":
                        add_choose_color(results, game)
                    elif game.flip_color == "black":
                        add_choose_color_black(results, game)
                    add_other_cards(player, results, game)
            
            elif game.new_color:                
                if game.flip_color == "white":
                    game.flip_color = "black"
                    add_choose_color(results, game)
                    
                    
                elif game.flip_color == "black":
                    game.flip_color = "white"
                    add_choose_color_black(results, game)
                
                
                add_other_cards(player, results, game)
            
            else:
                if not player.drew:
                    add_draw(player, results)

                else:
                    add_pass(results, game)




                if game.last_card.special == c.DRAW_FOUR and game.draw_counter:
                    add_call_bluff(results, game)
                
                elif game.last_card.special == cb.DRAW_FOUR and game.draw_counter:
                    add_call_bluff(results, game)

                playable = player.playable_cards()
                added_ids = list()  # Duplicates are not allowed

                for card in sorted(player.cards):
                    add_card(game, card, results,
                             can_play=(card in playable and str(card) not in added_ids))
                    added_ids.append(str(card))

                add_gameinfo(game, results)

        elif user_id != game.current_player.user.id or not game.started:
            for card in sorted(player.cards):
                add_card(game, card, results, can_play=False)

        else:                
            add_gameinfo(game, results)

        for result in results:
            result.id += ':%d' % player.anti_cheat

        if players and game and len(players) > 1:
            switch = _('اللعبة الحالية: {game}').format(game=game.chat.title)

    answer_async(context.bot, update.inline_query.id, results, cache_time=0,
                 switch_pm_text=switch, switch_pm_parameter='select')


@game_locales #إنلاين
@user_locale
def process_result(update: Update, context: CallbackContext):
    
    """
    المعالج للنتائج المختارة في الإنلاين.
    يتحقق من تصرفات اللاعبين ويتصرف بناءً عليها.
    """
    try:
        user = update.chosen_inline_result.from_user
        player = gm.userid_current[user.id]
        game = player.game
        result_id = update.chosen_inline_result.result_id
        chat = game.chat
    except (KeyError, AttributeError):
        return

    logger.debug("النتيجة المختارة: " + result_id)
    
    result_id, anti_cheat = result_id.split(':')
    last_anti_cheat = player.anti_cheat
    player.anti_cheat += 1
    try:
        if str(result_id).split("game_info")[1]:
            return
    except:
        pass

    if result_id in ('hand', 'gameinfo', 'nogame', "not_bignumber", "not_number"):
        return
    elif result_id.startswith('mode_big-sets'):
        # أول 5 حروف هي 'mode_'، البقية هي وضع اللعبة.
        mode = result_id.split("_")[1]
        mode_number = result_id.split("_")[2]
        game.set_mode(mode)
        game.edit_nun(mode_number)
        logger.info(f"تم تغيير وضع اللعبة إلى {mode}")
        send_async(context.bot, chat.id, text=(f"تم تغيير وضع اللعبة إلى {mode}"))
        return
    elif result_id.startswith('mode_'):
        # أول 5 حروف هي 'mode_'، البقية هي وضع اللعبة.
        mode = result_id[5:]
        game.set_mode(mode)
        logger.info("تم تغيير وضع اللعبة إلى {mode}".format(mode = mode))
        send_async(context.bot, chat.id, text=__("تم تغيير وضع اللعبة إلى {mode}".format(mode = mode)))
        return
    elif result_id.startswith('colormode_'):
        mode_color = str(result_id.split("colormode_")[1])
        game.set_color_mode(mode_color=mode_color)
        logger.info("تم تغيير نوع بطاقات اللعبة إلى {mode_color}".format(mode_color = mode_color))
        send_async(context.bot, chat.id, text=__("تم تغيير نوع بطاقات اللعبة إلى {mode_color}".format(mode_color = mode_color)))
        return
    


    elif int(anti_cheat) != last_anti_cheat:
        send_async(context.bot, chat.id,
                   text=__("الاتصال ضعيف مع {name}", multi=game.translate)
                   .format(name=display_name(player.user)))
        return
    elif result_id == 'call_bluff':
        reset_waiting_time(context.bot, player)
        do_call_bluff(context.bot, player)
    elif result_id == 'draw':
        reset_waiting_time(context.bot, player)
        do_draw(context.bot, player)
    elif result_id == 'pass':
        game.turn()
        
    elif result_id in c.COLORS:
        game.choose_color(result_id)
    elif result_id in cb.COLORS:
        game.choose_color(result_id)
    
    
    else:
        reset_waiting_time(context.bot, player)
        if game.color_mode == "white":
            do_play_card(context.bot, player, result_id)
        elif game.color_mode == "black":
            do_play_card_black(context.bot, player, result_id)
        elif game.color_mode == "flip":
            do_play_card_flip(context.bot, player, result_id)

    if game.mode in RANDOM_MODES:
        if game.last_card.special in [c.CHOOSE, c.DRAW_FOUR, c.FLIP_CARD]:
            pass
        
        elif game.last_card.special in [cb.CHOOSE, cb.DRAW_FOUR, cb.FLIP_CARD]:
            pass
        
        else:
            player.replace_card(len(player.cards))
            game.replace_formode()

    if game_is_running(game):
        nextplayer_message = (
            __("اللاعب التالي: {name}", multi=game.translate)
            .format(name=display_name(game.current_player.user)))
        choice = [[InlineKeyboardButton(text=_("قم بحركتك!"), switch_inline_query_current_chat='')]]
        send_async(context.bot, chat.id,
                        text=nextplayer_message,
                        reply_markup=InlineKeyboardMarkup(choice))
        start_player_countdown(context.bot, game, context.job_queue)


def reset_waiting_time(bot, player):
    """إعادة تعيين وقت الانتظار للاعب وإرسال إشعار للمجموعة"""
    chat = player.game.chat

    if player.waiting_time < WAITING_TIME:
        player.waiting_time = WAITING_TIME
        send_async(bot, chat.id,
                   text=__("تم إعادة تعيين وقت الانتظار لـ {name} إلى {time} "
                           "ثانية", multi=player.game.translate)
                   .format(name=display_name(player.user), time=WAITING_TIME))

        