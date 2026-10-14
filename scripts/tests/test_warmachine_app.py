import hashlib,importlib.util,io,json,struct,sys,unittest,zlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms
from cryptography.hazmat.decrepit.ciphers import modes
ROOT=Path(__file__).resolve().parents[1]
def module(filename,name):
 sp=importlib.util.spec_from_file_location(name,ROOT/filename);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
reader=module('extract-warmachine-app.py','reader');resolver=module('resolve-warmachine-forces.py','resolver')
def bundle(obj,encrypted=False):
 raw=json.dumps(obj).encode();z=zlib.compressobj(wbits=-15);payload=z.compress(raw)+z.flush()
 if encrypted:
  salt=b'X'*39;k=hashlib.pbkdf2_hmac('sha1',b'test-only',salt,50000,48);pad=16-len(payload)%16;payload+=bytes([pad])*pad
  enc=Cipher(algorithms.AES(k[:32]),modes.CFB(k[32:])).encryptor();payload=salt+enc.update(payload)+enc.finalize()
 return struct.pack('<i',1)+b'\x04test'+struct.pack('<i',0)+bytes([1,encrypted])+struct.pack('<ii',0,len(payload))+payload
class TestReader(unittest.TestCase):
 def test_plain(self):self.assertEqual(json.loads(reader.decode(bundle({'cards':[]}))[0]),{'cards':[]})
 def test_encrypted_padding(self):self.assertEqual(json.loads(reader.decode(bundle({'name':'á'},True),b'test-only')[0]),{'name':'á'})
 def test_truncated(self):
  with self.assertRaises(ValueError):reader.decode(bundle({})[:-1])
 def test_wrong_key(self):
  with self.assertRaises((ValueError,zlib.error,UnicodeError)):reader.decode(bundle({},True),b'wrong-key')
 def test_trailing_bytes(self):
  with self.assertRaises(ValueError):reader.decode(bundle({})+b'x')
 def test_recursive_help_and_option_grant(self):
  tables={'cards':{'c':{'guidStr':'c','modelIds':['m']}},'models':{'m':{'guidStr':'m','modelAdvantageIds':['a']}},'modelAdvantages':{'a':{'guidStr':'a','helpTermIds':['h']}},'helpTerms':{'h':{'guidStr':'h','artSegId':'s'}},'articleSegments':{'s':{'guidStr':'s','text':['rule']}},'cardOptions':{'o':{'guidStr':'o','grantedWeaponIds':['w'],'grantedStatAdj':['Model SPD:+1']}},'weapons':{'w':{'guidStr':'w'}}}
  result,missing=resolver.closure(tables,[('cards','c'),('cardOptions','o')]);self.assertFalse(missing);self.assertIn('s',result['articleSegments']);self.assertIn('w',result['weapons']);self.assertEqual(result['cardOptions']['o']['grantedStatAdj'],['Model SPD:+1'])
 def test_missing_reference(self):
  _,missing=resolver.closure({'cards':{'c':{'guidStr':'c','modelIds':['missing']}}},[('cards','c')]);self.assertEqual(missing,[{'collection':'models','guid':'missing'}])
 def test_cycles(self):
  result,missing=resolver.closure({'helpTerms':{'h':{'guidStr':'h','helpTermIds':['h']}}},[('helpTerms','h')]);self.assertFalse(missing);self.assertEqual(len(result['helpTerms']),1)
if __name__=='__main__':unittest.main()
