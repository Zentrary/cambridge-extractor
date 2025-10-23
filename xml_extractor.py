import requests
import json
import re
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

UI = f"""
{Fore.GREEN}
  ███████╗███████╗███╗   ██╗████████╗██████╗  █████╗ ██████╗ ██╗   ██╗
  ╚══███╔╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
    ███╔╝ █████╗  ██╔██╗ ██║   ██║   ██████╔╝███████║██████╔╝ ╚████╔╝ 
   ███╔╝  ██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗██╔══██║██╔══██╗  ╚██╔╝  
  ███████╗███████╗██║ ╚████║   ██║   ██║  ██║██║  ██║██║  ██║   ██║   
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
                                                                    
{Style.RESET_ALL}
  by z3nTr4ry

  ---------------------------------
  1. Continue
  2. GitHub
  3. Exit
  --------------------------------
"""

def download_data_js(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if "ajaxData" not in response.text:
            raise ValueError("Not a valid data.js file")
        return response.text
    except Exception as e:
        print(f"{Fore.RED}  Download error:{Style.RESET_ALL} {e}")
        return None

def decode_unicode_escapes(text):
    decoded = text.encode().decode('unicode_escape')
    return decoded.replace('\r\n', '\n')

def parse_js_object(content):
    try:
        match = re.search(r'ajaxData\s*=\s*(\{.*?\});', content, re.DOTALL)
        if not match:
            raise ValueError("ajaxData object not found")
        js_object_str = match.group(1)
        js_object_str = re.sub(r"'([^']*)':", r'"\1":', js_object_str)
        data = eval(js_object_str)
        return data
    except Exception as e:
        print(f"{Fore.RED}  Error parsing JS object:{Style.RESET_ALL} {e}")
        return None

def format_xml(xml_content):
    try:
        root = ET.fromstring(xml_content)
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding='unicode')
    except:
        return xml_content

def is_activity_finished(xml_content):
    return "You have finished the activity." in xml_content

def extract_multiple_questions_from_single_file(xml_content):
    try:
        root = ET.fromstring(xml_content)
        questions_data = []
        choice_interactions = root.findall('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}choiceInteraction')
        for i, interaction in enumerate(choice_interactions, 1):
            question_text, answers, correct_answer = "", [], ""
            contentblock = root.find('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}div[@id="contentblock"]')
            if contentblock is not None:
                paragraphs = contentblock.findall('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}p')
                for p in paragraphs:
                    text = ''.join(p.itertext()).strip()
                    if text and ('strong' in str(p) and (str(i) + '.' in text or str(i) + ':' in text)):
                        question_text = re.sub(r'<[^>]+>', '', text).strip()
                        break
            choices = interaction.findall('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}simpleChoice')
            for choice in choices:
                choice_text = ''.join(choice.itertext()).strip()
                if choice_text:
                    answers.append(choice_text)
                    feedback = choice.get('answerfeedback', '')
                    if '#feedback:p1#' in feedback:
                        correct_answer = choice_text
            if question_text and correct_answer:
                questions_data.append({
                    'question_number': i,
                    'question': question_text,
                    'answers': answers,
                    'correct_answer': correct_answer
                })
        return questions_data
    except Exception as e:
        print(f"{Fore.RED}  Multiple questions extract error:{Style.RESET_ALL} {e}")
        return []

def extract_question_and_answers(xml_content):
    try:
        root = ET.fromstring(xml_content)
        question, answers, correct_answer = "", [], ""
        contentblock = root.find('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}div[@id="contentblock"]')
        if contentblock is not None:
            for p in contentblock.findall('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}p'):
                text = ''.join(p.itertext()).strip()
                if text and ('______' in text or '?' in text or len(text) > 20):
                    question = text
                    break
        choices = root.findall('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}simpleChoice')
        for choice in choices:
            choice_text = ''.join(choice.itertext()).strip()
            if choice_text:
                feedback = choice.get('answerfeedback', '')
                if '#feedback:p1#' in feedback:
                    correct_answer = choice_text
                answers.append(choice_text)
        if not correct_answer:
            response_decl = root.find('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}responseDeclaration')
            if response_decl is not None:
                correct_response = response_decl.find('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}correctResponse')
                if correct_response is not None:
                    value_elem = correct_response.find('.//{http://www.imsglobal.org/xsd/imsqti_v2p1}value')
                    if value_elem is not None:
                        correct_id = value_elem.text
                        for choice in choices:
                            if choice.get('identifier') == correct_id:
                                correct_answer = ''.join(choice.itertext()).strip()
                                break
        return {'question': question, 'answers': answers, 'correct_answer': correct_answer}
    except Exception as e:
        print(f"{Fore.RED}  Extract error:{Style.RESET_ALL} {e}")
        return {'question': "", 'answers': [], 'correct_answer': ""}

