#!/usr/bin/env python3
"""梅花易数排卦器：由数或卦起本卦，自动生成互卦、变卦、体用与生克判定。

规则出自邵雍《梅花易数》（郑同《梅花易数讲义》白话本）：
卦以八除（整除取 8），爻以六除（整除取 6）；动者为用、静者为体；
互卦去初爻与上爻，2·3·4 为下互、3·4·5 为上互；乾坤无互则互其变卦。

用法（二选一）：
  python paigua.py --num 34 --shichen 9
  python paigua.py --shang 2 --xia 3 --dong 1
可选：--season 春|夏|秋|冬|四季月    --multi 3   （多爻动时守"上体下用"）
输出：本卦、互卦、变卦、体用、五行、生克、党数、旺衰、应期提示。
"""

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 先天卦数：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

# 爻位自下而上，1=阳 0=阴；符号、五行、先天数、后天方位
TRIGRAM = {
    "乾": {"bits": [1, 1, 1], "sym": "☰", "wu": "金", "num": 1, "fang": "西北"},
    "兑": {"bits": [1, 1, 0], "sym": "☱", "wu": "金", "num": 2, "fang": "西"},
    "离": {"bits": [1, 0, 1], "sym": "☲", "wu": "火", "num": 3, "fang": "南"},
    "震": {"bits": [1, 0, 0], "sym": "☳", "wu": "木", "num": 4, "fang": "东"},
    "巽": {"bits": [0, 1, 1], "sym": "☴", "wu": "木", "num": 5, "fang": "东南"},
    "坎": {"bits": [0, 1, 0], "sym": "☵", "wu": "水", "num": 6, "fang": "北"},
    "艮": {"bits": [0, 0, 1], "sym": "☶", "wu": "土", "num": 7, "fang": "东北"},
    "坤": {"bits": [0, 0, 0], "sym": "☷", "wu": "土", "num": 8, "fang": "西南"},
}

BITS2TRI = {tuple(v["bits"]): k for k, v in TRIGRAM.items()}

# (上卦, 下卦) -> 卦名
GUAMING = {
    ("乾", "乾"): "乾为天", ("乾", "兑"): "天泽履", ("乾", "离"): "天火同人",
    ("乾", "震"): "天雷无妄", ("乾", "巽"): "天风姤", ("乾", "坎"): "天水讼",
    ("乾", "艮"): "天山遁", ("乾", "坤"): "天地否",
    ("兑", "乾"): "泽天夬", ("兑", "兑"): "兑为泽", ("兑", "离"): "泽火革",
    ("兑", "震"): "泽雷随", ("兑", "巽"): "泽风大过", ("兑", "坎"): "泽水困",
    ("兑", "艮"): "泽山咸", ("兑", "坤"): "泽地萃",
    ("离", "乾"): "火天大有", ("离", "兑"): "火泽睽", ("离", "离"): "离为火",
    ("离", "震"): "火雷噬嗑", ("离", "巽"): "火风鼎", ("离", "坎"): "火水未济",
    ("离", "艮"): "火山旅", ("离", "坤"): "火地晋",
    ("震", "乾"): "雷天大壮", ("震", "兑"): "雷泽归妹", ("震", "离"): "雷火丰",
    ("震", "震"): "震为雷", ("震", "巽"): "雷风恒", ("震", "坎"): "雷水解",
    ("震", "艮"): "雷山小过", ("震", "坤"): "雷地豫",
    ("巽", "乾"): "风天小畜", ("巽", "兑"): "风泽中孚", ("巽", "离"): "风火家人",
    ("巽", "震"): "风雷益", ("巽", "巽"): "巽为风", ("巽", "坎"): "风水涣",
    ("巽", "艮"): "风山渐", ("巽", "坤"): "风地观",
    ("坎", "乾"): "水天需", ("坎", "兑"): "水泽节", ("坎", "离"): "水火既济",
    ("坎", "震"): "水雷屯", ("坎", "巽"): "水风井", ("坎", "坎"): "坎为水",
    ("坎", "艮"): "水山蹇", ("坎", "坤"): "水地比",
    ("艮", "乾"): "山天大畜", ("艮", "兑"): "山泽损", ("艮", "离"): "山火贲",
    ("艮", "震"): "山雷颐", ("艮", "巽"): "山风蛊", ("艮", "坎"): "山水蒙",
    ("艮", "艮"): "艮为山", ("艮", "坤"): "山地剥",
    ("坤", "乾"): "地天泰", ("坤", "兑"): "地泽临", ("坤", "离"): "地火明夷",
    ("坤", "震"): "地雷复", ("坤", "巽"): "地风升", ("坤", "坎"): "地水师",
    ("坤", "艮"): "地山谦", ("坤", "坤"): "坤为地",
}

