import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pilot',ROOT/'build-print-profiles.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PilotTests(unittest.TestCase):
 def test_original_spiral_layout(self):
  import json
  layout=json.loads((ROOT/'assets/spiral-layout.json').read_text())['branches']
  self.assertEqual(sum(v is not None for branch in layout.values() for v in branch),42)
  d=m.damage({'healthType':'Spiral','healthValue1':'8','healthValue2':'12','healthValue3':'10'})
  points=[tuple(layout[str(c['branch'])][c['position']-1]) for a in d['aspects'] for c in a['cells']]
  self.assertEqual(len(set(points)),30)
  self.assertEqual(layout['1'][0],[565,524])
 def test_adjustment_order(self):self.assertEqual(m.adjust('4','Model SPD',['Model SPD:+2','Model SPD:8','Model SPD:-1']),'7')
 def test_special_stats(self):
  for value in ['-','SP 8','2/3']:self.assertEqual(m.adjust(value,'Weapon RNG',['Weapon RNG:+2']),value)
 def test_grid_spaces_are_boxes(self):
  card={'healthType':'Grid',**{'healthValue'+str(i):' ,-,L,-,,-' for i in range(1,7)}}
  self.assertEqual(m.damage(card)['total'],18)
 def test_spiral_odd_distribution(self):
  d=m.damage({'healthType':'Spiral','healthValue1':'5','healthValue2':'8','healthValue3':'8'})
  self.assertEqual(d['total'],21);self.assertEqual([(c['branch'],c['position']) for c in d['aspects'][0]['cells']],[(1,1),(1,2),(1,3),(2,3),(1,4)])
 def test_reject_unknown_damage(self):
  with self.assertRaises(ValueError):m.damage({'healthType':'unknown'})
 def test_clean_navigation_only(self):self.assertEqual(m.clean('<b>Rule</b> (LINK) ★Attack'),'Rule  ★Attack')
class MultiDamageTests(unittest.TestCase):
 def test_named_tracks(self):
  c={'healthType':'Box Multi','healthValue1':'8','healthValue2':'8','healthValue3':'8','healthName1':['Anathan'], 'healthName2':['Dogreth'],'healthName3':['Valak']}
  d=m.damage(c);self.assertEqual(d['total'],24);self.assertEqual([r['total'] for r in d['rows']],[8,8,8]);self.assertEqual(d['rows'][1]['name'],'Dogreth')
 def test_empty_tracks_not_printed(self):
  d=m.damage({'healthType':'Box Multi','healthValue1':'5','healthValue2':'0','healthValue3':''});self.assertEqual(len(d['rows']),1)
class LargeSpiralTests(unittest.TestCase):
 def test_original_large_spiral_geometry_and_totals(self):
  import json
  layout=json.loads((ROOT/'assets/spiral-large-layout.json').read_text())['branches']
  self.assertEqual(sum(c is not None for b in layout.values() for c in b),72)
  d=m.damage({'healthType':'Spiral Large','healthValue1':'13','healthValue2':'24','healthValue3':'19'})
  self.assertEqual(d['total'],56)
  coords=[layout[str(c['branch'])][c['position']-1] for a in d['aspects'] for c in a['cells']]
  self.assertTrue(all(p is not None for p in coords));self.assertEqual(len(coords),56)
  self.assertTrue(all(0<=v<=1024 for p in coords for v in p))
 def test_large_spiral_capacity_rejected(self):
  with self.assertRaises(ValueError):m.damage({'healthType':'Spiral Large','healthValue1':'25','healthValue2':'24','healthValue3':'19'})
if __name__=='__main__':unittest.main()
