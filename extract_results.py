#!/usr/bin/env python3
"""
extract_results.py — 将实验日志中的所有评估结果提取到独立文件夹。

用法:
  python extract_results.py <exp_dir> [output_dir] [stdout_log]

示例:
  python extract_results.py ./logs/exp_260717_184456_A2FUSION_... 
  python extract_results.py ./logs/exp_260717_184456_A2FUSION_... ./results/my_run

输出结构:
  <output_dir>/
    ├── summary.json           # 所有 AP 汇总（按confidence/condition/class/IoU）
    ├── summary_table.md       # Markdown 格式对比表
    ├── per_condition/         # 按天气/道路条件的详细结果
    │   ├── all.json
    │   ├── urban.json
    │   └── ...
    ├── config.yml             # 实验配置副本
    └── raw/                   # complete_results.txt 原样备份
"""

import os
import sys
import json
import shutil
import re
from pathlib import Path
from collections import defaultdict


IOU_ORDER = ['0.7', '0.5', '0.3']
CONDITION_ORDER = [
    'all',
    'urban', 'highway', 'countryside', 'alleyway', 'parkinglots', 'shoulder', 'mountain', 'university',
    'day', 'night',
    'normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow',
]
CLASS_ORDER = ['sed', 'bus']


def normalize_iou(value):
    """Normalize IoU strings like 0.70 to 0.7 for consistent JSON keys."""
    return f"{float(value):g}"


def ordered_values(values, preferred):
    """Return values in a stable preferred order, then append unseen values."""
    value_set = set(values)
    ordered = [v for v in preferred if v in value_set]
    ordered.extend(sorted(value_set - set(preferred)))
    return ordered


def format_metric_value(value):
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def format_plain_list(values):
    return "[" + ", ".join(str(v) for v in values) + "]"


def metric_values(cls_data, metric, ious=IOU_ORDER):
    metric_data = cls_data.get(metric, {})
    return [metric_data.get(iou, '-') for iou in ious]


