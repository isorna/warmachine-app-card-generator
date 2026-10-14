"""Render validated profiles with the approved MPC layout; one image per face."""
import argparse,html,json,math,re,os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,white,Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader,PdfWriter
from pypdf.generic import RectangleObject
W,H=431.28,269.28
FONT_DIR=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
pdfmetrics.registerFont(TTFont('Symbols',str(FONT_DIR/'seguisym.ttf')))
for n,f in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(n,str(FONT_DIR/f)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
INK=HexColor('#23272a');RED=HexColor('#742d35');GOLD=HexColor('#bda473');PAPER=HexColor('#f6f3eb');LIGHT=HexColor('#e6e0d3');MUTED=HexColor('#66635e')
FACTION_THEMES=json.loads((Path(__file__).parent/'assets/faction-palettes.json').read_text(encoding='utf8'))
def faction_theme(name):
 key=re.sub(r'[^a-z0-9]+','-',str(name).lower()).strip('-')
 key=FACTION_THEMES['aliases'].get(key,key)
 return {k:HexColor(v) for k,v in FACTION_THEMES['palettes'].get(key,FACTION_THEMES['palettes'][FACTION_THEMES['fallback']]).items()}
def blend(a,b,t):
 return Color(a.red+(b.red-a.red)*t,a.green+(b.green-a.green)*t,a.blue+(b.blue-a.blue)*t)

def esc(s):return html.escape(str(s)).replace('\n','<br/>').replace('★','<font name="Symbols">★</font>')
class Renderer:
 def __init__(self,root,out):
  self.root=root;self.out=out;self.c=canvas.Canvas(str(out/'cartas-mpc.pdf'),pagesize=(W,H));self.pages=[];self.fonts=[];self.sourceLabel='DATOS APP'
 def rect(self,x,y,w,h,col,stroke=None):
  self.c.setFillColor(col);self.c.setStrokeColor(stroke or col);self.c.setLineWidth(.45);self.c.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))
 def text(self,x,y,s,size=8,font='Body',color=INK):
  self.c.setFillColor(color);self.c.setFont(font,size);self.c.drawString(x,H-y-size*.82,str(s))
 def par(self,s,x,y,w,size=8,draw=True):
  pp=Paragraph(s,ParagraphStyle('body',fontName='Body',fontSize=size,leading=size*1.13,textColor=INK));_,h=pp.wrap(w,1000)
  if draw:pp.drawOn(self.c,x,H-y-h)
  return h
 def icon(self,path,x,y,size=15):
  if path:self.c.drawImage(str(self.root/path),x,H-y-size,size,size,mask='auto')
 def section(self,x,y,title,w):
  self.rect(x,y,w,12,LIGHT);self.text(x+3,y+3,title,6.8,'Bold',RED)
 def header_background(self,hh,theme):
  # Vector gradient and engraved rings stay sharp at any print resolution.
  c=self.c;c.saveState()
  clip=c.beginPath();clip.rect(0,H-hh,W,hh);c.clipPath(clip,stroke=0,fill=0)
  for i in range(160):
   self.rect(i*W/160,0,W/160+.1,hh,blend(theme['start'],theme['end'],i/159))
  c.setStrokeColor(blend(theme['end'],theme['muted'],.18));c.setLineWidth(.5)
  cx,cy=W-39,H-hh/2
  for radius in [20,25,40,44,59,64,80,84]:c.circle(cx,cy,radius,stroke=1,fill=0)
  for i in range(24):
   a=i*math.pi/12
   c.line(cx+65*math.cos(a),cy+65*math.sin(a),cx+78*math.cos(a),cy+78*math.sin(a))
  c.setStrokeColor(blend(theme['end'],theme['muted'],.10));c.setLineWidth(.35)
  for x in range(-50,450,24):c.line(x,H,x+hh,H-hh)
  c.restoreState()
 def header(self,p,label,front=False):
  theme=faction_theme(p.get('faction','General'))
  self.rect(0,0,W,H,PAPER);self.rect(0,0,8.64,H,theme['end']);hh=49 if front else 34;self.header_background(hh,theme);self.rect(0,hh,W,1.6,GOLD)
  size=14 if front else 11
  while pdfmetrics.stringWidth(p['name'].upper(),'Bold',size)>389 and size>8:size-=.25
  self.text(21,18,p['name'].upper(),size,'Bold',theme['text'])
  if front:self.text(21,38,p['faction'].upper()+' / '+p['type'].upper(),6.5,'Bold',theme['muted'])
  self.text(21,245,self.sourceLabel,5.3,'Bold',MUTED);self.text(260,245,label,5.3,'Bold',MUTED)
 def finish(self,p,kind):
  self.pages.append({'page':len(self.pages)+1,'profile':p['name'],'instanceId':p['instanceId'],'kind':kind});self.c.showPage()
 def health(self,d,x,y,w):
  if d['kind']=='none':
   self.section(x,y,'DAÑO',w);self.text(x,y+16,'Sin track en el perfil de origen',6.3,color=MUTED);return
  self.section(x,y,('ESPIRAL' if d['kind']=='spiral' else 'DAÑO')+' / '+str(d['total']),w)
  if d['kind']=='track':
   for i in range(d['total']):self.rect(x+(i%10)*10.5,y+17+(i//10)*11,8,8,white,INK)
  elif d['kind']=='tracks':
   if len(d['rows'])>3 or any(r['total']>10 for r in d['rows']):raise ValueError('Multi damage needs larger layout')
   for j,row in enumerate(d['rows']):
    yy=y+14+j*17
    self.text(x,yy,row['name'],5.7,'Bold')
    for i in range(row['total']):self.rect(x+i*10.5,yy+7,7,6,white,INK)
  elif d['kind']=='grid':
   for j in range(6):self.text(x+10+j*14,y+14,j+1,6,'Bold',RED)
   for i,row in enumerate(d['rows']):
    for j,v in enumerate(row):
     if v!='-':
      self.rect(x+8+j*14,y+23+i*6.5,6,6,white,INK)
      if v.strip():self.text(x+9+j*14,y+23.7+i*6.5,v.strip(),4.6,'Bold')
  elif d['kind']=='spiral':
   large=d['sourceType'] in ['SpiralLarge','Spiral Large']
   assets=Path(__file__).parent/'assets'
   geometry=json.loads((assets/('spiral-large-layout.json' if large else 'spiral-layout.json')).read_text());layout=geometry['branches']
   side=78;ox=x+(w-side)/2;oy=y+13;scale=side/1024
   self.c.drawImage(str(Path(os.environ.get('WARMACHINE_ASSETS',str(Path(__file__).resolve().parents[1]/'.local/assets')))/('health_spiral_arms_large_COLOR.png' if large else 'health_spiral_arms_COLOR.png')),ox,H-oy-side,side,side,mask='auto')
   colors=[HexColor('#03465e'),HexColor('#7b1d18'),HexColor('#154c11')]
   for ai,label in enumerate(['M','B','S']):self.text(x+79+ai*9,y+3,label,6,'Bold',colors[ai])
   for ai,aspect in enumerate(d['aspects']):
    for cell in aspect['cells']:
     cx,cy=layout[str(cell['branch'])][cell['position']-1]
     self.c.setFillColor(white);self.c.setStrokeColor(colors[ai]);self.c.setLineWidth(.45)
     radius=geometry['diameters'][str(cell['branch'])][cell['position']-1]*scale/2 if large else 2.65
     self.c.circle(ox+cx*scale,H-oy-cy*scale,radius,fill=1,stroke=1)
   labels=[geometry['labels'][str(i)] for i in range(1,7)] if large else [(145,160),(391,36),(978,324),(976,579),(445,958),(210,807)]
   for n,(cx,cy) in enumerate(labels,1):
    self.text(ox+cx*scale-1.5,oy+cy*scale-2,str(n),5.5,'Bold',colors[(n-1)//2])

 def command_front(self,p):
  self.header(p,'FRENTE',True);self.section(21,60,'COMMAND CARD',389)
  self.text(21,82,'COSTE '+p['points'],10,'Bold')
  self.text(21,105,'USO LIMITADO' if p['limitUse'] else 'USO NO LIMITADO',9,'Bold')
  if p['portrait']:self.c.drawImage(str(self.root/p['portrait']),250,H-84-125,150,125,preserveAspectRatio=True,anchor='c',mask='auto')
  if p['grantedCards']:
   self.section(21,130,'PERFILES CONCEDIDOS / '+str(p['grantedCardCount']),210)
   self.par(' · '.join(esc(g['name']) for g in p['grantedCards']),21,149,210,9)
  self.text(21,229,'Reglas completas en el reverso y suplementos',8,color=MUTED);self.finish(p,'front')
 def front(self,p):
  if p.get('isCommand'):return self.command_front(p)
  if len(p['models'])!=1:raise ValueError('Multi-model layout not yet supported')
  m=p['models'][0];self.header(p,'FRENTE',True)
  keys=['SPD','MAT','RAT','DEF','ARM']+[k for k in ['ARC','AAT','CTRL','FURY','THR','ESS'] if m['statistics'].get(k)]
  cw=389/len(keys)
  for i,k in enumerate(keys):
   x=21+i*cw;self.rect(x,56,cw-2,28,LIGHT);self.text(x+5,59,'CTL' if k=='CTRL' else k,6,'Bold',MUTED);self.text(x+5,69,m['statistics'].get(k) or '-',12,'Bold')
  spiral=p['damage']['kind']=='spiral'
  ph=40 if spiral else 58
  self.c.drawImage(str(self.root/p['portrait']),21,H-90-ph,108,ph,preserveAspectRatio=True,anchor='c',mask='auto')
  iconStep=min(20,106/max(1,len(m['advantages'])))
  for i,a in enumerate(m['advantages']):self.icon(a['icon'],22+i*iconStep,132 if spiral else 149,min(16,iconStep-2))
  self.text(141 if spiral else 21,235 if spiral else 168,('PC CONJUNTO ' if p.get('groupName') else 'PC ')+p['points']+'   FA '+p['fieldAllowance']+'   '+m['baseSize'],7,'Bold')
  self.health(p['damage'],21,151 if spiral else 178,108)
  x=141;ww=269;self.section(x,91,'ARMAS / ATAQUES',ww)
  xx=[x+3,x+119,x+145,x+172,x+198,x+224]
  for pos,label in zip(xx,['ARMA','ATK','RNG','ROF','AOE','POW']):self.text(pos,107,label,5.7,'Bold',MUTED)
  y=118;compact=len(m['weapons'])==3 and bool(p['options'])
  for w in m['weapons']:
   self.rect(x,y,ww,16 if compact else 17,LIGHT);n=w['name']+(' ×'+str(w['quantity']) if w['quantity']>1 else '')
   h=self.par('<b>'+esc(n)+'</b>',xx[0],y+2,110,7 if compact else 7.5);assert h<=17,('weapon title',n)
   atk=m['statistics'].get('MAT' if w['type']=='Melee' else 'RAT','-')
   for pos,val in zip(xx[1:],[atk]+[w['statistics'].get(k) or '-' for k in ['RNG','ROF','AOE','POW']]):self.text(pos+2,y+5,val,8,'Bold')
   y+=17 if compact else 19
   for i,q in enumerate(w['qualities']):self.icon(q['icon'],x+3+i*19,y,12 if compact else 14)
   self.text(x+100,y+4,('MELÉ' if w['type']=='Melee' else 'DISTANCIA')+(' / '+w['location'] if w['location'] else ''),5.5,'Bold',MUTED)
   y+=13 if compact else 17
  if p['options']:
   if compact:
    y+=3;y+=self.par('<b>CONFIG.:</b> '+' · '.join(esc(o['name']) for o in p['options']),x+3,y,ww-6,7.5)
   else:
    self.section(x,y+2,'CONFIGURACIÓN SELECCIONADA',ww);y+=18
    y+=self.par(' · '.join(esc(o['name']) for o in p['options']),x+3,y,ww-6,8)
  if y>235:raise ValueError('Front overflow '+p['name'])
  if not spiral:self.text(x,235,'Reglas e iconos explicados en las caras de referencia',6,color=MUTED)
  self.finish(p,'front')
 def blocks(self,p):
  out=[]
  def group(label,rules):
   if not rules:return
   out.append(('heading',label));out.extend(('rule',r) for r in rules)
  if p['feat']['name']:group('FEAT',[p['feat']])
  group('REGLAS DE COMMAND CARD' if p.get('isCommand') else 'HABILIDADES DEL PERFIL',p['abilities']+[a for m in p['models'] for a in m['abilities']])
  for m in p['models']:
   for w in m['weapons']:group('ARMA / '+w['name'].upper(),w['abilities'])
  if p['spells']:
   out.append(('heading','HECHIZOS' if p['type'] in ['Warlock','Warcaster'] else 'ANIMUS'));out.extend(('spell',s) for s in p['spells'])
  seen=set()
  for label,rules in [('VENTAJAS',[a for m in p['models'] for a in m['advantages']]),('CUALIDADES DE ARMAS',[q for m in p['models'] for w in m['weapons'] for q in w['qualities']])]:
   unique=[]
   for r in rules:
    if r['id'] not in seen:seen.add(r['id']);unique.append(r)
   group(label,unique)
  return out
 def rules(self,p):
  blocks=self.blocks(p);width=189.5;size=8;limit=237
  def height(kind,d):
   if kind=='heading':return 16
   if kind=='spell':return 22+self.par(esc(d['description']),0,0,width,size,False)+5
   text='<b>'+esc(d['name'])+'.</b> '+esc(d['description'])
   return self.par(text,0,0,width-(17 if d.get('icon') else 0),size,False)+6
  expanded=[]
  for kind,d in blocks:
   if kind=='heading' or height(kind,d)<=165:
    expanded.append((kind,d));continue
   words=re.findall(r'\S+\s*',d['description']);chunk='';part=0
   for word in words:
    trial=dict(d,description=chunk+word,name=d['name']+(' (cont.)' if part else ''))
    if chunk and height(kind,trial)>165:
     expanded.append((kind,dict(d,description=chunk.strip(),name=d['name']+(' (cont.)' if part else ''))));part+=1;chunk=word
    else:chunk+=word
   if chunk:expanded.append((kind,dict(d,description=chunk.strip(),name=d['name']+(' (cont.)' if part else ''))))
  blocks=expanded
  pages=[];page=[];col=0;y=42;category=None
  for i,(kind,d) in enumerate(blocks):
   h=height(kind,d);need=h+(height(*blocks[i+1]) if kind=='heading' and i+1<len(blocks) else 0)
   if need>195:raise ValueError('Rule block too tall: '+str(d))
   if y+need>limit:
    col+=1;y=42
    if col==2:pages.append(page);page=[];col=0
    if kind!='heading' and category:
     page.append(('heading',category+' / CONT.',col,y));y+=16
   if kind=='heading':category=d
   page.append((kind,d,col,y));y+=h
  if page:pages.append(page)
  for n,page in enumerate(pages):
   self.header(p,'REGLAS '+str(n+1)+'/'+str(len(pages)))
   for kind,d,col,y in page:
    x=21+col*199.5
    if kind=='heading':self.section(x,y,d,width)
    elif kind=='rule':
     offset=17 if d.get('icon') else 0
     if offset:self.icon(d['icon'],x,y,14)
     self.par('<b>'+esc(d['name'])+'.</b> '+esc(d['description']),x+offset,y,width-offset,size)
    else:
     self.rect(x,y,width,19,LIGHT);self.par('<b>'+esc(d['name'])+'</b>',x+2,y+2,66,6.8)
     for j,k in enumerate(['COST','RNG','AOE','POW','DUR','OFF']):
      sx=x+70+j*19.7;self.text(sx,y+1,k,4.6,'Bold',MUTED);self.text(sx+1,y+9,d['statistics'].get(k) or '-',6.2,'Bold')
     self.par(esc(d['description']),x,y+22,width,size)
   self.finish(p,'rules-'+str(n+1));self.fonts.append(size)
  # Every profile starts on a front and ends on a reverse; pad odd total face count.
  if (1+len(pages))%2:
   self.header(p,'REFERENCIA / REVERSO COMPLEMENTARIO');self.section(21,45,'IDENTIFICACIÓN DEL PERFIL',389)
   self.text(21,65,p['faction']+' / '+p['type'],10,'Bold')
   self.par('Configuración: '+esc(' · '.join(o['name'] for o in p['options']) or 'Perfil base'),21,85,389,9)
   self.par('Las caras anteriores contienen las reglas completas de este perfil. Esta cara mantiene emparejadas las cartas complementarias.',21,112,350,9)
   self.finish(p,'reference-back')
 def save(self):
  self.c.save();r=PdfReader(self.out/'cartas-mpc.pdf');w=PdfWriter()
  for p in r.pages:p.trimbox=RectangleObject([8.64,8.64,W-8.64,H-8.64]);p.bleedbox=RectangleObject([0,0,W,H]);w.add_page(p)
  with open(self.out/'cartas-mpc.pdf','wb') as f:w.write(f)
  (self.out/'print-manifest.json').write_text(json.dumps({'pages':self.pages,'rulesFontPt':8,'widthPx':1797,'heightPx':1122,'dpi':300,'format':'MPC large landscape'},ensure_ascii=False,indent=2),encoding='utf8')
def main():
 a=argparse.ArgumentParser();a.add_argument('profiles',type=Path);a.add_argument('--output',required=True,type=Path);args=a.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 data=json.loads((args.profiles/'print-profiles.json').read_bytes());r=Renderer(args.profiles,args.output)
 stamp=Path(data['snapshot']).name[:8]
 r.sourceLabel='DATOS APP '+stamp[6:8]+'/'+stamp[4:6]+'/'+stamp[:4]
 for p in data['cards']:r.front(p);r.rules(p)
 r.save();print(json.dumps({'pages':len(r.pages),'cards':len(r.pages)//2,'output':str(args.output)}))
if __name__=='__main__':main()
