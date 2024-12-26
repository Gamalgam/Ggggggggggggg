#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram bot to play UNO in group chats
# Copyright (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""Defines helper functions to build the inline result list"""

import numbers
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedSticker as Sticker
import card_dark as cb
import card as c
from utils import display_color, display_color_group, display_name, display_color_dark, display_color_group_dark
from internationalization import _, __


def add_choose_color(results, game):
    """Add choose color options"""
    for color in c.COLORS:
        results.append(
            InlineQueryResultArticle(
                id=color,
                title=_("اختر اللون"),
                description=display_color(color),
                input_message_content=InputTextMessageContent(
                    display_color_group(color, game))
            )
        )


def add_choose_color_black(results, game):
    """Add choose color options"""
    for color in cb.COLORS:
        results.append(
            InlineQueryResultArticle(
                id=color,
                title=_("اختر اللون"),
                description=display_color_dark(color),
                input_message_content=InputTextMessageContent(
                    display_color_group_dark(color, game))
            )
        )


def add_other_cards(player, results, game):
    """إضافة بطاقات اليد عند اختيار الألوان"""
    player.cards.sort()
    results.append(
        InlineQueryResultArticle(
            "hand",
            title=_("بطاقة (اضغط لرؤية حالة اللعبة):",
                    "بطاقات (اضغط لرؤية حالة اللعبة):",
                    len(player.cards)),
            description=', '.join([repr(card) for card in (player.cards)]),
            input_message_content=game_info(game)
        )
    )


def player_list(game):
    """توليد قائمة بأسماء اللاعبين"""
    return [_("{number}🃏  {name}",
              "{number}🃏  {name}",
              len(player.cards))
            .format(name=player.user.first_name, number=len(player.cards))
            for player in game.players]

def lose_game(results):
    """إضافة نص إذا خسر المستخدم في اللعبة"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title=_("للأسف، لقد خسرت!"),
            input_message_content=InputTextMessageContent(_('أنت الآن لا تلعب. استخدم /new لبدء لعبة جديدة أو /join للانضمام إلى اللعبة الحالية في هذه المجموعة'))
        )
    )

def add_no_game(results):
    """إضافة نص إذا كان المستخدم لا يلعب"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title=_("أنت لا تلعب!"),
            input_message_content=InputTextMessageContent(_('أنت الآن لا تلعب. استخدم /new لبدء لعبة جديدة أو /join للانضمام إلى اللعبة الحالية في هذه المجموعة'))
        )
    )

def add_not_started(results):
    """إضافة نص إذا لم تبدأ اللعبة بعد"""
    results.append(
        InlineQueryResultArticle(
            "nogame",
            title=_("اللعبة لم تبدأ بعد!"),
            description=("فقط منشئ اللعبة يمكنه تغيير الوضع!"),
            input_message_content=InputTextMessageContent(
                _('فقط منشئ اللعبة يمكنه تغيير الوضع!'))
        )
    )

def add_mode_classic(results):
    """تغيير الوضع إلى الكلاسيكي"""
    results.append(
        InlineQueryResultArticle(
            "mode_classic",
            title=_("🎻 الوضع الكلاسيكي"),
            description=(
                "البطاقات من 0 إلى 9، انعكاس، تخطي، +2، +4، تغيير اللون"),
            input_message_content=InputTextMessageContent(_('عادي 🎻'))
        )
    )

def add_mode_fast(results):
    """تغيير الوضع إلى السريع"""
    results.append(
        InlineQueryResultArticle(
            "mode_fast",
            title=_("🚀 الوضع السريع"),
            description=(
                "مجموعة بطاقات UNO العادية، يتم تخطي اللاعب تلقائيًا بعد انتهاء الوقت"),
            input_message_content=InputTextMessageContent(_('سريع! 🚀'))
        )
    )

def add_mode_wild(results):
    """تغيير الوضع إلى الوضع البري"""
    results.append(
        InlineQueryResultArticle(
            "mode_wild",
            title=_("🐉 وضع البرية"),
            description=(
                "البطاقات من 1 إلى 5، انعكاس، تخطي، +2، +4، تغيير اللون (المزيد من البطاقات الخاصة)"),
            input_message_content=InputTextMessageContent(
                _('في البرية~ 🐉'))
        )
    )

