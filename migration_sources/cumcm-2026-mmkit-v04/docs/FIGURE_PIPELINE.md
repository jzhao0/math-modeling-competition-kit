# CUMCM Figure Pipeline (v0.3)

图中一切数值必须真实，但**视觉表现本身也是建模竞赛的优化目标**。MMKit 把科学真值层与展示层分开：结果数据/模型结构决定“画什么”，渲染后端决定“怎么画得更清楚、更有竞争力”。

## A. 数值/证据图（EVIDENCE_NUMERICAL）

- 真值来源：冻结 CSV/JSON/结果表。
- 后端：Python、R、可选 Origin。
- 可重建：数据 + 脚本/Origin项目/明确步骤 → 图。
- 数值、排序、区间、单位必须与冻结结果一致。
- 当 exact reading 重要时保留直接数值标签、误差/区间或邻近表格。

## B. 结构/科学图（STRUCTURAL_SCIENTIFIC）

- 用于状态转移、Bayes 更新、返工循环、多级装配、网络/流程等。
- 允许 Draw.io/SVG、Python/R、Origin 或经人工 QA 的 AI 草稿。
- 图应放在对应推导附近，和公式共同解释模型，而不是统一堆在结果章节。
- 必须人工核对文本、箭头、变量、方向、单位和公式语义；优先保留可编辑源。

## C. 展示型图（SHOWCASE_PRESENTATION）

展示型图可以承担“让作品更好看、更有记忆点”的作用，但必须锚定已验证的模型/结果。

允许：

- 三维柱状图、立体柱/条；
- 立体折线、ribbon/extruded trend；
- 空间曲面、网格、等高投影；
- 透视卡片/层级式结构图；
- 渐变、阴影、材质感和更强的构图层次。

约束不是“禁止装饰”，而是：

- 不发明数据；
- 不改变数值排序或方向；
- 不把纯装饰深度标成量轴；
- 不靠透视遮住关键误差/区间/标签；
- 未计算的插值曲面不能伪装成精确结果。

## 3D 两种模式

### DATA_3D

第三维是真实参数、响应或状态。适合：

- 双参数敏感性/稳健性；
- 成本/收益响应面；
- 空间/时间/状态三维数据；
- surface + contour/projection 组合。

### PRESENTATION_3D

深度纯属展示层。适合：

- 分类结果改成 3D columns；
- 单趋势改成带透视的 ribbon/extruded line；
- 为页面增加空间层次和竞赛观感。

这类图不需要人为造一个“第三变量”。深度轴不显示虚假的数值刻度即可。

## 后端路由

```text
冻结结果/模型
   ↓
FIGURE_PLAN + figure contract
   ├─ Python / matplotlib    （确定性默认）
   ├─ R / ggplot2            （统计/grammar-of-graphics）
   ├─ Origin MCP             （可选，高观感 2D/3D/曲面/等高线）
   └─ Draw.io / SVG          （结构图）
   ↓
科学 QA + 展示 QA
   ↓
就近插入论文
```

Origin 路由详见 `docs/ORIGIN_MCP_BACKEND.md`。Origin 只是渲染/分析后端，不是数值真值源；必须在赛前的实际 Windows 主机上完成安装和 doctor/smoke 后才能依赖。

## Figure contract

每张正式图至少记录：

- figure id；
- intent（EVIDENCE / STRUCTURAL / SHOWCASE）；
- 支撑的 claim 或页面作用；
- reader question；
- source data/result；
- visual encoding；
- backend；
- dimensions/units；
- presentation layer；
- annotation plan；
- editable source / reconstruction path；
- QA owner/status。

## 评委视角检查

最终不要只问“有没有图”，还要问：

1. 这张图是否比文字/表格更快传达信息？
2. 它在页面上是否形成视觉焦点和层次？
3. 字体、标签在 100% PDF 和 A4 打印是否可读？
4. 3D 透视是否让结果更好看而没有造成错误读数？
5. 图是否紧贴解释它的正文，而不是为了数量被放到别处？
6. 同一篇论文是否有 2D/3D/结构图的合理变化，避免视觉疲劳？
7. 图、表、公式、正文的数字和含义是否一致？

机器可读策略见 `config/figure_quality.yaml` 与 `config/contest_visual.yaml`。
