---
name: github-weekly-report
description: >
  从 GitHub issues 和 PR 生成结构化中文周报。
  当用户要求生成周报、工作进展总结、冲刺回顾或团队活动摘要时使用此技能。
  触发词包括："生成周报"、"项目进展"、"工作报告"、"weekly report"、"sprint 总结"，
  或任何需要汇总某团队在一组仓库中 GitHub 活动的请求。
---

# GitHub 周报生成技能

通过读取 GitHub issues 和 PR，将活动映射到具名团队成员，生成结构化中文周报。

---

## 前置输入（执行前确认）

开始前，确认以下信息已就绪。未指定时使用下方默认配置，用户可覆盖。

### 主线仓库（默认）
```
https://github.com/co-agent-serving/meta-sprint
```

### 相关仓库（默认）
- `https://github.com/hw-native-sys` 组织下所有仓库
- `https://github.com/LL-mixed/ub_sim`
- `https://github.com/xwhu/pypto_workspace/tree/main/rust_llm_server`
- `https://github.com/co-agent-serving` 组织下所有仓库

### 团队成员名单（默认）

| 姓名 | GitHub ID |
|---|---|
| 王成照 | zhaozhaozz |
| 吴治锋 | wuzhf9 |
| 黎亮 | LL-mixed |
| 段诗锦 | sjduan |
| 杨耀东 | high-cloud |
| 刘旭 | ndleslx |
| 郑左贺 | bumble0918 |
| 方竟志 | puddingfjz |
| 陈神爱 | hashiqiqixian |
| 靳宗泉 | vegetabledoww |
| 赵敏 | zmnobug |
| 黄卓 | sunghajung6688 |
| 许峰 | superxf |
| 王明哲 | asanrocks |
| 胡欣蔚 | xwhu |

### 时间范围（默认）
最近 **7 天**，用户可自定义。

---

> 如有任何输入项与默认值不同，请在开始前向用户确认。

---

## 第一阶段：数据收集

### 步骤 1.1 · 读取主线工作项

对主线仓库中每个 open issue：
- 读取 **issue 正文** 和 **所有评论**
- 提取：当前状态、阻塞点、近期决策
- 记录正文或评论中提到的关联 issue 和 PR

### 步骤 1.2 · 在相关仓库中查找关联活动

在每个相关仓库中，检索**时间范围内有更新**且满足以下任一条件的 issue 和 PR：
- 被某个主线 issue 引用（通过 URL、`#编号` 或关键词匹配），**或**
- 作者或 assignee 属于团队成员

收集字段：标题、URL、状态（open/merged/closed）、作者、assignees、participants、关联 issue。

### 步骤 1.3 · 递归解析每个工作项的责任人

对每个主线 issue，按以下方式递归收集参与人员：

```
初始集合 = {主线 issue 的 author 和 assignees 和 participants}
扩展 = 对每个关联 issue/PR → 添加其 {author 和 assignees 和 participants} 到集合中
重复，直到没有新的 issue/PR 为止
```

然后对每个人进行分类：
- **在团队名单中** → 使用其中文姓名
- **不在名单中** → 标注为 `（协同人 @github-id）`

按相关度排序：直接 assignee > 关联 PR 作者 > 关联 issue 作者。

---

## 第二阶段：识别成员其他工作项

成员其他工作项 = 团队成员参与的 issue/PR，**但其内容与任何主线工作项无直接关联**。

### 数据收集方式

对每位团队成员，使用以下两种搜索确保覆盖：

1. **`author:{成员}` 搜索**：捕获成员作为作者提交的 issue/PR
2. **`involves:{成员}` 搜索**：捕获成员作为 commenter、reviewer 或被 @mention 参与的 issue/PR

> `involves:` 搜索可能返回大量结果，需人工判断参与深度：
> 有实质 review 评论（非仅 bot 评论）→ 纳入；仅点赞/轻微表态 → 忽略。

### 过滤规则

1. 保留 `author`、`assignee` 或实质性 commenter/reviewer 在团队名单中的条目。
2. 排除已作为第一部分某工作项核心内容的条目。
3. 按团队成员姓名分组。
4. 描述中注明参与角色（如"review [PR#xxx]"、"参与 [issue#xxx]"）。

---

## 第三阶段：生成 Markdown 草稿供用户确认

### 步骤 3.1 · 生成本地 MD 文件

将报告输出为 Markdown 文件，保存到本地，文件名格式为 `weekly-report-{YYYY-MM-DD}.md`。

MD 文件模板：

```markdown
# Serving Agent 周报
{开始日期} ~ {结束日期}

---

## 一、Serving Agent 工作项

### {工作项名称} · [{仓库+编号}]({issue链接})

- **进展（{进度}%）**：{以事件为主语，约50字，不出现人名，issue/PR 用 [仓+编号](url) 格式}
- **下一步计划**：{建议，不出现人名}
- **责任人**：{姓名A @github-id · 姓名B @github-id · （协同人 @github-id）}

### {工作项N+1} ...

---

## 二、成员其他工作项

- **{姓名A}**：{简要描述，issue/PR 用 [仓+编号](url) 格式}
- **{姓名B}**：{简要描述}
```

