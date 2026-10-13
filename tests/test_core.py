import pathlib,sys,tempfile,unittest,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from core import normalize,run_one
class Tests(unittest.TestCase):
 def test_byte_symbols(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/'a';b=pathlib.Path(d)/'b';a.write_bytes(bytes([0,1,0,1]));normalize(a,1,'byte-per-symbol',4,b);self.assertEqual(b.read_bytes(),a.read_bytes())
 def test_bad_width(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/'a';b=pathlib.Path(d)/'b';a.write_bytes(bytes([0,2]));
   with self.assertRaises(ValueError):normalize(a,1,'byte-per-symbol',2,b)
 def test_packed_4bit(self):
  with tempfile.TemporaryDirectory() as d:
   a=pathlib.Path(d)/'a';b=pathlib.Path(d)/'b';a.write_bytes(bytes([0x12,0xF0]));normalize(a,4,'packed-msb',3,b);self.assertEqual(b.read_bytes(),bytes([1,2,15]))
 def test_generator_repeatable(self):
  sys.path.insert(0,str(ROOT/'scripts'));from generate import generate
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);generate(p/'a',4,1000,'markov',100);generate(p/'b',4,1000,'markov',100);self.assertEqual((p/'a').read_bytes(),(p/'b').read_bytes())
 def test_health_engine(self):
  binary=ROOT/'engine'/('ip4_health.exe' if sys.platform=='win32' else 'ip4_health')
  if not binary.exists():self.skipTest('Compile C engine first')
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'data.bin';p.write_bytes(bytes([0]*16));r=subprocess.run([str(binary),str(p),'1','16','5','8','6'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);j=json.loads(r.stdout);self.assertTrue(j['health_alarm']);self.assertEqual(j['rct_alarms'],1);self.assertEqual(j['apt_alarms'],2)
if __name__=='__main__':unittest.main()