SHENG = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}   # 我生
KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}      # 我克

SHICHEN = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

SEASON_WANG = {
    "春": (["震", "巽"], ["坤", "艮"]),
    "夏": (["离"], ["乾", "兑"]),
    "秋": (["乾", "兑"], ["震", "巽"]),
    "冬": (["坎"], ["离"]),
    "四季月": (["坤", "艮"], ["坎"]),
}


def tri_by_num(n):
    """先天数 1-8 取卦；0 或 8 都取坤。"""
    n = n % 8 or 8
    return ORDER[n - 1]


def relation_of(a, b):
    """a 对 b 的五行关系。"""
    if a == b:
        return "比和"
    if KE[a] == b:
        return "克"
    if SHENG[a] == b:
        return "生"
    if KE[b] == a:
        return "被克"
    return "被生"


def judge(ti, yong):
    rel = relation_of(TRIGRAM[ti]["wu"], TRIGRAM[yong]["wu"])
    return {
        "克": "体克用：诸事吉，但事在己、须主动",
        "被克": "用克体：诸事凶，事来克己",
        "生": "体生用：耗失之患（泄气），费力而所得少",
        "被生": "用生体：进益之喜，事来就我",
        "比和": "体用比和：百事顺遂",
    }[rel]


def build(num=None, shichen=None, shang=None, xia=None, dong=1, multi=None):
    if num is not None:
        up_i = num % 8 or 8
        low_i = (num + shichen) % 8 or 8
        up, low = ORDER[up_i - 1], ORDER[low_i - 1]
        total = num + shichen
    else:
        up, low = tri_by_num(shang), tri_by_num(xia)
        total = None
    moving = multi if multi else [dong]

    lines = TRIGRAM[low]["bits"] + TRIGRAM[up]["bits"]
    changed = list(lines)
    for n in moving:
        changed[(n - 1) % 6] ^= 1
    bian_low = BITS2TRI[tuple(changed[0:3])]
    bian_up = BITS2TRI[tuple(changed[3:6])]

    hu_low = BITS2TRI[tuple(lines[1:4])]
    hu_up = BITS2TRI[tuple(lines[2:5])]

    if multi:  # 多爻动：仍守"上体下用"
        ti, yong = up, low
        ti_side = "上"
    elif 1 <= moving[0] <= 3:
        ti, yong, ti_side = up, low, "上"
    else:
        ti, yong, ti_side = low, up, "下"

    # 体互 / 用互：与体卦同侧者为体互
    if ti_side == "上":
        ti_hu, yong_hu = hu_up, hu_low
    else:
        ti_hu, yong_hu = hu_low, hu_up

    def party(t):
        """统计与 t 同五行的卦（体/用/互上下/变）。"""
        groups = {"体": [ti], "用": [yong], "互": [hu_up, hu_low], "变": [bian_up, bian_low]}
        return sum(1 for g in groups.values() for x in g if TRIGRAM[x]["wu"] == TRIGRAM[t]["wu"])

    ke_ti = [x for x in (yong, hu_up, hu_low, bian_up, bian_low)
             if relation_of(TRIGRAM[x]["wu"], TRIGRAM[ti]["wu"]) == "克"]
    sheng_ti = [x for x in (yong, hu_up, hu_low, bian_up, bian_low)
                if relation_of(TRIGRAM[x]["wu"], TRIGRAM[ti]["wu"]) == "生"]

    yingqi = []
    if yong in sheng_ti:
        yingqi.append("用卦生体：事即成，应期近（用卦卦气之日）")
    if hu_up in sheng_ti or hu_low in sheng_ti:
        yingqi.append("互卦生体：渐成，应期居中")
    if bian_up in sheng_ti or bian_low in sheng_ti:
        yingqi.append("变卦生体：稍迟，但终有吉")
    if ke_ti:
        days = sum(TRIGRAM[x]["num"] for x in ke_ti)
        yingqi.append("有克体之卦 %s（先天数合计 %d），主阻节，按日计阻" % ("/".join(ke_ti), days))

    return {
        "本卦": {
            "名": GUAMING[(up, low)], "上卦": up, "下卦": low,
            "爻": "".join("—" if b else "--" for b in reversed(lines)),
        },
        "动爻": "、".join("第%d爻" % n for n in moving),
        "互卦": {"下互": hu_low, "上互": hu_up, "体互": ti_hu, "用互": yong_hu},
        "变卦": GUAMING[(bian_up, bian_low)],
        "体用": {
            "体": "%s（%s）" % (ti, TRIGRAM[ti]["wu"]),
            "用": "%s（%s）" % (yong, TRIGRAM[yong]["wu"]),
            "体位": ti_side,
            "主断": judge(ti, yong),
            "体党": party(ti), "用党": party(yong),
        },
        "变卦对体": {"上": relation_of(TRIGRAM[bian_up]["wu"], TRIGRAM[ti]["wu"]),
                    "下": relation_of(TRIGRAM[bian_low]["wu"], TRIGRAM[ti]["wu"])},
        "互对体": [relation_of(TRIGRAM[hu_up]["wu"], TRIGRAM[ti]["wu"]),
                  relation_of(TRIGRAM[hu_low]["wu"], TRIGRAM[ti]["wu"])],
        "应期提示": yingqi,
        "_total": total,
    }


