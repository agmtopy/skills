#!/usr/bin/env python3
"""
评估天气对比技能的测试结果
"""
import json
import re
import os
from pathlib import Path

def check_assertion(output_text, assertion):
    """检查单个断言是否通过"""
    check_type = assertion.get("check_type")
    expected = assertion.get("expected")

    if check_type == "contains":
        return expected in output_text
    elif check_type == "contains_all":
        return all(exp in output_text for exp in expected)
    elif check_type == "contains_any":
        return any(exp in output_text for exp in expected)
    elif check_type == "regex_match":
        pattern = re.compile(expected)
        return bool(pattern.search(output_text))
    else:
        return False

def evaluate_test_case(eval_dir):
    """评估单个测试用例"""
    # 读取元数据
    metadata_path = eval_dir / "eval_metadata.json"
    if not metadata_path.exists():
        print(f"Warning: No metadata found in {eval_dir}")
        return None

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # 评估 with_skill 和 without_skill
    results = {}

    for run_type in ["with_skill", "without_skill"]:
        run_dir = eval_dir / run_type
        outputs_dir = run_dir / "outputs"

        if not outputs_dir.exists():
            print(f"Warning: No outputs directory for {run_type} in {eval_dir}")
            continue

        # 读取所有输出文件
        output_text = ""
        for output_file in outputs_dir.glob("*"):
            if output_file.is_file() and output_file.suffix in [".txt", ".md", ".json"]:
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        output_text += f.read() + "\n"
                except Exception as e:
                    print(f"Error reading {output_file}: {e}")

        if not output_text:
            continue

        # 评估所有断言
        assertions_results = []
        for assertion in metadata.get("assertions", []):
            passed = check_assertion(output_text, assertion)
            assertions_results.append({
                "text": assertion.get("description", assertion.get("name")),
                "passed": passed,
                "evidence": f"Expected: {assertion.get('expected')}"
            })

        # 计算通过率
        passed_count = sum(1 for r in assertions_results if r["passed"])
        total_count = len(assertions_results)
        pass_rate = passed_count / total_count if total_count > 0 else 0

        results[run_type] = {
            "pass_rate": pass_rate,
            "passed": passed_count,
            "total": total_count,
            "expectations": assertions_results
        }

        # 保存 grading.json
        grading_path = run_dir / "grading.json"
        with open(grading_path, 'w', encoding='utf-8') as f:
            json.dump({
                "pass_rate": pass_rate,
                "passed": passed_count,
                "total": total_count,
                "expectations": assertions_results
            }, f, ensure_ascii=False, indent=2)

        print(f"✓ Evaluated {run_type} for {eval_dir.name}: {passed_count}/{total_count} assertions passed")

    return results

def main():
    """主函数"""
    workspace = Path("/mnt/e/soft/skills/weather-compare/weather-compare-workspace/iteration-1")

    all_results = {}

    # 遍历所有测试用例
    for eval_dir in sorted(workspace.glob("eval-*")):
        if eval_dir.is_dir():
            print(f"\n{'='*60}")
            print(f"Evaluating: {eval_dir.name}")
            print('='*60)

            results = evaluate_test_case(eval_dir)
            if results:
                all_results[eval_dir.name] = results

    # 生成汇总报告
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)

    for eval_name, results in all_results.items():
        print(f"\n{eval_name}:")
        for run_type, stats in results.items():
            print(f"  {run_type}: {stats['passed']}/{stats['total']} passed ({stats['pass_rate']*100:.1f}%)")

    # 保存汇总结果
    summary_path = workspace / "evaluation_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Evaluation summary saved to: {summary_path}")

if __name__ == "__main__":
    main()
