import calendar
import base64
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from services.app_storage import (
    list_history_records,
    load_history_record,
    make_message,
    message_date,
    message_time,
    save_history_record,
    save_mood,
    save_profile,
    update_history_messages,
)
from services.local_ai import DIMENSIONS, generate_reply, make_report, score_messages
from services.message_format import messages_to_readable_text, normalize_messages
from services.proactive_engine import maybe_add_care_proactive
from services.safety import assess_message_safety, attach_safety_metadata, make_safety_reply
from ui.crisis_alert import queue_crisis_alert, render_crisis_alert_if_needed


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "assets" / "diary_templates"
TEMPLATE_FILES = {
    "cover": "cover.jpg",
    "intro": "intro.jpg",
    "calendar": "calendar.jpg",
    "history": "history.jpg",
    "chat": "chat.jpg",
}


DIARY_CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
.stApp { background: #f6d9df; }
.block-container { max-width: 1180px; padding-top: 1rem; }
.diary-shell {
    border: 3px solid #8f8f8f;
    border-radius: 8px;
    background: #f6d9df;
    overflow: hidden;
    box-shadow: 0 16px 42px rgba(90,64,74,.18);
    margin-bottom: 16px;
}
.diary-tabs {
    height: 54px;
    background: #d7dde6;
    border-bottom: 3px solid #8f8f8f;
    display: flex;
    align-items: end;
    gap: 2px;
    padding: 0 14px;
    overflow-x: auto;
}
.diary-tab {
    min-width: 58px;
    height: 40px;
    border: 3px solid #8f8f8f;
    border-bottom: 0;
    border-radius: 14px 14px 0 0;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    color: #8a8a8a;
}
.diary-tab.small { min-width: 72px; font-size: 13px; }
.diary-tab.active { background: #aebddd; color: #fff; }
.diary-tab.month-active { background: #efc6d1; color: #666; }
.diary-page {
    min-height: 650px;
    padding: 30px 36px;
    position: relative;
    overflow: hidden;
}
.cover-scene {
    min-height: 610px;
    display: grid;
    grid-template-columns: 1fr 1.25fr 1fr;
    align-items: center;
    gap: 20px;
    position: relative;
}
.cover-scene:after {
    content: "";
    position: absolute;
    left: -36px;
    right: -36px;
    bottom: -30px;
    height: 188px;
    background: #eca7b8;
    border-top: 3px solid #333;
    z-index: 0;
}
.cover-scene > div {
    position: relative;
    z-index: 1;
}
.big-bubble {
    background: white;
    border: 3px solid #333;
    border-radius: 50%;
    min-height: 310px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    text-align: center;
}
.big-bubble:after {
    content: "";
    position: absolute;
    right: 52px;
    bottom: -35px;
    width: 48px;
    height: 64px;
    background: #fff;
    border-right: 3px solid #333;
    border-bottom: 3px solid #333;
    transform: rotate(24deg);
}
.title-year {
    color: #aa94cf;
    font-size: 62px;
    font-weight: 950;
    letter-spacing: 4px;
    text-shadow: 2px 2px 0 #333;
    line-height: 1;
}
.title-main {
    color: #8ab49e;
    font-size: 52px;
    font-weight: 950;
    letter-spacing: 2px;
    text-shadow: 2px 2px 0 #333;
    line-height: 1.05;
}
.doodle { text-align: center; font-size: 82px; margin: 28px 0; }
.cover-prop {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 96px;
    min-height: 84px;
    margin: 10px;
    font-size: 62px;
}
.cover-side-note {
    display: inline-block;
    background: #fffaf0;
    border: 3px solid #333;
    border-radius: 8px;
    padding: 12px 16px;
    transform: rotate(-4deg);
    font-size: 38px;
}
.loading-text {
    text-align: center;
    color: #704d59;
    font-size: 24px;
    font-weight: 800;
    margin-top: 18px;
}
.intro-grid {
    min-height: 420px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 34px;
    align-items: center;
}
.intro-title { text-align: center; }
.avatar-frame {
    width: 150px;
    height: 150px;
    margin: 0 auto 20px;
    background: #fff;
    border: 3px solid #333;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 82px;
}
.profile-lines {
    max-width: 520px;
    margin: 0 auto 14px auto;
    color: #282229;
    font-weight: 900;
    font-size: 19px;
}
.profile-lines span {
    display: inline-block;
    min-width: 120px;
}
.profile-form-wrap {
    max-width: 760px;
    margin: -22px auto 0 auto;
}
.tip-box {
    background: rgba(255,255,255,.62);
    border: 2px dashed #d09aa8;
    border-radius: 12px;
    padding: 12px 16px;
    color: #735861;
    margin: 12px 0;
    font-size: 17px;
}
.calendar-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    margin-bottom: 16px;
}
.month-title {
    color: #8f83c6;
    font-size: 62px;
    font-weight: 950;
    letter-spacing: 3px;
    text-shadow: 2px 2px 0 #333;
}
.calendar-note {
    flex: 1;
    max-width: 520px;
    min-height: 64px;
    border: 3px solid #333;
    border-radius: 24px;
    background: #fff;
    padding: 12px 20px;
    color: #66535a;
    font-size: 18px;
}
.calendar-deco {
    display: grid;
    grid-template-columns: 126px 1fr 120px;
    align-items: center;
    gap: 14px;
    margin-bottom: 10px;
}
.calendar-bear {
    font-size: 86px;
    text-align: center;
}
.calendar-cloud {
    min-height: 74px;
    background: #fff;
    border: 3px solid #333;
    border-radius: 42px;
    box-shadow: 0 5px 0 rgba(0,0,0,.04);
    position: relative;
}
.calendar-cloud:before,
.calendar-cloud:after {
    content: "⭐";
    position: absolute;
    top: -18px;
    font-size: 34px;
}
.calendar-cloud:before { left: -28px; }
.calendar-cloud:after { right: -22px; }
.calendar-cat {
    font-size: 72px;
    text-align: center;
}
.mood-calendar {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    background: #fff;
    border: 3px solid #333;
}
.mood-calendar th {
    height: 36px;
    background: #aeb9dc;
    color: #834e59;
    border: 2px solid #333;
}
.mood-calendar td {
    height: 92px;
    border: 2px solid #333;
    vertical-align: top;
    padding: 6px;
    position: relative;
    font-weight: 700;
}
.mood-emoji {
    position: absolute;
    left: 50%;
    top: 52%;
    transform: translate(-50%, -50%);
    font-size: 32px;
}
.history-title {
    color: #8c747b;
    font-size: 32px;
    font-weight: 950;
    margin-bottom: 16px;
}
.history-header {
    display: grid;
    grid-template-columns: 100px 1fr;
    align-items: center;
    gap: 18px;
    margin-bottom: 12px;
}
.history-month {
    color: #8f83c6;
    font-size: 58px;
    font-weight: 950;
    line-height: .9;
    text-shadow: 2px 2px 0 #333;
}
.history-bubble {
    min-height: 88px;
    background: #fff;
    border: 3px solid #333;
    border-radius: 48px;
}
.history-spread {
    display: grid;
    grid-template-columns: 1fr 1.35fr;
    gap: 50px;
}
.history-column {
    display: grid;
    gap: 0;
}
.history-column.left { margin-top: 150px; }
.history-column.right { margin-top: 0; }
.history-card {
    height: 156px;
    display: grid;
    grid-template-columns: 116px 1fr;
    background: #fff;
    border: 2px solid #333;
    overflow: hidden;
    border-radius: 0;
}
.history-card:first-child { border-radius: 8px 8px 0 0; }
.history-card:last-child { border-radius: 0 0 8px 8px; }
.history-card + .history-card { border-top: 0; }
.history-column.right .history-card { height: 117px; }
.history-column.right .history-card .history-summary { height: 42px; }
.history-card.empty {
    opacity: .55;
    background: rgba(255,255,255,.62);
}
.history-date {
    background: #aeb9dc;
    border-right: 2px solid #333;
    padding: 12px;
    color: #2f3450;
    font-weight: 900;
}
.history-body {
    padding: 14px;
    color: #67555d;
    background-image:
        linear-gradient(#e7e7e7 1px, transparent 1px),
        linear-gradient(90deg, #e7e7e7 1px, transparent 1px);
    background-size: 20px 20px;
}
.history-summary {
    height: 58px;
    overflow: hidden;
    line-height: 1.45;
    word-break: break-word;
}
.history-meta { color: #9a626d; font-size: 14px; margin-top: 12px; }
.chat-paper {
    min-height: 620px;
    background: #fffefc;
    border: 3px solid #333;
    border-radius: 8px;
    padding: 86px 28px 100px;
    position: relative;
    background-image:
        linear-gradient(#edf0f2 1px, transparent 1px),
        linear-gradient(90deg, #edf0f2 1px, transparent 1px);
    background-size: 22px 22px;
}
.history-dialog {
    padding-bottom: 42px;
}
.history-dialog .msg-stack {
    max-width: min(72%, 760px);
}
.chat-paper:before {
    content: "⭐  🧦";
    position: absolute;
    left: 38px;
    top: 26px;
    font-size: 44px;
    transform: rotate(-12deg);
    z-index: 0;
}
.chat-paper:after {
    content: "🐴";
    position: absolute;
    right: 54px;
    bottom: 38px;
    font-size: 74px;
    transform: rotate(-5deg);
    z-index: 0;
}
.chat-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #73565c;
    font-weight: 900;
    margin-bottom: 18px;
    position: relative;
    z-index: 1;
}
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin: 18px 0;
    position: relative;
    z-index: 1;
}
.msg-row.user { justify-content: flex-end; }
.msg-row.assistant { justify-content: flex-start; }
.msg-avatar {
    width: 54px;
    height: 54px;
    background: #fff;
    border: 2px solid #333;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    flex: 0 0 auto;
}
.msg-stack { max-width: 68%; }
.msg-bubble {
    border: 2px solid #333;
    border-radius: 12px;
    padding: 12px 16px;
    color: #4d3f44;
    font-size: 17px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
    box-shadow: 2px 3px 0 rgba(0,0,0,.08);
}
.msg-row.user .msg-bubble { background: #ffe2e9; }
.msg-row.assistant .msg-bubble { background: #e8f4ff; }
.msg-time { font-size: 13px; color: #79676c; margin-top: 4px; }
.score-pill {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    background: #fff;
    border: 2px solid #d09aa8;
    color: #765965;
    margin: 4px;
    font-weight: 800;
}
.stButton > button {
    border-radius: 12px !important;
    border: 2px solid #9a6a73 !important;
    background: #fff !important;
    color: #6a4a52 !important;
    font-weight: 850 !important;
}
.stButton {
    position: relative;
    z-index: 35;
}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border: 2px solid #c6949d !important;
    border-radius: 10px !important;
    background: #fffdfc !important;
}
.template-frame {
    width: 100%;
    aspect-ratio: 1178 / 884;
    background-repeat: no-repeat;
    background-position: center top;
    background-size: 100% 100%;
    position: relative;
    margin: 0 auto 14px auto;
}
.template-cover,
.template-intro {
    width: 100vw;
    height: 100vh;
    aspect-ratio: auto;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
    margin-top: -1rem;
    margin-bottom: 0;
    background-size: 100% 100%;
}
.template-calendar {
    width: 100vw;
    height: 100vh;
    aspect-ratio: auto;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);
    margin-top: -1rem;
    margin-bottom: 0;
    background-size: 100% 100%;
}
.template-history { aspect-ratio: 1093 / 819; }
.template-chat { aspect-ratio: 1101 / 826; }
.template-overlay {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}
.template-overlay:has(.calendar-modal-shade:target) {
    pointer-events: auto;
}
.tpl-text {
    position: absolute;
    color: #2c2528;
    font-size: clamp(12px, 1.45vw, 18px);
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.tpl-mood {
    position: absolute;
    transform: translate(-50%, -50%);
    font-size: clamp(18px, 3vw, 34px);
}
.tpl-day-hotspot {
    position: absolute;
    display: block;
    padding: 0;
    border: 0;
    border-radius: 8px;
    background: transparent;
    cursor: pointer;
    pointer-events: auto;
    z-index: 6;
}
.tpl-day-hotspot:hover,
.tpl-day-hotspot.selected {
    background: rgba(255, 204, 216, .20);
    outline: 2px dashed rgba(238, 113, 139, .72);
    outline-offset: -5px;
}
.tpl-mood-entry {
    position: absolute;
    display: grid;
    grid-template-rows: auto 1fr;
    align-items: start;
    justify-items: center;
    gap: 1px;
    overflow: hidden;
    color: #6d5260;
    font-family: "Comic Sans MS", "Comic Sans", "Gaegu", "Microsoft YaHei", cursive;
    font-weight: 800;
    text-align: center;
    pointer-events: none;
    z-index: 5;
}
.calendar-modal-shade {
    position: fixed;
    inset: 0;
    display: none;
    align-items: center;
    justify-content: center;
    background: rgba(76, 42, 55, .18);
    z-index: 40;
    pointer-events: auto;
}
.calendar-modal-shade:target {
    display: flex;
}
.calendar-modal {
    width: min(430px, 88vw);
    padding: 18px 20px 20px;
    border: 2px solid rgba(168, 101, 116, .86);
    border-radius: 20px;
    background: rgba(255, 247, 250, .98);
    box-shadow: 0 18px 44px rgba(104, 58, 75, .28);
    color: #7a5360;
    font-family: "Comic Sans MS", "Comic Sans", "Gaegu", "Microsoft YaHei", cursive;
    pointer-events: auto;
}
.calendar-modal-title {
    font-size: 17px;
    font-weight: 900;
    margin-bottom: 12px;
}
.calendar-emoji-row {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
    margin: 8px 0 14px;
}
.calendar-emoji-row label {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 34px;
    border: 2px solid rgba(198, 148, 157, .52);
    border-radius: 12px;
    background: rgba(255, 255, 255, .72);
    font-weight: 850;
    cursor: pointer;
    user-select: none;
    pointer-events: auto;
}
.calendar-emoji-row label:hover {
    border-color: rgba(224, 106, 132, .9);
    background: #fff;
}
.calendar-emoji-row label:has(input:checked) {
    border-color: #ef6f8f;
    background: #ffe6ee;
    box-shadow: 0 0 0 2px rgba(239, 111, 143, .18);
}
.calendar-emoji-row input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
}
.calendar-modal input[type="text"] {
    width: 100%;
    box-sizing: border-box;
    border: 1px solid rgba(198, 148, 157, .72);
    border-radius: 12px;
    background: #fffdfc;
    color: #6d5260;
    font: inherit;
    padding: 9px 10px;
    margin: 4px 0 14px;
    pointer-events: auto;
}
.calendar-modal-actions {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
}
.calendar-modal-actions button,
.calendar-modal-actions a {
    min-height: 36px;
    border-radius: 14px;
    border: 2px solid rgba(154, 106, 115, .72);
    background: #fff;
    color: #6a4a52;
    font: inherit;
    font-weight: 900;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    pointer-events: auto;
}
.tpl-mood-entry .entry-emoji {
    font-size: clamp(18px, 2.15vw, 30px);
    line-height: 1;
}
.tpl-mood-entry .entry-event {
    width: 100%;
    font-size: clamp(8px, .72vw, 12px);
    line-height: 1.15;
    word-break: break-word;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
}
.tpl-card {
    position: absolute;
    overflow: hidden;
    color: #55484e;
    font-size: clamp(10px, 1.1vw, 14px);
    line-height: 1.35;
}
.tpl-history-hotspot {
    position: absolute;
    display: block;
    border-radius: 8px;
    background: transparent;
    pointer-events: auto;
    z-index: 7;
}
.tpl-history-hotspot:hover {
    background: rgba(255, 204, 216, .16);
    outline: 2px dashed rgba(238, 113, 139, .62);
    outline-offset: -5px;
}
.tpl-date-chip {
    position: absolute;
    height: 5.2%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.4%;
    background: #aeb8d7;
    color: #333;
    font-size: clamp(11px, 1.35vw, 16px);
    line-height: 1;
    box-sizing: border-box;
}
.tpl-date-chip.sun { color: #d8878e; }
.tpl-msg {
    position: relative;
    max-width: 58%;
    padding: 10px 14px;
    margin: 10px 0;
    border-radius: 12px;
    border: 2px solid #333;
    font-size: clamp(12px, 1.35vw, 16px);
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
}
.tpl-chat-list {
    position: absolute;
    left: 8%;
    right: 8%;
    top: 16%;
    bottom: 12%;
    overflow: hidden;
}
.tpl-diary-page-text {
    position: absolute;
    overflow: hidden;
    color: #5a454b;
    font-size: clamp(15px, 1.7vw, 22px);
    line-height: 1.85;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: "KaiTi", "STKaiti", "Microsoft YaHei", cursive;
}
.tpl-diary-page-text.left {
    left: 12%;
    top: 26%;
    width: 34%;
    height: 42%;
}
.tpl-diary-page-text.right {
    left: 56%;
    top: 24%;
    width: 33%;
    height: 44%;
    color: #4b5666;
}
.tpl-diary-empty {
    color: rgba(152, 113, 123, .42);
}
.tpl-msg.user {
    margin-left: auto;
    background: #ffe2e9;
}
.tpl-msg.assistant {
    margin-right: auto;
    background: #e8f4ff;
}
.tpl-avatar {
    display: inline-flex;
    width: 34px;
    height: 34px;
    border: 2px solid #333;
    border-radius: 8px;
    background: #fff;
    align-items: center;
    justify-content: center;
    margin: 0 6px;
}
.cover-enter-action div.stButton {
    position: fixed;
    left: 50%;
    bottom: 5vh;
    transform: translateX(-50%);
    z-index: 20;
    width: min(360px, 72vw);
}
.intro-profile-floating div[data-testid="stForm"] {
    position: fixed;
    left: 55.5vw;
    top: 49.5vh;
    z-index: 20;
    width: min(330px, 34vw);
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
.intro-profile-floating div[data-testid="stForm"] [data-testid="stVerticalBlock"] {
    gap: clamp(6px, 1.05vh, 12px);
}
.intro-profile-floating div[data-testid="stForm"] label {
    display: none !important;
}
.intro-profile-floating div[data-testid="stForm"] input,
.intro-profile-floating div[data-testid="stForm"] div[data-baseweb="select"] > div {
    min-height: clamp(24px, 3.5vh, 34px) !important;
    height: clamp(24px, 3.5vh, 34px) !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: rgba(255,255,255,.18) !important;
    box-shadow: none !important;
    color: #2c2528 !important;
    font-size: clamp(12px, 1.45vw, 18px) !important;
    font-weight: 800 !important;
    padding: 0 8px !important;
}
.intro-profile-floating div[data-testid="stForm"] .stButton {
    position: fixed;
    left: 50%;
    bottom: 5vh;
    transform: translateX(-50%);
    width: min(260px, 54vw);
}
.intro-template-active div[data-testid="stForm"],
div[data-testid="stForm"]:has(#intro-template-form-anchor) {
    position: fixed;
    left: 55.5vw;
    top: 49.5vh;
    z-index: 20;
    width: min(330px, 34vw);
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
div[data-testid="stForm"]:has(#intro-template-form-anchor) label {
    display: none !important;
}
div[data-testid="stForm"]:has(#intro-template-form-anchor) input,
div[data-testid="stForm"]:has(#intro-template-form-anchor) div[data-baseweb="select"] > div {
    min-height: clamp(24px, 3.5vh, 34px) !important;
    height: clamp(24px, 3.5vh, 34px) !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: rgba(255,255,255,.18) !important;
    box-shadow: none !important;
    color: #2c2528 !important;
    font-size: clamp(12px, 1.45vw, 18px) !important;
    font-weight: 800 !important;
    padding: 0 8px !important;
}
div[data-testid="stForm"]:has(#intro-template-form-anchor) .stButton {
    position: fixed;
    left: 50%;
    bottom: 5vh;
    transform: translateX(-50%);
    width: min(260px, 54vw);
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) {
    position: fixed;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    z-index: 30;
    width: min(430px, 88vw);
    max-height: none;
    overflow: visible;
    padding: 16px 18px 18px !important;
    border: 2px solid rgba(168, 101, 116, .86) !important;
    border-radius: 20px !important;
    background: rgba(255, 247, 250, .98) !important;
    box-shadow: 0 18px 44px rgba(104, 58, 75, .28) !important;
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) label,
div[data-testid="stForm"]:has(#calendar-editor-anchor) [data-testid="stMarkdownContainer"] p {
    color: #7a5360 !important;
    font-family: "Comic Sans MS", "Comic Sans", "Gaegu", "Microsoft YaHei", cursive !important;
    font-weight: 850 !important;
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) input {
    border: 1px solid rgba(198, 148, 157, .72) !important;
    border-radius: 12px !important;
    background: #fffdfc !important;
    color: #6d5260 !important;
    font-family: "Comic Sans MS", "Comic Sans", "Gaegu", "Microsoft YaHei", cursive !important;
    font-size: 15px !important;
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) .stRadio {
    margin-top: 0;
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) [role="radiogroup"] {
    gap: 5px 8px !important;
    flex-wrap: wrap !important;
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) [role="radio"] {
    min-height: 26px !important;
}
div[data-testid="stForm"]:has(#calendar-editor-anchor) .stButton > button {
    min-height: 36px;
    border-radius: 14px !important;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) {
    position: relative;
    width: min(1101px, calc(100vw - 72px));
    aspect-ratio: 1475 / 670;
    margin: 0 auto 14px auto;
    padding: 0 !important;
    border: 0 !important;
    background-repeat: no-repeat !important;
    background-position: center top !important;
    background-size: 100% 100% !important;
    box-shadow: none !important;
    overflow: hidden;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) label {
    display: none !important;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) [data-testid="stTextArea"] {
    position: absolute;
    left: 12.2%;
    top: 31.5%;
    width: 35.8%;
    z-index: 5;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) textarea {
    height: calc(min(454px, calc((100vw - 72px) * 670 / 1475)) * .39) !important;
    min-height: 168px !important;
    resize: none !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #57434b !important;
    font-family: "KaiTi", "STKaiti", "Microsoft YaHei", cursive !important;
    font-size: clamp(16px, 1.5vw, 21px) !important;
    line-height: 1.78 !important;
    padding: 0 8px !important;
    caret-color: #ef3f55 !important;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) textarea::placeholder {
    color: rgba(152, 113, 123, .38) !important;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) div[data-testid="stFormSubmitButton"] {
    position: absolute;
    left: 42%;
    top: 75.8%;
    width: 8.5%;
    z-index: 7;
}
div[data-testid="stForm"]:has(#diary-entry-form-anchor) div[data-testid="stFormSubmitButton"] button,
.diary-flip-control .stButton > button {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #ef3f55 !important;
    font-size: clamp(18px, 2.2vw, 34px) !important;
    font-weight: 950 !important;
    padding: 0 !important;
    min-height: auto !important;
}
.diary-right-reply {
    position: absolute;
    left: 57.4%;
    top: 25.8%;
    width: 33.4%;
    height: 45%;
    overflow: hidden;
    z-index: 4;
    color: #4b5666;
    font-size: clamp(16px, 1.5vw, 21px);
    line-height: 1.78;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: "KaiTi", "STKaiti", "Microsoft YaHei", cursive;
}
.diary-flip-link {
    position: absolute;
    left: 84.2%;
    top: 74.8%;
    z-index: 8;
    color: #ef3f55 !important;
    font-size: clamp(18px, 2.2vw, 34px);
    font-weight: 950;
    text-decoration: none !important;
    font-family: "Microsoft YaHei", sans-serif;
}
.diary-flip-control {
    position: fixed;
    left: calc(50vw + min(1101px, calc(100vw - 72px)) * .34);
    top: calc(1rem + min(500px, calc((100vw - 72px) * 670 / 1475)) * .75);
    z-index: 25;
    width: calc(min(1101px, calc(100vw - 72px)) * .12);
}
.diary-action-row {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 10px 0 16px;
}
@media (max-width: 850px) {
    .cover-scene, .intro-grid, .history-spread, .calendar-deco, .history-header {
        grid-template-columns: 1fr;
    }
    .calendar-head { flex-direction: column; align-items: stretch; }
    .msg-stack { max-width: 78%; }
    .history-column.left { margin-top: 0; }
    .history-column.right .history-card,
    .history-card { height: 138px; }
    .intro-profile-floating div[data-testid="stForm"] {
        left: 15vw;
        top: 42vh;
        width: 70vw;
    }
    div[data-testid="stForm"]:has(#intro-template-form-anchor) {
        left: 15vw;
        top: 42vh;
        width: 70vw;
    }
    div[data-testid="stForm"]:has(#diary-entry-form-anchor) {
        position: static;
        width: 100%;
        margin-top: 8px;
    }
    div[data-testid="stForm"]:has(#diary-entry-form-anchor) [data-testid="stTextArea"],
    div[data-testid="stForm"]:has(#diary-entry-form-anchor) div[data-testid="stFormSubmitButton"],
    .diary-right-reply,
    .diary-flip-link {
        position: static;
        width: auto;
        height: auto;
        margin: 10px 16px;
    }
    .diary-flip-control {
        position: static;
        width: 100%;
        margin-bottom: 12px;
    }
    .diary-action-row {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def _inject_css() -> None:
    st.markdown(DIARY_CSS, unsafe_allow_html=True)


def _template_path(name: str) -> Optional[Path]:
    filename = TEMPLATE_FILES.get(name)
    if not filename:
        return None
    path = TEMPLATE_DIR / filename
    return path if path.exists() else None


def _template_data_url(name: str) -> Optional[str]:
    path = _template_path(name)
    if not path:
        return None
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _clean_html_fragment(fragment: str) -> str:
    return "".join(line.strip() for line in str(fragment or "").splitlines() if line.strip())


def _render_template(name: str, overlays: str = "") -> bool:
    url = _template_data_url(name)
    if not url:
        return False
    clean_overlays = _clean_html_fragment(overlays)
    st.markdown(
        f"<div class=\"template-frame template-{name}\" style=\"background-image: url('{url}');\">"
        f"<div class=\"template-overlay\">{clean_overlays}</div></div>",
        unsafe_allow_html=True,
    )
    return True


def _template_help() -> None:
    st.info(
        "要完全使用原图且不改变原图字体，请把 5 张模板图放到 "
        "`assets/diary_templates/`，文件名分别为 "
        "`cover.jpg`, `intro.jpg`, `calendar.jpg`, `history.jpg`, `chat.jpg`。"
    )


def _weekday_en(dt: datetime) -> str:
    return ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][dt.weekday()]


def _month_tab() -> str:
    return str(datetime.now().month)


def _mood_entry(moods: Dict[str, Any], key: str) -> Dict[str, str]:
    value = moods.get(key, "")
    if isinstance(value, dict):
        return {
            "emoji": str(value.get("emoji", "") or ""),
            "event": str(value.get("event", "") or "")[:30],
        }
    return {"emoji": str(value or ""), "event": ""}


def _query_value(name: str) -> str:
    value = st.query_params.get(name, "")
    if isinstance(value, list):
        return str(value[0] if value else "")
    return str(value or "")


def _consume_calendar_save(year: int, month: int) -> None:
    day_key = _query_value("mood_day")
    if not day_key:
        return
    try:
        picked = datetime.strptime(day_key, "%Y-%m-%d")
    except Exception:
        st.query_params.clear()
        st.rerun()
        return
    if picked.year == year and picked.month == month:
        if _query_value("mood_clear"):
            save_mood(day_key, "", "")
        else:
            save_mood(day_key, _query_value("mood_emoji"), _query_value("mood_event"))
    st.query_params.clear()
    st.rerun()


def _tabs(active: str) -> str:
    tabs = ["COVER", "INTRO", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "NOTE", "INFO"]
    html = ['<div class="diary-tabs">']
    for item in tabs:
        klass = "diary-tab"
        if item in ["COVER", "INTRO", "NOTE", "INFO"]:
            klass += " small"
        if str(item) == str(active):
            klass += " active" if item in ["COVER", "INTRO", "NOTE", "INFO"] else " month-active"
        html.append(f'<div class="{klass}">{item}</div>')
    html.append("</div>")
    return "".join(html)


def _open_shell(active: str) -> None:
    st.markdown(f'<div class="diary-shell">{_tabs(active)}<div class="diary-page">', unsafe_allow_html=True)


def _close_shell() -> None:
    st.markdown("</div></div>", unsafe_allow_html=True)


def _back_home_button() -> None:
    if st.button("← 返回功能选择", key="psy_back_home"):
        st.session_state.page = "home"
        st.rerun()


def render_cover() -> None:
    year = datetime.now().year
    if _render_template("cover"):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("进入我的心理日记本", use_container_width=True, key="enter_diary_tpl"):
                st.session_state.diary_stage = "INTRO" if not st.session_state.get("diary_profile") else _month_tab()
                st.rerun()
        return

    _template_help()
    _open_shell("COVER")
    st.markdown(
        f"""
        <div class="cover-scene">
            <div>
                <div class="cover-prop">🪴</div>
                <div class="doodle">🐰📖</div>
                <div class="cover-side-note">🍰</div>
            </div>
            <div>
                <div class="big-bubble">
                    <div class="title-year">{year}</div>
                    <div class="title-main">EVERY<br/>HEALING<br/>DIARY</div>
                </div>
                <div class="loading-text">Opening your diary...</div>
            </div>
            <div>
                <div class="doodle">🐻✏️</div>
                <div class="cover-prop">🐱</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _close_shell()
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("进入我的心理日记本", use_container_width=True, key="enter_diary"):
            st.session_state.diary_stage = "INTRO" if not st.session_state.get("diary_profile") else _month_tab()
            st.rerun()


def render_intro() -> None:
    year = datetime.now().year
    profile = st.session_state.get("diary_profile") or {}
    profile_overlays = f"""
        <div class="tpl-text" style="left:57%;top:51%;width:22%;">{escape(profile.get("name", ""))}</div>
        <div class="tpl-text" style="left:57%;top:56%;width:22%;">{escape(profile.get("mbti", ""))}</div>
        <div class="tpl-text" style="left:57%;top:61%;width:22%;">{escape(profile.get("sns", ""))}</div>
        <div class="tpl-text" style="left:61%;top:66%;width:18%;">{escape(profile.get("deco_level", ""))}</div>
        <div class="tpl-text" style="left:62%;top:71%;width:20%;">{escape(profile.get("signature", ""))}</div>
    """
    if _render_template("intro", profile_overlays):
        with st.form("diary_profile_form_tpl"):
            st.markdown('<span id="intro-template-form-anchor"></span>', unsafe_allow_html=True)
            (c1,) = st.columns(1)
            with c1:
                name = st.text_input("NAME", value=profile.get("name", st.session_state.get("user_nickname", "")), label_visibility="collapsed")
                mbti = st.text_input("MBTI", value=profile.get("mbti", ""), placeholder="可不填", label_visibility="collapsed")
                sns = st.text_input("SNS @", value=profile.get("sns", ""), placeholder="可不填", label_visibility="collapsed")
            with c1:
                deco_level = st.selectbox("DECO LEVEL", ["Lv.1", "Lv.2", "Lv.3", "Lv.4"], index=0, label_visibility="collapsed")
                companion = st.text_input("AI COMPANION", value=profile.get("companion", "Echo"), label_visibility="collapsed")
                signature = st.text_input("SIGNATURE", value=profile.get("signature", ""), placeholder="写一句给自己的话", label_visibility="collapsed")
            submitted = st.form_submit_button("START", use_container_width=True)
        if submitted:
            save_profile({
                "name": name.strip() or "日记本主人",
                "mbti": mbti.strip(),
                "sns": sns.strip(),
                "deco_level": deco_level,
                "companion": companion.strip() or "Echo",
                "signature": signature.strip(),
            })
            st.session_state.diary_stage = _month_tab()
            st.rerun()
        return

    _open_shell("INTRO")
    st.markdown(
        f"""
        <div class="intro-grid">
            <div class="intro-title">
                <div class="title-year">{year}</div>
                <div class="title-main">EVERY<br/>HEALING<br/>DIARY</div>
            </div>
            <div>
                <div class="avatar-frame">🐰</div>
                <div class="profile-lines">
                    <div><span>NAME :</span> {escape(profile.get("name", "________"))}</div>
                    <div><span>MBTI :</span> {escape(profile.get("mbti", "________"))}</div>
                    <div><span>SNS :</span> @{escape(profile.get("sns", "________"))}</div>
                    <div><span>DECO LEVEL :</span> {escape(profile.get("deco_level", "Lv.__"))}</div>
                    <div><span>SIGNATURE :</span> {escape(profile.get("signature", "________"))}</div>
                </div>
            </div>
        </div>
        <div class="profile-form-wrap">
        """,
        unsafe_allow_html=True,
    )
    with st.form("diary_profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("NAME", value=profile.get("name", st.session_state.get("user_nickname", "")))
            mbti = st.text_input("MBTI", value=profile.get("mbti", ""), placeholder="可不填")
            sns = st.text_input("SNS @", value=profile.get("sns", ""), placeholder="可不填")
        with c2:
            deco_level = st.selectbox("DECO LEVEL", ["Lv.1", "Lv.2", "Lv.3", "Lv.4"], index=0)
            companion = st.text_input("AI COMPANION", value=profile.get("companion", "Echo"))
            signature = st.text_input("SIGNATURE", value=profile.get("signature", ""), placeholder="写一句给自己的话")
        submitted = st.form_submit_button("START", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    _close_shell()

    if submitted:
        save_profile({
            "name": name.strip() or "日记本主人",
            "mbti": mbti.strip(),
            "sns": sns.strip(),
            "deco_level": deco_level,
            "companion": companion.strip() or "Echo",
            "signature": signature.strip(),
        })
        st.session_state.diary_stage = _month_tab()
        st.rerun()


def render_calendar() -> None:
    today = datetime.now()
    year, month = today.year, today.month
    moods = st.session_state.get("diary_moods", {}) or {}
    _consume_calendar_save(year, month)

    if _template_path("calendar"):
        options = ["", "😊", "🙂", "😐", "😕", "😢", "😡", "😴", "🥰", "🌧️", "🌈"]
        cal_for_overlay = calendar.Calendar(firstweekday=6)
        weeks_for_overlay = cal_for_overlay.monthdayscalendar(year, month)
        overlay_parts = []
        modal_parts = []
        row_tops = [26.55, 38.05, 49.65, 61.55, 73.7, 85.1]
        row_heights = [10.35, 10.35, 10.45, 10.55, 10.65, 8.5]

        for row_idx, week in enumerate(weeks_for_overlay):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                key = f"{year}-{month:02d}-{day:02d}"
                entry = _mood_entry(moods, key)
                cell_left = 15.6 + col_idx * 11.75
                cell_top = row_tops[min(row_idx, len(row_tops) - 1)]
                cell_height = row_heights[min(row_idx, len(row_heights) - 1)]
                modal_id = f"calendar-modal-{key}"
                overlay_parts.append(
                    f'<a class="tpl-day-hotspot" href="#{modal_id}" '
                    f'style="left:{cell_left:.2f}%;top:{cell_top:.2f}%;width:11.75%;height:{cell_height:.2f}%;" aria-label="编辑 {key}"></a>'
                )
                if entry["emoji"] or entry["event"]:
                    overlay_parts.append(
                        f'<div class="tpl-mood-entry" style="left:{cell_left + 1.1:.2f}%;top:{cell_top + 2.55:.2f}%;width:9.5%;height:{max(cell_height - 2.75, 5.8):.2f}%;">'
                        f'<div class="entry-emoji">{escape(entry["emoji"])}</div>'
                        f'<div class="entry-event">{escape(entry["event"])}</div></div>'
                    )

                radios = []
                for option in options:
                    label = "不填写" if option == "" else option
                    checked = " checked" if option == entry["emoji"] or (option == "" and not entry["emoji"]) else ""
                    radios.append(f'<label><input type="radio" name="mood_emoji" value="{escape(option)}"{checked}> {escape(label)}</label>')
                modal_parts.append(
                    f'<div class="calendar-modal-shade" id="{modal_id}">'
                    f'<form class="calendar-modal" method="get">'
                    f'<input type="hidden" name="mood_day" value="{key}">'
                    f'<div class="calendar-modal-title">给 {month} 月 {day} 日贴一小格心情</div>'
                    f'<div>心情</div><div class="calendar-emoji-row">{"".join(radios)}</div>'
                    f'<label>小事件（30字内）</label>'
                    f'<input type="text" name="mood_event" value="{escape(entry["event"])}" maxlength="30" placeholder="今天发生的小事件...">'
                    f'<div class="calendar-modal-actions">'
                    f'<button type="submit">保存</button>'
                    f'<button type="submit" name="mood_clear" value="1">清空</button>'
                    f'<a href="#calendar">返回</a>'
                    f'</div></form></div>'
                )

        overlay_parts.extend(modal_parts)
        st.markdown('<span id="calendar"></span>', unsafe_allow_html=True)
        _render_template("calendar", "".join(overlay_parts))
        return

    _open_shell(str(month))
    st.markdown(
        f"""
        <div class="calendar-head">
            <div class="month-title">{month}<span style="font-size:42px;margin-left:14px;">{today.strftime("%B").upper()}</span></div>
            <div class="calendar-note">今天是 {today.strftime("%Y.%m.%d")} · {_weekday_en(today)}，点击日期格记录心情和 30 字内小事件。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _close_shell()


def _history_card(record: Optional[Dict[str, Any]], fallback_dt: datetime) -> str:
    if record:
        raw_time = record.get("updated_at") or record.get("created_at") or ""
        try:
            dt = datetime.fromisoformat(raw_time)
        except Exception:
            dt = fallback_dt
        summary = escape(record.get("summary", ""))
        mood = escape(record.get("mood", "") or "📝")
        meta = dt.strftime("%H:%M")
        body = f"""
            <div style="font-size:28px">{mood}</div>
            <div class="history-summary">{summary}</div>
            <div class="history-meta">{meta}</div>
        """
        empty_class = ""
    else:
        dt = fallback_dt
        body = '<div class="history-summary"></div>'
        empty_class = " empty"

    return f"""
    <div class="history-card{empty_class}">
        <div class="history-date">{_weekday_en(dt)}<br/><span style="font-size:26px">{dt.day}</span></div>
        <div class="history-body">{body}</div>
    </div>
    """


def render_history() -> None:
    open_history_id = _query_value("open_history")
    if open_history_id:
        st.session_state.selected_history_id = open_history_id
        st.session_state.diary_stage = "HISTORY_CHAT"
        st.query_params.clear()
        st.rerun()

    records = list_history_records("psytest")
    page_size = 7
    total_pages = max(1, (len(records) + page_size - 1) // page_size)
    page = min(st.session_state.get("diary_history_page", 0), total_pages - 1)
    start = page * page_size
    cells: List[Optional[Dict[str, Any]]] = records[start:start + page_size]
    cells += [None] * (page_size - len(cells))

    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    fallback_dates = [monday + timedelta(days=offset) for offset in range(7)]

    if _template_path("history"):
        slots = [
            (4.0, 32.0, 42.0, 16.0),
            (4.0, 52.8, 42.0, 16.0),
            (4.0, 73.5, 42.0, 16.0),
            (54.0, 10.8, 42.0, 15.0),
            (54.0, 31.2, 42.0, 15.0),
            (54.0, 51.8, 42.0, 15.0),
            (54.0, 72.4, 42.0, 15.0),
        ]
        overlay_parts = []
        date_slots = [
            (4.0, 33.2, 13.6),
            (4.0, 54.2, 13.6),
            (4.0, 75.3, 13.6),
            (52.2, 11.0, 13.6),
            (52.2, 33.1, 13.6),
            (52.2, 55.0, 13.6),
            (52.2, 77.0, 13.6),
        ]
        for idx, dt in enumerate(fallback_dates):
            x, y, w = date_slots[idx]
            sun_class = " sun" if dt.weekday() == 6 else ""
            overlay_parts.append(
                f"""
                <div class="tpl-date-chip{sun_class}" style="left:{x}%;top:{y}%;width:{w}%;">
                    <span>{_weekday_en(dt)}</span><span>{dt.day}</span>
                </div>
                """
            )
        for idx, record in enumerate(cells):
            if not record:
                continue
            x, y, w, h = slots[idx]
            raw_time = record.get("updated_at") or record.get("created_at") or ""
            try:
                dt = datetime.fromisoformat(raw_time)
                meta = dt.strftime("%H:%M")
            except Exception:
                meta = ""
            summary = escape(record.get("summary", ""))
            mood = escape(record.get("mood", "") or "📝")
            overlay_parts.append(
                f"""
                <a class="tpl-history-hotspot" href="?open_history={escape(record['id'])}" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%;" aria-label="打开这条记录"></a>
                <div class="tpl-card" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%;">
                    <div style="font-size:clamp(16px,2vw,28px);">{mood}</div>
                    <div>{summary}</div>
                    <div style="color:#9a626d;margin-top:4px;">{meta}</div>
                </div>
                """
            )
        _render_template("history", "".join(overlay_parts))

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("上一页", disabled=page <= 0, use_container_width=True, key="history_prev_tpl"):
                st.session_state.diary_history_page = max(0, page - 1)
                st.rerun()
        with c2:
            st.caption(f"第 {page + 1} / {total_pages} 页 · 共 {len(records)} 条")
        with c3:
            if st.button("下一页", disabled=page >= total_pages - 1, use_container_width=True, key="history_next_tpl"):
                st.session_state.diary_history_page = min(total_pages - 1, page + 1)
                st.rerun()
        return

    _open_shell("INFO")
    st.markdown(
        f"""
        <div class="history-header">
            <div class="history-month">{today.month}<br/><span style="font-size:18px;text-shadow:none;color:#333;">{today.year}<br/>{today.strftime("%b").upper()}</span></div>
            <div class="history-bubble"></div>
        </div>
        <div class="history-title">HISTORY RECORDS</div>
        """,
        unsafe_allow_html=True,
    )
    left_cards = "".join(_history_card(cells[i], fallback_dates[i]) for i in range(3))
    right_cards = "".join(_history_card(cells[i], fallback_dates[i]) for i in range(3, 7))
    st.markdown(
        f"""
        <div class="history-spread">
            <div class="history-column left">{left_cards}</div>
            <div class="history-column right">{right_cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _close_shell()

    for row in range(4):
        cols = st.columns(2)
        for col_idx in range(2):
            idx = row * 2 + col_idx
            if idx >= page_size:
                continue
            record = cells[idx]
            with cols[col_idx]:
                if record:
                    if st.button("打开这条记录", key=f"open_hist_{record['id']}", use_container_width=True):
                        st.session_state.selected_history_id = record["id"]
                        st.session_state.diary_stage = "HISTORY_CHAT"
                        st.rerun()
                else:
                    st.button("空白记录框", key=f"empty_hist_{page}_{idx}", disabled=True, use_container_width=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("上一页", disabled=page <= 0, use_container_width=True, key="history_prev"):
            st.session_state.diary_history_page = max(0, page - 1)
            st.rerun()
    with c2:
        st.markdown(f"<div class='tip-box' style='text-align:center'>第 {page + 1} / {total_pages} 页 · 共 {len(records)} 条</div>", unsafe_allow_html=True)
    with c3:
        if st.button("下一页", disabled=page >= total_pages - 1, use_container_width=True, key="history_next"):
            st.session_state.diary_history_page = min(total_pages - 1, page + 1)
            st.rerun()


def _message_html(msg: Dict[str, Any], user_avatar: str = "🐰", ai_avatar: str = "🐻") -> str:
    role = msg.get("role", "assistant")
    content = escape(str(msg.get("content", ""))).replace("\n", "<br/>")
    t = message_time(msg)
    if role == "user":
        return f"""
        <div class="msg-row user">
            <div class="msg-stack"><div class="msg-bubble">{content}</div><div class="msg-time" style="text-align:right">{escape(t)}</div></div>
            <div class="msg-avatar">{user_avatar}</div>
        </div>
        """
    return f"""
    <div class="msg-row assistant">
        <div class="msg-avatar">{ai_avatar}</div>
        <div class="msg-stack"><div class="msg-bubble">{content}</div><div class="msg-time">{escape(t)}</div></div>
    </div>
    """


def _latest_exchange(messages: List[Dict[str, Any]]) -> Dict[str, str]:
    user_text = ""
    assistant_text = ""
    for msg in reversed(messages):
        role = msg.get("role")
        content = str(msg.get("content", ""))
        if role == "assistant" and not assistant_text:
            assistant_text = content
        elif role == "user" and not user_text:
            user_text = content
        if user_text and assistant_text:
            break
    if not user_text:
        assistant_text = ""
    return {"user": user_text, "assistant": assistant_text}


def _chat_paper(messages: List[Dict[str, Any]], title: str) -> None:
    now = datetime.now()
    date_text = message_date(messages[0]) if messages else now.strftime("%Y.%m.%d")
    exchange = st.session_state.get("psy_visible_exchange")
    if not isinstance(exchange, dict):
        exchange = _latest_exchange(messages)
    user_text = str(exchange.get("user") or "")
    assistant_text = str(exchange.get("assistant") or "")

    if _template_path("chat"):
        left_html = escape(user_text).replace("\n", "<br/>") or '<span class="tpl-diary-empty">把想说的话写在这里...</span>'
        right_html = escape(assistant_text).replace("\n", "<br/>") or '<span class="tpl-diary-empty">日记会在这里回应你。</span>'
        parts = [
            f'<div class="tpl-text" style="left:8%;top:9%;width:42%;">{escape(date_text)} · {_weekday_en(now)} · {now.strftime("%H:%M")}</div>',
            f'<div class="tpl-diary-page-text left">{left_html}</div>',
            f'<div class="tpl-diary-page-text right">{right_html}</div>',
        ]
        _render_template("chat", "".join(parts))
        return

    left_html = escape(user_text).replace("\n", "<br/>") or "把想说的话写在这里..."
    right_html = escape(assistant_text).replace("\n", "<br/>") or "日记会在这里回应你。"
    html = [
        '<div class="chat-paper">',
        f'<div class="chat-top"><div>{escape(date_text)} · {_weekday_en(now)} · {now.strftime("%H:%M")}</div><div>{escape(title)}</div></div>',
        f'<div class="history-spread"><div class="msg-bubble">{left_html}</div><div class="msg-bubble">{right_html}</div></div>',
    ]
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _history_dialog(messages: List[Dict[str, Any]], title: str, record: Dict[str, Any]) -> None:
    messages = normalize_messages(messages)
    raw_time = record.get("updated_at") or record.get("created_at") or record.get("timestamp") or ""
    try:
        time_text = datetime.fromisoformat(str(raw_time)).strftime("%Y.%m.%d %H:%M")
    except Exception:
        time_text = str(raw_time)[:16]
    rows = "".join(
        _clean_html_fragment(_message_html(msg))
        for msg in messages
        if str(msg.get("content", "")).strip()
    )
    if not rows:
        rows = '<div class="tip-box">这条记录还没有可显示的对话内容。</div>'
    st.markdown(
        f"<div class=\"chat-paper history-dialog\">"
        f"<div class=\"chat-top\"><div>{escape(time_text)}</div><div>{escape(title or '历史对话')}</div></div>"
        f"{rows}</div>",
        unsafe_allow_html=True,
    )


def _turn_diary_page() -> None:
    st.session_state.psy_visible_exchange = {"user": "", "assistant": ""}
    st.session_state.psy_diary_text = ""
    st.session_state.show_psy_report = False
    st.rerun()


def _apply_psy_proactive(messages: List[Dict[str, Any]], scores: Dict[str, int], force: bool = False) -> bool:
    messages, added, _ = maybe_add_care_proactive("psytest", messages, scores, force=force)
    if not added:
        return False
    record_id = save_history_record(
        "psytest",
        messages,
        scores,
        st.session_state.get("psy_record_id"),
        title="AI 心理评测主动关怀",
        mood="",
    )
    st.session_state.psy_record_id = record_id
    st.session_state.psy_messages = messages
    st.session_state.psy_scores = scores
    st.session_state.psy_visible_exchange = _latest_exchange(messages)
    return True


def render_live_chat() -> None:
    messages = st.session_state.get("psy_messages", [])
    scores = st.session_state.get("psy_scores") or score_messages(messages)
    if _apply_psy_proactive(messages, scores):
        messages = st.session_state.get("psy_messages", [])
        scores = st.session_state.get("psy_scores") or score_messages(messages)

    _chat_paper(messages, "双人聊天")

    prompt = st.chat_input("把想说的话写在这里...", key="psy_live_chat_input")

    if prompt and prompt.strip():
        user_text = prompt.strip()
        assessment = assess_message_safety(user_text)
        messages.append(attach_safety_metadata(make_message("user", user_text), assessment))
        scores = score_messages(messages)
        if assessment.needs_support:
            reply = make_safety_reply(assessment, "Echo")
            assistant_message = make_message("assistant", reply)
            assistant_message["safety_response"] = True
            assistant_message["safety_level"] = assessment.level
            if assessment.is_crisis:
                assistant_message["crisis_popup"] = True
                queue_crisis_alert("psytest", assessment, user_text, "Echo")
            messages.append(assistant_message)
        else:
            with st.spinner("Echo 正在右页写回复..."):
                reply = generate_reply("psytest", user_text, messages, scores)
            messages.append(make_message("assistant", reply))
        record_id = save_history_record("psytest", messages, scores, st.session_state.get("psy_record_id"), mood="")
        st.session_state.psy_record_id = record_id
        st.session_state.psy_messages = messages
        st.session_state.psy_scores = scores
        st.session_state.psy_diary_text = ""
        st.session_state.psy_visible_exchange = {"user": user_text, "assistant": reply}
        st.rerun()

    score_html = "".join(f'<span class="score-pill">{name}: {scores.get(key, 5)}/10</span>' for key, name in DIMENSIONS.items())
    st.markdown(f"<div>{score_html}</div>", unsafe_allow_html=True)
    if st.session_state.get("show_psy_report"):
        st.markdown(make_report(scores, messages), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("生成/查看报告", use_container_width=True, key="show_report"):
            st.session_state.show_psy_report = not st.session_state.get("show_psy_report", False)
            st.rerun()
    with c2:
        if st.button("历史记录", use_container_width=True, key="go_history_from_chat"):
            st.session_state.diary_stage = "INFO"
            st.rerun()
    with c3:
        if st.button("主动关怀", use_container_width=True, key="psy_force_proactive"):
            if _apply_psy_proactive(messages, scores, force=True):
                st.rerun()
            st.toast("先写下一点心情，Echo 会更懂你。")
    with c4:
        if st.button("重新开始一次评估", use_container_width=True, key="reset_psy_chat"):
            st.session_state.psy_messages = [make_message("assistant", "新的日记页打开了。今天先从哪里说起？")]
            st.session_state.psy_scores = {}
            st.session_state.psy_record_id = None
            st.session_state.show_psy_report = False
            st.session_state.psy_diary_text = ""
            st.session_state.psy_visible_exchange = {"user": "", "assistant": ""}
            st.rerun()

def render_history_chat() -> None:
    record_id = st.session_state.get("selected_history_id")
    record = load_history_record(record_id) if record_id else None
    if not record:
        st.warning("这条历史记录没有找到。")
        if st.button("返回历史记录"):
            st.session_state.selected_history_id = None
            st.session_state.diary_stage = "INFO"
            st.rerun()
        return

    messages = normalize_messages(record.get("messages") or record.get("display_messages") or [])
    _open_shell("NOTE")
    _history_dialog(messages, record.get("title") or "历史对话", record)
    _close_shell()

    text_record = record.get("conversation_text") or messages_to_readable_text(
        messages,
        record.get("title") or "历史对话",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("返回历史记录", use_container_width=True, key="back_history_list"):
            st.session_state.selected_history_id = None
            st.session_state.diary_stage = "INFO"
            st.rerun()
    with c2:
        if st.button("把这条记录接着聊", use_container_width=True, key="continue_history"):
            st.session_state.psy_messages = messages
            st.session_state.psy_scores = record.get("scores", {})
            st.session_state.psy_record_id = record_id
            st.session_state.selected_history_id = None
            st.session_state.diary_stage = "NOTE"
            st.rerun()
    with c3:
        st.download_button(
            "下载文字记录",
            data=text_record,
            file_name=f"{record_id}_对话记录.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_history_text",
        )

    prompt = st.chat_input("继续追问或补充这条历史记录...", key="history_chat_input")
    if prompt:
        assessment = assess_message_safety(prompt)
        messages.append(attach_safety_metadata(make_message("user", prompt), assessment))
        scores = score_messages(messages)
        if assessment.needs_support:
            assistant_message = make_message("assistant", make_safety_reply(assessment, "Echo"))
            assistant_message["safety_response"] = True
            assistant_message["safety_level"] = assessment.level
            if assessment.is_crisis:
                assistant_message["crisis_popup"] = True
                queue_crisis_alert("psytest_history", assessment, prompt, "Echo")
            messages.append(assistant_message)
        else:
            messages.append(make_message("assistant", generate_reply("psytest", prompt, messages, scores)))
        update_history_messages(record_id, messages, scores)
        st.rerun()


def render_nav() -> None:
    stage = st.session_state.get("diary_stage", _month_tab())
    if stage not in ("NOTE", "INFO"):
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("双人聊天", use_container_width=True, key="nav_chat_calendar"):
                st.session_state.diary_stage = "NOTE"
                st.rerun()
        with c2:
            if st.button("历史记录", use_container_width=True, key="nav_history_calendar"):
                st.session_state.diary_stage = "INFO"
                st.rerun()
        with c3:
            _back_home_button()
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("心情日历", use_container_width=True, key="nav_calendar"):
            st.session_state.diary_stage = _month_tab()
            st.rerun()
    with c2:
        if st.button("双人聊天", use_container_width=True, key="nav_chat"):
            st.session_state.diary_stage = "NOTE"
            st.rerun()
    with c3:
        if st.button("历史记录", use_container_width=True, key="nav_history"):
            st.session_state.diary_stage = "INFO"
            st.rerun()
    with c4:
        _back_home_button()


def render_psytest_diary() -> None:
    _inject_css()
    render_crisis_alert_if_needed()
    stage = st.session_state.get("diary_stage", "cover")

    if stage == "cover":
        st.markdown(
            """
            <style>
            div.stButton {
                position: fixed;
                left: 50%;
                bottom: 5vh;
                transform: translateX(-50%);
                z-index: 20;
                width: min(360px, 72vw);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        render_cover()
        return
    if stage == "INTRO" or not st.session_state.get("diary_profile"):
        render_intro()
        _back_home_button()
        return
    if stage == "INFO":
        render_history()
    elif stage == "HISTORY_CHAT":
        render_history_chat()
    elif stage == "NOTE":
        render_live_chat()
    else:
        render_calendar()

    if stage != "HISTORY_CHAT":
        render_nav()
