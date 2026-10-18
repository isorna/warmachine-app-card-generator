"""Materialize current saved-force options for printing; reject unsupported semantics."""
import argparse,copy,hashlib,json,re,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from app_paths import public_cache

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def loc(v):return next((x for x in v if x),'') if isinstance(v,list) else str(v or '')
def clean(v):
 s=re.sub(r'<[^>]+>','',loc(v)).replace('\u2013','-').replace('\u2014','-')
 return re.sub(r'\s+LINK\b', '', s.replace('(LINK)', '')).strip()
def ordered(ids,sorting):
 order={s.split(':',1)[1]:int(s.split(':',1)[0]) for s in sorting if ':' in s}
 return sorted(ids,key=lambda x:order.get(x,9999))
def adjust(value,field,changes):
 value=str(value)
 if value and (value[0].isalpha() or value=='-' or '/' in value or '\\' in value):return value
 valid=bool(re.fullmatch(r'-?\d+',value));n=int(value) if valid else 0
 for ch in changes:
  target,op=ch.split(':',1)
  if target!=field:continue
  if re.fullmatch(r'[+-]\d+',op):n+=int(op)
  elif op.isdigit():n=int(op)
  else:raise ValueError('Unsupported stat adjustment: '+ch)
 return str(n) if valid or n else value

def damage(card):
 typ=card['healthType'];vals=[card.get('healthValue'+str(i),'') for i in range(1,9)]
 out={'sourceType':typ,'sourceValues':vals,'topologyVerified':True}
 if typ=="Don't Display":out['kind']='none'
 elif typ=='Box':out.update(kind='track',total=int(vals[0]),name=clean(card.get('healthName1','')))
 elif typ=='Box Multi':
  rows=[]
  for i,v in enumerate(vals,1):
   if not v or v=='0':continue
   if not str(v).isdigit():raise ValueError('Invalid multi damage value')
   rows.append({'name':clean(card.get('healthName'+str(i),'')) or 'Model '+str(i),'total':int(v),'sourceIndex':i})
  out.update(kind='tracks',rows=rows,total=sum(r['total'] for r in rows))
 elif typ in ['Grid','Grid Large']:
  rows=[v.split(',') for v in vals[:6]]
  columns=12 if typ=='Grid Large' else 6
  if any(len(r)!=columns for r in rows) or any(v.strip() for v in vals[6:]):raise ValueError('Unexpected grid dimensions')
  # Empty/space is an active generic box; '-' is an absent position.
  out.update(kind='grid-large' if typ=='Grid Large' else 'grid',rows=rows,total=sum(v!='-' for r in rows for v in r))
 elif typ in ['Spiral','SpiralLarge','Spiral Large']:
  aspects=[]
  for i,v in enumerate(vals[:3]):
   n=int(v);maxn=14 if typ=='Spiral' else 24
   if not 0<=n<=maxn:raise ValueError('Spiral outside app capacity')
   positions=[(i*2+1,1),(i*2+1,2)]+[(i*2+b,pos) for pos in range(3,14) for b in (1,2)]
   aspects.append({'aspect':'MBS'[i],'total':n,'cells':[{'branch':b,'position':p} for b,p in positions[:n]]})
  out.update(kind='spiral',aspects=aspects,total=sum(x['total'] for x in aspects))
 else:raise ValueError('Unsupported damage type: '+typ)
 return out

