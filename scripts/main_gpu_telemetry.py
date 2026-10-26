"""MAIN-only NVIDIA telemetry exporter. Standard library; no Docker GPU privileges."""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import time

FIELDS = ('name','utilization.gpu','memory.used','memory.total','temperature.gpu',
          'power.draw','power.limit','clocks.sm','pstate')

def measure(binary='nvidia-smi'):
    result = subprocess.run([binary,'--query-gpu='+','.join(FIELDS),
                             '--format=csv,noheader,nounits'],
                            capture_output=True,text=True,timeout=5,check=True,
                            encoding='utf-8',errors='replace')
    row = next(csv.reader(result.stdout.splitlines()), [])
    if len(row) != len(FIELDS):
        raise ValueError('nvidia_smi_unexpected_output')
    row = [item.strip() for item in row]
    def num(index):
        try:
            n = float(row[index])
            return n if n == n and abs(n) != float('inf') else None
        except ValueError:
            return None
    used,total,power,limit = num(2),num(3),num(5),num(6)
    return {'available':True,'timestamp_ms':int(time.time()*1000),'gpu':{
        'name':row[0], 'utilization_percent':num(1),
        'memory_used_mib':used,'memory_total_mib':total,
        'memory_percent':round(used/total*100,2) if used is not None and total and total>0 else None,
        'temperature_c':num(4),'power_w':power,'power_limit_w':limit,
        'power_percent':round(power/limit*100,2) if power is not None and limit and limit>0 else None,
        'sm_clock_mhz':num(7),'pstate':row[8]}}

def write_atomic(destination, payload):
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+'.tmp')
    temporary.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    os.replace(temporary,destination)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=r'H:\\temp\\EZSTUDIO_ASSISTANT_GPU\\telemetry.json')
    parser.add_argument('--interval',type=float,default=2.0)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    if not 1 <= args.interval <= 30:
        parser.error('--interval must be 1..30')
    path=Path(args.output)
    while True:
        try:
            write_atomic(path,measure())
        except (OSError, ValueError, subprocess.SubprocessError):
            write_atomic(path,{'available':False,'timestamp_ms':int(time.time()*1000),'error':'nvidia_smi_unavailable'})
        if args.once:break
        time.sleep(args.interval)

if __name__=='__main__':
    main()
