"""Analyze attack_test_reports.jsonl to get some insight to the chatbot 
performance against prompt attack"""
import json


def analyze_each_line(file_path: str) -> None:
    """Read the attack_test_report.jsonl file and extract important information
    there"""
    # Count for prompt injection
    injection_success_count = 0
    injection_fail_count = 0
    injection_total_attack = 0

    # Count for prompt leaking
    leaking_success_count = 0
    leaking_fail_count = 0
    leaking_total_attack = 0

    # Count for jailbreaking
    jailbreaking_success_count = 0
    jailbreaking_fail_count = 0
    jailbreaking_total_attack = 0
    # Path to the jsonl file that store the case that the chatbot was successfully attacked
    success_report_path = r"./app/tests/test_results/attack_retry.jsonl"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    # Change the report to json (or dictionary)
                    single_report_dict = json.loads(line)
                    is_attack_success = single_report_dict.get("is success")
                    attack_type = single_report_dict.get("type of attack")
                    if is_attack_success is True:
                        if attack_type == "prompt injection":
                            injection_success_count += 1
                        elif attack_type == "prompt leaking":
                            leaking_success_count += 1
                        elif attack_type == "jailbreaking":
                            jailbreaking_success_count += 1
                        attack_success_record = {
                            "type of attack": single_report_dict.get("type of attack"),
                            "attack prompt": single_report_dict.get("attack prompt"),
                            "chatbot response": single_report_dict.get("chatbot response"),
                            "explanation": single_report_dict.get("explanation")
                        }
                        with open(success_report_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps(attack_success_record) + '\n')
                        
                    elif is_attack_success is False:
                        if attack_type == "prompt injection":
                            injection_fail_count += 1
                        elif attack_type == "prompt leaking":
                            leaking_fail_count += 1
                        elif attack_type == "jailbreaking":
                            jailbreaking_fail_count += 1
                    
                    if attack_type == "prompt injection":
                        injection_total_attack += 1
                    elif attack_type == "prompt leaking":
                        leaking_total_attack += 1
                    elif attack_type == "jailbreaking":
                        jailbreaking_total_attack += 1
                except json.JSONDecodeError:
                    print(f"⚠️ Skipped the line:\n{line.strip()}\nbecause it is unreadable")
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"--------------------- PROMPT INJECTION ----------------------------")
    print(f"✅ Number of attacks failed: {injection_fail_count}")
    print(f"❌ Number of attacks succeeded: {injection_success_count}")
    print(f"📊 Total attacks: {injection_total_attack}")

    if injection_total_attack != 0:
        injection_safe_rate = injection_fail_count / injection_total_attack
        print(f"📈 Safety rate: {injection_safe_rate}")
        print(f"The cases that the prompt injection attack succeed is stored in file: {success_report_path}")

    print(f"--------------------- PROMPT LEAKING ----------------------------")
    print(f"✅ Number of attacks failed: {leaking_fail_count}")
    print(f"❌ Number of attacks succeeded: {leaking_success_count}")
    print(f"📊 Total attacks: {leaking_total_attack}")
    if leaking_total_attack != 0:
        leaking_safe_rate = leaking_fail_count / leaking_total_attack
        print(f"📈 Safety rate: {leaking_safe_rate}")
        print(f"The cases that the prompt leaking attack succeed is stored in file: {success_report_path}")

    print(f"--------------------- JAILBREAKING ----------------------------")
    print(f"✅ Number of attacks failed: {jailbreaking_fail_count}")
    print(f"❌ Number of attacks succeeded: {jailbreaking_success_count}")
    print(f"📊 Total attacks: {jailbreaking_total_attack}")

    if jailbreaking_total_attack != 0:
        jailbreaking_safe_rate = jailbreaking_fail_count / jailbreaking_total_attack
        print(f"📈 Safety rate: {jailbreaking_safe_rate}")
        print(f"The cases that the jailbreaking attack succeed is stored in file: {success_report_path}")

                
if __name__ == "__main__":
    analyze_each_line(r"./app/tests/test_results/attack_test_reports.jsonl")