"""CPU mathematical checks, not a GLSL execution or Flame render test."""
import math
from pathlib import Path
import random
import re
import xml.etree.ElementTree as ET

def solve_cholesky(d, o, c):
    l00 = math.sqrt(d[0]); l10 = o[0]/l00; l20 = o[1]/l00
    l11 = math.sqrt(d[1]-l10*l10)
    l21 = (o[2]-l20*l10)/l11
    l22 = math.sqrt(d[2]-l20*l20-l21*l21)
    y0 = c[0]/l00; y1 = (c[1]-l10*y0)/l11
    y2 = (c[2]-l20*y0-l21*y1)/l22
    a2 = y2/l22; a1 = (y1-l21*a2)/l11
    return [(y0-l10*a1-l20*a2)/l00, a1, a2]

def solve_cofactor(d, o, c):
    r,g,b = d; rg,rb,gb = o
    cof = [g*b-gb*gb, rb*gb-rg*b, rg*gb-rb*g,
           r*b-rb*rb, rg*rb-r*gb, r*g-rg*rg]
    det = r*cof[0]+rg*cof[1]+rb*cof[2]
    return [(cof[0]*c[0]+cof[1]*c[1]+cof[2]*c[2])/det,
            (cof[1]*c[0]+cof[3]*c[1]+cof[4]*c[2])/det,
            (cof[2]*c[0]+cof[4]*c[1]+cof[5]*c[2])/det]

def weights(width):
    h = max(1,min(256,width))/2
    return [(k,max(0,min(k+.5,h)-max(k-.5,-h)))
            for k in range(-math.ceil(h), math.ceil(h)+1)]

def axis_blur(im, width, axis):
    h,w = len(im),len(im[0]); taps = weights(width); total = sum(v for k,v in taps)
    return [[sum(v*im[min(h-1,max(0,y+(k if axis==0 else 0)))][min(w-1,max(0,x+(k if axis==1 else 0)))]
                 for k,v in taps)/total for x in range(w)] for y in range(h)]

def blur(im, width):
    return axis_blur(axis_blur(im,width,1),width,0)

def error(a,b):
    return max(abs(x-y) for ar,br in zip(a,b) for x,y in zip(ar,br))

def guided(guide, matte, width, detail):
    h,w = len(matte),len(matte[0])
    channels = [[[guide[y][x][c] for x in range(w)] for y in range(h)] for c in range(3)]
    def mul(a,b): return [[x*y for x,y in zip(ar,br)] for ar,br in zip(a,b)]
    mi = [blur(c,width) for c in channels]; mp = blur(matte,width)
    square = [blur(mul(c,c),width) for c in channels]
    cross = [blur(mul(channels[a],channels[b]),width) for a,b in ((0,1),(0,2),(1,2))]
    ip = [blur(mul(c,matte),width) for c in channels]
    ab = [[[0.0 for x in range(w)] for y in range(h)] for c in range(4)]
    for y in range(h):
        for x in range(w):
            m = [v[y][x] for v in mi]
            d = [square[c][y][x]-m[c]**2+10**(-detail) for c in range(3)]
            o = [cross[c][y][x]-m[a]*m[b] for c,(a,b) in enumerate(((0,1),(0,2),(1,2)))]
            cov = [ip[c][y][x]-m[c]*mp[y][x] for c in range(3)]
            a = solve_cholesky(d,o,cov)
            for c in range(3): ab[c][y][x] = a[c]
            ab[3][y][x] = mp[y][x]-sum(a[c]*m[c] for c in range(3))
    ab = [blur(v,width) for v in ab]
    return [[sum(ab[c][y][x]*guide[y][x][c] for c in range(3))+ab[3][y][x]
             for x in range(w)] for y in range(h)]

rng = random.Random(123)
worst = 0
for _ in range(1000):
    v = [[rng.uniform(-1,1) for j in range(3)] for i in range(3)]
    m = [[sum(v[k][i]*v[k][j] for k in range(3))+(0.001 if i==j else 0) for j in range(3)] for i in range(3)]
    d = [m[i][i] for i in range(3)]; o = [m[0][1],m[0][2],m[1][2]]
    c = [rng.uniform(-1,1) for i in range(3)]
    a,b = solve_cholesky(d,o,c),solve_cofactor(d,o,c)
    worst = max(worst, max(abs(x-y) for x,y in zip(a,b)))
assert worst < 1e-7, worst
print(f'PASS: 1000 covariance solves vs gizmo-style cofactor inverse; max error {worst:.3g}')

im = [[rng.random() for x in range(9)] for y in range(7)]
for width in (1,2,3,4.5,30,256):
    taps = weights(width); total = sum(v for k,v in taps)
    direct = [[sum(wx*wy*im[min(6,max(0,y+ky))][min(8,max(0,x+kx))]
                   for ky,wy in taps for kx,wx in taps)/total**2
               for x in range(9)] for y in range(7)]
    assert error(blur(im,width),direct)<1e-12
print('PASS: separable box vs direct 2D box, fractional/even widths and image boundaries')

guide = [[[rng.random() for c in range(3)] for x in range(9)] for y in range(7)]
assert error(guided(guide,im,1,3.5),im)<1e-10
for p in (0,.35,1):
    matte = [[p]*9 for _ in range(7)]
    assert error(guided(guide,matte,5,3.5),matte)<1e-10
flat = [[[.2,.4,.6] for x in range(9)] for y in range(7)]
assert error(guided(flat,im,5,3.5),blur(blur(im,5),5))<1e-10
print('PASS: identity width, constant matte, flat guide gives twice-box-blurred matte')

# Equal-luminance red/green boundary: RGB guidance should retain this edge.
guide = [[([1,0,0] if x<8 else [0,.2126/.7152,0]) for x in range(17)] for _ in range(5)]
matte = [[float(x<8) for x in range(17)] for _ in range(5)]
q = guided(guide,matte,7,3.5)
assert q[2][7]-q[2][8]>.95
print('PASS: equal-luminance colour edge remains sharp with RGB guidance')

out = Path(__file__).resolve().parent/'matchbox'
xml = ET.parse(out/'GuidedMatte.xml').getroot()
seen = set()
for n,sh in enumerate(xml.findall('Shader'),1):
    assert sh.get('Index')==str(n) and sh.get('OutputBitDepth')==('Float16' if n==11 else 'Float32')
    source = (out/f'GuidedMatte.{n}.glsl').read_text()
    for ref in re.findall(r'adsk_results_pass(\d+)\b',source): assert int(ref)<n
    for u in sh.findall('Uniform'):
        name=u.get('Name')
        if u.find('Duplicate') is not None: assert name in seen
        seen.add(name)
assert len(xml.findall('Shader'))==11
print('PASS: XML, 11-pass dependency ordering, internal Float32 / output Float16, linked controls')
print('This CPU check does not execute GLSL or establish GPU precision, Flame rendering, or Nuke pixel parity.')
