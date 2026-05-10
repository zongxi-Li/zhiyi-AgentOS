<template>
  <section class="contract-planner">
    <header class="planner-header">
      <div class="title-block">
        <span class="crumb">联邦智能 / 法律顾问 / 合同起草</span>
        <h1>软件开发合同起草 - 关键条款骨架</h1>
      </div>
      <div class="header-actions">
        <button type="button">共享</button>
        <button type="button">版本</button>
        <button class="primary" type="button">保存草案</button>
      </div>
    </header>

    <div class="planner-grid">
      <aside class="left-column">
        <section class="panel domain-panel">
          <div class="panel-head">
            <h2>职业领域</h2>
            <span>专业树</span>
          </div>
          <div class="domain-tree">
            <div class="tree-group">
              <button class="tree-parent expanded" type="button">
                <span></span>
                法律
              </button>
              <div class="tree-children">
                <button type="button">民商事</button>
                <button class="active" type="button">合同法务</button>
                <button type="button">公司法务</button>
                <button type="button">知识产权</button>
                <button type="button">劳动法务</button>
              </div>
            </div>
            <div class="tree-group muted">
              <button class="tree-parent" type="button">
                <span></span>
                技术
              </button>
              <button class="tree-parent" type="button">
                <span></span>
                财务
              </button>
              <button class="tree-parent" type="button">
                <span></span>
                运营
              </button>
            </div>
          </div>
        </section>

        <section class="panel skill-panel">
          <div class="panel-head">
            <h2>嫁接技能</h2>
            <span>已启用 4 项</span>
          </div>
          <div class="skill-list">
            <div v-for="skill in attachedSkills" :key="skill.name">
              <span class="skill-icon" :class="skill.tone">{{ skill.short }}</span>
              <div>
                <strong>{{ skill.name }}</strong>
                <small>{{ skill.desc }}</small>
              </div>
            </div>
          </div>
        </section>

        <section class="panel pool-panel">
          <div class="panel-head">
            <h2>通用技能池</h2>
            <button type="button">全部</button>
          </div>
          <div class="pool-tags">
            <span v-for="tag in poolTags" :key="tag">{{ tag }}</span>
          </div>
        </section>

        <section class="panel config-panel">
          <div class="panel-head">
            <h2>当前配置</h2>
          </div>
          <dl>
            <div>
              <dt>专业体</dt>
              <dd>法律顾问</dd>
            </div>
            <div>
              <dt>任务类型</dt>
              <dd>合同起草</dd>
            </div>
            <div>
              <dt>知识范围</dt>
              <dd>民法典合同编、软件开发案例库</dd>
            </div>
            <div>
              <dt>输出风格</dt>
              <dd>严谨版 + 客户友好版</dd>
            </div>
          </dl>
        </section>
      </aside>

      <main class="center-column">
        <section class="panel map-panel">
          <div class="map-toolbar">
            <nav class="map-tabs">
              <button class="active" type="button">思维树</button>
              <button type="button">时间线</button>
              <button type="button">对比视图</button>
            </nav>
            <div class="zoom-tools">
              <button type="button">-</button>
              <span>100%</span>
              <button type="button">+</button>
            </div>
          </div>

          <div class="mind-map" aria-label="合同起草思维树">
            <svg class="map-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <path d="M50 16 C50 23 28 21 28 28" />
              <path d="M50 16 C50 23 50 23 50 30" />
              <path d="M50 36 C50 44 32 43 32 51" />
              <path d="M50 36 C50 44 68 43 68 51" />
              <path d="M32 57 C38 65 45 63 50 70" />
              <path d="M68 57 C62 65 55 63 50 70" />
              <path d="M50 76 C50 81 50 83 50 88" />
            </svg>

            <article
              v-for="node in mindNodes"
              :key="node.id"
              class="mind-node"
              :class="[node.tone, { active: node.active }]"
              :style="{ left: node.x + '%', top: node.y + '%' }"
            >
              <div class="confidence">{{ node.confidence }}</div>
              <strong>{{ node.title }}</strong>
              <span>{{ node.desc }}</span>
            </article>

            <div class="mini-map">
              <span></span>
              <span></span>
              <span class="active"></span>
            </div>
          </div>
        </section>

        <section class="panel inspector-panel">
          <div class="inspector-tabs">
            <button class="active" type="button">节点详情</button>
            <button type="button">思考过程</button>
            <button type="button">引用资料</button>
            <button type="button">备选方案</button>
          </div>
          <div class="node-detail">
            <div class="detail-title">
              <span class="node-number">03</span>
              <div>
                <h2>法律适用选择</h2>
                <p>结合项目性质，将本任务定位为软件开发服务合同，优先适用民法典合同编、著作权法及数据安全相关条款。</p>
              </div>
              <span class="detail-status">高置信</span>
            </div>
            <div class="evidence-grid">
              <article v-for="item in evidenceItems" :key="item.title">
                <strong>{{ item.title }}</strong>
                <p>{{ item.desc }}</p>
              </article>
            </div>
          </div>
        </section>

        <section class="panel command-panel">
          <span class="add-icon">+</span>
          <input
            id="contract-command"
            name="contract-command"
            value="请将知识产权、验收标准、违约责任展开为可直接放入合同的条款"
            readonly
            aria-label="补充指令"
          />
          <button type="button">生成</button>
        </section>
      </main>

      <aside class="right-column">
        <section class="panel assistant-panel">
          <div class="panel-head">
            <h2>数字人助手</h2>
            <span class="online-dot">在线</span>
          </div>
          <div class="assistant-card">
            <div class="assistant-avatar-stage">
              <DigitalHuman
                v-if="digitalHumanRoleId"
                :role-id="digitalHumanRoleId"
                :style="'realistic'"
                transparent
              />
              <div v-else class="digital-human-preparing">正在连接数字人...</div>
            </div>
            <strong>{{ digitalHumanRoleName }} - 张明</strong>
            <p>已定位合同核心风险：交付验收边界、需求变更成本、源代码权属与保密责任。</p>
          </div>
          <button class="voice-button" type="button">播放讲解</button>
        </section>

        <section class="panel context-panel">
          <div class="panel-head">
            <h2>当前上下文</h2>
            <span>已锁定</span>
          </div>
          <div class="context-list">
            <div v-for="item in contextItems" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </section>

        <section class="panel reference-panel">
          <div class="panel-head">
            <h2>推荐资料</h2>
            <span>相关度</span>
          </div>
          <div class="reference-list">
            <article v-for="ref in references" :key="ref.title">
              <div>
                <strong>{{ ref.title }}</strong>
                <p>{{ ref.source }}</p>
              </div>
              <em>{{ ref.score }}</em>
            </article>
          </div>
        </section>

        <section class="panel suggestion-panel">
          <div class="panel-head">
            <h2>下一步建议</h2>
          </div>
          <ol>
            <li>确认付款节点是否与交付验收绑定。</li>
            <li>补充需求变更的审批与报价机制。</li>
            <li>明确源代码、部署文档、接口文档交付清单。</li>
          </ol>
        </section>
      </aside>
    </div>

    <footer class="status-footer">
      <span>联邦节点：北京 · 上海 · 深圳</span>
      <span>知识版本：law-contract-2026.05</span>
      <span>自动保存：10:34:22</span>
      <span>当前页面仅展示前端静态效果</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import DigitalHuman from '@/components/DigitalHuman.vue'
