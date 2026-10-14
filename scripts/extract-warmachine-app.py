"""Read the locally installed Warmachine App cache; never modify it or persist keys."""
import argparse, hashlib, io, json, os, struct, sys, zlib
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.decrepit.ciphers import modes

VERSION='1.0.0'
MAX_PAYLOAD=128*1024*1024

def exact(s,n):
    if n<0 or n>MAX_PAYLOAD: raise ValueError('Invalid field length')
    b=s.read(n)
    if len(b)!=n: raise ValueError('Truncated bundle')
    return b

def integer(s): return struct.unpack('<i',exact(s,4))[0]

def string(s):
    n=0
    for shift in range(0,35,7):
        b=exact(s,1)[0];n|=(b&127)<<shift
        if not b&128: return exact(s,n).decode('utf8')
    raise ValueError('Invalid string prefix')

def decode(data,password=None):
    s=io.BytesIO(data);version=integer(s);name=string(s);kind=integer(s)
    flags=exact(s,2)
    if any(b not in (0,1) for b in flags): raise ValueError('Invalid flags')
    compressed,encrypted=flags
    count=integer(s)
    if not 0<=count<=100000: raise ValueError('Invalid GUID count')
    for _ in range(count): string(s)
    payload=exact(s,integer(s))
    if s.read(1): raise ValueError('Unexpected trailing bundle bytes')
    if encrypted:
        if not password: raise ValueError('Local public profile key is unavailable')
        salt_len=len(b'DETERMINISTIC_SALT_FOR_TESTING_12345678')
        if len(payload)<salt_len: raise ValueError('Truncated encrypted payload')
        key=hashlib.pbkdf2_hmac('sha1',password,payload[:salt_len],50000,48)
        dec=Cipher(algorithms.AES(key[:32]),modes.CFB(key[32:])).decryptor()
        payload=dec.update(payload[salt_len:])+dec.finalize()
        pad=payload[-1] if payload else 0
        if not 1<=pad<=16 or payload[-pad:]!=bytes([pad])*pad: raise ValueError('Invalid encrypted padding')
        payload=payload[:-pad]
    if compressed:
        d=zlib.decompressobj(-zlib.MAX_WBITS);payload=d.decompress(payload,MAX_PAYLOAD+1)
        if len(payload)>MAX_PAYLOAD or not d.eof or d.unused_data: raise ValueError('Invalid or oversized deflate stream')
    parsed=json.loads(payload)
    if not isinstance(parsed,dict): raise ValueError('Bundle JSON must be an object')
    return payload,{'version':version,'name':name,'type':kind,'compressed':bool(compressed),'encrypted':bool(encrypted),'guidCount':count}

def local_key():
    import winreg
    candidates=[]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Privateer Press\Warmachine App') as key:
        for i in range(winreg.QueryInfoKey(key)[1]):
            name,value,_=winreg.EnumValue(key,i)
            if not name.startswith('Profiles_'): continue
            if isinstance(value,bytes):value=value.decode('utf8').rstrip('\0')
            for profile in json.loads(value).get('profiles',[]):
                secret=profile.get('dataSources',{}).get('publicDataSource',{}).get('encryptionKey')
                if secret:candidates.append((secret.encode('utf8'),profile.get('profileName'),profile.get('dataVersion')))
    if len({v[0] for v in candidates})!=1: raise ValueError('Missing or ambiguous public profile key')
    return candidates[0]

def digest(b):return hashlib.sha256(b).hexdigest()
def writejson(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def extract(app,output):
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from app_paths import public_cache
    cache=public_cache(app);sources=sorted(cache.glob('*.bundle'))
    if not sources:raise ValueError('No local .bundle files found')
    output.mkdir(parents=True,exist_ok=False)
    bundles=output/'bundles';bundles.mkdir();forces=output/'forces';forces.mkdir()
    password,profile,data_version=local_key()
    records=[];errors=[]
    inputs=sources+sorted(app.glob('force-*.json'))+[p for p in [cache/'bundle.index',cache/'bundleManifest.json'] if p.exists()]
    initial={p: digest(p.read_bytes()) for p in inputs}
    try:
        for p in inputs:
            raw=p.read_bytes()
            if digest(raw)!=initial[p]:raise ValueError('Source changed during extraction')
            if p.suffix=='.bundle':
                try:
                    payload,header=decode(raw,password);dest=bundles/p.with_suffix('.json').name;dest.write_bytes(payload)
                    records.append({'sourceFile':p.name,'outputFile':str(dest.relative_to(output)),'sourceSha256':digest(raw),'jsonSha256':digest(payload),'sourceBytes':len(raw),'jsonBytes':len(payload),'header':header})
                except Exception as e:
                    # No key or decrypted contents in exceptions/logs.
                    errors.append({'sourceFile':p.name,'errorType':type(e).__name__})
            elif p.name.startswith('force-'):
                json.loads(raw);(forces/p.name).write_bytes(raw)
            else:
                # Only known public manifests; never copy registry/account data.
                json.loads(raw);(output/p.name).write_bytes(raw)
        changed=[p.name for p in inputs if not p.exists() or digest(p.read_bytes())!=initial[p]]
        current=set(cache.glob('*.bundle'))|set(app.glob('force-*.json'))
        expected=set(sources)|set(p for p in inputs if p.name.startswith('force-'))
        stable=not changed and current==expected
        report={'schemaVersion':1,'extractorVersion':VERSION,'extractedAt':datetime.now(timezone.utc).isoformat(),'sourceDirectory':str(cache),'sourceProfile':profile,'sourceDataVersion':data_version,'encryptionKeyPersisted':False,'complete':not errors and stable,'stableSnapshot':stable,'bundleCount':len(records),'expectedBundles':len(sources),'forceCount':len(list(forces.glob('*.json'))),'files':records,'errors':errors,'changedSources':changed}
        writejson(output/'extraction-manifest.json',report)
        return report
    finally:password=None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-data',type=Path,default=Path(os.environ.get('USERPROFILE',str(Path.home())))/'AppData/LocalLow/Privateer Press/Warmachine App')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    output=args.output or Path(__file__).resolve().parents[1]/'output/warmachine-app/snapshots'/datetime.now().strftime('%Y%m%d-%H%M%S')
    report=extract(args.app_data,output)
    print(json.dumps({'output':str(output),'bundles':report['bundleCount'],'lists':report['forceCount'],'complete':report['complete'],'errors':report['errors']}))
    return 0 if report['complete'] else 2

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('Extraction failed: '+type(e).__name__,file=sys.stderr);sys.exit(2)
