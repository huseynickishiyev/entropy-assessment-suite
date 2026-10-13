#!/usr/bin/env python3
"""Reproducible synthetic data, with ground-truth metadata. Not physical entropy data."""
import argparse, json, math, pathlib, random

def generate(path, bits, samples, model, seed, p=0.8, fault_at=0.5):
    rng=random.Random(seed); k=1<<bits; out=bytearray(samples)
    for i in range(samples):
        if model=='uniform': v=rng.randrange(k)
        elif model=='biased': v=0 if rng.random()<p else rng.randrange(1,k)
        elif model=='markov': v=out[i-1] if i and rng.random()<p else rng.randrange(k)
        elif model=='stuck': v=0 if i>=int(samples*fault_at) else rng.randrange(k)
        elif model=='periodic':v=i%k
        else:raise ValueError(model)
        out[i]=v
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(out)
    probs=[p]+[(1-p)/(k-1)]*(k-1)
    truth = {'uniform': math.log2(k),'biased':-math.log2(max(probs))}.get(model)
    return {'file':path.name,'bits':bits,'samples':samples,'model':model,'seed':seed,'p':p,'fault_at':fault_at,'theoretical_min_entropy_per_symbol':truth,'ground_truth_note':'IID marginal min entropy only; null for dependent/nonstationary sources'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--out',type=pathlib.Path,default=pathlib.Path('datasets'));a.add_argument('--bits',type=int,choices=[1,4,8],default=1);a.add_argument('--samples',type=int,default=1000000);a.add_argument('--repeats',type=int,default=3);a.add_argument('--models',nargs='+',choices=['uniform','biased','markov','stuck','periodic'],default=['uniform','biased','markov','stuck','periodic']);a.add_argument('--seed',type=int,default=42000);a.add_argument('--p',type=float,default=0.8);a.add_argument('--fault-at',type=float,default=0.5);x=a.parse_args()
    if not (0<x.p<1 and 0<=x.fault_at<=1 and x.samples>=1 and x.repeats>0):a.error('invalid parameter')
    meta=[]
    for model in x.models:
        for j in range(x.repeats):
            seed=x.seed+j+100000*x.models.index(model)
            f=x.out/f'{model}_b{x.bits}_r{j:03}.bin'
            meta.append(generate(f,x.bits,x.samples,model,seed,x.p,x.fault_at));print(f)
    (x.out/'manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
if __name__=='__main__':main()