import { useDigitalHumanRole } from '@/composables/useDigitalHumanRole'

const { digitalHumanRoleId, digitalHumanRoleName } = useDigitalHumanRole()

const attachedSkills = [
  { short: '法', name: '法规检索', desc: '定位民法典、著作权与数据安全条款', tone: 'blue' },
  { short: '审', name: '风险审查', desc: '识别责任边界与异常履约风险', tone: 'orange' },
  { short: '写', name: '条款生成', desc: '生成可编辑合同文本', tone: 'green' },
  { short: '比', name: '版本对比', desc: '并列输出专业版与友好版', tone: 'purple' }
]

const poolTags = ['摘要生成', '问答检索', '表格提取', '引用校验', '格式排版', '合同归档', '术语解释', '风险评级']

const mindNodes = [
  { id: 'task', title: '任务理解', desc: '软件开发合同起草', confidence: '98%', x: 50, y: 12, tone: 'root', active: false },
  { id: 'keyword', title: '关键词提取', desc: '软件开发、验收、交付', confidence: '94%', x: 28, y: 30, tone: 'blue', active: false },
  { id: 'law', title: '法律适用选择', desc: '民法典合同编 + 著作权法', confidence: '92%', x: 50, y: 32, tone: 'orange', active: true },
  { id: 'lawyer', title: '骨架生成（律师视角）', desc: '强调责任、证据与违约', confidence: '89%', x: 32, y: 53, tone: 'green', active: false },
  { id: 'client', title: '骨架生成（客户友好版）', desc: '强调可读性与交付清单', confidence: '87%', x: 68, y: 53, tone: 'green', active: false },
  { id: 'merge', title: '对比与合并', desc: '合并差异条款与语气', confidence: '84%', x: 50, y: 72, tone: 'blue', active: false },
  { id: 'final', title: '最终版本生成', desc: '输出正式合同草案', confidence: '待执行', x: 50, y: 90, tone: 'muted', active: false }
]

