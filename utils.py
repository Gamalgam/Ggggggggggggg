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


import logging

from telegram.ext import InlineQueryHandler, ChosenInlineResultHandler, \
    CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from internationalization import _, __
from mwt import MWT
from shared_vars import gm, dispatcher

logger = logging.getLogger(__name__)

TIMEOUT = 2.5


def list_subtract(list1, list2):
    """ Helper function to subtract two lists and return the sorted result """
    list1 = list1.copy()

    for x in list2:
        list1.remove(x)

    return list(sorted(list1))


def display_name(user):
    """ Get the current players name including their username, if possible """
    user_name = user.first_name
    if user.username:
        user_name += ' (@' + user.username + ')'
    return user_name


# بطاقة لعبت

def display_color(color):
    """ تحويل رمز اللون إلى الاسم الفعلي للون """
    if color == "r":
        return _("{emoji} أحمر").format(emoji='❤️')
    if color == "b":
        return _("{emoji} أزرق").format(emoji='💙')
    if color == "g":
        return _("{emoji} أخضر").format(emoji='💚')
    if color == "y":
        return _("{emoji} أصفر").format(emoji='💛')

def display_color_group(color, game):
    """ تحويل رمز اللون إلى الاسم الفعلي للون """
    if color == "r":
        return __("{emoji} أحمر", game.translate).format(
            emoji='❤️')
    if color == "b":
        return __("{emoji} أزرق", game.translate).format(
            emoji='💙')
    if color == "g":
        return __("{emoji} أخضر", game.translate).format(
            emoji='💚')
    if color == "y":
        return __("{emoji} أصفر", game.translate).format(
            emoji='💛')

def display_color_dark(color):
    """ تحويل رمز اللون إلى الاسم الفعلي للون """
    if color == "w":
        return _("{emoji} أبيض").format(emoji='🤍')
    if color == "p":
        return _("{emoji} بنفسجي").format(emoji='💜')
    if color == "g":
        return _("{emoji} أخضر").format(emoji='💚')
    if color == "o":
        return _("{emoji} برتقالي").format(emoji='🧡')

def display_color_group_dark(color, game):
    """ تحويل رمز اللون إلى الاسم الفعلي للون """
    if color == "w":
        return __("{emoji} أبيض", game.translate).format(
            emoji='🤍')
    if color == "p":
        return __("{emoji} بنفسجي", game.translate).format(
            emoji='💜')
    if color == "g":
        return __("{emoji} أخضر", game.translate).format(
            emoji='💚')
    if color == "o":
        return __("{emoji} برتقالي", game.translate).format(
            emoji='🧡')

def error(bot, update, error):
    """معالج خطأ بسيط"""
    logger.exception(error)

def send_async(bot, *args, **kwargs):
    """إرسال رسالة بشكل غير متزامن"""
    if 'timeout' not in kwargs:
        kwargs['timeout'] = TIMEOUT

    try:
        dispatcher.run_async(bot.sendMessage, *args, **kwargs)
    except Exception as e:
        error(None, None, e)

def answer_async(bot, *args, **kwargs):
    """الرد على استعلام مضمن بشكل غير متزامن"""
    if 'timeout' not in kwargs:
        kwargs['timeout'] = TIMEOUT

    try:
        dispatcher.run_async(bot.answerInlineQuery, *args, **kwargs)
    except Exception as e:
        error(None, None, e)


def game_is_running(game):
    return game in gm.chatid_games.get(game.chat.id, list())


def user_is_creator(user, game):
    return user.id in game.owner


def user_is_admin(user, bot, chat):
    return user.id in get_admin_ids(bot, chat.id)


def user_is_creator_or_admin(user, game, bot, chat):
    return user_is_creator(user, game) or user_is_admin(user, bot, chat)


@MWT(timeout=60*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
