import sys, re, importlib, traceback, inspect, os
from contextlib import contextmanager

ufFirst=re.compile('\s*for r in range')

msg=None
if len(sys.argv) not in (2,4,6,8):
  msg='you must have exactly 1, 3, 5 or 7 input filenames'

if msg is None:
  mres=[re.match("([^.]*).py$",a) for a in sys.argv[1:]]
  if None in mres:
    bogons=[n for (n,m) in zip(sys.argv[1:],mres) if m is None]
    msg='%s are not valid python filenames'%bogons

if msg is not None:
  print("""%s
  Usage: python idrive.py [yourhw2.py yourcky.py [yourhw2_3.py yourcky_3.py [yourhw2_4.py yourcky_4.py]]] > [your UUN].txt"""%msg,file=sys.stderr)
  exit(1)

modNames=['cky','hw2_3','cky_3','hw2_4','cky_4','hw2_5','cky_5']
modFilenames=[m.group(1) for m in mres]

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

with suppress_stdout():
  try:
    mods=dict(zip(modNames[:len(modFilenames)],[importlib.import_module(n) for n in modFilenames]))
  except (ModuleNotFoundError, ImportError) as e:
    print("Filenames must be importable: %s"%e,file=sys.stderr)
    exit(2)

from cfg_fix import parse_grammar, Tree
grammar=parse_grammar("""
S -> NP VP
NP -> Det Nom | Nom | NP PP
Det -> NP "'s"
Nom -> N SRel | N
VP -> Vi | Vt NP | VP PP
PP -> Prep NP
SRel -> Relpro VP
Det -> 'a' | 'the'
N -> 'fish' | 'frogs' | 'soup' | 'children' | 'books'
Prep -> 'in' | 'for'
Vt -> 'saw' | 'ate' | 'read'
Vi -> 'fish' | 'swim'
Relpro -> 'that'
""") #'
chart=mods['cky'].CKY(grammar)


def callCount(modName,methodName):
  # attempt to count calls to this method
  pat=re.compile('[^#]*\.'+methodName+'\(')
  return sum(1 for l in inspect.getsourcelines(mods[modName])[0] if pat.match(l))

def getDocString(modName,className,methodName,firstPat):
  (lines,_)=inspect.getsourcelines(getattr(getattr(mods[modName],className),
                                           methodName))
  d=True
  n=0
  for l in lines:
    if d and l[-2]==':':
      d=False
      n+=1
      f=n
      continue
    if re.match("\s*"+firstPat,l):
      ff=n
      break
    n+=1
  return lines[f:ff]

anss={'cky':
      [('answer1a',(getDocString("cky","CKY","buildIndices",
                                 "self.unary=defaultdict"),)),
       ('answer1b',(getDocString("cky","CKY","unaryFill",
                                 "for r in range"),)),
       ('answer1c',(getDocString("cky","Cell","unaryUpdate",
                                 "if not recursive:"),)),
       ('answer1d',(getDocString("cky","CKY","recognise",
                                 "self.verbose="),)),
       ('answer1e',(getDocString("cky","CKY","maybeBuild",
                                 "self.log"),))]}
if 'hw2_3' in mods:
  anss.update([('hw2_3',
                [('answer3a',
                  '[l.symbol() for l in chart2.matrix[0][11].labels()]')])])
if 'cky_4' in mods:
  anss.update([('cky_4',
                [('answer4a',(callCount("cky_4","unaryUpdate"),))])])

if 'hw2_5' in mods:
  anss.update([('cky_5',[('answer5a',(callCount("hw2_5","parse"),))])])

res={}
for ans in anss.keys():
  subres={}
  res[ans]=subres
  for an in anss[ans]:
    if type(an) is str:
        (aname,aval)=(an,an)
    else:
        (aname,aval)=an
    try:
      if type(aval) is tuple:
        av=aval[0]
      else:
        av=eval(aval,mods[ans].__dict__)
    except Exception as e:
      av='%s.%s:"""%s threw Exception: %s"""'%(ans,aname,aval,traceback.format_exc().replace('"',"'"))
    subres[aname]=av

sents=["John gave a book to Mary.",
       "John gave Mary a book.",
       "John gave Mary a nice drawing book.",
       "John ate salad with mushrooms with a fork.",
       "Book a flight to NYC.",
       "Can you book a flight to London?",
       "Why did John book the flight?",
       "John told Mary that he will book a flight today."]

chart.recognise(["the","frogs","swim"])
res['hw2']=dict([('answer1f',[l.symbol() for l in chart.matrix[0][3].labels()])])
res['hw2']['answer1g']=chart.recognise(["not","a","sentence"])

if 'hw2_3' in mods:
  res['hw2_3']['answer3b']=mods['hw2_3'].chart2.recognise(["not","a","sentence"])
  ll="cdefghi"
  for i in range(7):
    res['hw2_3']['answer3'+ll[i]]=mods['hw2_3'].chart2.recognise(mods['hw2_3'].tokenise(sents[i]))

if 'cky_4' in mods:
  res['cky_4']['answer4b']=[mods['hw2_4'].chart2.recognise(mods['hw2_4'].tokenise(sents[i])) for i in range(8)]

if 'cky_5' in mods:
  pp=[mods['hw2_5'].chart2.parse(mods['hw2_5'].tokenise(sents[i])) for i in range(8)]
  res['cky_5']['answer5b']=[(len(p) if type(p) is list else 1) for p in pp]
  res['cky_5']['answer5c']=[(p[0].__class__.__name__ if type(p) is list else p.__class__.__name__) for p in pp]
  lp=(pp[7][0] if type(pp[7]) is list else pp[7])
  res['cky_5']['answer5d']=str(lp)

print("anss=%s"%res)