def add_mode_super_wild(results):
    """تغيير الوضع إلى وضع البرية الفائق"""
    results.append(
        InlineQueryResultArticle(
            "mode_super-wild",
            title=_("🔥🐉 وضع البرية الفائق"),
            description=(
                "البطاقات 0، انعكاس، تخطي، +2، +4، تغيير اللون (الكثير من البطاقات الخاصة)"),
            input_message_content=InputTextMessageContent(
                _('في البرية الخطرة~ 🔥🐉'))
        )
    )

def add_mode_big(results):
    """تغيير الوضع إلى الوضع الكبير"""
    results.append(
        InlineQueryResultArticle(
            "mode_big",
            title=_("🌎 وضع العالم الكبير"),
            description=(
                "أونو العادية، ولكن في البداية سيكون لديك الكثير من البطاقات"),
            input_message_content=InputTextMessageContent(_('في العالم الكبير🌎'))
        )
    )

def add_mode_big_wild(results):
    """تغيير الوضع إلى الوضع البري الكبير"""
    results.append(
        InlineQueryResultArticle(
            "mode_big-wild",
            title=_("🌎🐉 وضع العالم الكبير البري"),
            description=(
                "أونو العادية، ولكن في البداية سيكون لديك الكثير من البطاقات البرية"),
            input_message_content=InputTextMessageContent(
                _('في العالم البري الكبير🌎🐉'))
        )
    )

def add_mode_big_wild_text(results):
    """تغيير الوضع إلى الوضع البري الكبير النصي"""
    results.append(
        InlineQueryResultArticle(
            "mode_big-wild-text",
            title=_("🌎🐉✍️ وضع العالم الكبير البري النصي"),
            description=(
                "أونو العادية، ولكن في البداية سيكون لديك الكثير من البطاقات (المزيد من البطاقات الخاصة)"),
            input_message_content=InputTextMessageContent(
                _('في العالم البري النصي الكبير🌎🐉✍️'))
        )
    )

def add_mode_big_text(results):
    """تغيير الوضع إلى الوضع النصي الكبير"""
    results.append(
        InlineQueryResultArticle(
            "mode_big-text",
            title=_("🌎✍️ وضع العالم النصي الكبير"),
            description=(
                "أونو العادية، ولكن في البداية سيكون لديك الكثير من البطاقات (المزيد من البطاقات الخاصة)"),
            input_message_content=InputTextMessageContent(
                _('في العالم النصي الكبير🌎✍️'))
        )
    )

def add_mode_super_wild_text(results):
    """تغيير الوضع إلى الوضع البري الفائق النصي"""
    results.append(
        InlineQueryResultArticle(
            "mode_super-wild-text",
            title=_("🔥🐉✍️ وضع البرية الفائق النصي"),
            description=(
                "البطاقات 0، انعكاس، تخطي، +2، +4، تغيير اللون (الكثير من البطاقات الخاصة، وضع نصي)"),
            input_message_content=InputTextMessageContent(
                _('في البرية الخطرة النصية~ 🔥🐉✍️'))
        )
    )

def add_mode_num_text(results):
    """تغيير الوضع إلى الوضع النصي الرقمي"""
    results.append(
        InlineQueryResultArticle(
            "mode_number-text",
            title=_("🔢✍️ وضع النص الرقمي"),
            description=(
                "البطاقات من 0 إلى 9، من البطاقات الخاصة: +4، تغيير اللون (وضع نصي)"),
            input_message_content=InputTextMessageContent(
                _('الوضع النصي الرقمي 🔢✍️'))
        )
    )

def add_mode_num(results):
    """تغيير الوضع إلى الوضع الرقمي"""
    results.append(
        InlineQueryResultArticle(
            "mode_number",
            title=_("🔢 وضع الأرقام"),
            description=("البطاقات من 0 إلى 9، من البطاقات الخاصة: +4، تغيير اللون"),
            input_message_content=InputTextMessageContent(_('الوضع الرقمي 🔢'))
        )
    )

