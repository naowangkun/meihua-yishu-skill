# meihua-yishu-skill

一个把《梅花易数》（邵雍 原著，郑同《梅花易数讲义》白话本，华龄出版社 2009）的起卦断卦规则写成可执行 Skill 的仓库。

不是"随机起一卦"的玩具，而是把原书的算式、体用规则、应期算法固化成流程——**排卦交给脚本，断语按原书规则现场写**。

## 这是什么

- `meihua-yishu/SKILL.md`：主指令。三条硬规矩（不动不占、年月日必用农历、理在数先）、七步流程、固定五段输出格式（起卦→卦象→断据→结论→应期与失手条件）。
- `meihua-yishu/scripts/paigua.py`：排卦器。输入数＋时辰，输出本卦／互卦（含体互用互）／变卦／体用／五行生克／党数／旺衰／应期提示。纯标准库，无依赖。
- `meihua-yishu/references/xiangshu-tables.md`：先天卦数、八卦类象、生体克体兆象、卦气旺衰、十八占、失物方位、真生真克速判表。
- `meihua-yishu/references/zhanli-shili.md`：原书八则经典占例的完整推理链，用来校准断语粗细。
- `meihua-yishu/references/cezi.md`：卷四至卷六测字（相字）体系摘要，与卦占同源不同法。

## 用法

```bash
# 时间起卦：基数＝年支数＋农历月＋农历日，时辰序数 子1…亥12
python meihua-yishu/scripts/paigua.py --num 34 --shichen 9 --season 春

# 已知上下卦与动爻
python meihua-yishu/scripts/paigua.py --shang 2 --xia 3 --dong 1

# 多爻动（守"上体下用"）
python meihua-yishu/scripts/paigua.py --shang 8 --xia 7 --multi 2 5

# 机器可读
python meihua-yishu/scripts/paigua.py --num 25 --shichen 4 --json
```

## 算式（原书 p070–p072）

```
上卦 = 数 ÷ 8 取余（整除取 8，即坤）
下卦 = (数 + 时数) ÷ 8 取余
动爻 = (数 + 时数) ÷ 6 取余（整除取 6）
```

先天卦数：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8。

## 已验证

用原书占例回测，脚本结构与书一致：

| 占例 | 输入 | 脚本输出 | 原书 |
|---|---|---|---|
| 观梅占 | 34，申时9 | 泽火革，初爻动，互乾／巽，变泽山咸，体兑用离 | 一致（p086） |
| 牡丹占 | 25，卯时4 | 天风姤，五爻动，互重乾，变火风鼎，体巽用乾 | 一致（p091） |
| 地山谦例 | 24，午时7 | 地山谦，初爻动，变地火明夷 | 一致（p071） |

## 装到自己的环境

把 `meihua-yishu/` 整个目录放进你的 skills 目录（如 `.user_skills/`），新开会话即被识别。

## 说明

传统术数推演，供参照与研习，不替代医疗、法律、投资的专业判断。原书为 399 页扫描件，引用页码为该扫描版 PDF 页（PDF 页 ≈ 书页 + 55）。

## License

MIT，见 [LICENSE](LICENSE)。
