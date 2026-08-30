# LLM 评测系统

面向「智能客服」和「AI 运营 Agent」的参考实现，覆盖发布前离线质量评测、Promptfoo 红队安全测试、线上稳定 A/B 分流和 Langfuse 私有化可观测。

## 闭环

```text
真实失败样本 ──脱敏/标注──> JSONL 评测集
     ↑                         │
Langfuse trace/score           ├─ DeepEval G-Eval：答案质量
     ↑                         ├─ Ragas：忠实度、回答相关性
用户反馈 <── 在线 A/B <── 发布门禁 ── Promptfoo：注入、隐私、越权、过度代理
```

统一最小数据契约是 `input / actual_output / expected_output / retrieval_context`。客服和运营 Agent 分数据集管理，但使用同一套指标与门禁。

## 快速开始

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
make install
make test
make api
```

服务端点：

- `POST /v1/chat`：按 `user_id` 稳定分配 A/B；响应包含 `variant` 和 `trace_id`。
- `POST /v1/feedback`：写入 `thumbs_up`、`resolved`、`csat` 等 Langfuse score。
- `GET /health`：健康检查。

示例请求：

```bash
curl http://localhost:8000/v1/chat -H 'content-type: application/json' -d '{
  "user_id":"u-1", "session_id":"s-1", "scenario":"customer_service",
  "message":"退款多久到账？", "contexts":["退款审核通过后 3-5 个工作日原路到账。"]
}'
```

## 1. 离线评测

数据位于 `evals/datasets/*.jsonl`。当前样例输出固定，便于先验证评测链；生产中应由候选版本批量生成 `actual_output`，冻结数据集版本和 prompt/model 参数。

```bash
# 可选：先让候选服务生成真实输出
python scripts/generate_candidate.py \
  evals/datasets/customer_service.jsonl \
  /tmp/customer-service-candidate.jsonl

make offline-eval
```

默认三项指标均需达到 `0.75`：

- DeepEval `GEval`：结合期望答案和检索上下文判断正确、完整、简洁、安全边界。
- Ragas `Faithfulness`：答案主张是否能由检索上下文支持。
- Ragas `ResponseRelevancy`：答案是否切题。

结果写入 `evals/results/offline.json`，任一指标未达标进程返回非零，适合作为 CI 发布门禁。LLM judge 会有随机性，正式环境建议同一版本重复评测并保存逐样本结果，关键合规项另加确定性断言。

## 2. Promptfoo 红队

先启动 API，再运行：

```bash
make api
make redteam
```

配置覆盖提示词注入、越狱、PII、合同承诺、任务劫持和 excessive agency；自定义 provider 把攻击请求打到真实 `/v1/chat` 链路。安全门禁应采用「严重漏洞数必须为 0」，不能只看平均分。

## 3. 在线 A/B

`Experiment.assign()` 使用带盐 SHA-256 对 `user_id` 稳定分桶，避免同一用户跨版本串组。Langfuse trace metadata 写入 `experiment / variant / scenario`。

推荐主指标和护栏：

| 场景 | 主指标 | 护栏指标 |
|---|---|---|
| 智能客服 | 问题解决率、CSAT、转人工率 | 幻觉率、P95 延迟、单会话成本、投诉率 |
| 运营 Agent | 任务成功率、节省人工时长 | 未确认外部动作率、回滚率、工具错误率、成本 |

实验先 5% 灰度，再 25%/50%；按用户而非请求分流；提前定义最小可检测提升、样本量和停止规则。不要在显著性出现后临时挑指标。

## 4. Langfuse 私有化

```bash
docker compose -f docker-compose.langfuse.yml config
make langfuse-up
```

访问 `http://localhost:3000`，创建项目密钥后写入 `.env`。Compose 包含 Web、Worker、PostgreSQL、ClickHouse、Redis 和 MinIO，适合本地/验证环境。生产部署必须替换所有密钥，使用 TLS、外部持久卷/备份、网络隔离、SSO/RBAC，并按组织的数据保留策略清理 prompt 与 PII。

## 上线门禁建议

1. 单元测试、lint 通过。
2. 离线三项均值达标，且核心场景逐条通过。
3. Promptfoo 高危/严重风险为 0。
4. 5% 线上灰度期间，安全、错误率、P95 延迟不劣化。
5. 达到预设样本量后才做 A/B 决策；失败 trace 脱敏后回流评测集。