const evidenceItems = [
  { title: '合同性质', desc: '开发服务与成果交付并存，需要同时覆盖服务过程、验收和成果权属。' },
  { title: '核心条款', desc: '付款节点、验收标准、知识产权、保密义务、违约责任为主干结构。' },
  { title: '输出策略', desc: '先生成关键条款骨架，再由风险审查节点补充边界条件与例外情形。' }
]

const contextItems = [
  { label: '甲方角色', value: '委托开发方' },
  { label: '乙方角色', value: '软件服务供应商' },
  { label: '项目周期', value: '3 个月' },
  { label: '交付方式', value: '源码 + 部署文档 + 测试报告' },
  { label: '当前焦点', value: '关键条款骨架' }
]

const references = [
  { title: '民法典合同编相关条款', source: '国家法律法规数据库', score: '98%' },
  { title: '计算机软件著作权登记办法', source: '知识产权专题库', score: '93%' },
  { title: '软件开发合同争议裁判摘要', source: '案例库 · 近三年', score: '88%' },
  { title: '企业数据处理安全约定模板', source: '企业合规模板库', score: '84%' }
]
</script>

<style scoped>
.contract-planner {
  min-height: 100%;
  padding: 20px;
  box-sizing: border-box;
  color: #17233c;
  background: #f4f8fd;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

button {
  font: inherit;
}

.planner-header {
  min-height: 72px;
  padding: 14px 18px;
  border: 1px solid #dce7f3;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: 0 14px 36px rgba(35, 77, 128, 0.06);
}

.crumb {
  display: block;
  margin-bottom: 5px;
  color: #2b72ec;
  font-size: 12px;
  font-weight: 700;
}

.title-block h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.25;
  letter-spacing: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.header-actions button,
.panel-head button,
.zoom-tools button,
.command-panel button,
.voice-button {
  border: 1px solid #bdd2ef;
  border-radius: 7px;
  background: #ffffff;
  color: #1f65d7;
  cursor: pointer;
}

.header-actions button {
  height: 36px;
  padding: 0 14px;
}

.header-actions .primary,
.command-panel button,
.voice-button {
  border-color: transparent;
  color: #ffffff;
  background: linear-gradient(135deg, #2d7ff9, #1d5fd8);
}

.planner-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: minmax(240px, 270px) minmax(0, 1fr) minmax(260px, 300px);
  gap: 16px;
  align-items: start;
}

.left-column,
.right-column,
.center-column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel {
  border: 1px solid #dce7f3;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 30px rgba(36, 74, 121, 0.05);
}

.panel-head {
  padding: 14px 16px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.panel-head h2 {
  margin: 0;
  color: #1a2d4d;
  font-size: 15px;
}

.panel-head span,
.panel-head button {
  font-size: 12px;
}

.panel-head span {
  color: #7a8aa2;
}

.panel-head button {
  padding: 5px 10px;
}

.domain-tree {
  padding: 0 12px 14px;
}

.tree-parent,
.tree-children button {
  width: 100%;
  min-height: 34px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #405572;
  text-align: left;
  cursor: pointer;
}

.tree-parent {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.tree-parent span {
  width: 8px;
  height: 8px;
  border-right: 2px solid #6d7f98;
  border-bottom: 2px solid #6d7f98;
  transform: rotate(-45deg);
}

.tree-parent.expanded span {
  transform: rotate(45deg) translateY(-2px);
}

.tree-children {
  margin: 2px 0 8px 18px;
  padding-left: 12px;
  border-left: 1px solid #dce7f3;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.tree-children button {
  padding-left: 12px;
}

.tree-children button.active {
  color: #1d5fd8;
  background: #eef5ff;
  font-weight: 700;
}

.tree-group.muted {
  border-top: 1px solid #edf2f8;
  padding-top: 8px;
}

.skill-list {
  padding: 0 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.skill-list > div {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  align-items: center;
  padding: 10px;
  border: 1px solid #e4edf7;
  border-radius: 8px;
  background: #f9fbfe;
}

.skill-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: #ffffff;
  font-weight: 800;
}

.skill-icon.blue {
  background: #2d7ff9;
}

.skill-icon.orange {
  background: #f59e0b;
}

.skill-icon.green {
  background: #10b981;
}

.skill-icon.purple {
  background: #8b5cf6;
}

.skill-list strong {
  display: block;
  color: #1b2e4c;
  font-size: 13px;
}

.skill-list small {
  display: block;
  margin-top: 3px;
  color: #70819b;
  font-size: 12px;
}

.pool-tags {
  padding: 0 12px 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pool-tags span {
  padding: 7px 9px;
  border-radius: 7px;
  background: #eef5ff;
  border: 1px solid #dbe9ff;
  color: #236be8;
  font-size: 12px;
}

.config-panel dl {
  margin: 0;
  padding: 0 14px 14px;
}

.config-panel div {
  padding: 10px 0;
  border-top: 1px solid #edf2f8;
}

.config-panel dt {
  color: #7a8aa2;
  font-size: 12px;
}

.config-panel dd {
  margin: 5px 0 0;
  color: #1c3152;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.45;
}

.map-panel {
  padding: 16px;
}

.map-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.map-tabs {
  display: flex;
  gap: 6px;
  padding: 4px;
  border-radius: 8px;
  background: #eef4fb;
  min-width: 0;
  overflow-x: auto;
}

.map-tabs button {
  border: 0;
  border-radius: 6px;
  padding: 8px 12px;
  background: transparent;
  color: #60718c;
  white-space: nowrap;
  cursor: pointer;
}

.map-tabs button.active {
  color: #195ee4;
  background: #ffffff;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(30, 90, 180, 0.1);
}

.zoom-tools {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #60718c;
  font-size: 12px;
}

.zoom-tools button {
  width: 30px;
  height: 30px;
}

.mind-map {
  position: relative;
  height: 540px;
  margin-top: 16px;
  border-radius: 8px;
  overflow: hidden;
  background:
    linear-gradient(#edf3fb 1px, transparent 1px),
    linear-gradient(90deg, #edf3fb 1px, transparent 1px),
    #fbfdff;
  background-size: 28px 28px;
  border: 1px solid #dfeaf6;
}

.map-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.map-lines path {
  fill: none;
  stroke: #a9bdd7;
  stroke-width: 0.42;
  stroke-linecap: round;
}

.mind-node {
  position: absolute;
  width: 184px;
  min-height: 86px;
  padding: 12px 12px 12px 14px;
  border-radius: 8px;
  transform: translate(-50%, -50%);
  border: 1px solid #dce7f3;
  background: #ffffff;
  box-shadow: 0 12px 28px rgba(36, 74, 121, 0.08);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 40px;
  grid-template-areas:
    "title confidence"
    "desc desc";
  column-gap: 8px;
  row-gap: 7px;
}

.mind-node.active {
  border-color: #f1b15c;
  background: #fff8ed;
  box-shadow: 0 14px 32px rgba(245, 158, 11, 0.16);
}

.mind-node.root {
  border-color: #a9c8ff;
  background: #eef5ff;
}

.mind-node.green {
  border-color: #bbebd3;
  background: #f0fbf6;
}

.mind-node.blue {
  border-color: #bed8ff;
}

.mind-node.muted {
  color: #79889c;
  background: #f7f9fc;
}

.confidence {
  grid-area: confidence;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #1d5fd8;
  background: conic-gradient(#2d7ff9 0 78%, #dbeafe 78% 100%);
  font-size: 11px;
  font-weight: 800;
}

.mind-node.active .confidence {
  color: #b45309;
  background: conic-gradient(#f59e0b 0 72%, #ffedd5 72% 100%);
}

.mind-node strong {
  grid-area: title;
  display: block;
  color: #1a2d4d;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.mind-node span {
  grid-area: desc;
  display: block;
  color: #667790;
  font-size: 12px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.mini-map {
  position: absolute;
  right: 16px;
  bottom: 16px;
  width: 116px;
  height: 78px;
  border-radius: 8px;
  border: 1px solid #dce7f3;
  background: rgba(255, 255, 255, 0.88);
}

.mini-map span {
  position: absolute;
  width: 18px;
  height: 12px;
  border-radius: 4px;
  background: #c7d7ea;
}

.mini-map span:nth-child(1) {
  left: 18px;
  top: 18px;
}

.mini-map span:nth-child(2) {
  left: 48px;
  top: 34px;
}

.mini-map span:nth-child(3) {
  left: 78px;
  top: 48px;
}

.mini-map span.active {
  background: #f59e0b;
}

.inspector-panel {
  padding: 16px;
}

.inspector-tabs {
  display: flex;
  gap: 6px;
  padding: 4px;
  border-radius: 8px;
  background: #eef4fb;
  width: fit-content;
  max-width: 100%;
  overflow-x: auto;
}

.inspector-tabs button {
  border: 0;
  border-radius: 6px;
  padding: 8px 12px;
  background: transparent;
  color: #60718c;
  white-space: nowrap;
  cursor: pointer;
}

.inspector-tabs button.active {
  color: #195ee4;
  background: #ffffff;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(30, 90, 180, 0.1);
}

.node-detail {
  margin-top: 14px;
}

.detail-title {
  display: grid;
  grid-template-columns: 46px 1fr auto;
  gap: 12px;
  align-items: start;
}

.node-number {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #b45309;
  background: #ffedd5;
  font-weight: 800;
}

.detail-title h2 {
  margin: 0;
  color: #1a2d4d;
  font-size: 17px;
}

.detail-title p {
  margin: 7px 0 0;
  color: #64758f;
  font-size: 13px;
  line-height: 1.6;
}

.detail-status {
  padding: 6px 10px;
  border-radius: 14px;
  color: #047857;
  background: #d1fae5;
  font-size: 12px;
  font-weight: 700;
}

.evidence-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.evidence-grid article {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e4edf8;
  background: #f7faff;
}

.evidence-grid strong {
  color: #1b2e4c;
  font-size: 13px;
}

.evidence-grid p {
  margin: 7px 0 0;
  color: #64758f;
  font-size: 12px;
  line-height: 1.5;
}

.command-panel {
  padding: 10px;
  display: grid;
  grid-template-columns: 36px 1fr 82px;
  align-items: center;
  gap: 10px;
}

.add-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #eef5ff;
  color: #236be8;
  display: grid;
  place-items: center;
  font-size: 22px;
}

.command-panel input {
  height: 38px;
  border: 0;
  outline: 0;
  color: #1e314f;
  background: transparent;
  font-size: 14px;
}

.command-panel button {
  height: 38px;
}

.assistant-panel {
  padding-bottom: 16px;
}

.assistant-card {
  margin: 0 14px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e3edf8;
  background: #f7faff;
  text-align: center;
}

.assistant-avatar-stage {
  width: 100%;
  height: 178px;
  margin: 0 auto 12px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #dbeafe;
  background: linear-gradient(180deg, #f8fbff, #eef5ff);
}

.assistant-avatar-stage :deep(.digital-human-container) {
  border-radius: 8px;
  background: transparent;
}

.assistant-avatar-stage :deep(.loading-overlay),
.assistant-avatar-stage :deep(.error-overlay),
.assistant-avatar-stage :deep(.empty-overlay) {
  background: rgba(247, 250, 255, 0.82);
  backdrop-filter: blur(4px);
}

.digital-human-preparing {
  height: 100%;
  display: grid;
  place-items: center;
  color: #667790;
  font-size: 13px;
}

.assistant-card strong {
  color: #1a2d4d;
}

.assistant-card p {
  margin: 8px 0 0;
  color: #667790;
  font-size: 13px;
  line-height: 1.6;
}

.online-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.online-dot::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16a34a;
}

.voice-button {
  width: calc(100% - 28px);
  height: 38px;
  margin: 12px 14px 0;
}

.context-list {
  padding: 0 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.context-list div {
  padding: 10px 0;
  border-top: 1px solid #edf2f8;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.context-list span {
  color: #7a8aa2;
  font-size: 12px;
}

.context-list strong {
  color: #1c3152;
  font-size: 13px;
  text-align: right;
}

.reference-list {
  padding: 0 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reference-list article {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  padding: 11px;
  border-radius: 8px;
  border: 1px solid #e3edf8;
  background: #f7faff;
}

.reference-list strong {
  color: #1b2e4c;
  font-size: 13px;
}

.reference-list p {
  margin: 5px 0 0;
  color: #70819b;
  font-size: 12px;
}

.reference-list em {
  font-style: normal;
  color: #236be8;
  font-size: 12px;
  font-weight: 800;
}

.suggestion-panel ol {
  margin: 0;
  padding: 0 16px 16px 34px;
  color: #445974;
  font-size: 13px;
  line-height: 1.8;
}

.status-footer {
  margin-top: 16px;
  padding: 10px 14px;
  border: 1px solid #dce7f3;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  color: #6f8098;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
}

@media (max-width: 1540px) {
  .planner-grid {
    grid-template-columns: 260px minmax(560px, 1fr);
  }

  .right-column {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1320px) {
  .planner-grid {
    grid-template-columns: 250px minmax(0, 1fr);
  }
}

@media (max-width: 1060px) {
  .planner-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .planner-grid {
    grid-template-columns: 1fr;
  }

  .left-column,
  .right-column {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }

  .evidence-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .contract-planner {
    padding: 12px;
  }

  .left-column,
  .right-column {
    grid-template-columns: 1fr;
  }

  .mind-map {
    height: auto;
    padding: 14px;
    display: grid;
    gap: 12px;
    overflow: visible;
  }

  .map-lines,
  .mini-map {
    display: none;
  }

  .mind-node {
    position: relative;
    left: auto !important;
    top: auto !important;
    width: auto;
    min-height: 0;
    transform: none;
  }

  .map-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .detail-title,
  .command-panel {
    grid-template-columns: 1fr;
  }
}
</style>