def add_mode_text(results):
    """تغيير الوضع إلى النصي"""
    results.append(
        InlineQueryResultArticle(
            "mode_text",
            title=_("✍️ وضع النص"),
            description=(
                "البطاقات من 0 إلى 9، انعكاس، تخطي، +2، +4، تغيير اللون (وضع نصي)"),
            input_message_content=InputTextMessageContent(_('وضع النص ✍️'))
        )
    )

def add_mode_text_wild(results):
    """تغيير الوضع إلى نص بري"""
    results.append(
        InlineQueryResultArticle(
            "mode_text-wild",
            title=_("🐉✍️ وضع النص البري"),
            description=(
                "البطاقات من 1 إلى 5، انعكاس، تخطي، +2، +4، تغيير اللون (المزيد من البطاقات الخاصة، وضع نصي)"),
            input_message_content=InputTextMessageContent(_('وضع النص البري 🐉✍️'))
        )
    )

def add_mode_inverse_text(results):
    """تغيير الوضع إلى النص العكسي"""
    results.append(
        InlineQueryResultArticle(
            "mode_inverse-text",
            title=_("🔁✍️ وضع النص العكسي"),
            description=(
                "في هذا الوضع، يمكنك رمي البطاقات التي لا يمكن رميها! والعكس! (وضع نصي)"),
            input_message_content=InputTextMessageContent(
                _('الوضع النصي العكسي 🔁✍️'))
        )
    )

def add_mode_inverse(results):
    """تغيير الوضع إلى العكسي"""
    results.append(
        InlineQueryResultArticle(
            "mode_inverse",
            title=_("🔁 وضع العكسي"),
            description=(
                "في هذا الوضع، يمكنك رمي البطاقات التي لا يمكن رميها! والعكس!"),
            input_message_content=InputTextMessageContent(_('الوضع العكسي 🔁'))
        )
    )

def add_not_bignumber(results):
    """إضافة وضع عدم العدد الكبير"""
    results.append(
        InlineQueryResultArticle(
            f"not_bignumber", 
            title=_(f"⚙️ لقد حددت الكثير من البطاقات! (الحد الأقصى 35)"),
            description=(
                f"أونو العادية، ولكن في البداية سيكون لديك العدد الذي تحدده من البطاقات."),
            input_message_content=InputTextMessageContent(
                _(f'⚙️ لقد حددت الكثير من البطاقات! (الحد الأقصى 35)'))
        )
    )

def add_not_big_settigs(results):
    """إضافة وضع الإعدادات الكبيرة"""
    results.append(
        InlineQueryResultArticle(
            f"not_number",
            title=_(f"⚙️وضع إعدادات كبيرة (أدخل العدد)"),
            description=(
                f"أونو العادية، ولكن في البداية سيكون لديك العدد الذي تحدده من البطاقات."),
            input_message_content=InputTextMessageContent(
                _(f'⚙️لم تحدد عدد البطاقات!'))
        )
    )

def add_mode_big_settigs(results, nun):
    """تغيير الوضع إلى إعدادات كبيرة"""
    text_nun = f"عدد البطاقات: {nun}"
    results.append(
        InlineQueryResultArticle(
            f"mode_big-sets_{nun}",
            title=_(f"⚙️وضع إعدادات كبيرة ({text_nun})"),
            description=(
                f"أونو العادية، ولكن في البداية سيكون لديك العدد الذي تحدده من البطاقات."),
            input_message_content=InputTextMessageContent(
                _(f'في العالم المخصص ⚙️({text_nun})'))
        )
    )

def add_mode_bigtext_settigs(results, nun):
    """تغيير الوضع إلى إعدادات نصية كبيرة"""
    text_nun = f"عدد البطاقات: {nun}"
    results.append(
        InlineQueryResultArticle(
            f"mode_big-sets-text_{nun}",
            title=_(f"⚙️✍️وضع إعدادات نصية كبيرة ({text_nun})"),
            description=(
                f"أونو العادية، ولكن في البداية سيكون لديك العدد الذي تحدده من البطاقات."),
            input_message_content=InputTextMessageContent(
                _(f'في العالم النصي المخصص ⚙️✍️({text_nun})'))
        )
    )