def parse_complete_results(filepath):
    """解析 complete_results.txt 为结构化数据。
    
    格式:
        Conf thr: 0.3, Condition: all
        cls: sed
        iou: 0.7 0.5 0.3 
        bev: 37.36 63.92 70.23 
        3d  :9.85 44.47 67.10 
    """
    with open(filepath, 'r') as f:
        text = f.read()
    
    results = {}
    current_conf = None
    current_condition = None
    current_cls = None
    current_iou = []
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Conf thr line
        m = re.match(r'Conf thr:\s*([\d.]+),\s*Condition:\s*(\S+)', line)
        if m:
            current_conf = m.group(1)
            current_condition = m.group(2)
            if current_conf not in results:
                results[current_conf] = {}
            if current_condition not in results[current_conf]:
                results[current_conf][current_condition] = {}
            continue
        
        # cls line
        m = re.match(r'cls:\s*(\S+)', line)
        if m:
            current_cls = m.group(1)
            if current_cls not in results[current_conf][current_condition]:
                results[current_conf][current_condition][current_cls] = {}
            continue
        
        # iou line
        m = re.match(r'iou:\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
        if m:
            current_iou = [normalize_iou(m.group(1)), normalize_iou(m.group(2)), normalize_iou(m.group(3))]
            continue
        
        # bev line
        m = re.match(r'bev:\s*([\d.e+\-]+)\s+([\d.e+\-]+)\s+([\d.e+\-]+)', line)
        if m:
            for idx, iou_val in enumerate(current_iou):
                if 'BEV' not in results[current_conf][current_condition][current_cls]:
                    results[current_conf][current_condition][current_cls]['BEV'] = {}
                results[current_conf][current_condition][current_cls]['BEV'][iou_val] = float(m.group(idx + 1))
            continue
        
        # 3d line
        m = re.match(r'3d\s*:\s*([\d.e+\-]+)\s+([\d.e+\-]+)\s+([\d.e+\-]+)', line)
        if m:
            for idx, iou_val in enumerate(current_iou):
                if '3D' not in results[current_conf][current_condition][current_cls]:
                    results[current_conf][current_condition][current_cls]['3D'] = {}
                results[current_conf][current_condition][current_cls]['3D'][iou_val] = float(m.group(idx + 1))
            continue
    
    return results


def parse_stdout_eval_results(filepath):
    """解析 stdout 日志中的 KITTI eval 块。

    支持格式:
        -----conf0.0-----
        sed AP(Average Precision)@0.70, 0.70, 0.70:
        bbox AP:92.75, 92.75, 92.75
        bev  AP:43.50, 43.50, 43.50
        3d   AP:11.59, 11.59, 11.59

    stdout 里没有条件细分，因此统一写到 condition='all'。
    """
    with open(filepath, 'r') as f:
        text = f.read()

    results = {}
    current_conf = None
    current_cls = None
    current_iou = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = re.match(r'-+conf([\d.]+)-+', line)
        if m:
            current_conf = m.group(1)
            results.setdefault(current_conf, {'all': {}})
            current_cls = None
            current_iou = None
            continue

        m = re.match(r'(\S+)\s+AP\(Average Precision\)@([\d.]+),', line)
        if m and current_conf is not None:
            current_cls = m.group(1)
            current_iou = normalize_iou(m.group(2))
            results[current_conf]['all'].setdefault(current_cls, {'BEV': {}, '3D': {}})
            continue

        if current_conf is None or current_cls is None or current_iou is None:
            continue

        m = re.match(r'bev\s+AP:\s*([\d.e+\-]+)', line)
        if m:
            results[current_conf]['all'][current_cls]['BEV'][current_iou] = float(m.group(1))
            continue

        m = re.match(r'3d\s+AP:\s*([\d.e+\-]+)', line)
        if m:
            results[current_conf]['all'][current_cls]['3D'][current_iou] = float(m.group(1))
            continue

    return results


def build_summary_table(results, conf='0.3', condition='all'):
    """构建 Markdown 对比表。"""
    if conf not in results or condition not in results[conf]:
        return "N/A"
    
    data = results[conf][condition]
    lines = []
    lines.append(f"## Results: conf={conf}, condition={condition}")
    lines.append("")
    metric_cols = [f"{metric}@{iou}" for metric in ['BEV', '3D'] for iou in IOU_ORDER]
    lines.append("| Class | " + " | ".join(metric_cols) + " |")
    lines.append("|-------|" + "|".join(["------"] * len(metric_cols)) + "|")
    
    for cls_name in ordered_values(data.keys(), CLASS_ORDER):
        vals = []
        for metric in ['BEV', '3D']:
            vals.extend(metric_values(data[cls_name], metric))
        lines.append(f"| {cls_name} | " + " | ".join(format_metric_value(v) for v in vals) + " |")
    
    return '\n'.join(lines)


def build_weather_table(results, conf='0.3'):
    """按条件构建 BEV/3D 在 0.7/0.5/0.3 IoU 下的完整汇总表。"""
    if conf not in results:
        return "N/A"
    
    conditions = ordered_values(results[conf].keys(), CONDITION_ORDER)
    all_classes = set()
    for cond in conditions:
        all_classes.update(results[conf][cond].keys())
    all_classes = ordered_values(all_classes, CLASS_ORDER)
    
    lines = []
    for metric in ['BEV', '3D']:
        for iou in IOU_ORDER:
            lines.append(f"## Per-Condition {metric}@{iou} (conf={conf})")
            lines.append("| Condition | " + " | ".join(all_classes) + " |")
            lines.append("|-----------|" + "|".join(["------"] * len(all_classes)) + "|")
            for cond in conditions:
                vals = []
                for cls_name in all_classes:
                    v = results[conf][cond].get(cls_name, {}).get(metric, {}).get(iou, '-')
                    vals.append(format_metric_value(v))
                lines.append(f"| {cond} | " + " | ".join(vals) + " |")
            lines.append("")
    
    return '\n'.join(lines).rstrip()


def build_condition_blocks(results, conf='0.3'):
    """构建接近 validate_kitti_conditional stdout 的完整块状结果。"""
    if conf not in results:
        return "N/A"

    lines = []
    conditions = ordered_values(results[conf].keys(), CONDITION_ORDER)
    for cond in conditions:
        lines.append(f"Conf thr:  {conf} , Condition:  {cond}")
        classes = ordered_values(results[conf][cond].keys(), CLASS_ORDER)
        for idx, cls_name in enumerate(classes):
            cls_data = results[conf][cond][cls_name]
            bev = metric_values(cls_data, 'BEV')
            td = metric_values(cls_data, '3D')
            lines.append(f"Cls:  {cls_name}")
            lines.append(f"IoU: {format_plain_list(IOU_ORDER)}")
            lines.append(f"BEV:  {format_plain_list(bev)}")
            lines.append(f"3D:  {format_plain_list(td)}")
            lines.append("==================================================" if idx < len(classes) - 1 else "--------------------------------------------------")

    return '\n'.join(lines)


def write_summary_outputs(results, conf_thr, output_dir, exp_name, source='complete_results'):
    """Write JSON/Markdown summaries for one confidence threshold."""
    output_dir = Path(output_dir)

    json_path = output_dir / f'summary_conf{conf_thr}.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  -> {json_path}")

    md_path = output_dir / f'summary_conf{conf_thr}.md'
    with open(md_path, 'w') as f:
        f.write(f"# Experiment: {exp_name}\n\n")
        f.write(f"Confidence threshold: {conf_thr}\n\n")
        f.write(f"Source: {source}\n\n")
        f.write(build_summary_table(results, conf_thr, 'all'))
        f.write("\n\n---\n\n")
        f.write(build_weather_table(results, conf_thr))
    print(f"  -> {md_path}")

    block_path = output_dir / f'condition_blocks_conf{conf_thr}.txt'
    with open(block_path, 'w') as f:
        f.write(build_condition_blocks(results, conf_thr))
        f.write("\n")
    print(f"  -> {block_path}")

    return json_path, md_path, block_path


def extract_experiment(exp_dir, output_dir, stdout_log=None):
    """主函数：从 exp_dir 提取所有结果到 output_dir。"""
    exp_dir = Path(exp_dir)
    output_dir = Path(output_dir)
    
    if not exp_dir.exists():
        print(f"Error: {exp_dir} not found")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ── 1. Find and parse complete_results.txt ──
    results_files = list(exp_dir.rglob('complete_results.txt'))
    
    parsed_confs = set()

    if not results_files:
        print(f"Warning: No complete_results.txt found in {exp_dir}")
    else:
        for rf in results_files:
            # Determine conf threshold from path (e.g., .../none/0.3/complete_results.txt)
            rel = rf.relative_to(exp_dir)
            conf_thr = 'unknown'
            for part in rel.parts:
                if re.match(r'[\d.]+', part):
                    conf_thr = part
                    break
            
            print(f"Parsing: {rf}")
            results = parse_complete_results(str(rf))
            parsed_confs.update(results.keys())
            
            # Save full JSON and Markdown tables
            write_summary_outputs(results, conf_thr, output_dir, exp_dir.name)
            
            # Per-condition JSON
            cond_dir = output_dir / 'per_condition'
            cond_dir.mkdir(exist_ok=True)
            for cond_name, cond_data in results.get(conf_thr, {}).items():
                cond_path = cond_dir / f'{cond_name}_conf{conf_thr}.json'
                with open(cond_path, 'w') as f:
                    json.dump(cond_data, f, indent=2)
            print(f"  → {cond_dir}/ (per-condition JSON)")

    # ── 1b. Parse stdout log fallback ──
    if stdout_log is not None:
        stdout_log = Path(stdout_log)
        if stdout_log.exists():
            stdout_results = parse_stdout_eval_results(str(stdout_log))
            raw_dir = output_dir / 'raw'
            raw_dir.mkdir(exist_ok=True)
            shutil.copy2(stdout_log, raw_dir / stdout_log.name)

            for conf_thr in sorted(stdout_results.keys(), key=float):
                if conf_thr in parsed_confs:
                    print(f"Stdout log: conf={conf_thr} already has complete_results.txt; skip summary overwrite")
                    continue
                print(f"Parsing stdout fallback: {stdout_log} (conf={conf_thr})")
                results = {conf_thr: stdout_results[conf_thr]}
                write_summary_outputs(results, conf_thr, output_dir, exp_dir.name, source=f'stdout_log:{stdout_log.name}')

                cond_dir = output_dir / 'per_condition'
                cond_dir.mkdir(exist_ok=True)
                cond_path = cond_dir / f'all_conf{conf_thr}_stdout.json'
                with open(cond_path, 'w') as f:
                    json.dump(stdout_results[conf_thr]['all'], f, indent=2)
                print(f"  -> {cond_path}")
        else:
            print(f"Warning: stdout log not found: {stdout_log}")
    
    # ── 2. Copy config ──
    for cfg_name in ['config.yml', 'ASF_v2_0_final.yml', 'cfg_*.yml']:
        for cfg_file in exp_dir.glob(cfg_name):
            dest = output_dir / cfg_file.name
            shutil.copy2(cfg_file, dest)
            print(f"Config: {cfg_file} → {dest}")
    
    # ── 3. Raw backup ──
    raw_dir = output_dir / 'raw'
    raw_dir.mkdir(exist_ok=True)
    for rf in results_files:
        dest = raw_dir / f'complete_results_{rf.parent.parent.name}_{rf.parent.name}.txt'
        shutil.copy2(rf, dest)
    print(f"Raw: {raw_dir}/")
    
    # ── 4. Checkpoint info ──
    models_dir = exp_dir / 'models'
    if models_dir.exists():
        ckpts = sorted(models_dir.glob('model_*.pt'))
        info = {
            'num_checkpoints': len(ckpts),
            'checkpoints': [str(c.name) for c in ckpts],
            'sizes': {c.name: f"{c.stat().st_size / 1e6:.1f}MB" for c in ckpts}
        }
        with open(output_dir / 'checkpoints.json', 'w') as f:
            json.dump(info, f, indent=2)
        print(f"Checkpoints: {len(ckpts)} saved → {output_dir}/checkpoints.json")
    
    print(f"\n✅ Done! Results saved to: {output_dir}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_results.py <exp_dir> [output_dir] [stdout_log]")
        print("Example: python extract_results.py ./logs/exp_260717_184456_A2FUSION_... ./results/my_run ./logs/repro_asf.log")
        sys.exit(1)
    
    exp_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f"./results/{Path(exp_dir).name}"
    stdout_log = sys.argv[3] if len(sys.argv) > 3 else None
    extract_experiment(exp_dir, output_dir, stdout_log)