def save_xml_files(data, output_dir="decoded_xml"):
    Path(output_dir).mkdir(exist_ok=True)
    saved_files = []
    for filename, xml_content in data.items():
        try:
            decoded_xml = decode_unicode_escapes(xml_content)
            formatted_xml = format_xml(decoded_xml)
            output_path = Path(output_dir) / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_xml)
            saved_files.append(str(output_path))
        except Exception as e:
            print(f"{Fore.RED}  Error saving {filename}:{Style.RESET_ALL} {e}")
    return saved_files

def delete_all_xml(output_dir="decoded_xml"):
    folder = Path(output_dir)
    if folder.exists():
        for f in folder.glob("*.xml"):
            try:
                f.unlink()
            except:
                pass

def process_xml_files(xml_files):
    print(f"\n  Processing {len(xml_files)} files...")
    time.sleep(1)
    os.system("cls")
    processed_count = skipped_count = 0
    sorted_files = sorted(xml_files, key=lambda x: Path(x).name)
    for xml_file in sorted_files:
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            if is_activity_finished(xml_content):
                skipped_count += 1
                continue
            multiple_questions = extract_multiple_questions_from_single_file(xml_content)
            if multiple_questions:
                print(f"\n{Fore.YELLOW}  {Path(xml_file).name}{Style.RESET_ALL} ({len(multiple_questions)} questions)")
                for q in multiple_questions:
                    print(f"  Q{q['question_number']}: {q['question']}")
                    print(f"  Options: {', '.join(q['answers'])}")
                    print(f"  Correct: {Fore.GREEN}{q['correct_answer']}{Style.RESET_ALL}\n")
                processed_count += 1
            else:
                result = extract_question_and_answers(xml_content)
                if result['question'] and result['correct_answer']:
                    print(f"\n{Fore.YELLOW}  {Path(xml_file).name}{Style.RESET_ALL}")
                    print(f"  Question: {result['question']}")
                    print(f"  Options: {', '.join(result['answers'])}")
                    print(f"  Correct: {Fore.GREEN}{result['correct_answer']}{Style.RESET_ALL}")
                    processed_count += 1
                else:
                    skipped_count += 1
        except Exception as e:
            print(f"{Fore.RED}  Error processing {xml_file}:{Style.RESET_ALL} {e}")
            skipped_count += 1
    print(f"\n  Summary: {Fore.GREEN}{processed_count} processed{Style.RESET_ALL}, {Fore.RED}{skipped_count} skipped{Style.RESET_ALL}")

def main():
    os.system("cls")
    print(UI)
    while True:
        choice = input(f"\n  {Fore.CYAN}[>] Enter choice: {Style.RESET_ALL}").strip()
        if choice == '3':
            print(f"\n  {Fore.CYAN}Goodbye!{Style.RESET_ALL}")
            break
        elif choice == '2':
            print(f"  {Fore.CYAN}GitHub: https://github.com/z3nTr4ry{Style.RESET_ALL}")
            continue
        elif choice == '1':
            url = input(f"\n  [>] Enter data.js URL: ").strip()
            if not url:
                print(f"{Fore.RED}  Please enter a valid URL{Style.RESET_ALL}")
                continue
            print(f"\n  Processing...")
            content = download_data_js(url)
            if not content:
                continue
            data = parse_js_object(content)
            if not data:
                continue
            xml_files = save_xml_files(data)
            if not xml_files:
                print(f"{Fore.RED}  No XML files saved{Style.RESET_ALL}")
                continue
            process_xml_files(xml_files)

            print("\n  --------------------------------")
            print(f"  {Fore.CYAN}1. Continue{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}2. Exit{Style.RESET_ALL}")
            print("  --------------------------------")
            next_choice = input(f"  {Fore.CYAN}[>] Enter choice: {Style.RESET_ALL}").strip()

            delete_all_xml()

            if next_choice == '2':
                print(f"\n  {Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                break
            else:
                os.system("cls")
                print(UI)
        else:
            print(f"{Fore.RED}  Invalid choice, please select 1–3{Style.RESET_ALL}")

if __name__ == "__main__":
    main()