def add_mode_random_settigs(results):
    """تغيير الوضع إلى وضع عشوائي"""
    results.append(
        InlineQueryResultArticle(
            f"mode_random",
            title=_(f"🪐وضع عشوائي"),
            description=(
                f"أونو العادية، ولكن في كل دور ستتغير بطاقات كل لاعب"),
            input_message_content=InputTextMessageContent(
                _(f'في العالم العشوائي 🪐'))
        )
    )

def add_mode_random_text_settigs(results):
    """تغيير الوضع إلى وضع نصي عشوائي"""
    results.append(
        InlineQueryResultArticle(
            f"mode_random-text",
            title=_(f"🪐✍️وضع نصي عشوائي"),
            description=(
                f"أونو العادية، ولكن في كل دور ستتغير بطاقات كل لاعب"),
            input_message_content=InputTextMessageContent(
                _(f'في العالم النصي العشوائي 🪐✍️'))
        )
    )




def add_all_modes(results):
    """All modes"""
    add_mode_classic(results)
    add_mode_text(results)

    add_mode_fast(results)

    add_mode_wild(results)
    add_mode_text_wild(results)

    add_mode_super_wild(results)
    add_mode_super_wild_text(results)

    add_mode_inverse(results)
    add_mode_inverse_text(results)

    add_mode_num(results)
    add_mode_num_text(results)

    add_mode_big(results)
    add_mode_big_text(results)

    add_mode_big_wild(results)
    add_mode_big_wild_text(results)
    
    add_mode_random_settigs(results)
    add_mode_random_text_settigs(results)

def add_text_modes(results):
    """Text modes"""
    add_mode_text(results)
    add_mode_text_wild(results)
    add_mode_super_wild_text(results)
    add_mode_inverse_text(results)
    add_mode_num_text(results)
    add_mode_big_text(results)
    add_mode_big_wild_text(results)
    add_mode_random_text_settigs(results)

def add_none_text_modes(results):
    """None text modes"""
    add_mode_classic(results)
    add_mode_fast(results)
    add_mode_wild(results)
    add_mode_super_wild(results)
    add_mode_inverse(results)
    add_mode_num(results)
    add_mode_big(results)
    add_mode_big_wild(results)
    add_mode_random_settigs(results)


def add_draw(player, results):
    """إضافة خيار السحب"""
    n = player.game.draw_counter or 1

    results.append(
        Sticker(
            "draw", sticker_file_id=c.STICKERS['option_draw'],
            input_message_content=InputTextMessageContent(__('سحب(ت) {number} بطاقة',
                                                             'سحب(ت) {number} بطاقات', n,
                                                             multi=player.game.translate)
                                                          .format(number=n))
        )
    )

def add_gameinfo(game, results):
    """إضافة خيار عرض معلومات اللعبة"""

    results.append(
        Sticker(
            "gameinfo",
            sticker_file_id=c.STICKERS['option_info'],
            input_message_content=game_info(game)
        )
    )

def add_pass(results, game):
    """إضافة خيار التمرير"""
    results.append(
        Sticker(
            "pass", sticker_file_id=c.STICKERS['option_pass'],
            input_message_content=InputTextMessageContent(
                __('تمرير', multi=game.translate)
            )
        )
    )

def add_call_bluff(results, game):
    """إضافة خيار لمكافحة الخداع"""
    results.append(
        Sticker(
            "call_bluff",
            sticker_file_id=c.STICKERS['option_bluff'],
            input_message_content=InputTextMessageContent(__("أعتقد أن هذا خداع!",
                                                             multi=game.translate))
        )
    )

