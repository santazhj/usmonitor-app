# A Level Mathematics — AS Pure Mathematics 1 (P1) 模拟卷

面向 Cambridge International 9709 **Paper 1 (Pure Mathematics 1)** 的十套模拟试卷，按真实考试格式编写：

| 项目 | 说明 |
|---|---|
| 时长 | 1 小时 50 分钟 |
| 总分 | 75 分 |
| 题量 | 每卷 12 题，分值 3–10 分，按难度递增 |
| 语言 | 英文（与真实考试一致） |
| 计算器 | 允许使用科学计算器 |

## 目录

```
papers/         P1-Practice-Paper-01.pdf … 10.pdf   给学生的试卷
mark-schemes/   P1-Mark-Scheme-01.pdf … 10.pdf      评分标准（含 M/A/B 分点，勿在考前给学生）
progress-tracker.md                                  十套卷的知识点掌握追踪表（批改后填写）
src/            试卷与评分标准的 Markdown 源文件 + 生成 PDF 的脚本
```

## 知识点覆盖

每一套都覆盖 P1 全部八个板块（对应 9709 大纲 1.1–1.8）：

| 板块 | 每卷题目 |
|---|---|
| Quadratics 二次函数、判别式、不等式 | 配方、判别式（相切/不交）、二次不等式、换元二次 |
| Functions 函数 | 复合函数、反函数与定义域/值域、单调限制、图像变换 |
| Coordinate geometry 坐标几何 | 直线（垂直平分线、垂足）、圆方程、切线、弦 |
| Circular measure 弧度制 | 弧长、扇形面积、弓形、组合图形 |
| Trigonometry 三角 | 恒等式证明、二次型三角方程、复合角 sin(2x−π/3) 型方程、精确值 |
| Series 数列 | 等差、等比、无穷和、应用题、**二项式展开** |
| Differentiation 微分 | 驻点与性质、切线法线、增减区间、链式法则 (ax+b)^n、变化率、最值应用 |
| Integration 积分 | 由导数求曲线、定积分面积（含 x 轴下方）、两曲线之间面积、**旋转体体积** |

> 注意：**二项式展开**和**旋转体体积**不在你整理的清单里，但都是 9709 P1 大纲的正式考点，真题几乎每年都考，所以试卷里保留了。如果学生还没学，可先跳过这两类题（每卷各 1 题，约 3–4 分），批改时我会单独标注。

## 使用流程

1. 让学生在 **1 小时 50 分钟** 内独立完成一套（建议从 Paper 1 开始，按顺序做）。
2. 把学生的答卷（拍照或打字均可，请保留完整过程）发回本会话，说明是第几套。
3. 我按评分标准逐题批改，输出：
   - 每题得分与总分、对应等级（A: ≥ 60/75，B: ≥ 52，C: ≥ 44，D: ≥ 36，E: ≥ 28，参考近年 P1 分数线的大致区间）；
   - 按八个板块统计的掌握情况；
   - 每道错题的清晰讲解（错在哪一步、正确解法、同类题提醒）；
   - 更新 `progress-tracker.md`。

## 重新生成 PDF

```bash
cd src/tools && npm i katex markdown-it
python3 assemble.py 1 ../paper01.md /tmp/p01.md && ./topdf.sh /tmp/p01.md ../../papers/P1-Practice-Paper-01.pdf
MD_BREAKS=1 ./topdf.sh ../ms01.md ../../mark-schemes/P1-Mark-Scheme-01.pdf
```

需要无头 Chromium（脚本默认使用 Playwright 安装路径）。
