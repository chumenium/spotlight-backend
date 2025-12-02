"""
管理者管理API
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from utils.auth import jwt_required
from models.selectdata import (
    get_user_name_iconpath,get_search_history,get_user_contents,get_spotlight_contents,
    get_play_history,get_user_spotlightnum,get_notification,get_unloaded_num,get_spotlight_num
)
from models.updatedata import enable_notification, disable_notification,chenge_icon
from models.createdata import (
    add_content_and_link_to_users, insert_comment, insert_playlist, insert_playlist_detail,
    insert_search_history, insert_play_history, insert_notification, insert_report
)
from utils.s3 import upload_to_s3, get_cloudfront_url, delete_file_from_url
import os
import re
import base64

admin_bp = Blueprint('amdin', __name__, url_prefix='/api/admin')