class Builder:
 def __init__(self,tables,app,out):self.t=tables;self.app=app;self.out=out;self.media={}
 def entity(self,k,i):
  if i not in self.t.get(k,{}):raise ValueError('Missing '+k+' '+i)
  return self.t[k][i]
 def asset(self,path):
  if not path:return None
  relative=Path(path.lstrip('/\\'));cache=public_cache(self.app);p=(cache/relative).resolve()
  if not p.is_relative_to(cache.resolve()):raise ValueError('Invalid media path')
  if not p.exists():raise ValueError('Missing current media: '+path)
  raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();dest=self.out/'media'/(digest[:16]+p.suffix.lower());dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
  self.media[str(dest.relative_to(self.out))]={'source':str(p),'sha256':digest}
  return str(dest.relative_to(self.out))
 def rule(self,k,i):
  d=self.entity(k,i);description=clean(d.get('description',''))
  if not description:
   pieces=[]
   for hid in d.get('helpTermIds',[]):
    h=self.entity('helpTerms',hid)
    if h.get('artSegId'):pieces.append(clean(self.entity('articleSegments',h['artSegId']).get('body','')))
   description='\n'.join(dict.fromkeys(s for s in pieces if s))
  return {'id':i,'name':loc(d['name']),'description':description,'icon':self.asset(d.get('iconPath',''))}
 def build(self,inst):
  c=self.entity('cards',inst['_cardId']);opts=[]
  if c.get('grantsCardOptToOthersInPlay') and any(inst.get(f'_cardOption{n}Ids') for n in range(1,7)):raise ValueError('Cross-card grants require context')
  for slot in range(1,7):
   ids=inst.get(f'_cardOption{slot}Ids',[])
   for oid in ids:
    if oid not in c.get(f'cardOption{slot}Ids',[]):raise ValueError('Option not valid for slot '+oid)
    opts.append(self.entity('cardOptions',oid))
  grants={}
  for o in opts:
   for k,v in o.items():
    if k.startswith('granted') or k.startswith('grantd'):grants.setdefault(k,[]).extend(v)
  changes=grants.get('grantedStatAdj',[])
  if any(not re.fullmatch(r'(Model|Weapon) [A-Z]+:[+-]?\d+',s) for s in changes):raise ValueError('Unsupported adjustment grammar')
  if inst.get('_spellCardIds'):raise ValueError('Spell rack requires explicit adapter')
  mid=ordered(c['modelIds'],c.get('modelSorting',[]))+grants.get('grantedModelIds',[])
  models=[]
  for mi in mid:
   m=self.entity('models',mi)
   if m.get('metadata') or m.get('healthJson'):raise ValueError('Model metadata/healthJson requires adapter')
   stats={k[4:]:adjust(v,'Model '+k[4:],changes) for k,v in m.items() if k.startswith('stat')}
   adv=[];base=m.get('baseSize','')
   for aid in m['modelAdvantageIds']+grants.get('grantedModelAdvantageIds',[]):
    a=self.entity('modelAdvantages',aid);n=loc(a['name'])
    if re.fullmatch(r'z_\d+mm',n):base=n[2:];continue
    adv.append(self.rule('modelAdvantages',aid))
   weapons=[]
   for wi in ordered(m['weaponIds'],m.get('weaponSorting',[]))+grants.get('grantedWeaponIds',[]):
    w=self.entity('weapons',wi)
    if w.get('metadata'):raise ValueError('Weapon metadata requires adapter')
    weapons.append({'id':wi,'name':loc(w['name']),'type':w['weaponType'],'quantity':w.get('weaponCount',1),'location':w.get('weaponLocation',''),'statistics':{k[4:]:adjust(v,'Weapon '+k[4:],changes) for k,v in w.items() if k.startswith('stat')},'qualities':[self.rule('weaponQualities',q) for q in w['weaponQualityIds']+grants.get('grantdWeaponQualityIds',[])],'abilities':[self.rule('weaponAbilities',a) for a in ordered(w['weaponAbilityIds'],w.get('weaponAbilitySorting',[]))+grants.get('grantedWeaponAbilityIds',[])]})
   models.append({'id':mi,'name':loc(m['name']),'portrait':self.asset(m.get('portraitPath','')),'statistics':stats,'baseSize':base,'advantages':adv,'abilities':[self.rule('modelAbilities',a) for a in ordered(m['modelAbilityIds'],m.get('modelAbilitySorting',[]))+grants.get('grantedModelAbilityIds',[])],'weapons':weapons})
  spells=[]
  for sid in ordered(c['spellIds'],c.get('spellSorting',[]))+grants.get('grantedSpellIds',[]):
   s=self.entity('spells',sid);spells.append({'id':sid,'name':loc(s['name']),'description':clean(s['description']),'statistics':{k[4:]:v for k,v in s.items() if k.startswith('stat')}})
  costs=[c['pointCost']]+[o['pointCost'] for o in opts];points=str(sum(int(x or 0) for x in costs)) if any(costs) and all(not x or re.fullmatch(r'\d+',x) for x in costs) else (' + '.join(x for x in costs if x) or '-')
  portrait=c['portraitPath']
  for o in opts:
   if o.get('changeMainPortrait') and o.get('portraitPath'):portrait=o['portraitPath']
  return {'sourceCardId':c['guidStr'],'instanceId':inst['guidStr'],'name':loc(c['name']),'type':loc(self.entity('cardTypes',c['cardTypeId'])['name']),'faction':loc(self.entity('factions',c['factionId'])['name']),'portrait':self.asset(portrait),'fieldAllowance':c['fieldAllowance'],'points':points,'pointCostSources':costs,'options':[{'id':o['guidStr'],'name':loc(o['name'])} for o in opts],'statAdjustments':changes,'models':models,'damage':damage(c),'abilities':[self.rule('cardAbilities',a) for a in ordered(c['cardAbilityIds'],c.get('cardAbilitySorting',[]))+grants.get('grantedCardAbilityIds',[])],'spells':spells,'feat':{'name':loc(c['featName']),'description':clean(c['featDescription'])},'modifiersApplied':True}
