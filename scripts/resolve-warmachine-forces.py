"""Build an auditable GUID catalog and resolve saved forces without dropping source fields."""
import argparse,collections,json,hashlib
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def name(v):return next((s for s in v.get('name',[]) if s),'')
REFS={'commandCardAbilityIds':'commandCardAbilities','grantedCardIds':'cards','modelIds':'models','weaponIds':'weapons','spellIds':'spells','modelAbilityIds':'modelAbilities','weaponAbilityIds':'weaponAbilities','cardAbilityIds':'cardAbilities','modelAdvantageIds':'modelAdvantages','weaponQualityIds':'weaponQualities','helpTermIds':'helpTerms','articleSegmentIds':'articleSegments','grantedModelIds':'models','grantedWeaponIds':'weapons','grantedSpellIds':'spells','grantedCardAbilityIds':'cardAbilities','grantedModelAbilityIds':'modelAbilities','grantedWeaponAbilityIds':'weaponAbilities','grantedModelAdvantageIds':'modelAdvantages','grantdWeaponQualityIds':'weaponQualities'}

def index(root):
 tables=collections.defaultdict(dict);origins=collections.defaultdict(list);conflicts=[]
 for path in sorted((root/'bundles').glob('*.json')):
  for key,values in read(path).items():
   if not isinstance(values,list):continue
   for v in values:
    if not isinstance(v,dict) or not v.get('guidStr'):continue
    guid=v['guidStr'];prev=tables[key].get(guid)
    if prev is not None and prev!=v:conflicts.append({'collection':key,'guid':guid,'source':path.name})
    tables[key][guid]=v;origins[key+'/'+guid].append(path.name)
 if conflicts:raise ValueError('Conflicting GUID definitions: '+str(len(conflicts)))
 return dict(tables),dict(origins)

def closure(tables,roots):
 found=collections.defaultdict(dict);missing=[];pending=list(roots)
 while pending:
  kind,guid=pending.pop()
  if guid in found[kind]:continue
  v=tables.get(kind,{}).get(guid)
  if v is None:
   if {'collection':kind,'guid':guid} not in missing:missing.append({'collection':kind,'guid':guid})
   continue
  found[kind][guid]=v
  if kind=='helpTerms' and v.get('artSegId'):pending.append(('articleSegments',v['artSegId']))
  for field,target in REFS.items():
   for rid in v.get(field,[]):pending.append((target,rid))
 return dict(found),missing

def resolve(root):
 manifest=read(root/'extraction-manifest.json')
 if not manifest.get('complete'):raise ValueError('Incomplete snapshot')
 for rec in manifest['files']:
  if hashlib.sha256((root/rec['outputFile']).read_bytes()).hexdigest()!=rec['jsonSha256']:raise ValueError('Snapshot integrity mismatch')
 tables,origins=index(root);out=root/'resolved';out.mkdir(exist_ok=True)
 write(out/'catalog.json',{'schemaVersion':1,'collections':tables,'sourceBundles':origins})
 summaries=[]
 for f in sorted((root/'forces').glob('*.json')):
  force=read(f);instances=force['_forceCards'];ids=[v['guidStr'] for v in instances];roots=[];problems=[];selected=[]
  if len(ids)!=len(set(ids)):problems.append({'type':'duplicateInstanceId'})
  for inst in instances:
   cid=inst['_cardId'];roots.append(('cards',cid));card=tables.get('cards',{}).get(cid,{})
   options=[]
   for slot in range(1,7):
    for oid in inst.get(f'_cardOption{slot}Ids',[]):
     roots.append(('cardOptions',oid));options.append({'slot':slot,'id':oid,'definition':tables.get('cardOptions',{}).get(oid)})
     if oid not in card.get(f'cardOption{slot}Ids',[]):problems.append({'type':'optionNotInCardSlot','instanceId':inst['guidStr'],'optionId':oid,'slot':slot})
   for sid in inst.get('_spellCardIds',[]):roots.append(('spellCards',sid))
   for aid in inst.get('_attachedForceCardIds',[]):
    if aid not in ids:problems.append({'type':'missingAttachmentInstance','id':aid})
   selected.append({'instance':inst,'cardName':name(card),'selectedOptions':options,'damageSource':{k:v for k,v in card.items() if k.startswith('health') or k=='forceField'}})
  for cid in force.get('_commandCardIds',[]):roots.append(('commandCards',cid))
  entities,missing=closure(tables,roots)
  doc={'schemaVersion':1,'sourceSnapshot':str(root),'force':force,'instances':selected,'entities':entities,'missingReferences':missing,'issues':problems,'referencesComplete':not missing,'modifiersApplied':False,'printReady':False}
  dest=out/(f.stem+'.resolved.json');write(dest,doc)
  summaries.append({'name':force['_forceName'],'file':dest.name,'instances':len(instances),'selectedOptions':sum(len(x['selectedOptions']) for x in selected),'missingReferences':missing,'issues':problems})
 report={'schemaVersion':1,'snapshot':str(root),'entityCounts':{k:len(v) for k,v in tables.items()},'guidConflicts':0,'forces':summaries,'missingReferenceCount':sum(len(x['missingReferences']) for x in summaries),'issueCount':sum(len(x['issues']) for x in summaries),'scope':'Resolved source graph; selected grants preserved, not yet applied to print statistics. Damage topology preserved raw; not inferred.'}
 write(out/'validation-report.json',report)
 print(json.dumps({'catalogCards':len(tables.get('cards',{})),'forces':len(summaries),'instances':sum(x['instances'] for x in summaries),'selectedOptions':sum(x['selectedOptions'] for x in summaries),'missingReferences':report['missingReferenceCount'],'issues':report['issueCount'],'output':str(out)}))
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);a=p.parse_args();r=resolve(a.snapshot);raise SystemExit(2 if r['missingReferenceCount'] or r['issueCount'] else 0)
