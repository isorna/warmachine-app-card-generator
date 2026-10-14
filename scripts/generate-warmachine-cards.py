"""Select a saved force, materialize all its profiles and export paired MPC faces."""
import argparse,datetime,importlib.util,json,re,subprocess,sys,tempfile,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from app_paths import resolve_paths, public_cache
from prepare_assets import prepare_assets

def module(name,file):
 spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run(script,*args,allowed=(0,)):
 result=subprocess.run([sys.executable,str(HERE/script),*map(str,args)])
 if result.returncode not in allowed:raise RuntimeError(f'{script}: error {result.returncode}')

def select_force(forces,choice):
 matches=[f for f in forces if choice in (f['force']['guidStr'],f['force']['_forceName'])]
 if len(matches)!=1:raise ValueError('Nombre inexistente o duplicado: utiliza el GUID de la lista.')
 return matches[0]

def normalize_obsolete_options(force,tables):
 import copy
 force=copy.deepcopy(force);warnings=[];ignored=set();pairs=set()
 for row in force['instances']:
  inst=row['instance'];card=tables['cards'].get(inst['_cardId'],{})
  # Only a fixed current card with no selectable slots. Do not repair modular cards.
  if not card or any(card.get(f'cardOption{n}Ids') for n in range(1,7)):continue
  for n in range(1,7):
   key=f'_cardOption{n}Ids';ids=inst.get(key,[])
   # One unresolved legacy selection per slot: app First() throws, getter catches.
   if len(ids)==1 and ids[0] not in tables.get('cardOptions',{}):
    oid=ids[0];inst[key]=[];ignored.add(oid);pairs.add((inst['guidStr'],oid,n))
    warnings.append({'profile':row['cardName'],'instance':inst['guidStr'],'slot':n,'optionId':oid,'reason':'Referencia antigua ausente en perfil fijo; omitida como en la app actual'})
 force['missingReferences']=[r for r in force.get('missingReferences',[]) if not (r['collection']=='cardOptions' and r['guid'] in ignored)]
 force['issues']=[r for r in force.get('issues',[]) if not (r.get('type')=='optionNotInCardSlot' and (r.get('instanceId'),r.get('optionId'),r.get('slot')) in pairs)]
 force['referencesComplete']=not force['missingReferences']
 return force,warnings

def name_tokens(name):
 import re
 return set(x for x in re.findall(r"[^\W\d_]+",name.casefold()) if x not in ['s','damage'])

def printable_components(card):
 import copy,math
 if not card['models']:raise ValueError('Perfil sin modelos')
 result=[];multi=len(card['models'])>1
 damage=card['damage'];assignments={i:[] for i in range(len(card['models']))}
 if multi and damage['kind']!='none':
  if damage['kind']=='track':rows=[{'name':damage.get('name',''),'total':damage['total']}]
  elif damage['kind']=='tracks':rows=damage['rows']
  else:raise ValueError('Varios modelos con daño no nominal: requiere adaptador')
  for row in rows:
   tokens=name_tokens(row['name'])
   matches=[i for i,m in enumerate(card['models']) if tokens and tokens<=name_tokens(m['name'])]
   if len(matches)!=1:raise ValueError('Fila de daño ambigua: '+row['name'])
   assignments[matches[0]].append(row)
 for i,model in enumerate(card['models']):
  item=copy.deepcopy(card);item['models']=[copy.deepcopy(model)]
  if multi:
   item['componentIndex']=i+1;item['groupName']=card['name']
   item['name']=card['name'] if model['name']==card['name'] else card['name']+' / '+model['name']
   if model.get('portrait'):item['portrait']=model['portrait']
   rows=assignments[i]
   item['damage']={'kind':'tracks','rows':rows,'total':sum(r['total'] for r in rows),'sourceType':damage['sourceType']} if rows else {'kind':'none','sourceType':"Don't Display"}
  # Supplemental fronts preserve every weapon / health row at readable size.
  weapons=model.get('weapons',[]);rows=item['damage'].get('rows',[]) if item['damage']['kind']=='tracks' else []
  count=max(1,math.ceil(len(weapons)/3),math.ceil(len(rows)/3))
  for j in range(count):
   part=copy.deepcopy(item)
   if count>1:
    part['name']+=f' / {j+1}-{count}';part['supplementIndex']=j+1
    part['models'][0]['weapons']=weapons[j*3:(j+1)*3]
    if rows:
     selected=rows[j*3:(j+1)*3];part['damage']=dict(item['damage'],rows=selected,total=sum(r['total'] for r in selected)) if selected else {'kind':'none','sourceType':"Don't Display"}
   result.append(part)
 return result