### 步骤 3.2 · 提示用户确认

文件生成后，告知用户：

> 周报草稿已生成：`docs/report/weekly-report-{YYYY-MM-DD}.md`
> 请用 VS Code 打开查看，修改完成后回复"确认"，或告知需要调整的内容。
> 确认后可选择是否发送到飞书群。

等待用户回复，根据反馈修改内容后重新输出文件，直到用户确认。

---

## 第四阶段：发送到飞书群（用户确认后按需执行）

用户确认 MD 内容无误后，询问：

> 是否需要发送到飞书群？如需发送，请提供飞书群机器人 Webhook URL。

用户确认发送后，将 MD 内容改写为飞书卡片 JSON 并发送。

### 卡片结构

```
┌─────────────────────────────────────┐
│  📋 Serving Agent 周报               │
│  {开始日期} ~ {结束日期}             │
├─────────────────────────────────────┤
│  一、工作项（每项一个分组）           │
│  ┌─────────────────────────────┐    │
│  │ 🔵 工作项名称  [进度%]       │    │
│  │ 进展：约50字描述             │    │
│  │ 下一步：建议                 │    │
│  │ 责任人：姓名A · 姓名B        │    │
│  └─────────────────────────────┘    │
├─────────────────────────────────────┤
│  二、成员其他工作项                  │
└─────────────────────────────────────┘
```

### 卡片 JSON 模板

```json
{
  "msg_type": "interactive",
  "card": {
    "config": { "wide_screen_mode": true },
    "header": {
      "title": { "tag": "plain_text", "content": "📋 Serving Agent 周报" },
      "subtitle": { "tag": "plain_text", "content": "{开始日期} ~ {结束日期}" },
      "template": "blue"
    },
    "elements": [
      {
        "tag": "div",
        "text": { "tag": "lark_md", "content": "**一、Serving Agent 工作项**" }
      },
      { "tag": "hr" },
      {
        "tag": "div",
        "fields": [
          {
            "is_short": false,
            "text": {
              "tag": "lark_md",
              "content": "**🔵 {工作项名称}** · [{仓库+编号}]({issue链接})　`{进度}%`\n**进展：**{约50字，不出现人名}\n**下一步：**{计划，不出现人名}\n**责任人：**{姓名A · 姓名B · （协同人 @id）}"
            }
          }
        ]
      },
      { "tag": "hr" },
      {
        "tag": "div",
        "text": { "tag": "lark_md", "content": "**二、成员其他工作项**" }
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**{姓名A}：**{简要描述}\n**{姓名B}：**{简要描述}\n**{姓名C}、{姓名D}：**本周在相关仓库中无可见 issue/PR 活动"
        }
      }
    ]
  }
}
```

### 发送命令

```bash
curl -X POST "{飞书群机器人 Webhook URL}" \
  -H "Content-Type: application/json" \
  -d '{卡片 JSON}'
```

---

### 写作规范

| 规范 | 说明 |
|---|---|
| **一句话进展长度** | 进展由**约 50 字文字描述** + **紧跟的 issue/PR 链接**组成，50 字仅指文字部分 |
| **issue/PR 引用格式** | MD 文件用标准 Markdown `[仓+编号](url)`；飞书卡片用 `lark_md` 同格式 |
| **PR 链接位置** | PR/issue 链接必须紧跟在对应的进展分句后面，而非堆砌在进展行末尾 |
| **进展行不出现人名** | 一句话进展和下一步计划中均不得出现任何人名 |
| **事件为主语** | 进展句子以事件/系统/功能为主语，而非以人为主语 |
| **进度百分比** | 根据 issue 状态、评论时效和关联 PR 合并情况综合估算 |
| **协同人标注** | 不在名单中的人员标注为 `（协同人 @github-id）`，多人合并：`（协同人 @id1 · @id2 · @id3）` |
| **第二部分去重** | 若某成员的工作已作为第一部分某工作项的核心内容，则不再出现在第二部分 |
| **无活动成员** | 在第二部分末尾合并为一行列出 |

---

## 判断参考

### 何时标注为"协同人"

只要某人的 github-id **不在团队名单中**，无论贡献多重要，一律标注为协同人。

### 进度百分比估算

| 信号 | 判断 |
|---|---|
| 所有关联 PR 已合并，issue 已关闭 | ~100% |
| 大部分 PR 已合并，issue 仍开启 | 70–90% |
| 有活跃 PR 正在 review | 40–70% |
| issue 活跃但无已合并 PR | 10–40% |
| 时间范围内无任何活动 | 维持上次已知进度不变 |

### 第一部分与第二部分的边界

- **第一部分**：工作内容与某个主线 issue 目标直接相关。
- **第二部分**：团队成员参与，但工作内容与所有主线 issue 目标无直接关联（如独立修 bug、外部贡献、未纳入冲刺的工具性工作）。

如果难以判断，优先归入第一部分，放在最相关的工作项下。