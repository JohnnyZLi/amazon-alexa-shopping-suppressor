#!/usr/bin/env python3
from __future__ import annotations
import math, struct, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "icons"
SIZES = (16, 32, 48, 128)
SS = 6

# Chrome Web Store guidance for a square 128 px extension icon calls for
# 16 px of transparent padding on every side around a 96 px artwork box.
STORE_ICON_SIZE = 128
STORE_ARTWORK_SIZE = 96


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
        return (p1[0]-p3[0])*(p2[1]-p3[1])-(p1[1]-p3[1])*(p2[0]-p3[0])
    p=(px,py)
    d1,d2,d3=s(p,a,b),s(p,b,c),s(p,c,a)
    neg=(d1<0) or (d2<0) or (d3<0)
    pos=(d1>0) or (d2>0) or (d3>0)
    return not (neg and pos)


def render(size):
    n=size*SS
    buf=[(0,0,0,0)]*(n*n)

    if size == STORE_ICON_SIZE:
        artwork = STORE_ARTWORK_SIZE * SS
        offset = ((STORE_ICON_SIZE - STORE_ARTWORK_SIZE) // 2) * SS
        inset = 0.0
    else:
        artwork = n
        offset = 0.0
        inset = 0.025*artwork

    radius=0.18*artwork

    cx, cy = offset + 0.49*artwork, offset + 0.43*artwork
    rx, ry = 0.29*artwork, 0.225*artwork
    ring=0.043*artwork
    tail=((offset+0.33*artwork,offset+0.57*artwork),(offset+0.25*artwork,offset+0.69*artwork),(offset+0.40*artwork,offset+0.61*artwork))
    inner_tail=((offset+0.335*artwork,offset+0.56*artwork),(offset+0.292*artwork,offset+0.635*artwork),(offset+0.385*artwork,offset+0.595*artwork))
    ax,ay,bx,by=offset+0.27*artwork,offset+0.25*artwork,offset+0.76*artwork,offset+0.76*artwork
    slash_r=0.052*artwork

    for y in range(n):
        yf=y+0.5
        for x in range(n):
            xf=x+0.5
            local_x = xf - offset
            local_y = yf - offset
            if local_x < 0 or local_y < 0 or local_x > artwork or local_y > artwork:
                continue
            if not rounded_rect_inside(local_x,local_y,artwork,inset,radius):
                continue
            t=local_y/artwork
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
