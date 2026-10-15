import unittest,tempfile,importlib.util,re
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('renderer',ROOT/'render-cards.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LongRulesTest(unittest.TestCase):
 def test_every_word_survives_pagination(self):
  tokens=[f'word{i:04d}' for i in range(900)]
  card={'name':'Test long rule','instanceId':'test','abilities':[{'name':'Long ability','description':' '.join(tokens)}],'models':[],'spells':[],'feat':{'name':''},'options':[],'faction':'Test','type':'Test'}
  with tempfile.TemporaryDirectory() as tmp:
   r=m.Renderer(Path(tmp),Path(tmp));r.rules(card);r.save()
   text=' '.join(p.extract_text() for p in PdfReader(Path(tmp)/'cartas-mpc.pdf').pages)
  self.assertEqual(re.findall(r'word\d{4}',text),tokens)
class SmallDeckExportTest(unittest.TestCase):
 def test_two_page_deck_exports_paired_images(self):
  import subprocess,sys,json
  from reportlab.pdfgen import canvas
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);c=canvas.Canvas(str(root/'cartas-mpc.pdf'),pagesize=(431.28,269.28))
   for i in range(2):c.drawString(30,220,'Test');c.showPage()
   c.save();(root/'print-manifest.json').write_text(json.dumps({'pages':[{'page':1},{'page':2}]}))
   subprocess.run([sys.executable,str(ROOT/'export-cards.py'),str(root)],check=True,capture_output=True)
   self.assertTrue((root/'mpc/001-front.png').exists());self.assertTrue((root/'mpc/001-back.png').exists());self.assertTrue((root/'cartas-mpc.zip').exists())
if __name__=='__main__':unittest.main()

class ArmyRulesRenderTest(unittest.TestCase):
 def test_army_without_models_renders_complete_rules_and_pairs(self):
  card={'name':'Army reference','instanceId':'army','type':'Army','faction':'Test','isArmyRules':True,'portrait':None,'models':[],'abilities':[{'name':'Army rule','description':'Unique complete army rule.'}],'feat':{'name':''},'spells':[],'options':[]}
  with tempfile.TemporaryDirectory() as tmp:
   r=m.Renderer(Path(tmp),Path(tmp));r.front(card);r.rules(card);r.save()
   pdf=PdfReader(Path(tmp)/'cartas-mpc.pdf');text=' '.join(p.extract_text() for p in pdf.pages)
   self.assertEqual(len(pdf.pages)%2,0);self.assertIn('Unique complete army rule.',text)
   self.assertNotIn('SPD',pdf.pages[0].extract_text());self.assertNotIn('COMMAND CARD',text)
