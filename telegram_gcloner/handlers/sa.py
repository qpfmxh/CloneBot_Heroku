#!/usr/bin/python3
# -*- coding: utf-8 -*-
import configparser
import datetime
import logging
import os
import shutil
import time
from pathlib import Path
from zipfile import ZipFile

from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

from utils.config_loader import config
from utils.restricted import restricted_private

logger = logging.getLogger(__name__)


def init(dispatcher: Dispatcher):
    """Provide handlers initialization."""
    dispatcher.add_handler(CommandHandler('sa', get_sa, filters=~Filters.update.edited_message))
    dispatcher.add_handler(MessageHandler(Filters.private & Filters.document, get_sa))


@restricted_private
def get_sa(update, context):
    instruction_text = 'SA 파일이 포함된 ZIP 파일을 업로드하려면 비공개 채팅을 하십시오，그리고 텔레그램 제목에 쓰세요/sa。\n' \
                       '모바일 사용자는 먼저 ZIP 파일을 업로드하십시오，/sa를 사용하여 메시지에 회신。'
    if update.message and update.message.caption and update.message.caption.startswith('/sa'):
        document = update.message.document
    elif update.message and update.message.reply_to_message:
        document = update.message.reply_to_message.document
    else:
        update.message.reply_text(instruction_text)
        return

    if not document:
        update.message.reply_text(instruction_text)
        return
    gclone_path = os.path.join(config.BASE_PATH,
                               'gclone_config',
                               str(update.effective_user.id))
    current_time = datetime.datetime.now()
    file_name = document.file_name

    if not file_name.endswith('zip'):
        update.message.reply_text('zip 파일만 허용됩니다。')
        return

    file_pah = os.path.join(gclone_path,
                            "{}_{}_{}".format(current_time.strftime("%Y-%m-%d"),
                                              current_time.strftime("%H-%M-%S"), file_name))
    if not os.path.isdir(gclone_path):
        Path(gclone_path).mkdir(parents=True, exist_ok=True)
    file = document.get_file(timeout=20)
    file.download(custom_path=file_pah)

    zip_path = os.path.join(gclone_path, 'current')

    # remove old files
    if os.path.isdir(zip_path):
        shutil.rmtree(zip_path)
        while os.path.exists(zip_path):
            time.sleep(1)
    Path(zip_path).mkdir(parents=True, exist_ok=True)

    # unzip files
    with ZipFile(file_pah, 'r') as zip_file:
        for member in zip_file.namelist():
            filename = os.path.basename(member)
            # skip directories
            if not filename:
                continue

            source = zip_file.open(member)
            target = open(os.path.join(zip_path, filename), "wb")
            with source, target:
                shutil.copyfileobj(source, target)

    # remove non json
    puppet_file = None
    json_count = 1
    for f in os.listdir(zip_path):
        current_file = os.path.join(zip_path, f)
        if not f.endswith('.json'):
            os.remove(current_file)
        elif not puppet_file:
            puppet_file = os.path.join(zip_path, 'google_drive_puppet.json')
            shutil.copy(current_file, puppet_file)
        else:
            json_count += 1
    if not puppet_file:
        update.message.reply_text(instruction_text)
        return

    # generate config file
    config_file = configparser.ConfigParser()
    config_file.add_section('gc')
    config_file.set('gc', 'type', 'drive')
    config_file.set('gc', 'scope', 'drive')
    config_file.set('gc', 'service_account_file', puppet_file)
    config_file.set('gc', 'service_account_file_path', zip_path + os.path.sep)
    config_file.set('gc', 'root_folder_id', 'root')

    with open(os.path.join(zip_path, 'rclone.conf'), 'w') as file_to_write:
        config_file.write(file_to_write)

    update.message.reply_text('총 {}개의 SA 파일이 수신 및 구성되었습니다。'.format(json_count))
    logger.info('{} service account files have been saved for {}.'.format(json_count, update.effective_user.id))
