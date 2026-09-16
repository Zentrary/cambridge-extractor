import requests
import json
import re
import os
import sys
import time
import codecs
import datetime
import html as html_module
import webbrowser
import hashlib
import xml.etree.ElementTree as ET

from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

UI = f"""
{Fore.GREEN}
                                                         
   ▄▄▄▄▄▄▄                                                 
  ███▀▀▀▀▀        ██                      ██               
  ███▄▄    ██ ██ ▀██▀▀ ████▄  ▀▀█▄ ▄████ ▀██▀▀ ▄███▄ ████▄ 
  ███       ███   ██   ██ ▀▀ ▄█▀██ ██     ██   ██ ██ ██ ▀▀ 
  ▀███████ ██ ██  ██   ██    ▀█▄██ ▀████  ██   ▀███▀ ██    
                                                                                                                                                             
{Style.RESET_ALL}
  by z3nTr4ry

  ---------------------------------
  1. Continue
  2. GitHub
  3. View Database
  4. Exit
  --------------------------------
"""

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

    def skibidy(self, message):
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

    def gyattflush(self):
        try:
            self.original_stdout.flush()
        except Exception:
            pass
        if self.file:
            try:
                self.file.flush()
            except Exception:
                pass

    def ohio_close(self):
        if self.file:
            try:
                self.file.close()
            except Exception:
                pass

class PomlikeheeyaDB:
    def __init__(self, db_file="answers_db.json"):
        self.db_file = Path(db_file)
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

    def skibidikey(self, url):
        return hashlib.sha256(url.strip().encode('utf-8')).hexdigest()[:16]

    def get(self, url):
        key = self.skibidikey(url)
        return self.data.get(key)

    def set(self, url, answers, xml_files=None):
        key = self.skibidikey(url)
        self.data[key] = {
            'url': url,
            'saved_at': datetime.datetime.now().isoformat(),
            'answers': answers,
            'xml_files': xml_files or [],
        }
        return self._save()

    def list_all(self):
        return self.data

    def delete(self, url):
        key = self.skibidikey(url)
        if key in self.data:
            del self.data[key]
            return self._save()
        return False

    def count(self):
        return len(self.data)


