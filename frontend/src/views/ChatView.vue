<template>
  <section class="main-home">
    <header class="top-strip">
      <div class="brand-mark">
        <div class="brand-symbol">L</div>
        <span>联邦智能</span>
      </div>
      <button class="profile-button" type="button">
        <span class="profile-avatar"></span>
        <span class="chevron"></span>
      </button>
    </header>

    <main class="home-stage">
      <section class="hero-copy">
        <h1>你好，有什么可以帮你？</h1>
        <p>联邦智能，连接知识，驱动未来。</p>
      </section>

      <section class="prompt-panel" aria-label="输入问题">
        <div class="mode-row">
          <button class="mode-pill active" type="button">普通模式</button>
          <button class="mode-pill" type="button">专家模式</button>
        </div>
        <textarea
          id="main-prompt"
          name="main-prompt"
          class="prompt-input"
          placeholder="输入你的问题，或粘贴文件 / 图片..."
          rows="3"
        />
        <div class="prompt-actions">
          <button class="attachment-button" type="button" aria-label="上传附件">
            <span></span>
          </button>
          <button class="send-button" type="button" aria-label="发送">
            <span></span>
          </button>
        </div>
      </section>

      <section class="history-panel">
        <div class="history-title">历史记录</div>
        <button
          v-for="item in historyItems"
          :key="item.title"
          class="history-row"
          type="button"
        >
          <span class="row-icon"></span>
          <span class="row-title">{{ item.title }}</span>
          <span class="row-time">{{ item.time }}</span>
        </button>
        <button class="more-button" type="button">查看更多 <span></span></button>
      </section>
    </main>
  </section>
</template>

<script setup lang="ts">
const historyItems = [
  { title: '撰写一份企业数据安全合规方案', time: '今天 10:32' },
  { title: '解释联邦学习的工作原理', time: '今天 09:18' },
  { title: '帮我优化这段 Python 代码', time: '昨天 16:45' },
  { title: '生成一篇关于人工智能的演讲稿', time: '昨天 14:21' },
  { title: '比较区块链与传统数据库的优劣', time: '昨天 11:07' }
]
</script>

<style scoped>
.main-home {
  min-height: 100%;
  color: #14213d;
  background:
    radial-gradient(circle at 50% 18%, rgba(59, 130, 246, 0.08), transparent 32%),
    linear-gradient(180deg, #fbfdff 0%, #f7faff 100%);
  display: flex;
  flex-direction: column;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.top-strip {
  height: 72px;
  padding: 0 28px;
  border-bottom: 1px solid #e8eef7;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-mark,
.profile-button,
.history-row,
.more-button,
.mode-pill,
.attachment-button,
.send-button {
  border: 0;
  font: inherit;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0;
}

.brand-symbol {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: #ffffff;
  background: linear-gradient(135deg, #2f78ff 0%, #0f56d9 100%);
  box-shadow: 0 10px 28px rgba(47, 120, 255, 0.22);
  font-weight: 800;
}

.profile-button {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  background: transparent;
  cursor: pointer;
}

.profile-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 34%, #f7c8b8 0 17%, transparent 18%),
    linear-gradient(160deg, #17213a 0 42%, #f5f8fc 43% 100%);
  border: 3px solid #ffffff;
  box-shadow: 0 8px 20px rgba(27, 47, 86, 0.14);
}

.chevron,
.more-button span {
  width: 8px;
  height: 8px;
  border-right: 2px solid #476286;
  border-bottom: 2px solid #476286;
  transform: rotate(45deg);
}

.home-stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 118px 28px 64px;
}

.hero-copy {
  text-align: center;
  margin-bottom: 56px;
}

.hero-copy h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.22;
  font-weight: 500;
  color: #16284d;
  letter-spacing: 0;
}

.hero-copy p {
  margin: 16px 0 0;
  font-size: 18px;
  color: #8aa0bd;
  letter-spacing: 0;
}

.prompt-panel {
  width: min(760px, 100%);
  min-height: 176px;
  padding: 20px 22px 22px;
  border: 1px solid #dce7f5;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 18px 60px rgba(31, 78, 141, 0.08);
}

.mode-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.mode-pill {
  height: 36px;
  padding: 0 24px;
  border-radius: 18px;
  color: #5d6f8e;
  background: transparent;
  cursor: pointer;
}

.mode-pill.active {
  color: #1f6fff;
  background: #ffffff;
  border: 1px solid #d7e6ff;
  box-shadow: inset 0 0 0 1px rgba(62, 122, 255, 0.04);
  font-weight: 600;
}

.prompt-input {
  width: 100%;
  height: 70px;
  resize: none;
  border: 0;
  outline: 0;
  background: transparent;
  color: #18325a;
  font-size: 17px;
  line-height: 1.65;
  font-family: inherit;
}

.prompt-input::placeholder {
  color: #9aaac2;
}

.prompt-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.attachment-button {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  position: relative;
}

.attachment-button span {
  position: absolute;
  width: 18px;
  height: 22px;
  left: 10px;
  top: 8px;
  border: 2px solid #7c91b1;
  border-left-color: transparent;
  border-bottom-left-radius: 11px;
  border-top-right-radius: 11px;
  transform: rotate(35deg);
}

.send-button {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82ff 0%, #1e62df 100%);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.28);
  cursor: pointer;
  display: grid;
  place-items: center;
}

.send-button span {
  width: 17px;
  height: 17px;
  clip-path: polygon(0 0, 100% 50%, 0 100%, 20% 54%);
  background: #ffffff;
  transform: translateX(1px);
}

.history-panel {
  width: min(660px, 100%);
  margin-top: 34px;
  padding: 20px 32px 22px;
  border: 1px solid #dce7f5;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 18px 48px rgba(44, 75, 126, 0.06);
}

.history-title {
  font-size: 17px;
  font-weight: 700;
  color: #273b5f;
  padding-bottom: 14px;
  border-bottom: 1px solid #e3eaf4;
}

.history-row {
  width: 100%;
  min-height: 52px;
  display: grid;
  grid-template-columns: 24px 1fr auto;
  align-items: center;
  gap: 18px;
  background: transparent;
  border-bottom: 1px solid #e3eaf4;
  color: #324668;
  cursor: pointer;
}

.row-icon {
  width: 18px;
  height: 16px;
  border: 1.8px solid #8ba0bd;
  border-radius: 5px;
  position: relative;
}

.row-icon::after {
  content: "";
  position: absolute;
  left: 4px;
  bottom: -5px;
  width: 6px;
  height: 6px;
  border-left: 1.8px solid #8ba0bd;
  border-bottom: 1.8px solid #8ba0bd;
  background: #ffffff;
  transform: skewY(-28deg);
}

.row-title {
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-time {
  color: #8095b4;
}

.more-button {
  height: 42px;
  margin: 10px auto 0;
  padding: 0 18px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #2372ff;
  background: transparent;
  cursor: pointer;
}

.more-button span {
  border-color: #2372ff;
  transform: rotate(45deg) translateY(-2px);
}

@media (max-width: 900px) {
  .home-stage {
    padding-top: 72px;
  }

  .hero-copy h1 {
    font-size: 28px;
  }

  .history-panel {
    padding: 18px;
  }
}
</style>
