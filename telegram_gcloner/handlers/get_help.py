#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging

from telegram.ext import Dispatcher, CommandHandler

from utils.config_loader import config
from utils.callback import callback_delete_message
from utils.restricted import restricted

logger = logging.getLogger(__name__)


def init(dispatcher: Dispatcher):
    """Provide handlers initialization."""
    dispatcher.add_handler(CommandHandler('help', get_help))


@restricted
def get_help(update, context):
    message = 'Google 드라이브 링크를 보내거나 Google 드라이브로 정보를 전달하여 수동으로 덤프하십시오.。\n' \
              '/sa 및 /folders를 사용한 구성 필요\n\n' \
              '다음은 이 BOT의 명령입니다：\n\n' \
              '/folders - 즐겨찾기 폴더 설정\n' \
              '/sa - 비공개 채팅 전용, sa가 포함된 ZIP 폴더 업로드, 제목에 /sa를 작성하여 서비스 계정 설정\n' \
              '/4999baoyue - 개인채팅만 가능, 업무협상, 쪽지 첨부 부탁드립니다\n' \
              '/help - 도움말 출력\n'
    rsp = update.message.reply_text(message)
    rsp.done.wait(timeout=60)
    message_id = rsp.result().message_id
    if update.message.chat_id < 0:
        context.job_queue.run_once(callback_delete_message, config.TIMER_TO_DELETE_MESSAGE,
                                   context=(update.message.chat_id, message_id))
        context.job_queue.run_once(callback_delete_message, config.TIMER_TO_DELETE_MESSAGE,
                                   context=(update.message.chat_id, update.message.message_id))
