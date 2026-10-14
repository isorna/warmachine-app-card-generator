import importlib.util,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('selector',ROOT/'generate-warmachine-cards.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SelectorTests(unittest.TestCase):
 def test_exact_name_or_guid(self):
  a={'force':{'_forceName':'Demo','guidStr':'a'}};b={'force':{'_forceName':'Demo','guidStr':'b'}}
  self.assertIs(m.select_force([a,b],'b'),b)
  with self.assertRaises(ValueError):m.select_force([a,b],'Demo')
 def test_unknown_name(self):
  with self.assertRaises(ValueError):m.select_force([],'x')
 def test_missing_references_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   cards,media,errors=m.materialize({'referencesComplete':False,'issues':[],'instances':[]},{},Path(d),Path(d))
   self.assertTrue(errors);self.assertEqual(cards,[])
 def test_empty_force_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertTrue(m.materialize({'referencesComplete':True,'instances':[]},{},Path(d),Path(d))[2])
class LegacyOptionTests(unittest.TestCase):
 def fixture(self,modular=False):
  force={'instances':[{'cardName':'Fixed','instance':{'guidStr':'i','_cardId':'c','_cardOption1Ids':['old']}}], 'referencesComplete':False,'missingReferences':[{'collection':'cardOptions','guid':'old'}],'issues':[{'type':'optionNotInCardSlot','instanceId':'i','optionId':'old','slot':1}]}
  return force,{'cards':{'c':{'cardOption1Ids':['valid'] if modular else []}},'cardOptions':{}}
 def test_fixed_legacy_matches_app_and_preserves_source(self):
  force,t=self.fixture();out,w=m.normalize_obsolete_options(force,t)
  self.assertEqual(len(w),1);self.assertEqual(out['instances'][0]['instance']['_cardOption1Ids'],[])
  self.assertEqual(force['instances'][0]['instance']['_cardOption1Ids'],['old']);self.assertTrue(out['referencesComplete']);self.assertEqual(out['issues'],[])
 def test_modular_not_repaired(self):
  force,t=self.fixture(True);out,w=m.normalize_obsolete_options(force,t);self.assertEqual(w,[]);self.assertFalse(out['referencesComplete'])
 def test_known_invalid_option_not_discarded(self):
  force,t=self.fixture();t['cardOptions']['old']={};out,w=m.normalize_obsolete_options(force,t);self.assertEqual(w,[]);self.assertTrue(out['issues'])
 def test_multiple_missing_selections_not_guessed(self):
  force,t=self.fixture();force['instances'][0]['instance']['_cardOption1Ids'].append('other');out,w=m.normalize_obsolete_options(force,t);self.assertEqual(w,[])
 def test_defense_components_keep_abilities_separate(self):
  c={'name':'Defenses','models':[{'name':'Defenses','abilities':['general']},{'name':'Powder Keg','abilities':['explosion']}],'damage':{'kind':'none'}}
  items=m.printable_components(c);self.assertEqual(len(items),2);self.assertEqual(items[1]['name'],'Defenses / Powder Keg');self.assertEqual(items[1]['models'][0]['abilities'],['explosion'])
class ComponentDamageTests(unittest.TestCase):
 def card(self,rows):
  return {'name':'Alyce','models':[{'name':'Little Alyce','weapons':[]},{'name':'Big Alyce','weapons':[]}],'damage':{'kind':'tracks','sourceType':'Box Multi','rows':rows}}
 def test_damage_matches_names_not_order(self):
  cards=m.printable_components(self.card([{'name':'Big Alyce','total':8},{'name':'Little Alyce','total':5}]))
  self.assertEqual([c['damage']['total'] for c in cards],[5,8])
 def test_ambiguous_damage_fails(self):
  with self.assertRaises(ValueError):m.printable_components(self.card([{'name':'Alyce','total':5}]))
 def test_unnamed_damage_fails(self):
  with self.assertRaises(ValueError):m.printable_components(self.card([{'name':'','total':5}]))
 def test_all_damage_rows_preserved_in_supplements(self):
  rows=[{'name':str(i),'total':8} for i in range(8)]
  c={'name':'Unit','models':[{'name':'Grunt','weapons':[]}],'damage':{'kind':'tracks','sourceType':'Box Multi','rows':rows,'total':64}}
  cards=m.printable_components(c);self.assertEqual(len(cards),3);self.assertEqual([r for p in cards for r in p['damage']['rows']],rows)
 def test_all_weapons_preserved(self):
  weapons=[{'name':str(i)} for i in range(7)];c={'name':'Jack','models':[{'name':'Jack','weapons':weapons}],'damage':{'kind':'none'}}
  cards=m.printable_components(c);self.assertEqual([w for p in cards for w in p['models'][0]['weapons']],weapons)
class CommandSelectionTests(unittest.TestCase):
 def test_selected_command_materialized_without_model_instances(self):
  c={'guidStr':'cmd','name':['Command'],'description':['Complete rule.'],'metadata':'','commandCardAbilityIds':[],'limitUse':True}
  force={'referencesComplete':True,'instances':[],'force':{'_commandCardIds':['cmd']}}
  with tempfile.TemporaryDirectory() as tmp:
   cards,media,errors=m.materialize(force,{'commandCards':{'cmd':c}},Path(tmp),Path(tmp))
  self.assertEqual(errors,[]);self.assertEqual(len(cards),1);self.assertTrue(cards[0]['isCommand']);self.assertEqual(cards[0]['abilities'][0]['description'],'Complete rule.')
 def test_missing_command_blocks_export(self):
  force={'referencesComplete':True,'instances':[],'force':{'_commandCardIds':['missing']}}
  with tempfile.TemporaryDirectory() as tmp:
   cards,media,errors=m.materialize(force,{},Path(tmp),Path(tmp))
  self.assertEqual(cards,[]);self.assertTrue(errors)
if __name__=='__main__':unittest.main()