def main():
    ap = argparse.ArgumentParser(description="梅花易数排卦")
    ap.add_argument("--num", type=int, help="起卦的基数（年支+月+日 或 报数/物数/声数）")
    ap.add_argument("--shichen", type=int, help="时辰序数 1-12（子1…亥12）")
    ap.add_argument("--shang", type=int, help="上卦先天数 1-8")
    ap.add_argument("--xia", type=int, help="下卦先天数 1-8")
    ap.add_argument("--dong", type=int, default=None, help="动爻 1-6")
    ap.add_argument("--multi", type=int, nargs="+", help="多爻动，如 --multi 2 5")
    ap.add_argument("--season", choices=list(SEASON_WANG), help="四时，用于判卦气旺衰")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    if a.num is not None:
        if not a.shichen:
            ap.error("--num 模式必须同时给 --shichen 1-12")
        base = a.num
        dong = a.dong or ((base + a.shichen) % 6 or 6)
        r = build(num=base, shichen=a.shichen, dong=dong, multi=a.multi)
    else:
        if not (a.shang and a.xia):
            ap.error("需要 --num/--shichen，或 --shang/--xia")
        dong = a.dong or 1
        r = build(shang=a.shang, xia=a.xia, dong=dong, multi=a.multi)

    if a.season:
        wang, shuai = SEASON_WANG[a.season]
        ti = r["体用"]["体"][0]
        r["卦气"] = "%s：体 %s %s" % (
            a.season, r["体用"]["体"],
            "旺相" if ti in wang else ("衰囚" if ti in shuai else "平"))

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    print("【本卦】%s（%s上%s下）  %s" % (r["本卦"]["名"], r["本卦"]["上卦"], r["本卦"]["下卦"], r["本卦"]["爻"]))
    print("【动爻】%s" % r["动爻"])
    print("【互卦】上互 %s、下互 %s（体互 %s，用互 %s）"
          % (r["互卦"]["上互"], r["互卦"]["下互"], r["互卦"]["体互"], r["互卦"]["用互"]))
    print("【变卦】%s" % r["变卦"])
    print("【体用】体 %s ／ 用 %s（体在%s）" % (r["体用"]["体"], r["体用"]["用"], r["体用"]["体位"]))
    print("【主断】%s" % r["体用"]["主断"])
    print("【党数】体党 %d ／ 用党 %d" % (r["体用"]["体党"], r["体用"]["用党"]))
    if "卦气" in r:
        print("【卦气】%s" % r["卦气"])
    print("【应期】%s" % ("；".join(r["应期提示"]) or "无生体之卦、亦无克体之卦，应期需另取变卦卦气"))


if __name__ == "__main__":
    main()
