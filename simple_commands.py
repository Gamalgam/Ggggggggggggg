
from telegram import ParseMode, InlineKeyboardMarkup, \
    InlineKeyboardButton, Update

from telegram import ParseMode, Update
from telegram.ext import CommandHandler, CallbackContext
from asyncio import sleep
from user_setting import UserSetting
from utils import send_async
from shared_vars import dispatcher
from internationalization import _, user_locale
from contextlib import suppress
import subprocess
import time

ADMIN = 7386549277


@user_locale
def help_handler(update: Update, context: CallbackContext):
    """معالج لأمر /help"""
    help_text = _(
"""<b>اتبع هذه الخطوات:</b>
1. أضف هذا البوت إلى المجموعة
2. في المجموعة، ابدأ لعبة جديدة باستخدام /new أو انضم إلى لعبة موجودة بالفعل
ابدأ اللعبة بـ /join
«3. بعد انضمام لاعبين على الأقل، ابدأ اللعبة باستخدام»
/go
4. أدخل <code>@uno113bot</code> في نافذة الدردشة واضغط على <b>مسافة</b>. 
سترى بطاقاتك (تم تمييز بعضها باللون الرمادي)، 
أي خيارات إضافية، مثل الرسم و <b>?</b> لرؤية 
الحالة الحالية للعبة. <b>البطاقات الرمادية</b> هي تلك التي 
<b>لا يمكن لعبها</b> في الوقت الحالي. 
اضغط على الخيار لتنفيذ 
الإجراء المختار.
يمكن للاعبين الانضمام إلى اللعبة في أي وقت. (إذا كانت اللعبة مفتوحة)
لمغادرة اللعبة، استخدم /leave. 
إذا استغرق اللاعب أكثر من 90 ثانية للعب، 
يمكنك استخدام /skip لتخطي هذا اللاعب. 
استخدم /notify_me لتلقي رسالة شخصية عند بدء لعبة جديدة.


<b>الإحصائيات:</b>
/stats - عرض إحصائيات ألعابك
/delstats - حذف إحصائيات ألعابك

<b>أوامر أخرى (فقط لمنشئ اللعبة):</b>
/close - إغلاق اللوبي
/open - فتح اللوبي
/kill - إنهاء اللعبة
/kick - طرد لاعب من اللعبة 
(ردًا على رسالة المستخدم)""")
    send_async(context.bot, update.message.chat_id, text=help_text,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True)



