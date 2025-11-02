<template>
  <div class="landing">
    <header class="top-bar">
      <div class="brand" @click="triggerChat">
        <span class="logo">🥘</span>
        <div class="text">
          <h1>GustoBot</h1>
          <p>智能菜谱知识助理</p>
        </div>
      </div>
      <nav class="nav-links">
        <a href="#features">功能亮点</a>
        <a href="#workflow">工作流程</a>
        <a href="#datasets">数据源</a>
        <a href="#faq">常见问题</a>
      </nav>
      <button class="cta" type="button" @click="triggerChat">立即对话</button>
    </header>

    <main class="content">
      <section class="hero">
        <div class="headline">
          <div class="headline-badge">
            <span class="spark">✨</span>
            多源知识 · 智能检索 · 实时引用
          </div>
          <h2>全天候 <span>菜谱顾问</span>，懂典故更懂食材</h2>
          <p>
            接入菜谱历史、典故、原料知识、文件解析等能力，结合智能路由与 rerank 机制，秒级返回可信、有据可查的答案。
          </p>
          <div class="hero-actions">
            <button class="primary" type="button" @click="triggerChat">开始新对话</button>
            <button class="secondary" type="button" @click="triggerChat">上传资料试试</button>
          </div>
          <ul class="hero-meta">
            <li>
              <div class="icon-circle">📚</div>
              <div>
                <span class="value">8+</span>
                <span class="label">结构化数据表</span>
              </div>
            </li>
            <li>
              <div class="icon-circle">🧠</div>
              <div>
                <span class="value">39</span>
                <span class="label">Milvus 向量篇章</span>
              </div>
            </li>
            <li>
              <div class="icon-circle">🛠️</div>
              <div>
                <span class="value">5</span>
                <span class="label">智能路由工具</span>
              </div>
            </li>
          </ul>
        </div>
        <div class="hero-card">
          <div class="card-header">
            <span class="badge">知识库工作流</span>
            <span class="status online">Postgres · 正常</span>
          </div>
          <div class="card-body">
            <article class="sample">
              <h3><span>📌</span> 示例问题</h3>
              <ul>
                <li>佛跳墙的历史典故是什么？</li>
                <li>青蒜和蒜苗有哪些营养差异？</li>
                <li>总结上传文档中的菜谱亮点。</li>
              </ul>
            </article>
            <div class="divider"></div>
            <article class="pipeline">
              <h3><span>🧭</span> 当前路由</h3>
              <ol>
                <li><span class="step">1</span> Router 分类：kb-query</li>
                <li><span class="step">2</span> Postgres 相似检索</li>
                <li><span class="step">3</span> Rerank 精排 & 引用生成</li>
              </ol>
            </article>
          </div>
          <footer class="card-footer">
            <span>🔄 自动兜底：Milvus · Rerank ≥ 0.8</span>
            <span>📎 支持文件问答、图谱检索</span>
          </footer>
        </div>
      </section>

      <section id="features" class="feature-grid">
        <article class="feature-card">
          <div class="feature-icon">🧠</div>
          <h3>多路由智能体</h3>
          <p>自动选择知识库、图谱、文件解析、Text2SQL 等工具，回答准确高效。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">📑</div>
          <h3>可信引用</h3>
          <p>回答附带来源 documentId、score，方便复核与追踪。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">⚡</div>
          <h3>快速接入</h3>
          <p>REST API、文件上传、LLM 提示词一体化，轻松融入业务场景。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🧩</div>
          <h3>弹性扩展</h3>
          <p>Docker Compose 一键部署，自动导入 Excel、Milvus、pgvector 数据。</p>
        </article>
      </section>

      <section id="workflow" class="workflow">
        <h3>知识库工作流</h3>
        <div class="timeline">
          <div class="node">
            <span class="dot"></span>
            <div>
              <h4>查询分类</h4>
              <p>Router 结合 LLM + 关键词启发，判断是 KB / Graph / Text2SQL / 文件处理。</p>
            </div>
          </div>
          <div class="node">
            <span class="dot"></span>
            <div>
              <h4>Postgres 优先</h4>
              <p>pgvector 采用相似度 ≥ 0.5 且 rerank ≥ 0.8，命中后直接返回结果。</p>
            </div>
          </div>
          <div class="node">
            <span class="dot"></span>
            <div>
              <h4>Milvus 兜底</h4>
              <p>降阈值粗召回，rerank ≥ 0.8 方可呈现，保证覆盖率与准确度兼顾。</p>
            </div>
          </div>
        </div>
      </section>

      <section id="datasets" class="datasets">
        <h3>数据源概览</h3>
        <ul>
          <li><strong>PostgreSQL：</strong> Excel 导入的历史菜谱表、searchable_documents（8 条结构化数据）。</li>
          <li><strong>Milvus：</strong> data.txt 切片向量（39 篇），支持 rerank 精排。</li>
          <li><strong>Neo4j：</strong> 19,655 个菜品节点 + 188,338 条步骤关系，支撑图谱问答。</li>
        </ul>
      </section>

      <section id="faq" class="faq">
        <h3>常见问题</h3>
        <details>
          <summary>如何接入我的业务系统？</summary>
          <p>通过 `/api/v1/chat` 与 `/api/v1/upload/file` 完成对话、文件问答接入，支持 session 管理。</p>
        </details>
        <details>
          <summary>知识库数据多久更新一次？</summary>
          <p>Excel / data.txt 改动后重新构建容器即可自动导入，也可以运行脚本手动刷新。</p>
        </details>
        <details>
          <summary>是否支持图谱、Text2SQL 等自定义工具？</summary>
          <p>Router 预置 GraphRAG、Text2SQL、文件解析等工具，可根据业务需求扩展。</p>
        </details>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{ (e: "start-chat"): void }>();

