import asyncio
import json
import re
import os
import sys
import codecs
import datetime
import time
import traceback
import requests
import xml.etree.ElementTree as ET
import hashlib
import html as html_module
from pathlib import Path
from colorama import Fore, Style, init
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    import msvcrt

    def masked_input(prompt=""):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        chars = []
        while True:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):
                sys.stdout.write('\n')
                sys.stdout.flush()
                break
            elif ch == '\x08':
                if chars:
                    chars.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == '\x03':
                raise KeyboardInterrupt
            elif ch == '\x1a':
                raise EOFError
            elif ch in ('\x00', '\xe0'):
                msvcrt.getwch()
            else:
                chars.append(ch)
                sys.stdout.write('*')
                sys.stdout.flush()
        return ''.join(chars)
else:
    import termios
    import tty

    def masked_input(prompt=""):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        chars = []
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    break
                elif ch == '\x7f':
                    if chars:
                        chars.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ch == '\x03':
                    raise KeyboardInterrupt
                elif ch == '\x04':
                    raise EOFError
                else:
                    chars.append(ch)
                    sys.stdout.write('*')
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ''.join(chars)

init(autoreset=True)

CONFIG_DIR = Path("configs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = CONFIG_DIR / "settings.json"

STRINGS = {
    'th': {
        'ui_title': 'Login & แสดงเฉลยจากแบบฝึกหัด',
        'ui_view_db': 'ดูฐานข้อมูล',
        'ui_change_lang': 'เปลี่ยนภาษา (TH/EN)',
        'ui_exit': 'ออกจากโปรแกรม',
        'ui_menu_header': 'เมนูหลัก',

        'accounts_header': 'บัญชี Cambridge One / Chrome profiles',
        'accounts_empty': '[!] ยังไม่มีบัญชีในระบบ',
        'accounts_add': 'เพิ่มบัญชีใหม่',
        'accounts_cancel': 'ยกเลิก',
        'accounts_select': 'เลือก',
        'accounts_new_email': 'Email บัญชีใหม่',
        'accounts_invalid_email': '[-] Email ไม่ถูกต้อง',
        'accounts_added': '[+] เพิ่มบัญชี {email} แล้ว',
        'accounts_invalid_choice': '[-] ตัวเลือกไม่ถูกต้อง',
        'accounts_saved_pwd': '[saved password]',

        'login_opening_profile': '[*] กำลังเปิด Chrome profile: {path}',
        'login_browser_opened': '[+] เปิดเบราว์เซอร์แบบเก็บ session แล้ว',
        'login_checking_session': '[*] กำลังตรวจสอบ session...',
        'login_current_url': '[*] URL ปัจจุบัน: {url}',
        'login_session_ok': '[+] Session ยังใช้งานได้',
        'login_use_saved_pwd': '[+] ใช้รหัสผ่านที่บันทึกไว้',
        'login_enter_pwd': '[>] Password ของ {email}: ',
        'login_save_pwd_q': '[>] บันทึกรหัสผ่าน? (1=yes / 0=no): ',
        'login_pwd_saved': '[+] บันทึกรหัสผ่านแล้ว',
        'login_no_pwd': '[-] ไม่ได้ใส่รหัสผ่าน',
        'login_logging_in': '[*] Logging in...',
        'login_success': '[+] Login successful!',
        'login_failed': '[-] Login ไม่สำเร็จ',
        'login_cancel': '[!] ยกเลิก',

        'courses_header': 'คอร์สที่มี Digital Workbook',
        'courses_not_found': '[!] ไม่พบคอร์ส',
        'courses_select': 'เลือกคอร์ส:',
        'courses_refresh': 'รีเฟรชรายการคอร์ส',
        'courses_exit': 'ออกจากโปรแกรม',
        'courses_found': '[+] พบ {n} คอร์ส',
        'courses_opening': '[*] กำลังเปิด Digital Workbook: {name}',
        'courses_opened': '[+] คลิก Digital Workbook สำเร็จ',
        'courses_open_failed': '[-] ไม่พบ Digital Workbook',
        'courses_fetching': '[*] Fetching courses with Digital Workbooks...',

        'units_header': 'เลือกบทที่ต้องการดู',
        'units_not_found': '[!] ไม่พบบทเรียน',
        'units_back': 'กลับไปเลือกคอร์สใหม่',
        'units_select': 'เลือกบท (ตัวเลข): ',
        'units_loading': '[*] กำลังโหลด Units...',
        'units_found': '[+] พบ {n} บทเรียน',
        'units_opening': '[*] กำลังเปิดบท: {name}',
        'units_opened': '[+] เปิดบทสำเร็จ',
        'units_open_failed': '[-] ไม่พบบทนี้',
        'units_exercises_fetching': '[*] Fetching exercises in: {name}',
        'units_exercises_found': '[+] พบ {n} Lesson',

        'exercises_back': 'กลับไปเลือกบทใหม่',
        'exercises_select': 'เลือกแบบฝึกหัด (ตัวเลข): ',
        'exercises_none': '[!] ไม่มีแบบฝึกหัด',
        'exercises_selected': '[*] เลือก: {name}',
        'exercises_opening': '[*] กำลังเปิดแบบฝึกหัด: {name}',
        'exercises_opened': '[+] เปิดแบบฝึกหัดสำเร็จ',
        'exercises_open_failed': '[-] ไม่พบแบบฝึกหัดนี้',
        'exercises_already_open': '[+] อยู่ในหน้าแบบฝึกหัดข้อนี้เรียบร้อยแล้ว',
        'exercises_back_workbook': '[*] กำลังย้อนกลับสู่หน้า Workbook...',

        'cached_found': '[+] พบข้อมูลในฐานข้อมูล (saved at {time})',
        'cached_use_q': '[>] ใช้ข้อมูลที่บันทึกไว้? (1=yes / 0=no): ',
        'cached_header': 'เฉลยจากฐานข้อมูล: {name}',
        'datajs_fetching': '[*] กำลังดึงฐานข้อมูลคำตอบ',
        'datajs_not_found': '[-] ไม่พบ data.js',
        'datajs_parse_failed': '[-] ไม่สามารถแกะ data.js ได้',
        'answers_header': 'เฉลยแบบฝึกหัด: {name}',

        'printq_context': 'Context',
        'printq_audio': 'Audio',
        'printq_options': 'Options',
        'printq_correct': 'Correct',
        'printq_correct_id': 'Correct (id)',
        'printq_not_found': 'text not found',
        'printq_questions': 'questions',
        'summary': 'Summary',
        'summary_processed': 'processed',
        'summary_skipped': 'skipped',
        'summary_saved': '[+] saved to database',
        'summary_skip_finished': '[skip] {name} - activity finished',
        'summary_skip_noans': '[skip] {name} - no answers found',

        'db_empty': '[!] ฐานข้อมูลว่างเปล่า',
        'db_header': 'ฐานข้อมูลคำตอบ (ทั้งหมด {n} รายการ)',
        'db_saved_at': 'บันทึกเมื่อ',
        'db_xml_count': 'จำนวน XML',
        'db_select_view': 'เลือกหมายเลขเพื่อดูรายละเอียด (หรือ Enter เพื่อกลับ): ',
        'db_invalid_number': '[-] หมายเลขไม่ถูกต้อง',
        'db_enter_number': '[-] กรุณาใส่ตัวเลข',

        'input_enter_back': '[>] กด Enter เพื่อกลับ...',
        'input_enter_close': '[>] กด Enter เพื่อปิดเบราว์เซอร์...',
        'input_enter': '[>] กด Enter...',
        'input_choice': '[>] Enter choice: ',
        'input_invalid': 'ตัวเลือกไม่ถูกต้อง กรุณาเลือก 1-4',
        'input_number': '[-] กรุณาใส่ตัวเลข',

        'closing_browser': '[*] กำลังปิดเบราว์เซอร์...',
        'closed_browser': '[+] ปิดเบราว์เซอร์เรียบร้อย',
        'exit_program': '[*] กำลังออกจากโปรแกรม...',
        'goodbye': 'ลาก่อน!',
        'error_prefix': '[-] Error: {msg}',
        'fatal_prefix': '[-] Fatal Error: {msg}',
        'log_saved': '[*] log saved to: {path}',
        'log_session': 'Session log: {path}',
        'db_loaded': '[+] database loaded ({n} entries)',

        'lang_current': 'ภาษาปัจจุบัน: ไทย',
        'lang_switched': '[+] เปลี่ยนภาษาเป็น ไทย เรียบร้อย',
        'lang_menu_header': 'เลือกภาษา',
        'lang_th': 'ภาษาไทย',
        'lang_en': 'English',
        'lang_back': 'กลับเมนูหลัก',
    },
    'en': {
        'ui_title': 'Login & Show Answers from Exercises',
        'ui_view_db': 'View Database',
        'ui_change_lang': 'Change Language (TH/EN)',
        'ui_exit': 'Exit',
        'ui_menu_header': 'Main Menu',

        'accounts_header': 'Cambridge One Accounts / Chrome profiles',
        'accounts_empty': '[!] No accounts yet',
        'accounts_add': 'Add new account',
        'accounts_cancel': 'Cancel',
        'accounts_select': 'Select',
        'accounts_new_email': 'New account email',
        'accounts_invalid_email': '[-] Invalid email',
        'accounts_added': '[+] Added account {email}',
        'accounts_invalid_choice': '[-] Invalid choice',
        'accounts_saved_pwd': '[saved password]',

        'login_opening_profile': '[*] Opening Chrome profile: {path}',
        'login_browser_opened': '[+] Browser opened with saved session',
        'login_checking_session': '[*] Checking session...',
        'login_current_url': '[*] Current URL: {url}',
        'login_session_ok': '[+] Session still valid',
        'login_use_saved_pwd': '[+] Using saved password',
        'login_enter_pwd': '[>] Password for {email}: ',
        'login_save_pwd_q': '[>] Save password? (1=yes / 0=no): ',
        'login_pwd_saved': '[+] Password saved',
        'login_no_pwd': '[-] No password entered',
        'login_logging_in': '[*] Logging in...',
        'login_success': '[+] Login successful!',
        'login_failed': '[-] Login failed',
        'login_cancel': '[!] Cancelled',

        'courses_header': 'Courses with Digital Workbook',
        'courses_not_found': '[!] No courses found',
        'courses_select': 'Select course:',
        'courses_refresh': 'Refresh course list',
        'courses_exit': 'Exit program',
        'courses_found': '[+] Found {n} courses',
        'courses_opening': '[*] Opening Digital Workbook: {name}',
        'courses_opened': '[+] Digital Workbook clicked',
        'courses_open_failed': '[-] Digital Workbook not found',
        'courses_fetching': '[*] Fetching courses with Digital Workbooks...',

        'units_header': 'Select a unit',
        'units_not_found': '[!] No units found',
        'units_back': 'Back to course selection',
        'units_select': 'Select unit (number): ',
        'units_loading': '[*] Loading Units...',
        'units_found': '[+] Found {n} units',
        'units_opening': '[*] Opening unit: {name}',
        'units_opened': '[+] Unit opened',
        'units_open_failed': '[-] Unit not found',
        'units_exercises_fetching': '[*] Fetching exercises in: {name}',
        'units_exercises_found': '[+] Found {n} Lesson(s)',

        'exercises_back': 'Back to unit selection',
        'exercises_select': 'Select exercise (number): ',
        'exercises_none': '[!] No exercises',
        'exercises_selected': '[*] Selected: {name}',
        'exercises_opening': '[*] Opening exercise: {name}',
        'exercises_opened': '[+] Exercise opened',
        'exercises_open_failed': '[-] Exercise not found',
        'exercises_already_open': '[+] Already in this exercise page',
        'exercises_back_workbook': '[*] Going back to Workbook...',

        'cached_found': '[+] Found in database (saved at {time})',
        'cached_use_q': '[>] Use saved data? (1=yes / 0=no): ',
        'cached_header': 'Answers from database: {name}',
        'datajs_fetching': '[*] Fetching answer database',
        'datajs_not_found': '[-] data.js not found',
        'datajs_parse_failed': '[-] Failed to parse data.js',
        'answers_header': 'Exercise answers: {name}',

        'printq_context': 'Context',
        'printq_audio': 'Audio',
        'printq_options': 'Options',
        'printq_correct': 'Correct',
        'printq_correct_id': 'Correct (id)',
        'printq_not_found': 'text not found',
        'printq_questions': 'questions',
        'summary': 'Summary',
        'summary_processed': 'processed',
        'summary_skipped': 'skipped',
        'summary_saved': '[+] saved to database',
        'summary_skip_finished': '[skip] {name} - activity finished',
        'summary_skip_noans': '[skip] {name} - no answers found',

        'db_empty': '[!] database is empty',
        'db_header': 'answers database (total {n} entries)',
        'db_saved_at': 'saved at',
        'db_xml_count': 'XML count',
        'db_select_view': 'select number to view details (or Enter to return): ',
        'db_invalid_number': '[-] invalid number',
        'db_enter_number': '[-] please enter a number',

        'input_enter_back': '[>] Press Enter to return...',
        'input_enter_close': '[>] Press Enter to close browser...',
        'input_enter': '[>] Press Enter...',
        'input_choice': '[>] Enter choice: ',
        'input_invalid': 'Invalid choice, please select 1-4',
        'input_number': '[-] Please enter a number',

        'closing_browser': '[*] Closing browser...',
        'closed_browser': '[+] Browser closed',
        'exit_program': '[*] Exiting program...',
        'goodbye': 'Goodbye!',
        'error_prefix': '[-] Error: {msg}',
        'fatal_prefix': '[-] Fatal Error: {msg}',
        'log_saved': '[*] log saved to: {path}',
        'log_session': 'Session log: {path}',
        'db_loaded': '[+] database loaded ({n} entries)',

        'lang_current': 'Current language: English',
        'lang_switched': '[+] Language switched to English',
        'lang_menu_header': 'Select language',
        'lang_th': 'Thai',
        'lang_en': 'English',
        'lang_back': 'Back to main menu',
    },
}

class Lang:
    current = 'th'

    @classmethod
    def load(cls):
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    s = json.load(f)
                lang = s.get('language', 'th')
                if lang in ('th', 'en'):
                    cls.current = lang
        except Exception:
            pass

    @classmethod
    def save(cls):
        try:
            data = {}
            if SETTINGS_FILE.exists():
                try:
                    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data['language'] = cls.current
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def t(key, **kwargs):
    s = STRINGS.get(Lang.current, STRINGS['th']).get(key)
    if s is None:
        s = STRINGS['th'].get(key, key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return s
    return s

def UI_TEXT():
    return f"""
{Fore.GREEN}
                                                         
   ▄▄▄▄▄▄▄                                                 
  ███▀▀▀▀▀        ██                      ██               
  ███▄▄    ██ ██ ▀██▀▀ ████▄  ▀▀█▄ ▄████ ▀██▀▀ ▄███▄ ████▄ 
  ███       ███   ██   ██ ▀▀ ▄█▀██ ██     ██   ██ ██ ██ ▀▀ 
  ▀███████ ██ ██  ██   ██    ▀█▄██ ▀████  ██   ▀███▀ ██    
                                                                                                                                                             
{Style.RESET_ALL}
  by z3nTr4ry

  ---------------------------------
  1. {t('ui_title')}
  2. {t('ui_view_db')}
  3. {t('ui_change_lang')}
  4. {t('ui_exit')}
  --------------------------------
"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

class SkibidiLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"session_{ts}.log"
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        try:
            self.file = open(self.log_file, 'w', encoding='utf-8')
        except Exception:
            self.file = None
            self.original_stdout.write(
                f"[!] cannot open log file: {self.log_file}\n"
            )

    def write(self, message):
        try:
            self.original_stdout.write(message)
        except Exception:
            pass
        if self.file:
            try:
                clean = re.sub(r'\x1b\[[0-9;]*m', '', message)
                self.file.write(clean)
                self.file.flush()
            except Exception:
                pass

    def flush(self):
        try:
            self.original_stdout.flush()
        except Exception:
            pass
        if self.file:
            try:
                self.file.flush()
            except Exception:
                pass

    def isatty(self):
        return False

    def close(self):
        if self.file:
            try:
                self.file.close()
            except Exception:
                pass

class PomlikeheeyaDB:
    def __init__(self, db_file="configs/answers_db.json"):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        try:
            if self.db_file.exists():
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}  [!] cannot load database: {e}{Style.RESET_ALL}")
        return {}

    def _save(self):
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"{Fore.RED}  [!] cannot save database: {e}{Style.RESET_ALL}")
            return False

    def skibidikey(self, course, unit, exercise):
        raw = f"{course}||{unit}||{exercise}"
        return hashlib.sha256(raw.strip().encode('utf-8')).hexdigest()[:20]

    def get(self, course, unit, exercise):
        return self.data.get(self.skibidikey(course, unit, exercise))

    def set(self, course, unit, exercise, answers):
        key = self.skibidikey(course, unit, exercise)
        self.data[key] = {
            'course': course,
            'unit': unit,
            'exercise': exercise,
            'saved_at': datetime.datetime.now().isoformat(),
            'answers': answers,
        }
        return self._save()

    def list_all(self):
        return self.data

    def count(self):
        return len(self.data)

def sigma_normalizetext(text):
    if not text:
        return ""
    text = text.replace('â€™', "'").replace('â€œ', '"').replace('â€', '"')
    text = text.replace('â€“', '-').replace('â€˜', "'").replace('â', "'")
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00a0': ' ',
        '\u200b': '', '`': "'",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def rizz_decodeunicode(text):
    res = text
    try:
        res = codecs.decode(text, 'unicode_escape')
    except Exception:
        try:
            res = html_module.unescape(codecs.decode(text, 'unicode_escape'))
        except Exception:
            try:
                res = text.encode('latin-1', 'backslashreplace').decode('unicode_escape')
            except Exception:
                res = text
    return sigma_normalizetext(res)

def skibidi_detectns(root):
    tag = root.tag
    if '}' in tag:
        return tag.split('}')[0] + '}'
    return ''

def gyattfindallns(root, local_name):
    ns = skibidi_detectns(root)
    results = []
    if ns:
        results = root.findall(f'.//{ns}{local_name}')
    if not results:
        results = root.findall(f'.//{local_name}')
    return results

def ohiofindns(root, local_name, attr_id=None):
    ns = skibidi_detectns(root)
    if ns:
        if attr_id:
            for el in root.iter(f'{ns}{local_name}'):
                if el.get('id') == attr_id:
                    return el
        else:
            el = root.find(f'.//{ns}{local_name}')
            if el is not None:
                return el
    if attr_id:
        for el in root.iter(local_name):
            if el.get('id') == attr_id:
                return el
    else:
        el = root.find(f'.//{local_name}')
        if el is not None:
            return el
    return None

def sigma_isfinished(xml_content):
    return "You have finished the activity." in xml_content

def rizz_extractrubric(root):
    rubric = ohiofindns(root, 'div', 'rubric')
    if rubric is None:
        return ''
    for p in rubric.iter():
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag == 'p':
            text = ''.join(p.itertext()).strip()
            if text:
                return sigma_normalizetext(text)
    return sigma_normalizetext(''.join(rubric.itertext()).strip())

def gyatt_extractaudio(root):
    header_audio = ohiofindns(root, 'div', 'headerAudio')
    if header_audio is None:
        return ''
    data_author = header_audio.get('data-author', '') or ''
    try:
        audio_info = json.loads(html_module.unescape(data_author))
        return audio_info.get('mediaID', '')
    except Exception:
        m = re.search(r'"mediaID"\s*:\s*"([^"]+)"', data_author)
        return m.group(1) if m else ''

def skibidi_extractchoicetext(choice):
    text = ''.join(choice.itertext()).strip()
    if text:
        return sigma_normalizetext(text)
    for img in choice.iter():
        tag = img.tag.split('}')[-1] if '}' in img.tag else img.tag
        if tag == 'img':
            alt = img.get('alt', '') or ''
            if alt.strip():
                return sigma_normalizetext(alt)
    for media in choice.iter():
        tag = media.tag.split('}')[-1] if '}' in media.tag else media.tag
        if tag in ('audio', 'video'):
            for attr in ('alt', 'title', 'aria-label'):
                val = media.get(attr, '') or ''
                if val.strip():
                    return sigma_normalizetext(val)
    for attr in ('alt', 'title', 'aria-label'):
        val = choice.get(attr, '') or ''
        if val.strip():
            return sigma_normalizetext(val)
    return ''

def ohio_getresponsedecl(root, response_id):
    ns = skibidi_detectns(root)
    if ns:
        for rd in root.iter(f'{ns}responseDeclaration'):
            if (rd.get('identifier') or '').strip() == response_id:
                return rd
    for rd in root.iter('responseDeclaration'):
        if (rd.get('identifier') or '').strip() == response_id:
            return rd
    return None

def pom_getcorrectvalues(response_decl):
    if response_decl is None:
        return []
    values = []
    ns = skibidi_detectns(response_decl)
    if ns:
        cr = response_decl.find(f'.//{ns}correctResponse')
        if cr is not None:
            for v in cr.findall(f'.//{ns}value'):
                if v.text:
                    values.append(v.text.strip())
    if not values:
        cr = response_decl.find('.//correctResponse')
        if cr is not None:
            for v in cr.findall('.//value'):
                if v.text:
                    values.append(v.text.strip())
    return values

def rizz_parsemc(root, interactions, instruction, audio_filename):
    questions = []
    ns = skibidi_detectns(root)
    for i, interaction in enumerate(interactions, 1):
        answers = []
        correct_texts = []
        correct_ids = []

        choices = []
        if ns:
            choices = interaction.findall(f'.//{ns}simpleChoice')
        if not choices:
            choices = interaction.findall('.//simpleChoice')

        response_id = (interaction.get('responseIdentifier') or '').strip()
        response_decl = ohio_getresponsedecl(root, response_id)
        correct_ids = pom_getcorrectvalues(response_decl)

        if not correct_ids:
            for choice in choices:
                feedback = choice.get('answerfeedback', '') or ''
                if '#feedback:p1#' in feedback:
                    cid = (choice.get('identifier') or '').strip()
                    if cid:
                        correct_ids.append(cid)

        for choice in choices:
            choice_text = skibidi_extractchoicetext(choice)
            if not choice_text:
                continue
            answers.append(choice_text)
            choice_id = (choice.get('identifier') or '').strip()
            if choice_id in correct_ids:
                correct_texts.append(choice_text)

        if not correct_texts:
            for choice in choices:
                feedback = choice.get('answerfeedback', '') or ''
                if '#feedback:p1#' in feedback:
                    choice_text = skibidi_extractchoicetext(choice)
                    if choice_text:
                        correct_texts.append(choice_text)

        if answers:
            questions.append({
                'type': 'Multiple Choice',
                'question_number': i,
                'question': instruction or f'Question {i}',
                'instruction': instruction,
                'audio_filename': audio_filename,
                'answers': answers,
                'correct_answer': correct_texts[0] if correct_texts else '',
                'correct_answers': correct_texts,
                'is_multiple_answers': len(correct_texts) > 1,
                'correct_id': correct_ids[0] if correct_ids else '',
                'response_id': response_id,
            })
    return questions

def gyatt_getcontext(contentblock, interaction):
    if contentblock is None:
        return ''
    ns = skibidi_detectns(contentblock)
    paragraphs = []
    if ns:
        paragraphs = contentblock.findall(f'.//{ns}p')
    if not paragraphs:
        paragraphs = contentblock.findall('.//p')

    for p in paragraphs:
        found = False
        for sub in p.iter():
            if sub is interaction:
                found = True
                break
        if found:
            parts = []
            for child in p.iter():
                if child is interaction:
                    parts.append('[...]')
                if child.text:
                    parts.append(child.text)
                if child.tail:
                    parts.append(child.tail)
            return sigma_normalizetext(''.join(parts))[:300]
    return ''

def ohio_parsedropdown(root, interactions, instruction, audio_filename):
    questions = []
    ns = skibidi_detectns(root)
    contentblock = ohiofindns(root, 'div', 'contentblock')

    for i, interaction in enumerate(interactions, 1):
        response_id = (interaction.get('responseIdentifier') or '').strip()

        options = []
        choice_els = []
        if ns:
            choice_els = interaction.findall(f'.//{ns}inlineChoice')
        if not choice_els:
            choice_els = interaction.findall('.//inlineChoice')

        for choice in choice_els:
            text = skibidi_extractchoicetext(choice)
            cid = (choice.get('identifier') or '').strip()
            if text:
                options.append((cid, text))

        correct_ids = pom_getcorrectvalues(ohio_getresponsedecl(root, response_id))
        correct_id = correct_ids[0] if correct_ids else ''
        correct_answer = ''
        for cid, text in options:
            if cid == correct_id:
                correct_answer = text
                break

        if not correct_answer:
            for choice in choice_els:
                feedback = choice.get('answerfeedback', '') or ''
                if '#feedback:p1' in feedback:
                    correct_answer = skibidi_extractchoicetext(choice)
                    correct_id = (choice.get('identifier') or '').strip()
                    break

        context = gyatt_getcontext(contentblock, interaction)

        questions.append({
            'type': 'Dropdown',
            'question_number': i,
            'question': context or instruction or f'Dropdown {i}',
            'instruction': instruction,
            'audio_filename': audio_filename,
            'answers': [t for _, t in options],
            'correct_answer': sigma_normalizetext(correct_answer),
            'correct_id': correct_id,
            'response_id': response_id,
        })
    return questions

def pom_parsetextentry(root, interactions, instruction, audio_filename):
    questions = []
    contentblock = ohiofindns(root, 'div', 'contentblock')
    for i, interaction in enumerate(interactions, 1):
        response_id = (interaction.get('responseIdentifier') or '').strip()
        accepted = pom_getcorrectvalues(ohio_getresponsedecl(root, response_id))
        accepted = [sigma_normalizetext(a) for a in accepted]
        context = gyatt_getcontext(contentblock, interaction)
        questions.append({
            'type': 'Text Entry',
            'question_number': i,
            'question': context or instruction or f'Gap {i}',
            'instruction': instruction,
            'audio_filename': audio_filename,
            'answers': accepted,
            'correct_answer': accepted[0] if accepted else '',
            'response_id': response_id,
        })
    return questions

def sigma_parsegapmatch(root, interactions, instruction, audio_filename):
    questions = []
    ns = skibidi_detectns(root)
    contentblock = ohiofindns(root, 'div', 'contentblock')
    for i, interaction in enumerate(interactions, 1):
        gap_texts = {}
        gap_els = []
        if ns:
            gap_els = interaction.findall(f'.//{ns}gapText')
        if not gap_els:
            gap_els = interaction.findall('.//gapText')

        for gt in gap_els:
            gt_id = (gt.get('identifier') or '').strip()
            gt_text = skibidi_extractchoicetext(gt)
            if gt_id and gt_text:
                gap_texts[gt_id] = gt_text

        correct_pairs = []
        for rd in root.iter():
            tag = rd.tag.split('}')[-1] if '}' in rd.tag else rd.tag
            if tag != 'responseDeclaration':
                continue
            for child in rd.iter():
                ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if ctag == 'correctResponse':
                    for v in child.iter():
                        vtag = v.tag.split('}')[-1] if '}' in v.tag else v.tag
                        if vtag == 'value' and v.text:
                            correct_pairs.append(v.text.strip())

        id_to_text = {}
        for pair in correct_pairs:
            parts = pair.split()
            if len(parts) == 2:
                gt_id, gap_id = parts
                if gt_id in gap_texts:
                    id_to_text[gap_id] = gap_texts[gt_id]

        context_parts = []
        if contentblock is not None:
            for p in contentblock.iter():
                tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
                if tag != 'p':
                    continue
                text = ''.join(p.itertext()).strip()
                if not text or text.startswith('#') or text.startswith('Correct!') or text.startswith('Incorrect!'):
                    continue
                context_parts.append(sigma_normalizetext(text))

        questions.append({
            'type': 'Drag & Drop',
            'question_number': i,
            'question': ' | '.join(context_parts) if context_parts else instruction,
            'instruction': instruction,
            'audio_filename': audio_filename,
            'answers': list(gap_texts.values()),
            'correct_answer': '',
            'correct_pairs': id_to_text,
            'gap_texts': gap_texts,
        })
    return questions

def skibidi_extractanswers(xml_content):
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        print(f"{Fore.RED}  XML parse error:{Style.RESET_ALL} {e}")
        return []

    instruction = rizz_extractrubric(root)
    audio_filename = gyatt_extractaudio(root)
    questions = []

    mc = gyattfindallns(root, 'choiceInteraction')
    if mc:
        questions.extend(rizz_parsemc(root, mc, instruction, audio_filename))

    dd = gyattfindallns(root, 'inlineChoiceInteraction')
    if dd:
        questions.extend(ohio_parsedropdown(root, dd, instruction, audio_filename))

    te = gyattfindallns(root, 'textEntryInteraction')
    if te:
        questions.extend(pom_parsetextentry(root, te, instruction, audio_filename))

    gm = gyattfindallns(root, 'gapMatchInteraction')
    if gm:
        questions.extend(sigma_parsegapmatch(root, gm, instruction, audio_filename))

    return questions

def gyatt_printquestions(xml_file, questions):
    print(f"\n{Fore.YELLOW}  {Path(xml_file).name}{Style.RESET_ALL} ({len(questions)} {t('printq_questions')})")

    for q in questions:
        qtype = q.get('type', '?')
        qnum = q.get('question_number', '?')
        print(f"\n  {Fore.CYAN}[Q{qnum}] [{qtype}]{Style.RESET_ALL}")
        ctx = q.get('question') or q.get('instruction') or ''
        if ctx:
            print(f"      {t('printq_context')}: {ctx}")

        audio = q.get('audio_filename', '')
        if audio:
            print(f"      {t('printq_audio')}: {audio}")

        if qtype == 'Drag & Drop':
            pairs = q.get('correct_pairs', {})
            options = q.get('answers', [])
            if options:
                print(f"      {t('printq_options')}: {', '.join(options)}")
            if pairs:
                for gap_id, answer in sorted(pairs.items()):
                    print(f"      {Fore.GREEN}{gap_id} -> {answer}{Style.RESET_ALL}")
            continue

        options = q.get('answers', [])
        if options and qtype != 'Text Entry':
            print(f"      {t('printq_options')}: {', '.join(options)}")

        correct = q.get('correct_answer', '')
        correct_all = q.get('correct_answers', [])
        if correct_all and len(correct_all) > 1:
            print(f"      {Fore.GREEN}{t('printq_correct')}: {', '.join(correct_all)}{Style.RESET_ALL}")
        elif correct:
            print(f"      {Fore.GREEN}{t('printq_correct')}: {correct}{Style.RESET_ALL}")
        else:
            correct_id = q.get('correct_id', '')
            if correct_id:
                print(f"      {Fore.YELLOW}{t('printq_correct_id')}: {correct_id} - {t('printq_not_found')}{Style.RESET_ALL}")

def skibidi_processxmlfiles(data, db=None, course=None, unit=None, exercise=None):
    processed_count = 0
    skipped_count = 0
    all_results = {}

    for filename in sorted(data.keys()):
        if not filename.endswith('.xml'):
            continue
        xml_content = data[filename]

        if sigma_isfinished(str(xml_content)):
            print(f"{Fore.YELLOW}  {t('summary_skip_finished', name=filename)}{Style.RESET_ALL}")
            skipped_count += 1
            continue

        decoded_xml = rizz_decodeunicode(xml_content)
        questions = skibidi_extractanswers(decoded_xml)
        if questions:
            gyatt_printquestions(filename, questions)
            all_results[filename] = questions
            processed_count += 1
        else:
            print(f"{Fore.YELLOW}  {t('summary_skip_noans', name=filename)}{Style.RESET_ALL}")
            skipped_count += 1

    print(f"\n  {t('summary')}: {Fore.GREEN}{processed_count} {t('summary_processed')}{Style.RESET_ALL}, "
          f"{Fore.RED}{skipped_count} {t('summary_skipped')}{Style.RESET_ALL}")

    if all_results and db and course and unit and exercise:
        db.set(course, unit, exercise, all_results)
        print(f"  {Fore.GREEN}{t('summary_saved')}{Style.RESET_ALL}")

    return all_results

def pom_showdatabase(db):
    data = db.list_all()
    if not data:
        print(f"\n{Fore.YELLOW}  {t('db_empty')}{Style.RESET_ALL}")
        try:
            input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
        except Exception:
            pass
        return

    print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {t('db_header', n=len(data))}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

    entries = list(data.items())
    for i, (key, entry) in enumerate(entries, 1):
        course = entry.get('course', '?')
        unit = entry.get('unit', '?')
        exercise = entry.get('exercise', '?')
        saved_at = entry.get('saved_at', '')
        answers = entry.get('answers', {})
        xml_count = len(answers)

        print(f"\n  {Fore.WHITE}[{i}]{Style.RESET_ALL} {Fore.CYAN}{course} / {unit} / {exercise}{Style.RESET_ALL}")
        print(f"      {t('db_saved_at')}: {saved_at}")
        print(f"      {t('db_xml_count')}: {xml_count}")

    print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

    try:
        choice = input(f"\n  {Fore.CYAN}{t('db_select_view')}{Style.RESET_ALL}").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not choice:
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(entries):
            entry = entries[idx][1]
            clear_screen()
            print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {entry.get('course')} / {entry.get('unit')} / {entry.get('exercise')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {t('db_saved_at')}: {entry.get('saved_at', '')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

            for xml_name, questions in entry.get('answers', {}).items():
                gyatt_printquestions(xml_name, questions)
        else:
            print(f"{Fore.RED}  {t('db_invalid_number')}{Style.RESET_ALL}")
    except ValueError:
        print(f"{Fore.RED}  {t('db_enter_number')}{Style.RESET_ALL}")

    try:
        input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
    except Exception:
        pass

class CambridgeOneScraper:
    WINDOW_POSITION = "0,0"
    WINDOW_SIZE = "1680,1050"

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.configs_dir = Path("configs")
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        self.accounts_file = self.configs_dir / "cambridge_accounts.json"
        self.profiles_dir = Path("chrome_data")
        self.active_account = None
        self.playwright = None
        self.data_js_urls = []
        self.data_js_contents = {}
        self.last_data_js_url = None

    def _account_key(self, email):
        return hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()[:20]

    def _profile_dir(self, email):
        return self.profiles_dir / self._account_key(email)

    def load_accounts(self):
        try:
            if self.accounts_file.exists():
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            pass
        return []

    def save_account(self, email, password=None):
        email = email.strip()
        if not email:
            return False
        accounts = self.load_accounts()
        key = self._account_key(email)
        existing = next((a for a in accounts if a.get('key') == key), None)
        entry = {'key': key, 'email': email}
        if password:
            entry['password'] = password
        elif existing and existing.get('password'):
            entry['password'] = existing['password']
        accounts = [a for a in accounts if a.get('key') != key]
        accounts.insert(0, entry)
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def delete_account_password(self, email):
        accounts = self.load_accounts()
        key = self._account_key(email)
        for a in accounts:
            if a.get('key') == key:
                a.pop('password', None)
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    async def debug_wait(self, seconds=0.5):
        await asyncio.sleep(seconds)

    async def safe_wait_for_load(self, timeout=8000):
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout)
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
        except Exception:
            pass

    async def wait_for_loading_spinner(self, timeout=15):
        try:
            await self.page.wait_for_selector(
                '.loading, .spinner, [class*="spinner"], [class*="loading"]',
                state='detached', timeout=timeout * 1000
            )
        except Exception:
            pass

    def reset_data_js_tracking(self):
        self.data_js_urls.clear()
        self.data_js_contents.clear()

    async def init_browser(self, profile_dir=None):
        self.playwright = await async_playwright().start()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_dir = Path(profile_dir or (self.profiles_dir / "default"))
        profile_dir.mkdir(parents=True, exist_ok=True)

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir.resolve()),
            headless=False,
            viewport=None,
            args=[
                f'--window-position={self.WINDOW_POSITION}',
                f'--window-size={self.WINDOW_SIZE}',
            ]
        )
        self.browser = self.context.browser
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        self.page.on("response", self._on_response)

    def _on_response(self, response):
        try:
            url = response.url
            if 'data.js' in url:
                if url not in self.data_js_urls:
                    self.data_js_urls.append(url)
                    self.last_data_js_url = url
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(self._fetch_data_js_content(url, response))
                    except Exception:
                        pass
        except Exception:
            pass

    async def _fetch_data_js_content(self, url, response):
        try:
            body = await response.body()
            content = body.decode('utf-8', errors='replace')
            self.data_js_contents[url] = content
        except Exception:
            pass

    async def _wait_for_data_js(self, timeout=20):
        print(f"  {Fore.CYAN}{t('datajs_fetching')}{Style.RESET_ALL}")
        if self.data_js_urls:
            if all(u in self.data_js_contents for u in self.data_js_urls):
                return True

        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if self.data_js_urls and all(u in self.data_js_contents for u in self.data_js_urls):
                return True
            await asyncio.sleep(0.3)

        if self.data_js_urls:
            return True
        return False

    async def check_login_status(self):
        print(f"  {Fore.CYAN}{t('login_checking_session')}{Style.RESET_ALL}")
        try:
            await self.page.goto('https://www.cambridgeone.org/dashboard/learner/dashboard',
                                 wait_until='domcontentloaded', timeout=20000)
        except Exception:
            pass
        await self.debug_wait(2)
        try:
            await self.page.wait_for_load_state('networkidle', timeout=6000)
        except Exception:
            pass

        current_url = self.page.url.lower()
        print(f"  {Fore.CYAN}{t('login_current_url', url=current_url)}{Style.RESET_ALL}")

        if '/login' in current_url:
            return False
        try:
            login_form = await self.page.query_selector('input[type="password"], input[name="password"]')
            if login_form and await login_form.is_visible():
                return False
        except Exception:
            pass

        if 'dashboard' in current_url or '/learner/' in current_url:
            print(f"  {Fore.GREEN}{t('login_session_ok')}{Style.RESET_ALL}")
            return True
        return False

    async def login(self, email, password):
        print(f"\n  {Fore.CYAN}{t('login_logging_in')}{Style.RESET_ALL}")
        await self.page.goto('https://www.cambridgeone.org/login')
        await self.safe_wait_for_load()
        await self.debug_wait(1)

        email_selectors = [
            'input[type="text"][name="username"]', 'input[type="text"][name="loginID"]',
            'input[type="email"]', 'input.gigya-input-text', 'input[data-gigya-name="loginID"]',
            'input[id*="loginID"]', 'input[id*="login"]', 'input[placeholder*="username"]',
            'input[placeholder*="email"]',
        ]
        email_field = None
        for sel in email_selectors:
            try:
                el = await self.page.query_selector(sel)
                if el and await el.is_visible():
                    email_field = el
                    break
            except Exception:
                continue
        if not email_field:
            print(f"  {Fore.RED}[-] Could not find email field{Style.RESET_ALL}")
            return False

        await email_field.click()
        await email_field.fill('')
        await email_field.type(email, delay=20)
        await email_field.press('Tab')
        await self.debug_wait(0.5)

        pw_selectors = [
            'input[type="password"]', 'input.gigya-input-password',
            'input[id*="password"]', 'input[name="password"]',
        ]
        pw_field = None
        for sel in pw_selectors:
            try:
                el = await self.page.query_selector(sel)
                if el and await el.is_visible():
                    pw_field = el
                    break
            except Exception:
                continue
        if not pw_field:
            print(f"  {Fore.RED}[-] Could not find password field{Style.RESET_ALL}")
            return False

        await pw_field.click()
        await pw_field.fill('')
        await pw_field.type(password, delay=20)
        await pw_field.press('Enter')
        await self.debug_wait(3)

        try:
            await self.page.wait_for_load_state('networkidle', timeout=10000)
        except Exception:
            pass

        current_url = self.page.url
        if 'dashboard' in current_url or 'home' in current_url or 'classes' in current_url:
            print(f"  {Fore.GREEN}{t('login_success')}{Style.RESET_ALL}")
            return True
        try:
            page_text = await self.page.inner_text('body')
            if 'Active classes' in page_text or 'My classes' in page_text:
                print(f"  {Fore.GREEN}{t('login_success')}{Style.RESET_ALL}")
                return True
        except Exception:
            pass
        print(f"  {Fore.RED}{t('login_failed')}{Style.RESET_ALL}")
        return False

    async def get_courses_with_workbooks(self):
        print(f"\n  {Fore.CYAN}{t('courses_fetching')}{Style.RESET_ALL}")
        current_url = self.page.url
        if 'dashboard' not in current_url:
            await self.page.goto('https://www.cambridgeone.org/dashboard/learner/dashboard')
            await self.safe_wait_for_load()
            await self.debug_wait(1)

        try:
            await self.page.wait_for_selector('.umbrella-tile', timeout=12000)
        except Exception:
            pass

        courses_data = await self.page.evaluate('''
            () => {
                const courses = [];
                const tiles = document.querySelectorAll('.umbrella-tile');
                tiles.forEach(tile => {
                    const link = tile.querySelector('a.tile-section-link');
                    if (!link) return;
                    const ariaLabel = link.getAttribute('aria-label') || '';
                    if (!ariaLabel.includes('Digital Workbook')) return;
                    const nameElem = tile.querySelector('.my-progress');
                    const workbookName = nameElem ? nameElem.innerText.trim() : '';
                    let courseName = '';
                    const match = ariaLabel.match(/for\\s+([^\\-]+?)(?:\\s*[–-]|$)/);
                    if (match) courseName = match[1].trim();
                    else {
                        const allText = tile.innerText || '';
                        const lines = allText.split('\\n').filter(line => line.trim());
                        for (const line of lines) {
                            if (line.includes('Four Corners') || line.includes('Cambridge')) {
                                courseName = line.trim();
                                break;
                            }
                        }
                    }
                    if (!courseName) {
                        const parts = ariaLabel.split(' for ');
                        if (parts.length > 1) courseName = parts[1].trim();
                    }
                    if (workbookName && courseName) courses.push({ courseName, workbookName });
                });
                return courses;
            }
        ''')
        print(f"  {Fore.GREEN}{t('courses_found', n=len(courses_data))}{Style.RESET_ALL}")
        return courses_data

    async def click_workbook(self, course_name):
        print(f"  {Fore.CYAN}{t('courses_opening', name=course_name)}{Style.RESET_ALL}")
        result = await self.page.evaluate('''
            (courseName) => {
                const tiles = document.querySelectorAll('.umbrella-tile');
                for (const tile of tiles) {
                    const link = tile.querySelector('a.tile-section-link');
                    if (!link) continue;
                    const ariaLabel = link.getAttribute('aria-label') || '';
                    if (!ariaLabel.includes('Digital Workbook')) continue;
                    if (ariaLabel.includes(courseName)) { link.click(); return true; }
                    const text = tile.innerText || '';
                    if (text.includes(courseName)) { link.click(); return true; }
                }
                return false;
            }
        ''', course_name)
        if result:
            print(f"  {Fore.GREEN}{t('courses_opened')}{Style.RESET_ALL}")
            await self.safe_wait_for_load()
            await self.wait_for_loading_spinner(timeout=10)
            await self.debug_wait(2)
            return True
        print(f"  {Fore.RED}{t('courses_open_failed')}{Style.RESET_ALL}")
        return False

    async def get_all_units(self):
        print(f"\n  {Fore.CYAN}{t('units_loading')}{Style.RESET_ALL}")
        for _ in range(4):
            try:
                await self.wait_for_loading_spinner(timeout=8)
                await self.page.wait_for_selector('.card, .unit-detail, [class*="unit"]', timeout=5000)
                break
            except Exception:
                await asyncio.sleep(2)

        units_data = []
        for _ in range(3):
            units_data = await self.page.evaluate('''
                () => {
                    const units = [];
                    const cards = document.querySelectorAll('.card');
                    cards.forEach((card) => {
                        let unitName = '';
                        const h5 = card.querySelector('.unit-info .h5');
                        if (h5) unitName = h5.innerText.trim();
                        if (!unitName) {
                            const h5_2 = card.querySelector('.unit-detail .h5');
                            if (h5_2) unitName = h5_2.innerText.trim();
                        }
                        if (!unitName) {
                            const lines = (card.innerText || '').split('\\n').filter(l => l.trim());
                            for (const line of lines) {
                                if (line.match(/^\\d+\\s+\\w+/)) { unitName = line.trim(); break; }
                            }
                        }
                        if (unitName) units.push({ name: unitName });
                    });
                    if (units.length === 0) {
                        document.querySelectorAll('.unit-detail, [class*="unit-title"]').forEach(detail => {
                            const h5 = detail.querySelector('.h5, h5, .title');
                            if (h5) {
                                const name = h5.innerText.trim();
                                if (name) units.push({ name });
                            }
                        });
                    }
                    return units;
                }
            ''')
            if units_data:
                break
            await asyncio.sleep(2)
        print(f"  {Fore.GREEN}{t('units_found', n=len(units_data))}{Style.RESET_ALL}")
        return units_data

    async def click_unit(self, unit_name):
        print(f"  {Fore.CYAN}{t('units_opening', name=unit_name)}{Style.RESET_ALL}")
        result = await self.page.evaluate('''
            (unitName) => {
                let targetCard = null;
                for (const card of document.querySelectorAll('.card, [class*="unit"]')) {
                    if ((card.innerText || '').includes(unitName)) { targetCard = card; break; }
                }
                if (!targetCard) return false;
                const collapse = targetCard.querySelector('.collapse');
                if (collapse && collapse.classList.contains('show')) return true;
                const clickable = targetCard.querySelector('.unit-detail, .card-header, a, button, h5');
                if (clickable) { clickable.click(); return true; }
                return false;
            }
        ''', unit_name)
        if result:
            print(f"  {Fore.GREEN}{t('units_opened')}{Style.RESET_ALL}")
            await self.safe_wait_for_load()
            await self.debug_wait(1.5)
            return True
        print(f"  {Fore.RED}{t('units_open_failed')}{Style.RESET_ALL}")
        return False

    async def get_exercises_in_unit(self, unit_name):
        print(f"\n  {Fore.CYAN}{t('units_exercises_fetching', name=unit_name)}{Style.RESET_ALL}")
        try:
            await self.page.wait_for_selector(
                '.activity-info, [class*="activity"], [class*="lesson"], .card', timeout=8000
            )
        except Exception:
            pass

        exercises_data = await self.page.evaluate('''
            (unitName) => {
                const result = { unit_name: unitName, lessons: [] };
                let unitCard = null;
                const allCards = document.querySelectorAll('.card, [class*="unit"], [class*="product"]');
                for (const card of allCards) {
                    const cardText = (card.innerText || '').toLowerCase();
                    if (cardText.includes(unitName.toLowerCase())) { unitCard = card; break; }
                }
                if (!unitCard) unitCard = document.body;

                let currentLesson = null;
                const invalidNames = ['completed', 'in progress', 'not started', 'in-progress', 'not-started'];

                const checkStatus = (el) => {
                    const html = el.innerHTML || '';
                    if (html.includes('nemo-tick') || html.includes('green-tick') || html.includes('completed') || html.includes('svg')) {
                        return 'completed';
                    }
                    if (html.includes('inprogress') || html.includes('in-progress') || html.includes('progress')) {
                        return 'in-progress';
                    }
                    return 'pending';
                };

                const allNodes = Array.from(unitCard.querySelectorAll('*'));
                for (const node of allNodes) {
                    const text = (node.innerText || '').trim();
                    if (!text) continue;

                    const isLessonHeader = /^Lesson\\s+[A-Z]/i.test(text) && text.length < 20;
                    if (isLessonHeader) {
                        let existingLesson = result.lessons.find(l => l.name.toLowerCase() === text.toLowerCase());
                        if (!existingLesson) {
                            currentLesson = { name: text, exercises: [] };
                            result.lessons.push(currentLesson);
                        } else {
                            currentLesson = existingLesson;
                        }
                        continue;
                    }

                    const isActivity = node.matches('.activity-info, [class*="activity"], a[class*="activity"], button[class*="activity"]') ||
                        (node.tagName === 'A' && node.querySelector('.star, [class*="star"], i, img')) ||
                        (node.classList && Array.from(node.classList).some(c => c.includes('activity') || c.includes('item')));

                    if (isActivity) {
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        const exName = lines[0];
                        if (!exName || /^Lesson\\s+[A-Z]/i.test(exName) || exName.length < 2 ||
                            invalidNames.includes(exName.toLowerCase()) ||
                            exName.toLowerCase() === unitName.toLowerCase() ||
                            /^\\d+\\s+/.test(exName)) {
                            continue;
                        }
                        if (!currentLesson) {
                            currentLesson = { name: 'Lesson A', exercises: [] };
                            result.lessons.push(currentLesson);
                        }
                        if (!currentLesson.exercises.some(e => e.name.toLowerCase() === exName.toLowerCase())) {
                            currentLesson.exercises.push({ name: exName, status: checkStatus(node) });
                        }
                    }
                }

                if (result.lessons.length === 0 || result.lessons.every(l => l.exercises.length === 0)) {
                    result.lessons = [];
                    const fallbackLesson = { name: 'Exercises', exercises: [] };
                    const clickables = unitCard.querySelectorAll('a, button, [role="button"]');
                    clickables.forEach(item => {
                        const rawText = (item.innerText || '').trim();
                        if (!rawText) return;
                        const lines = rawText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        const name = lines[0];
                        if (name && name.length > 2 &&
                            !name.toLowerCase().includes('lesson') &&
                            !name.toLowerCase().includes('unit') &&
                            !invalidNames.includes(name.toLowerCase()) &&
                            name.toLowerCase() !== unitName.toLowerCase() &&
                            !/^\\d+\\s+/.test(name)) {
                            if (!fallbackLesson.exercises.some(e => e.name === name)) {
                                fallbackLesson.exercises.push({ name: name, status: checkStatus(item) });
                            }
                        }
                    });
                    if (fallbackLesson.exercises.length > 0) {
                        result.lessons.push(fallbackLesson);
                    }
                }
                return result;
            }
        ''', unit_name)

        print(f"  {Fore.GREEN}{t('units_exercises_found', n=len(exercises_data['lessons']))}{Style.RESET_ALL}")
        return exercises_data

    async def click_exercise(self, exercise_name):
        print(f"  {Fore.CYAN}{t('exercises_opening', name=exercise_name)}{Style.RESET_ALL}")

        current_url = self.page.url
        if '/view/' in current_url or '/activity/' in current_url or 'item' in current_url:
            current_title = await self.page.evaluate('''
                () => {
                    const el = document.querySelector('.activity-title, h1, header span, .product-title, .title');
                    return el ? el.innerText.trim().toLowerCase() : '';
                }
            ''')
            if current_title and exercise_name.lower() in current_title:
                print(f"  {Fore.GREEN}{t('exercises_already_open')}{Style.RESET_ALL}")
                await self.debug_wait(3)
                return True
            print(f"  {Fore.CYAN}{t('exercises_back_workbook')}{Style.RESET_ALL}")
            await self.page.go_back()
            await self.safe_wait_for_load()
            await self.debug_wait(1)

        result = await self.page.evaluate('''
            (exName) => {
                const cleanName = exName.trim().toLowerCase();
                const activities = document.querySelectorAll('.activity-info, [class*="activity"]');
                for (const act of activities) {
                    const textContent = (act.innerText || act.textContent || '').trim().toLowerCase();
                    if (textContent.includes(cleanName)) {
                        const target = act.querySelector('a, button, [role="button"], p, span') || act;
                        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        target.click();
                        return true;
                    }
                }
                const allClickables = document.querySelectorAll('a, button, [role="button"]');
                for (const elem of allClickables) {
                    const txt = (elem.innerText || elem.textContent || '').trim().toLowerCase();
                    if (elem.closest('.card-header') || elem.classList.contains('unit-detail')) continue;
                    if (txt === cleanName || (txt.includes(cleanName) && txt.length < cleanName.length + 20)) {
                        elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        elem.click();
                        return true;
                    }
                }
                return false;
            }
        ''', exercise_name)

        if result:
            print(f"  {Fore.GREEN}{t('exercises_opened')}{Style.RESET_ALL}")
            await self.safe_wait_for_load()
            await self.wait_for_loading_spinner(timeout=10)
            await self.debug_wait(3)
            return True
        print(f"  {Fore.RED}{t('exercises_open_failed')}{Style.RESET_ALL}")
        return False

    def _parse_js_object(self, content):
        m = re.search(r'ajaxData\s*=\s*', content)
        if not m:
            return None

        start_idx = m.end()
        decoder = json.JSONDecoder()
        try:
            data, end_idx = decoder.raw_decode(content, start_idx)
            return data
        except json.JSONDecodeError:
            last_brace = content.rfind('}')
            if last_brace > start_idx:
                snippet = content[start_idx:last_brace + 1]
                try:
                    data = json.loads(snippet)
                    return data
                except Exception:
                    return None
            return None
        except Exception:
            return None

    async def get_answers_from_data_js(self):
        if not self.data_js_urls:
            return None

        urls = list(dict.fromkeys(reversed(self.data_js_urls)))

        for url in urls:
            content = None
            if url in self.data_js_contents:
                content = self.data_js_contents[url]
            else:
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    content = response.text
                except Exception:
                    continue

            if not content:
                continue

            data = self._parse_js_object(content)
            if not data:
                continue

            return data

        return None

    async def close(self):
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass

def display_courses(courses):
    print(f"\n  {'=' * 70}")
    print(f"  {Fore.CYAN}{t('courses_header')}{Style.RESET_ALL}")
    print(f"  {'=' * 70}\n")
    if not courses:
        print(f"  {Fore.YELLOW}{t('courses_not_found')}{Style.RESET_ALL}")
        return
    for i, course in enumerate(courses, 1):
        print(f"  {Fore.WHITE}[{i}]{Style.RESET_ALL} {Fore.CYAN}{course['courseName']}{Style.RESET_ALL}")
        print(f"      {Fore.GREEN}{course['workbookName']}{Style.RESET_ALL}\n")

def display_units(units):
    print(f"\n  {'=' * 70}")
    print(f"  {Fore.CYAN}{t('units_header')}{Style.RESET_ALL}")
    print(f"  {'=' * 70}\n")
    if not units:
        print(f"  {Fore.YELLOW}{t('units_not_found')}{Style.RESET_ALL}")
        return
    for i, unit in enumerate(units, 1):
        print(f"  {Fore.WHITE}[{i}]{Style.RESET_ALL} {Fore.CYAN}{unit['name']}{Style.RESET_ALL}")

def display_exercises(data):
    print(f"\n  {'=' * 70}")
    print(f"  {Fore.CYAN}{data['unit_name']}{Style.RESET_ALL}")
    print(f"  {'=' * 70}\n")
    if not data.get('lessons'):
        print(f"  {Fore.YELLOW}{t('exercises_none')}{Style.RESET_ALL}")
        return
    exercise_counter = 1
    for lesson in data['lessons']:
        print(f"  {Fore.MAGENTA}+-- {lesson['name']}{Style.RESET_ALL}")
        for ex in lesson['exercises']:
            if ex['status'] == 'completed':
                print(f"  {Fore.GREEN}|   [{exercise_counter}] [OK] {ex['name']}{Style.RESET_ALL}")
            elif ex['status'] == 'in-progress':
                print(f"  {Fore.YELLOW}|   [{exercise_counter}] [..] {ex['name']}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.WHITE}|   [{exercise_counter}] [  ] {ex['name']}{Style.RESET_ALL}")
            exercise_counter += 1
        print(f"  {Fore.MAGENTA}+--{Style.RESET_ALL}\n")

def choose_account(scraper):
    while True:
        accounts = scraper.load_accounts()
        clear_screen()
        print(f"\n  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{t('accounts_header')}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")

        if accounts:
            for i, account in enumerate(accounts, 1):
                has_pwd = f" {t('accounts_saved_pwd')}" if account.get('password') else ''
                print(f"  [{i}] {account.get('email', '')}{has_pwd}")
        else:
            print(f"  {Fore.YELLOW}{t('accounts_empty')}{Style.RESET_ALL}")

        print(f"\n  {Fore.CYAN}[A] {t('accounts_add')}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}[0] {t('accounts_cancel')}{Style.RESET_ALL}")

        try:
            choice = input(f"\n  {Fore.CYAN}[>] {t('accounts_select')}: {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            return None, None, False

        if choice == '0' or not choice:
            return None, None, False

        if choice.lower() == 'a':
            try:
                new_email = input(f"\n  {Fore.CYAN}[>] {t('accounts_new_email')}: {Style.RESET_ALL}").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if not new_email or '@' not in new_email:
                print(f"  {Fore.RED}{t('accounts_invalid_email')}{Style.RESET_ALL}")
                time.sleep(1)
                continue
            scraper.save_account(new_email, None)
            print(f"  {Fore.GREEN}{t('accounts_added', email=new_email)}{Style.RESET_ALL}")
            time.sleep(1)
            return new_email, None, True

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(accounts):
                acc = accounts[idx]
                return acc.get('email', ''), acc.get('password'), True
        except ValueError:
            pass

        if '@' in choice:
            return choice, None, True

        print(f"  {Fore.RED}{t('accounts_invalid_choice')}{Style.RESET_ALL}")
        time.sleep(1)

async def show_answers_flow(scraper, db):
    email, saved_password, should_continue = choose_account(scraper)
    if not should_continue or not email:
        print(f"\n  {Fore.YELLOW}{t('login_cancel')}{Style.RESET_ALL}")
        return

    try:
        profile_dir = scraper._profile_dir(email)
        print(f"  {Fore.CYAN}{t('login_opening_profile', path=profile_dir)}{Style.RESET_ALL}")
        await scraper.init_browser(profile_dir)
        print(f"  {Fore.GREEN}{t('login_browser_opened')}{Style.RESET_ALL}")

        login_success = await scraper.check_login_status()

        if login_success:
            print(f"  {Fore.GREEN}{t('login_session_ok')}{Style.RESET_ALL}")
        else:
            password = None
            if saved_password:
                print(f"  {Fore.GREEN}{t('login_use_saved_pwd')}{Style.RESET_ALL}")
                password = saved_password
            else:
                password = masked_input(f"  {Fore.CYAN}{t('login_enter_pwd', email=email)}{Style.RESET_ALL}").strip()
                if password:
                    try:
                        save_choice = input(f"  {Fore.CYAN}{t('login_save_pwd_q')}{Style.RESET_ALL}").strip()
                    except Exception:
                        save_choice = '1'
                    if save_choice == '1':
                        scraper.save_account(email, password)
                        print(f"  {Fore.GREEN}{t('login_pwd_saved')}{Style.RESET_ALL}")

            if not password:
                print(f"  {Fore.RED}{t('login_no_pwd')}{Style.RESET_ALL}")
                await scraper.close()
                return

            login_success = await scraper.login(email, password)
            if login_success:
                scraper.save_account(email, password)

        if not login_success:
            print(f"  {Fore.RED}{t('login_failed')}{Style.RESET_ALL}")
            await scraper.close()
            return

        await scraper.debug_wait(1)
        clear_screen()

        while True:
            courses = await scraper.get_courses_with_workbooks()
            display_courses(courses)
            if not courses:
                print(f"  {Fore.YELLOW}{t('courses_not_found')}{Style.RESET_ALL}")
                try:
                    input(f"\n  {Fore.CYAN}{t('input_enter_close')}{Style.RESET_ALL}")
                except Exception:
                    pass
                return

            print(f"  {Fore.CYAN}{t('courses_select')}{Style.RESET_ALL}")
            for i, course in enumerate(courses, 1):
                print(f"  {i}. {course['courseName']}")
            print(f"  0. {t('courses_refresh')}")
            print(f"  X. {t('courses_exit')}")

            try:
                choice = input(f"\n  {Fore.CYAN}[>] {t('courses_select')}{Style.RESET_ALL}").strip()
            except (EOFError, KeyboardInterrupt):
                return

            if choice.lower() == 'x':
                print(f"\n  {Fore.CYAN}{t('exit_program')}{Style.RESET_ALL}")
                await scraper.close()
                sys.exit(0)

            if choice == '0' or not choice:
                clear_screen()
                continue

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(courses):
                    selected_course = courses[idx]
                    clear_screen()
                    if await scraper.click_workbook(selected_course['courseName']):
                        await run_unit_selection(scraper, db, selected_course)
                        clear_screen()
                else:
                    print(f"  {Fore.RED}{t('accounts_invalid_choice')}{Style.RESET_ALL}")
                    await scraper.debug_wait(1)
                    clear_screen()
            except ValueError:
                print(f"  {Fore.RED}{t('input_number')}{Style.RESET_ALL}")
                await scraper.debug_wait(1)
                clear_screen()

    except SystemExit:
        raise
    except Exception as e:
        print(f"\n  {Fore.RED}{t('error_prefix', msg=e)}{Style.RESET_ALL}")
        traceback.print_exc()
    finally:
        try:
            await scraper.close()
        except Exception:
            pass

async def run_unit_selection(scraper, db, selected_course):
    while True:
        units = await scraper.get_all_units()
        if not units:
            print(f"  {Fore.YELLOW}{t('units_not_found')}{Style.RESET_ALL}")
            try:
                input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
            except Exception:
                pass
            return

        clear_screen()
        display_units(units)
        print(f"\n  {Fore.CYAN}[0] {t('units_back')}{Style.RESET_ALL}")

        try:
            unit_choice = input(f"\n  {Fore.CYAN}{t('units_select')}{Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if unit_choice == '0' or not unit_choice:
            return

        try:
            unit_idx = int(unit_choice) - 1
            if 0 <= unit_idx < len(units):
                selected_unit = units[unit_idx]
                clear_screen()
                await scraper.click_unit(selected_unit['name'])
                exercises_data = await scraper.get_exercises_in_unit(selected_unit['name'])
                await run_exercise_selection(scraper, db, selected_course, selected_unit, exercises_data)
            else:
                print(f"  {Fore.RED}{t('accounts_invalid_choice')}{Style.RESET_ALL}")
                await scraper.debug_wait(1)
        except ValueError:
            print(f"  {Fore.RED}{t('input_number')}{Style.RESET_ALL}")
            await scraper.debug_wait(1)

async def run_exercise_selection(scraper, db, selected_course, selected_unit, exercises_data):
    while True:
        clear_screen()
        display_exercises(exercises_data)

        all_exercises = []
        for lesson in exercises_data.get('lessons', []):
            for ex in lesson['exercises']:
                all_exercises.append({'lesson': lesson['name'], 'name': ex['name'], 'status': ex['status']})

        if not all_exercises:
            print(f"  {Fore.YELLOW}{t('exercises_none')}{Style.RESET_ALL}")
            try:
                input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
            except Exception:
                pass
            return

        print(f"\n  {Fore.CYAN}[0] {t('exercises_back')}{Style.RESET_ALL}")

        try:
            ex_choice = input(f"\n  {Fore.CYAN}{t('exercises_select')}{Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if ex_choice == '0' or not ex_choice:
            return

        try:
            ex_idx = int(ex_choice) - 1
            if not (0 <= ex_idx < len(all_exercises)):
                print(f"  {Fore.RED}{t('accounts_invalid_choice')}{Style.RESET_ALL}")
                await scraper.debug_wait(1)
                continue

            selected_ex = all_exercises[ex_idx]
            exercise_name = selected_ex['name']
            print(f"\n  {Fore.CYAN}{t('exercises_selected', name=exercise_name)}{Style.RESET_ALL}")

            cached = db.get(selected_course['courseName'], selected_unit['name'], exercise_name)
            if cached:
                print(f"  {Fore.GREEN}{t('cached_found', time=cached.get('saved_at', ''))}{Style.RESET_ALL}")
                try:
                    use_cache = input(f"  {Fore.CYAN}{t('cached_use_q')}{Style.RESET_ALL}").strip()
                except Exception:
                    use_cache = '1'

                if use_cache == '1':
                    clear_screen()
                    print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}  {t('cached_header', name=exercise_name)}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
                    for xml_name, questions in cached.get('answers', {}).items():
                        gyatt_printquestions(xml_name, questions)
                    try:
                        input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
                    except Exception:
                        pass
                    continue

            scraper.reset_data_js_tracking()

            if not await scraper.click_exercise(exercise_name):
                print(f"  {Fore.RED}{t('exercises_open_failed')}{Style.RESET_ALL}")
                try:
                    input(f"\n  {Fore.CYAN}{t('input_enter')}{Style.RESET_ALL}")
                except Exception:
                    pass
                continue

            has_data = await scraper._wait_for_data_js(timeout=25)
            if not has_data:
                print(f"  {Fore.RED}{t('datajs_not_found')}{Style.RESET_ALL}")
                try:
                    input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
                except Exception:
                    pass
                try:
                    await scraper.page.go_back()
                    await scraper.safe_wait_for_load()
                except Exception:
                    pass
                continue

            data = await scraper.get_answers_from_data_js()
            if not data:
                print(f"  {Fore.RED}{t('datajs_parse_failed')}{Style.RESET_ALL}")
                try:
                    input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
                except Exception:
                    pass
                continue

            clear_screen()
            print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {t('answers_header', name=exercise_name)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

            skibidi_processxmlfiles(
                data,
                db=db,
                course=selected_course['courseName'],
                unit=selected_unit['name'],
                exercise=exercise_name
            )

            try:
                input(f"\n  {Fore.CYAN}{t('input_enter_back')}{Style.RESET_ALL}")
            except Exception:
                pass

        except ValueError:
            print(f"  {Fore.RED}{t('input_number')}{Style.RESET_ALL}")
            await scraper.debug_wait(1)

def change_language_menu():
    while True:
        clear_screen()
        print(f"\n  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{t('lang_menu_header')}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")
        print(f"  {Fore.WHITE}[1]{Style.RESET_ALL} {Fore.CYAN}{t('lang_th')}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}[2]{Style.RESET_ALL} {Fore.CYAN}{t('lang_en')}{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}[0]{Style.RESET_ALL} {Fore.CYAN}{t('lang_back')}{Style.RESET_ALL}")
        print(f"\n  {Fore.GREEN}{t('lang_current')}{Style.RESET_ALL}")

        try:
            c = input(f"\n  {Fore.CYAN}[>] {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if c == '1':
            Lang.current = 'th'
            Lang.save()
            print(f"  {Fore.GREEN}{t('lang_switched')}{Style.RESET_ALL}")
            time.sleep(1.2)
            return
        if c == '2':
            Lang.current = 'en'
            Lang.save()
            print(f"  {Fore.GREEN}{t('lang_switched')}{Style.RESET_ALL}")
            time.sleep(1.2)
            return
        if c == '0':
            return

async def main_async(db):
    scraper = CambridgeOneScraper()
    await show_answers_flow(scraper, db)

def skibidi_main():
    logger = SkibidiLogger(log_dir="logs")
    sys.stdout = logger
    sys.stderr = logger

    try:
        Lang.load()

        print(f"\n  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{t('log_session', path=logger.log_file)}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

        db = PomlikeheeyaDB("configs/answers_db.json")
        print(f"  {Fore.GREEN}{t('db_loaded', n=db.count())}{Style.RESET_ALL}")

        while True:
            clear_screen()
            print(UI_TEXT())

            try:
                choice = input(f"\n  {Fore.CYAN}{t('input_choice')}{Style.RESET_ALL}").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == '4':
                print(f"\n  {Fore.CYAN}{t('goodbye')}{Style.RESET_ALL}")
                break

            elif choice == '3':
                change_language_menu()

            elif choice == '2':
                pom_showdatabase(db)

            elif choice == '1':
                try:
                    asyncio.run(main_async(db))
                except SystemExit:
                    print(f"\n  {Fore.CYAN}{t('goodbye')}{Style.RESET_ALL}")
                    break
                except Exception as e:
                    print(f"\n  {Fore.RED}{t('error_prefix', msg=e)}{Style.RESET_ALL}")
                    traceback.print_exc()

            else:
                print(f"{Fore.RED}  {t('input_invalid')}{Style.RESET_ALL}")
                time.sleep(1)

    except Exception as e:
        print(f"\n{Fore.RED}  {t('fatal_prefix', msg=e)}{Style.RESET_ALL}")
        traceback.print_exc()

    finally:
        print(f"\n  {Fore.CYAN}{t('log_saved', path=logger.log_file)}{Style.RESET_ALL}")
        logger.close()
        sys.stdout = logger.original_stdout
        sys.stderr = logger.original_stderr

if __name__ == "__main__":
    skibidi_main()