@user_locale
def modes(update: Update, context: CallbackContext):
    """معالج لأمر /help"""
    modes_explanation = _(
"""
<b>يحتوي هذا الروبوت UNO على عدة أوضاع للعبة</b>:
🎻في الوضع الكلاسيكي، يتم استخدام مجموعة ورق UNO العادية ولا يوجد تخطي تلقائي.
🔢في وضع "<b>الأرقام</b>"، يتم استخدام مجموعة ورق UNO بدون الأوراق الخاصة ولا يوجد تخطي تلقائي.
🔁في وضع "<b>العكس</b>"، يتم استخدام مجموعة ورق UNO العادية، لكن يتم عكس كل الإجراءات، ولا يوجد تخطي تلقائي.
🎻في الوضع الكلاسيكي، يتم استخدام مجموعة ورق UNO العادية ولا يوجد تخطي تلقائي.
🚀في وضع "<b>السريع</b>"، يتم استخدام مجموعة ورق UNO العادية، ويتم تخطي اللاعب تلقائيًا إذا تأخر كثيرًا في لعب دوره.
🐉في وضع "<b>الطبيعة البرية</b>"، يتم استخدام مجموعة ورق تحتوي على العديد من الأوراق الخاصة، وتنوع أقل في الأرقام، بدون تخطي تلقائي.
🔥🐉في وضع "<b>الطبيعة البرية الخطيرة</b>"، يتم استخدام مجموعة أوراق تحتوي فقط على الأوراق الخاصة.
🌎في وضع "<b>العالم الكبير</b>"، يتم استخدام مجموعة ورق UNO العادية، ولكن في بداية اللعبة يتم توزيع <b>الكثير</b> من الأوراق.
🌎🐉في وضع "<b>العالم البري الكبير</b>"، يتم استخدام مجموعة ورق تحتوي على العديد من الأوراق الخاصة، وتوزيع كميات كبيرة من الأوراق في البداية. بدون تخطي تلقائي.
🌎⚙️في وضع "<b>العالم القابل للتخصيص</b>"، يتم استخدام مجموعة ورق UNO العادية، ولكن في بداية اللعبة يتم توزيع العدد الذي تحدده من الأوراق (بحد أقصى 35).
🪐في وضع "<b>العالم العشوائي</b>"، يتم استخدام مجموعة ورق UNO العادية، ولكن في كل جولة تتغير أوراق اللاعبين!
(<b>كما أن لكل هذه الأوضاع نسخة نصية ✍️</b>)

<b>أيضًا، يحتوي هذا الروبوت على عدة أنواع من الألعاب</b>:
"<b>🤍 الأوراق البيضاء</b>" - في هذا النوع من اللعبة يتم استخدام الأوراق العادية البيضاء.
"<b>🖤 الأوراق السوداء</b>" - في هذا النوع من اللعبة يتم استخدام الأوراق السوداء غير التقليدية.
"<b>🔀 أوراق Flip</b>" - في هذا النوع من اللعبة يتم استخدام مجموعتين من الأوراق في نفس الوقت!
<i>لتغيير المجموعة، يجب أن تلعب بورقة خاصة، وبعد ذلك يحدث "تبديل" وتتحول الأوراق.</i>

<b><i>لاحظ أنه إذا جمعت أكثر من 45 ورقة، ستخسر!</i></b>
لتغيير وضع اللعبة، يجب على <u>منشئ اللعبة</u> إدخال اسم الروبوت ومسافة، تمامًا كما يتم لعب ورقة، وستظهر جميع خيارات وضع اللعبة.
(<i>أو يمكنك استخدام الأزرار التي تظهر عند إنشاء لعبة جديدة</i>)
""")
    
    send_async(context.bot, update.message.chat_id, text=modes_explanation,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@user_locale
def source(update: Update, context: CallbackContext):
    """معالج لأمر /help"""
    source_text = _('هذا الروبوت هو نسخة من برنامج مجاني. ويخضع لترخيص "<b>AGPL</b>".\n'
      "<b>الكود الأصلي متاح هنا:</b> \n"
      "https://github.com/Dimoka113/Uno113bot")
    attributions = _("النسب:\n"
      '"<b>رمز Draw من:</b> '
      '<a href="http://www.faithtoken.com/">Faithtoken</a>\n'
      '"<b>رمز Pass من:</b> '
      '<a href="http://delapouite.com/">Delapouite</a>\n'
      "النسخ الأصلية متاحة على: http://game-icons.net\n"
      "الأيقونات، المحررة بواسطة <b>ɳick</b>\n"
      "الترجمة إلى الروسية، <a href='https://www.unorules.com/uno-flip-rules/'>uno flip</a> والتصحيح: <a href='https://t.me/This113bots'>This113bots</a>\n"
      "شكر خاص لـ: <a href='tg://user?id=1956508438'>MrKoteyka</a>")

    send_async(context.bot, update.message.chat_id, text=source_text + '\n' +
                                                 attributions,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@user_locale
def news(update: Update, context: CallbackContext):
    """معالج لأمر /news"""
    chat = update.message.chat
    ping = [[InlineKeyboardButton(text=_("👨‍💻This113bots"), url='https://t.me/This113bots')]]
    send_async(context.bot, chat.id,      
                    text=_("يمكنك قراءة أخبار البوتات هنا 👇"),
                      reply_markup=InlineKeyboardMarkup(ping),
                      parse_mode=ParseMode.HTML)


@user_locale
def stats(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat = update.message.chat
    us = UserSetting.get(id=user.id)
    if not us or not us.stats:
          ping = [[InlineKeyboardButton(text=_("تفعيل الإحصاءات!"), url='https://t.me/Uno113bot?start=stats_add')]]
          send_async(context.bot, chat.id,      
                    text=_("يرجى تفعيل الإحصاءات في الدردشة الخاصة مع البوت."),
                      reply_to_message_id=update.message.message_id,
                      reply_markup=InlineKeyboardMarkup(ping),
                      parse_mode=ParseMode.HTML)

    else:
        stats_text = list()

        n = us.games_played
        stats_text.append(
            _("الألعاب التي تم لعبها: {number}",
              "الألعاب التي تم لعبها: {number}",
              n).format(number=n)
        )

        n = us.first_places
        m = round((us.first_places / us.games_played) * 100) if us.games_played else 0
        stats_text.append(
            _("الألعاب التي تم الفوز بها: {number}. ({percent}%)",
              "الألعاب التي تم الفوز بها: {number}. ({percent}%)",
              n).format(number=n, percent=m)
        )

        n = us.cards_played
        stats_text.append(
            _("البطاقات المستخدمة: {number}",
              "البطاقات المستخدمة: {number}",
              n).format(number=n)
        )

        send_async(context.bot, update.message.chat_id,
                   text='\n'.join(stats_text))





def register():
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CommandHandler('source', source))
    dispatcher.add_handler(CommandHandler('news', news))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('modes', modes))