def add_card(game, card, results, can_play):
    """إضافة خيار يمثل بطاقة"""

    if game.color_mode == "white":
        if can_play:
            if str(game.mode).lower().find('text') == -1:
                results.append(
                    Sticker(str(card), sticker_file_id=c.STICKERS[str(card)])
                )
            if str(game.mode).lower().find('text') != -1:
                results.append(
                    Sticker(str(card), sticker_file_id=c.STICKERS[str(card)], input_message_content=InputTextMessageContent("ألقيت بطاقة: {card}".format(card=repr(card).replace('سحب +4', '+4').replace('سحب +2', '+2').replace('تغيير اللون', 'اختيار اللون')))
                            ))
        else:
            results.append(
                Sticker(f"game_info_{uuid4()}", sticker_file_id=c.STICKERS_GREY[str(card)],
                        input_message_content=game_info(game))
            )
    elif game.color_mode == "black":
        if can_play:
            if str(game.mode).lower().find('text') == -1:
                results.append(
                    Sticker(str(card), sticker_file_id=cb.STICKERS[str(card)])
                )
            if str(game.mode).lower().find('text') != -1:
                results.append(
                    Sticker(str(card), sticker_file_id=cb.STICKERS[str(card)], input_message_content=InputTextMessageContent("ألقيت بطاقة: {card}".format(card=repr(card).replace('سحب +4', '+4').replace('سحب +2', '+2').replace('تغيير اللون', 'اختيار اللون')))
                            ))
        else:
            results.append(
                Sticker(f"game_info_{uuid4()}", sticker_file_id=cb.STICKERS_GREY[str(card)],
                        input_message_content=game_info(game))
            )
    elif game.color_mode == "flip":
        if game.flip_color == "white":
            if can_play:
                if str(game.mode).lower().find('text') == -1:
                    results.append(
                        Sticker(
                            str(card), sticker_file_id=c.STICKERS[str(card)])
                    )
                if str(game.mode).lower().find('text') != -1:
                    results.append(
                        Sticker(str(card), sticker_file_id=c.STICKERS[str(card)], input_message_content=InputTextMessageContent("ألقيت بطاقة: {card}".format(card=repr(card).replace('سحب +4', '+4').replace('سحب +2', '+2').replace('تغيير اللون', 'اختيار اللون')))
                                ))
            else:
                results.append(
                    Sticker(f"game_info_{uuid4()}", sticker_file_id=c.STICKERS_GREY[str(card)],
                            input_message_content=game_info(game))
                )
        elif game.flip_color == "black":
            if can_play:
                if str(game.mode).lower().find('text') == -1:
                    results.append(
                        Sticker(
                            str(card), sticker_file_id=cb.STICKERS[str(card)])
                    )
                if str(game.mode).lower().find('text') != -1:
                    results.append(
                        Sticker(str(card), sticker_file_id=cb.STICKERS[str(card)], input_message_content=InputTextMessageContent("ألقيت بطاقة: {card}".format(card=repr(card).replace('سحب +4', '+4').replace('سحب +2', '+2').replace('تغيير اللون', 'اختيار اللون')))
                                ))
            else:
                results.append(
                    Sticker(f"game_info_{uuid4()}", sticker_file_id=cb.STICKERS_GREY[str(card)],
                            input_message_content=game_info(game))
                )

def game_info_text(game):
    players = player_list(game)
    return (
        _("اللاعب الحالي: {name}")
        .format(name=display_name(game.current_player.user)) +
        "\n" +
        _("آخر بطاقة: {card}").format(card=repr(game.last_card)) +
        "\n" +
        _("اللاعب: {player_list}",
          "اللاعبون:\n• {player_list}",
          len(players))
        .format(player_list="\n• ".join(players))
    )

def game_info(game):
    return InputTextMessageContent(game_info_text(game))

def add_color_replace(results):
    add_color_white(results)
    add_color_black(results)
    add_color_flip(results)

def add_color_black(results):
    results.append(
        InlineQueryResultArticle(
            "colormode_black",
            title=_("🖤 البطاقات السوداء"),
            description=("تغيير تصميم البطاقات إلى الأسود"),
            input_message_content=InputTextMessageContent(_('🖤 البطاقات السوداء'))
        )
    )

def add_color_white(results):
    results.append(
        InlineQueryResultArticle(
            "colormode_white",
            title=_("🤍 البطاقات البيضاء"),
            description=("تغيير تصميم البطاقات إلى الأبيض"),
            input_message_content=InputTextMessageContent(_('🤍 البطاقات البيضاء'))
        )
    )

def add_color_flip(results):
    """تغيير الوضع إلى الكلاسيكي"""
    results.append(
        InlineQueryResultArticle(
            "colormode_flip",
            title=_("🔀 بطاقات Flip"),
            description=("في هذه المجموعة، يتم استخدام بطاقات أونو Flip!"),
            input_message_content=InputTextMessageContent(_("Flip 🔀"))
        )
    )