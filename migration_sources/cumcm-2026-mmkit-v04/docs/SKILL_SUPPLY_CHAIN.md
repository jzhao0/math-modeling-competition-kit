# Skill Supply-Chain Review (MMKit v0.2 P1)

外部 Skill 均为第三方代码。冻结时记录的事实（不含猜测）：

| entry | source | pinned SHA (main) | license (evidence) | scripts/executables present | network behavior | install hooks |
| --- | --- | --- | --- | --- | --- | --- |
| supervisor_skills | HKUSTDial/Supervisor-Skills | aff5de9e... | CC BY-NC-SA 4.0 (LICENSE) | python lint reqs (requirements-lint.txt) | none evident | none evident |
| cumcm_live_workflow | haoxilin/cumcm-live-workflow-skill | 00c2567... | MIT (LICENSE) | none (doc/skill only) | none evident | none evident |
| nature_skills | Yuan1z0825/nature-skills | 596f65b... | Apache-2.0 (LICENSE) | index.html / pr-body scripts | some sub-skills may call external APIs | none evident at root |
| gdm_science_skills | google-deepmind/science-skills | 0b42509... | Apache-2.0 (LICENSE) | none | openalex/europepmc sub-skills call external APIs | none evident |
| paperbanana | stuinfla/paperbanana | ce648c6... | Apache-2.0 (LICENSE) | cli_generate.py, demo.py, Dockerfile | unknown (not executed) | unknown (not executed) |
| research_drawio | QIANJINYDX/research-drawio-skill | 8619cb9... | NO LICENSE FILE | none evident | none evident | none evident |
| math_modeling_reference | VectorAC/math-modeling-skill | 734639d... | NO LICENSE FILE | none evident | none evident | none evident |

## 安全纪律

1. 冻结期间未执行任何上游安装/构建/CLI 脚本；只做只读克隆与文件检查。
2. 任何执行（cli_generate.py、skill 安装钩子等）必须先人工审阅代码并在隔离目录运行。
3. 无许可证文件的仓库（research-drawio、math-modeling）：内容只做参考，不并入仓库、不对外分发；如需纳入须先获得作者授权。
4. 有外部 API 调用的能力（openalex 等）：竞赛期间遵守 AGENTS.md 第 6 节网络纪律，只使用赛前冻结缓存。
5. CC BY-NC-SA（Supervisor-Skills）：非商业许可；仅供队伍内部使用，不得公开再分发 skill 文本；论文引用其方法需按许可注明。
6. 克隆仓库存放于 vendor/repos/（gitignored，本地冻结）；UPSTREAM.yaml 元数据入库以便任何机器按 SHA 复现同等冻结。

## 复现冻结

```text
git clone --depth 1 --single-branch <source> vendor/repos/<name>
git -C vendor/repos/<name> checkout <sha>   # 或直接 clone 后 reset 到 UPSTREAM.yaml 记录的 SHA
```