function triggerChat() {
  emit("start-chat");
}
</script>

<style scoped lang="scss">
.landing {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff7ed 0%, #fff 55%);
  color: #3f3d56;
  padding-bottom: 120px;
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 6vw;
  background: rgba(255, 247, 237, 0.88);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(249, 115, 22, 0.15);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;

  .logo {
    font-size: 32px;
  }

  .text {
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      color: #ea580c;
    }

    p {
      margin: 0;
      font-size: 13px;
      color: #f97316;
      opacity: 0.85;
    }
  }
}

.nav-links {
  display: flex;
  gap: 18px;
  font-size: 14px;

  a {
    color: #9a3412;
    text-decoration: none;
    font-weight: 600;
    position: relative;

    &:after {
      content: "";
      position: absolute;
      left: 0;
      bottom: -6px;
      width: 100%;
      height: 2px;
      background: linear-gradient(135deg, #f97316, #ef4444);
      transform: scaleX(0);
      transform-origin: left;
      transition: transform 0.2s ease;
    }

    &:hover:after {
      transform: scaleX(1);
    }
  }
}

.cta {
  border: none;
  border-radius: 999px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #f97316, #ef4444);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 12px 24px rgba(239, 68, 68, 0.25);
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }
}

.content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 60px 6vw 0;
  display: flex;
  flex-direction: column;
  gap: 72px;
}

.hero {
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  align-items: stretch;
}

.headline {
  display: flex;
  flex-direction: column;
  gap: 24px;

  .headline-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(249, 115, 22, 0.15);
    color: #b45309;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;

    .spark {
      font-size: 14px;
    }
  }

  h2 {
    margin: 0;
    font-size: clamp(28px, 3.2vw, 42px);
    font-weight: 700;
    color: #1f2937;

    span {
      color: #ea580c;
    }
  }

  p {
    margin: 0;
    font-size: 15px;
    line-height: 1.7;
    color: #4b5563;
  }
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;

  button {
    border: none;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
  }

  .primary {
    background: linear-gradient(135deg, #f97316, #ef4444);
    color: #fff;
    box-shadow: 0 14px 24px rgba(239, 68, 68, 0.25);
  }

  .secondary {
    background: #fff;
    color: #f97316;
    border: 1px solid rgba(249, 115, 22, 0.3);
  }
}