def pomlikeheeyaimak(url):
    print(f"{Fore.CYAN}  [*] downloading: {url[:80]}...{Style.RESET_ALL}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if "ajaxData" not in response.text:
            raise ValueError("Not a valid data.js file")
        print(f"{Fore.GREEN}  [+] download success ({len(response.text)} bytes){Style.RESET_ALL}")
        return response.text
    except Exception as e:
        print(f"{Fore.RED}  [-] download error: {e}{Style.RESET_ALL}")
        return None

def gyattparsejs(content):
    print(f"{Fore.CYAN}  [*] parsing ajaxData...{Style.RESET_ALL}")
    m = re.search(r'ajaxData\s*=\s*', content)
    if not m:
        print(f"{Fore.RED}  [-] 'ajaxData =' not found{Style.RESET_ALL}")
        return None

    start_idx = m.end()
    decoder = json.JSONDecoder()
    try:
        data, end_idx = decoder.raw_decode(content, start_idx)
        print(f"{Fore.GREEN}  [+] parse success - found {len(data)} entries{Style.RESET_ALL}")
        return data
    except json.JSONDecodeError:
        last_brace = content.rfind('}')
        if last_brace > start_idx:
            snippet = content[start_idx:last_brace + 1]
            try:
                data = json.loads(snippet)
                print(f"{Fore.GREEN}  [+] parse success (fallback) - found {len(data)} entries{Style.RESET_ALL}")
                return data
            except Exception as e:
                print(f"{Fore.RED}  [-] error parsing JS object: {e}{Style.RESET_ALL}")
                return None
        return None

def ohio_parsejs(content):
    return gyattparsejs(content)

def sigma_normalizetext(text):
    if not text:
        return ""

    text = text.replace('â€™', "'").replace('â€œ', '"').replace('â€', '"')
    text = text.replace('â€“', '-').replace('â€˜', "'").replace('â', "'")
    replacements = {
        '\u2019': "'",
        '\u2018': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2013': '-',
        '\u2014': '-',
        '\u2026': '...',
        '\u00a0': ' ',
        '\u200b': '',
        '`': "'",
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
    res = sigma_normalizetext(res)
    return res

def skibidi_detectns(root):
    tag = root.tag
    if '}' in tag:
        ns = tag.split('}')[0] + '}'
        return ns
    return ''

def gyattfindallns(root, local_name):
    results = []
    ns = skibidi_detectns(root)
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

def pomformatxml(xml_content):
    try:
        root = ET.fromstring(xml_content)
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding='unicode')
    except Exception:
        return xml_content

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
        data_author_clean = html_module.unescape(data_author)
        audio_info = json.loads(data_author_clean)
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

def sigma_getfeedbackanswers(root, interaction):
    answers = []
    ns = skibidi_detectns(root)
    choices = []
    if ns:
        choices = interaction.findall(f'.//{ns}simpleChoice')
        if not choices:
            choices = interaction.findall(f'.//{ns}inlineChoice')
    if not choices:
        choices = interaction.findall('.//simpleChoice')
    if not choices:
        choices = interaction.findall('.//inlineChoice')

    for choice in choices:
        feedback = choice.get('answerfeedback', '') or ''
        if '#feedback:p1' in feedback:
            answers.append(choice)
    return answers

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
            text = ''.join(parts)
            return sigma_normalizetext(text)[:300]
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
            feedback_choices = sigma_getfeedbackanswers(root, interaction)
            if feedback_choices:
                correct_answer = skibidi_extractchoicetext(feedback_choices[0])
                correct_id = (feedback_choices[0].get('identifier') or '').strip()

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
    ns = skibidi_detectns(root)

    contentblock = ohiofindns(root, 'div', 'contentblock')

    for i, interaction in enumerate(interactions, 1):
        response_id = (interaction.get('responseIdentifier') or '').strip()

        accepted_answers = pom_getcorrectvalues(
            ohio_getresponsedecl(root, response_id)
        )
        accepted_answers = [sigma_normalizetext(a) for a in accepted_answers]
        context = gyatt_getcontext(contentblock, interaction)
        questions.append({
            'type': 'Text Entry',
            'question_number': i,
            'question': context or instruction or f'Gap {i}',
            'instruction': instruction,
            'audio_filename': audio_filename,
            'answers': accepted_answers,
            'correct_answer': accepted_answers[0] if accepted_answers else '',
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
            cr = None
            for child in rd.iter():
                ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if ctag == 'correctResponse':
                    cr = child
                    break
            if cr is not None:
                for v in cr.iter():
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

        all_options = list(gap_texts.values())
        questions.append({
            'type': 'Drag & Drop',
            'question_number': i,
            'question': ' | '.join(context_parts) if context_parts else instruction,
            'instruction': instruction,
            'audio_filename': audio_filename,
            'answers': all_options,
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

def rizz_savexmlfiles(data, output_dir="decoded_xml"):
    Path(output_dir).mkdir(exist_ok=True)
    saved_files = []
    for filename, xml_content in data.items():
        if not filename.endswith('.xml'):
            continue
        try:
            decoded_xml = rizz_decodeunicode(xml_content)
            formatted_xml = pomformatxml(decoded_xml)
            output_path = Path(output_dir) / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_xml)
            saved_files.append(str(output_path))
        except Exception as e:
            print(f"{Fore.RED}  Error saving {filename}:{Style.RESET_ALL} {e}")
    print(f"{Fore.GREEN}  [+] saved XML files: {len(saved_files)}{Style.RESET_ALL}")
    return saved_files

def ohio_deleteallxml(output_dir="decoded_xml"):
    folder = Path(output_dir)
    if folder.exists():
        for f in folder.glob("*.xml"):
            try:
                f.unlink()
            except Exception:
                pass

def gyatt_printquestions(xml_file, questions):
    print(f"\n{Fore.YELLOW}  {Path(xml_file).name}{Style.RESET_ALL} ({len(questions)} questions)")

    for q in questions:
        qtype = q.get('type', '?')
        qnum = q.get('question_number', '?')
        print(f"\n  {Fore.CYAN}[Q{qnum}] [{qtype}]{Style.RESET_ALL}")
        ctx = q.get('question') or q.get('instruction') or ''
        if ctx:
            print(f"      Context: {ctx}")

        audio = q.get('audio_filename', '')
        if audio:
            print(f"      Audio: {audio}")

        if qtype == 'Drag & Drop':
            pairs = q.get('correct_pairs', {})
            options = q.get('answers', [])
            if options:
                print(f"      Options: {', '.join(options)}")
            if pairs:
                for gap_id, answer in sorted(pairs.items()):
                    print(f"      {Fore.GREEN}{gap_id} -> {answer}{Style.RESET_ALL}")
            continue

        options = q.get('answers', [])
        if options and qtype != 'Text Entry':
            print(f"      Options: {', '.join(options)}")

        correct = q.get('correct_answer', '')
        correct_all = q.get('correct_answers', [])
        if correct_all and len(correct_all) > 1:
            print(f"      {Fore.GREEN}Correct: {', '.join(correct_all)}{Style.RESET_ALL}")
        elif correct:
            print(f"      {Fore.GREEN}Correct: {correct}{Style.RESET_ALL}")
        else:
            correct_id = q.get('correct_id', '')
            if correct_id:
                print(f"      {Fore.YELLOW}Correct (id): {correct_id} - text not found{Style.RESET_ALL}")

def skibidi_processxmlfiles(xml_files):
    print(f"\n  {Fore.CYAN}[*] processing {len(xml_files)} files...{Style.RESET_ALL}")
    time.sleep(1)
    os.system("cls")
    processed_count = 0
    skipped_count = 0
    all_results = {}
    sorted_files = sorted(xml_files, key=lambda x: Path(x).name)
    for xml_file in sorted_files:
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            if sigma_isfinished(xml_content):
                print(f"{Fore.YELLOW}  [skip] {Path(xml_file).name} - activity finished{Style.RESET_ALL}")
                skipped_count += 1
                continue

            questions = skibidi_extractanswers(xml_content)
            if questions:
                gyatt_printquestions(xml_file, questions)
                all_results[Path(xml_file).name] = questions
                processed_count += 1
            else:
                print(f"{Fore.YELLOW}  [skip] {Path(xml_file).name} - no answers found{Style.RESET_ALL}")
                skipped_count += 1
        except Exception as e:
            print(f"{Fore.RED}  Error processing {xml_file}:{Style.RESET_ALL} {e}")
            skipped_count += 1

    print(f"\n  Summary: {Fore.GREEN}{processed_count} processed{Style.RESET_ALL}, "
          f"{Fore.RED}{skipped_count} skipped{Style.RESET_ALL}")

    return all_results

def pom_showdatabase(db):
    data = db.list_all()
    if not data:
        print(f"\n{Fore.YELLOW}  [!] database is empty{Style.RESET_ALL}")
        try:
            input(f"\n  {Fore.CYAN}[>] press Enter to return...{Style.RESET_ALL}")
        except Exception:
            pass
        return

    print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  answers database (total {len(data)} entries){Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

    for i, (key, entry) in enumerate(data.items(), 1):
        url = entry.get('url', '')
        saved_at = entry.get('saved_at', '')
        answers = entry.get('answers', {})
        xml_count = len(answers)

        print(f"\n  {Fore.WHITE}[{i}]{Style.RESET_ALL} {Fore.CYAN}{url[:70]}{Style.RESET_ALL}")
        print(f"      saved at: {saved_at}")
        print(f"      XML count: {xml_count}")

    print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

    try:
        choice = input(f"\n  {Fore.CYAN}[>] select number to view details (or Enter to return): {Style.RESET_ALL}").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not choice:
        return

    try:
        idx = int(choice) - 1
        keys = list(data.keys())
        if 0 <= idx < len(keys):
            entry = data[keys[idx]]
            os.system("cls")
            print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  URL: {entry.get('url', '')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  saved at: {entry.get('saved_at', '')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")

            for xml_name, questions in entry.get('answers', {}).items():
                gyatt_printquestions(xml_name, questions)
        else:
            print(f"{Fore.RED}  [-] invalid number{Style.RESET_ALL}")
    except ValueError:
        print(f"{Fore.RED}  [-] please enter a number{Style.RESET_ALL}")

    try:
        input(f"\n  {Fore.CYAN}[>] press Enter to return...{Style.RESET_ALL}")
    except Exception:
        pass

def skibidi_main():
    logger = SkibidiLogger(log_dir="logs")
    sys.stdout = logger
    sys.stderr = logger
    try:
        print(f"\n  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Session log: {logger.log_file}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

        db = PomlikeheeyaDB("answers_db.json")
        print(f"  {Fore.GREEN}[+] database loaded ({db.count()} entries){Style.RESET_ALL}")

        os.system("cls")
        print(UI)

        while True:
            try:
                choice = input(f"\n  {Fore.CYAN}[>] Enter choice: {Style.RESET_ALL}").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == '4':
                print(f"\n  {Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                break

            elif choice == '2':
                print(f"  {Fore.CYAN}Opening GitHub profile...{Style.RESET_ALL}")
                webbrowser.open("https://github.com/Zentrary")
                continue

            elif choice == '1':
                url = input(f"\n  [>] Enter data.js URL: ").strip()
                if not url:
                    print(f"{Fore.RED}  Please enter a valid URL{Style.RESET_ALL}")
                    continue

                cached = db.get(url)
                if cached:
                    print(f"\n{Fore.GREEN}  [+] found in database (saved at {cached.get('saved_at', '')}){Style.RESET_ALL}")
                    print(f"  {Fore.CYAN}  showing answers...{Style.RESET_ALL}")
                    time.sleep(1)
                    os.system("cls")

                    print(f"\n{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}  showing answers from database{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}  {'=' * 60}{Style.RESET_ALL}")
                    for xml_name, questions in cached.get('answers', {}).items():
                        gyatt_printquestions(xml_name, questions)

                    print("\n  --------------------------------")
                    print(f"  {Fore.CYAN}1. Continue{Style.RESET_ALL}")
                    print(f"  {Fore.CYAN}2. Exit{Style.RESET_ALL}")
                    print("  --------------------------------")
                    try:
                        next_choice = input(f"  {Fore.CYAN}[>] Enter choice: {Style.RESET_ALL}").strip()
                    except Exception:
                        next_choice = '1'

                    if next_choice == '2':
                        print(f"\n  {Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                        break
                    else:
                        os.system("cls")
                        print(UI)
                        continue

                print(f"\n  Processing...")
                content = pomlikeheeyaimak(url)
                if not content:
                    continue

                data = ohio_parsejs(content)
                if not data:
                    continue

                xml_files = rizz_savexmlfiles(data)
                if not xml_files:
                    print(f"{Fore.RED}  No XML files saved{Style.RESET_ALL}")
                    continue

                results = skibidi_processxmlfiles(xml_files)

                if results:
                    if db.set(url, results, xml_files):
                        print(f"\n{Fore.GREEN}  [+] saved to database ({len(results)} XML){Style.RESET_ALL}")

                print("\n  --------------------------------")
                print(f"  {Fore.CYAN}1. Continue{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}2. Exit{Style.RESET_ALL}")
                print("  --------------------------------")
                next_choice = input(f"  {Fore.CYAN}[>] Enter choice: {Style.RESET_ALL}").strip()

                ohio_deleteallxml()

                if next_choice == '2':
                    print(f"\n  {Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break
                else:
                    os.system("cls")
                    print(UI)

            elif choice == '3':
                pom_showdatabase(db)
                os.system("cls")
                print(UI)

            else:
                print(f"{Fore.RED}  Invalid choice, please select 1-4{Style.RESET_ALL}")

    except Exception as e:
        print(f"\n{Fore.RED}  [-] Fatal Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

    finally:
        print(f"\n  {Fore.CYAN}[*] log saved to: {logger.log_file}{Style.RESET_ALL}")
        logger.ohio_close()
        sys.stdout = logger.original_stdout
        sys.stderr = logger.original_stderr

if __name__ == "__main__":
    skibidi_main()
