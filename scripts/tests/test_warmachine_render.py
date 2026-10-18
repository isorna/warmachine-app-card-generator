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

class LargeGridRenderTest(unittest.TestCase):
 def test_two_numbered_halves_and_system_positions(self):
  from unittest.mock import patch
  rows=[['-']*12 for _ in range(6)];rows[0][0]=' ';rows[3][6]='I';rows[5][11]='R'
  with tempfile.TemporaryDirectory() as tmp:
   r=m.Renderer(Path(tmp),Path(tmp))
   with patch.object(r,'rect') as rect,patch.object(r,'text') as text:
    r.health({'kind':'grid-large','total':3,'rows':rows},21,151,108)
    cells=[call.args[:4] for call in rect.call_args_list if call.args[2:4]==(7,7)]
    self.assertEqual(cells,[(21,185,7,7),(80,209,7,7),(120,225,7,7)])
    labels=[call.args[2] for call in text.call_args_list]
    self.assertEqual([v for v in labels if isinstance(v,int)],[1,2,3,4,5,6]*2)
    self.assertIn('IZQUIERDA',labels);self.assertIn('DERECHA',labels)

class WebGeometryTests(unittest.TestCase):
 def test_original_ring_positions_and_no_overlapping_cells(self):
  import math
  for typ,counts,ys in [('Web',[12,8,4],[34,431,201]),('Web Large',[30,16,10],[34,436,198]),('Web',[7,5,2],[34,431,201])]:
   d={'sourceType':typ,'rings':[{'ring':label,'total':n} for label,n in zip('OMI',counts)]}
   rings=m.web_geometry(d);cells=[c for r in rings for c in r['cells']]
   self.assertEqual(len(cells),sum(counts))
   for r,y,n in zip(rings,ys,counts):
    self.assertEqual(r['cells'][0][:2],(275,y));self.assertEqual(len(r['cells']),n)
   for i,(x,y,r) in enumerate(cells):
    self.assertTrue(r<=x<=550-r and r<=y<=550-r)
    for xx,yy,rr in cells[i+1:]:self.assertGreater(math.hypot(x-xx,y-yy),r+rr)
 def test_zero_ring_has_no_cells(self):
  rings=m.web_geometry({'sourceType':'Web','rings':[{'ring':l,'total':n} for l,n in zip('OMI',[1,0,1])]})
  self.assertEqual(rings[1]['cells'],[])