def command_profile(builder,oid):
 b=module('wm_command_helpers','build-print-profiles.py');c=builder.entity('commandCards',oid)
 if c.get('metadata'):raise ValueError('Command metadata no soportado')
 rules=[]
 if b.clean(c.get('description')):rules.append({'name':b.loc(c['name']),'description':b.clean(c['description'])})
 rules.extend(builder.rule('commandCardAbilities',aid) for aid in b.ordered(c['commandCardAbilityIds'],c.get('commandCardAbilitySorting',[])))
 rules.extend(builder.rule('modelAdvantages',aid) for aid in c.get('modelAdvantageIds',[]))
 rules.extend(builder.rule('weaponQualities',aid) for aid in c.get('weaponQualityIds',[]))
 granted=[{'id':gid,'name':b.loc(builder.entity('cards',gid)['name'])} for gid in c.get('grantedCardIds',[])]
 return {'sourceCardId':oid,'instanceId':'command-'+oid,'name':b.loc(c['name']),'type':'Command Card','faction':'COMMAND','points':c.get('pointCost') or '-','fieldAllowance':'-','portrait':builder.asset(c.get('mediaPath','')),'models':[],'damage':{'kind':'none'},'abilities':rules,'spells':[],'feat':{'name':'','description':''},'options':[],'limitUse':c['limitUse'],'grantedCards':granted,'grantedCardCount':c.get('grantedCardCount',''),'isCommand':True}

