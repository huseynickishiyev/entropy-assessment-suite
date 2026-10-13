"""Batch executor; no GUI dependency. NIST subprocess output retained unmodified."""
import csv, hashlib, json, os, pathlib, re, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def normalize(path, width, encoding, samples, destination):
    data=pathlib.Path(path).read_bytes(); mask=(1<<width)-1
    if encoding=='byte-per-symbol':
        if len(data)!=samples:raise ValueError(f'Expected {samples} bytes; got {len(data)}')
        if any(v>mask for v in data):raise ValueError('Symbol exceeds width')
        destination.write_bytes(data)
    elif encoding=='packed-msb':
        if len(data)!=(samples*width+7)//8:raise ValueError('Incorrect packed size')
        if width==8:destination.write_bytes(data);return
        values=bytearray(samples)
        for i in range(samples):
            v=0
            for bit in range(width):
                pos=i*width+bit;v=(v<<1)|((data[pos//8]>>(7-pos%8))&1)
            values[i]=v
        destination.write_bytes(values)
    else:raise ValueError('Unknown encoding')

def run_one(path, cfg, output):
    t0=time.perf_counter(); path=pathlib.Path(path); name=path.name
    result={'file':name,'path':str(path),'sha256':'','bits':cfg['bits'],'encoding':cfg['encoding'],'samples':cfg['samples'],'status':'error','seconds':0,'iid_status':'not_selected','non_iid_status':'not_selected','health_status':'not_selected','health_alarm':'','empirical_shannon':'','empirical_mcv_plugin':'','rct_alarms':'','apt_alarms':'','raw_iid':'','raw_non_iid':'','error':''}
    try:
        result['sha256']=digest(path)
        with tempfile.TemporaryDirectory(prefix='ip4_') as tmp:
            norm=pathlib.Path(tmp)/'input.bin';normalize(path,cfg['bits'],cfg['encoding'],cfg['samples'],norm)
            for track,enabled,filename in [('iid',cfg['iid'],'ea_iid'),('non_iid',cfg['non_iid'],'ea_non_iid')]:
                if not enabled:continue
                exe=pathlib.Path(cfg['nist_dir'])/(filename + ('.exe' if os.name == 'nt' else ''))
                if not exe.is_file():raise FileNotFoundError(f'Missing NIST executable: {exe}')
                verbosity = int(cfg.get('nist_verbosity', 0))
                if verbosity not in (0, 1, 2):
                    raise ValueError('Invalid NIST verbosity level')
                cmd = [
                    str(exe.resolve()),
                    '-i',
                    *(['-v'] * verbosity),
                    str(norm),
                    str(cfg['bits'])
                ]
                try:
                    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=cfg['timeout'],check=False)
                    status='ok' if p.returncode==0 else f'exit_{p.returncode}'
                    raw=p.stdout
                except subprocess.TimeoutExpired as exc:
                    status='timeout';raw=(exc.stdout or b'');raw=raw.decode('utf-8','replace') if isinstance(raw,bytes) else raw
                outfile=output/'raw'/f'{result["sha256"][:16]}_{track}.txt';outfile.write_text(raw,encoding='utf-8')
                result[track+'_status']=status;result['raw_'+track]=str(outfile)
            if cfg['health']:
                exe=pathlib.Path(cfg['health_bin'])
                if not exe.is_file():raise FileNotFoundError('Health C binary missing; compile engine/health.c')
                cmd=[str(exe.resolve()),str(norm),str(cfg['bits']),str(cfg['samples']),str(cfg['rct_cutoff']),str(cfg['apt_window']),str(cfg['apt_cutoff'])]
                p=subprocess.run(cmd,capture_output=True,text=True,timeout=cfg['timeout'])
                if p.returncode!=0:raise RuntimeError('health engine: '+p.stderr)
                h=json.loads(p.stdout)
                detail=output/'raw'/f'{result["sha256"][:16]}_health.json';detail.write_text(json.dumps(h,indent=2))
                result.update({k:h[k] for k in ['health_alarm','empirical_shannon','empirical_mcv_plugin','rct_alarms','apt_alarms']})
                result['health_status']='ok'
        statuses=[result[t+'_status'] for t in ['iid','non_iid','health'] if result[t+'_status']!='not_selected']
        result['status']='ok' if statuses and all(s=='ok' for s in statuses) else 'partial_failure'
    except Exception as exc:result['error']=str(exc)
    result['seconds']=round(time.perf_counter()-t0,3)
    return result

def save_results(rows, output, cfg):
    output.mkdir(parents=True,exist_ok=True)
    rows=sorted(rows,key=lambda r:r['path'])
    with (output/'results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (output/'results.json').write_text(json.dumps({'configuration':cfg,'results':rows},ensure_ascii=False,indent=2),encoding='utf-8')

def run_batch(files,cfg,output,progress=None):
    output=pathlib.Path(output);(output/'raw').mkdir(parents=True,exist_ok=True)
    rows=[]
    with ThreadPoolExecutor(max_workers=cfg['workers']) as pool:
        futures={pool.submit(run_one,p,cfg,output):p for p in files}
        for i,f in enumerate(as_completed(futures),1):
            row=f.result();rows.append(row)
            if progress:progress(i,len(futures),row)
    if rows:save_results(rows,output,cfg)
    return rows