.hero-meta {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  list-style: none;
  margin: 0;
  padding: 0;

  li {
    background: rgba(255, 247, 237, 0.82);
    border: 1px solid rgba(249, 115, 22, 0.2);
    border-radius: 12px;
    padding: 12px 16px;
    min-width: 140px;
    display: flex;
    align-items: center;
    gap: 10px;

    .icon-circle {
      width: 38px;
      height: 38px;
      border-radius: 14px;
      background: rgba(249, 115, 22, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: #b45309;
    }

    .value {
      font-size: 22px;
      font-weight: 700;
      color: #ea580c;
    }

    .label {
      display: block;
      font-size: 12px;
      color: #9a3412;
    }
  }
}

.hero-card {
  background: radial-gradient(circle at top, rgba(255, 255, 255, 0.92), #fff8f1 60%);
  border-radius: 20px;
  border: 1px solid rgba(249, 115, 22, 0.25);
  box-shadow: 0 24px 48px rgba(249, 115, 22, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.1), rgba(239, 68, 68, 0.1));
  color: #9a3412;
  font-weight: 600;

  .badge {
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(249, 115, 22, 0.15);
  }

  .status {
    font-size: 12px;

    &.online::before {
      content: "";
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #22c55e;
      margin-right: 6px;
      box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.15);
    }
  }
}

.card-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sample,
.pipeline {
  h3 {
    margin: 0 0 10px;
    font-size: 14px;
    color: #9a3412;

    span {
      margin-right: 6px;
    }
  }

  ul,
  ol {
    margin: 0;
    padding-left: 20px;
    font-size: 13px;
    color: #4b5563;
    line-height: 1.6;
  }

  .step {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(249, 115, 22, 0.2);
    color: #9a3412;
    font-size: 11px;
    margin-right: 6px;
  }
}

.divider {
  height: 1px;
  background: rgba(249, 115, 22, 0.25);
}

.card-footer {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #9a3412;
  background: rgba(249, 115, 22, 0.1);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.feature-card {
  padding: 20px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgba(249, 115, 22, 0.2);
  box-shadow: 0 18px 36px rgba(249, 115, 22, 0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;

  .feature-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: rgba(249, 115, 22, 0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: #b45309;
  }

  h3 {
    margin: 0 0 8px;
    font-size: 16px;
    color: #9a3412;
  }

  p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: #4b5563;
  }
}

.workflow {
  background: #fffdfb;
  border-radius: 20px;
  border: 1px solid rgba(249, 115, 22, 0.2);
  box-shadow: 0 18px 42px rgba(249, 115, 22, 0.1);
  padding: 28px;

  h3 {
    margin: 0 0 18px;
    font-size: 18px;
    color: #9a3412;
  }
}

.timeline {
  display: grid;
  gap: 18px;
}

.node {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: flex-start;
  color: #4b5563;

  .dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: radial-gradient(circle at center, #f97316 0%, #ef4444 70%);
    box-shadow: 0 0 0 6px rgba(249, 115, 22, 0.15);
    margin-top: 6px;
  }

  h4 {
    margin: 0 0 6px;
    font-size: 15px;
    color: #9a3412;
  }

  p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
  }
}

.datasets {
  background: #fff;
  border-radius: 20px;
  padding: 26px;
  border: 1px solid rgba(249, 115, 22, 0.18);
  box-shadow: 0 16px 36px rgba(249, 115, 22, 0.08);

  h3 {
    margin: 0 0 12px;
    font-size: 18px;
    color: #9a3412;
  }

  ul {
    margin: 0;
    padding-left: 20px;
    color: #4b5563;
    line-height: 1.7;
  }
}

.faq {
  background: #fffdfb;
  border-radius: 20px;
  border: 1px solid rgba(249, 115, 22, 0.18);
  box-shadow: 0 14px 32px rgba(249, 115, 22, 0.08);
  padding: 24px;
  display: grid;
  gap: 12px;

  h3 {
    margin: 0;
    font-size: 18px;
    color: #9a3412;
  }

  details {
    background: rgba(255, 247, 237, 0.6);
    border: 1px solid rgba(249, 115, 22, 0.18);
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 13px;
    color: #4b5563;

    summary {
      cursor: pointer;
      font-weight: 600;
      color: #9a3412;
    }

    p {
      margin: 8px 0 0;
      line-height: 1.6;
    }
  }
}

@media (max-width: 768px) {
  .top-bar {
    flex-wrap: wrap;
    gap: 16px;
  }

  .nav-links {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
    gap: 12px;
  }

  .cta {
    width: 100%;
  }

  .hero-card {
    order: -1;
  }
}
</style>
