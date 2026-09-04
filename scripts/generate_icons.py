#!/usr/bin/env python3
from __future__ import annotations
import math, struct, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "icons"
SIZES = (16, 32, 48, 128)
SS = 6

def rounded_rect_inside(x, y, n, inset, radius):
    left = top = inset
    right = bottom = n - inset
    if left + radius <= x <= right - radius and top <= y <= bottom:
        return True
    if top + radius <= y <= bottom - radius and left <= x <= right:
        return True
    cx = left + radius if x < left + radius else right - radius
    cy = top + radius if y < top + radius else bottom - radius
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2

def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    vv = vx*vx + vy*vy
    t = 0.0 if vv == 0 else max(0.0, min(1.0, (wx*vx + wy*vy)/vv))
    qx, qy = ax + t*vx, ay + t*vy
    return math.hypot(px-qx, py-qy)

def point_in_tri(px, py, a, b, c):
    def s(p1,p2,p3):
        return (p1[0]-p3[0])*(p2[1]-p3[1])-(p2[0]-p3[0])*(p1[1]-p3[1])
    p=(px,py)
    d1,d2,d3=s(p,a,b),s(p,b,c),s(p,c,a)
    neg=(d1<0) or (d2<0) or (d3<0)
    pos=(d1>0) or (d2>0) or (d3>0)
    return not (neg and pos)

def render(size):
    n=size*SS
    buf=[(0,0,0,0)]*(n*n)
    inset=0.025*n
    radius=0.18*n

    cx, cy = 0.49*n, 0.43*n
    rx, ry = 0.29*n, 0.225*n
    ring=0.043*n
    tail=((0.33*n,0.57*n),(0.25*n,0.69*n),(0.40*n,0.61*n))
    inner_tail=((0.335*n,0.56*n),(0.292*n,0.635*n),(0.385*n,0.595*n))
    ax,ay,bx,by=0.27*n,0.25*n,0.76*n,0.76*n
    slash_r=0.052*n

    for y in range(n):
        yf=y+0.5
        for x in range(n):
            xf=x+0.5
            if not rounded_rect_inside(xf,yf,n,inset,radius):
                continue
            t=yf/n
            r=int(5*(1-t)+8*t)
            g=int(55*(1-t)+79*t)
            b=int(96*(1-t)+132*t)
            color=(r,g,b,255)

            e=((xf-cx)/rx)**2 + ((yf-cy)/ry)**2
            irx,iry=rx-ring,ry-ring
            ei=((xf-cx)/irx)**2 + ((yf-cy)/iry)**2
            if e <= 1.0 and ei >= 1.0:
                color=(255,255,255,255)
            if point_in_tri(xf,yf,*tail):
                color=(255,255,255,255)
            if point_in_tri(xf,yf,*inner_tail):
                color=(r,g,b,255)

            if seg_dist(xf,yf,ax,ay,bx,by) <= slash_r:
                d=seg_dist(xf,yf,ax,ay,bx,by)/slash_r
                rr=int(255 - 18*d)
                gg=int(65 - 18*d)
                bb=int(67 - 10*d)
                color=(rr,max(35,gg),max(40,bb),255)
            buf[y*n+x]=color

    out=bytearray()
    for y in range(size):
        out.append(0)
        for x in range(size):
            sr=sg=sb=sa=0
            for yy in range(y*SS,(y+1)*SS):
                base=yy*n+x*SS
                for xx in range(SS):
                    r,g,b,a=buf[base+xx]
                    sr+=r*a; sg+=g*a; sb+=b*a; sa+=a
            count=SS*SS
            a=round(sa/count)
            if sa:
                r=round(sr/sa); g=round(sg/sa); b=round(sb/sa)
            else:
                r=g=b=0
            out.extend((r,g,b,a))
    return bytes(out)

def png_rgba(size, raw):
    sig=b"\x89PNG\r\n\x1a\n"
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
    ihdr=struct.pack(">IIBBBBB",size,size,8,6,0,0,0)
    return sig+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for size in SIZES:
        p=OUT/f"icon-{size}.png"
        p.write_bytes(png_rgba(size,render(size)))
        print(p.relative_to(ROOT))

if __name__=="__main__":
    main()
