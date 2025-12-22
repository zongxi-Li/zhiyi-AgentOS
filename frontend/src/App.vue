<template>
  <ErrorBoundary>
    <div id="app">
      <el-container class="app-container">
        <!-- 顶部导航栏 -->
        <el-header class="app-header">
          <div class="header-content">
            <div class="logo">
              <h1>Kinlin AI</h1>
            </div>
            <el-menu
              mode="horizontal"
              :default-active="activeMenu"
              router
              class="header-menu"
            >
              <el-menu-item index="/chat">
                <el-icon><ChatDotRound /></el-icon>
                <span>文本对话</span>
              </el-menu-item>
              <el-menu-item index="/voice">
                <el-icon><Microphone /></el-icon>
                <span>语音对话</span>
              </el-menu-item>
              <el-menu-item index="/roles">
                <el-icon><User /></el-icon>
                <span>角色</span>
              </el-menu-item>
              <el-menu-item index="/rag">
                <el-icon><Search /></el-icon>
                <span>知识库</span>
              </el-menu-item>
              <el-menu-item index="/settings">
                <el-icon><Setting /></el-icon>
                <span>设置</span>
              </el-menu-item>
            </el-menu>
          </div>
        </el-header>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </div>
  </ErrorBoundary>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, User, Setting, Microphone, Search } from '@element-plus/icons-vue'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  height: 100vh;
}

.app-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
  height: 60px !important;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  color: #409eff;
}

.header-menu {
  border-bottom: none;
}

.app-main {
  padding: 0;
  overflow: hidden;
}
</style>