def materialize(force,tables,app,out):
 builder=module('wm_builder','build-print-profiles.py').Builder(tables,app,out)
 cards=[];errors=[]
 if not force.get('referencesComplete') or force.get('issues'):errors.append({'profile':'Lista','reason':'Referencias incompletas o incidencias en el snapshot','details':force.get('missingReferences',[])})
 for row in force['instances']:
  try:
   card=builder.build(row['instance'])
   if not card['portrait']:raise ValueError('Falta imagen del perfil')
   cards.extend(printable_components(card))
  except (ValueError,KeyError,TypeError) as e:errors.append({'profile':row.get('cardName','?'),'instance':row['instance']['guidStr'],'reason':str(e)})
 for oid in force.get('force',{}).get('_commandCardIds',[]):
  try:cards.append(command_profile(builder,oid))
  except (ValueError,KeyError,TypeError) as e:errors.append({'profile':'Command '+oid,'reason':str(e)})
 if not cards and not errors:errors.append({'profile':'Lista','reason':'Lista vacia'})
 return cards,builder.media,errors

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--snapshot',type=Path,help='Reutilizar snapshot; por defecto actualizar desde la app')
 p.add_argument('--force',help='Nombre exacto o GUID; omitir para selector interactivo')
 p.add_argument('--list',action='store_true');p.add_argument('--check-all',action='store_true')
 p.add_argument('--app-data',type=Path)
 p.add_argument('--app-install',type=Path)
 p.add_argument('--configure',action='store_true',help='Detectar, validar y guardar rutas locales')
 p.add_argument('--doctor',action='store_true',help='Comprobar rutas, clave local y recursos sin exportar listas')
 p.add_argument('--output-root',type=Path,default=HERE.parent/'output/warmachine-app/cards')

 a=p.parse_args()
 install,a.app_data=resolve_paths(a.app_install,a.app_data,a.configure)
 print('Instalacion:',install);print('Datos:',a.app_data)
 if a.configure:return 0
 if a.doctor:
  module('wm_reader','extract-warmachine-app.py').local_key()
  prepare_assets(install,HERE.parent/'.local/assets')
  print('OK: rutas, cache, clave local y espirales disponibles. Listas:',len(list(a.app_data.glob('force-*.json'))))
  return 0
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 snapshot=a.snapshot
 if snapshot is None:
  snapshot=HERE.parent/'output/warmachine-app/snapshots'/stamp
  run('extract-warmachine-app.py','--app-data',a.app_data,'--output',snapshot)
  run('resolve-warmachine-forces.py',snapshot,allowed=(0,2))
 resolved=snapshot/'resolved';read=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
 tables=read(resolved/'catalog.json')['collections'];forces=[read(f) for f in sorted(resolved.glob('force-*.resolved.json'))]
 if not forces:raise ValueError('No hay listas guardadas en este snapshot')
 if a.list or not a.force and not a.check_all:
  for i,f in enumerate(forces,1):
   effective,notices=normalize_obsolete_options(f,tables)
   status=' [referencias pendientes]' if not effective['referencesComplete'] or effective.get('issues') else (' [avisos de opciones antiguas]' if notices else '')
   print(f"{i:2}. {f['force']['_forceName']} ({len(f['instances'])} perfiles)"+status)
 if a.list:return 0
 a.output_root.mkdir(parents=True,exist_ok=True)
 if a.check_all:
  report=[]
  for f in forces:
   f,warnings=normalize_obsolete_options(f,tables)
   with tempfile.TemporaryDirectory() as temp:
    cards,media,errors=materialize(f,tables,a.app_data,Path(temp))
    report.append({'name':f['force']['_forceName'],'profiles':len(f['instances']),'materializable':not errors,'errors':errors})
  target=a.output_root/('compatibility-'+stamp+'.json');target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
  for r in report:print(r['name'],':','DATOS OK (maquetacion pendiente)' if r['materializable'] else '; '.join(e['profile']+': '+e['reason'] for e in r['errors']))
  print('Informe:',target);return 0
 if a.force:force=select_force(forces,a.force)
 else:
  while True:
   value=input('Numero de lista (0 para salir): ').strip()
   if value=='0':return 0
   if value.isdigit() and 1<=int(value)<=len(forces):force=forces[int(value)-1];break
   print('Selecciona uno de los numeros mostrados.')
 force,warnings=normalize_obsolete_options(force,tables)
 for warning in warnings:print('AVISO: '+warning['profile']+': '+warning['reason']+' (slot '+str(warning['slot'])+')')
 name=force['force']['_forceName'];slug=re.sub(r'[^\w-]+','-',name).strip('-') or 'lista';out=a.output_root/(slug+'-'+stamp);out.mkdir()
 with tempfile.TemporaryDirectory(prefix='wm-cards-',dir=a.output_root) as temp:
  staging=Path(temp);cards,media,errors=materialize(force,tables,a.app_data,staging)
  if errors:
   (out/'errores.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf8')
   for e in errors:print(e['profile']+': '+e['reason'])
   print('No se ha exportado la lista. Informe:',out/'errores.json');return 2
  payload={'warnings':warnings,'schemaVersion':1,'snapshot':str(snapshot),'forceName':name,'forceId':force['force']['guidStr'],'cards':cards,'scope':'saved force profiles and selected command cards'}
  (staging/'print-profiles.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
  (staging/'media-manifest.json').write_text(json.dumps(media,ensure_ascii=False,indent=2),encoding='utf8')
  try:
   asset_dir=prepare_assets(install,HERE.parent/'.local/assets')
   os.environ['WARMACHINE_ASSETS']=str(asset_dir)
   run('render-cards.py',staging,'--output',staging)
   run('export-cards.py',staging)
  except Exception as e:
   (out/'errores.json').write_text(json.dumps({'stage':'render/export','reason':str(e)},indent=2));print('No se ha exportado la lista. Informe:',out/'errores.json');return 2
  import shutil
  for item in staging.iterdir():shutil.move(str(item),str(out/item.name))
  (out/'avisos.json').write_text(json.dumps(warnings,ensure_ascii=False,indent=2),encoding='utf8')
  (out/'resultado.json').write_text(json.dumps({'force':name,'snapshot':str(snapshot),'profiles':len(cards),'commandCardsIncluded':len(force['force'].get('_commandCardIds',[])),'pdf':'cartas-mpc.pdf','zip':'cartas-mpc.zip'},ensure_ascii=False,indent=2),encoding='utf8')
 print('Cartas generadas:',out);print('PDF: cartas-mpc.pdf | MPC: cartas-mpc.zip')
 if force['force'].get('_commandCardIds'):print('Command cards seleccionadas incluidas.')
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,RuntimeError,OSError) as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
