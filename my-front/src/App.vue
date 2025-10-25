<script setup>
import Sidebar from './components/Sidebar.vue'
import ProjectGrid from './components/ProjectGrid.vue'
import AIChatPanel from './components/AIChatPanel.vue'
import { ref } from 'vue'
const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

// 控制是否显示 AI 面板以及被链接的项目 id
const aiOpen = ref(false)
const linkedProject = ref(null)
const backendOnline = ref(false)

async function checkHealth(){
	try{
		const r = await fetch(`${apiBase}/health`, { cache:'no-store' })
		backendOnline.value = r.ok
	}catch{ backendOnline.value = false }
}

// 简单轮询，开页立即检测
checkHealth()
setInterval(checkHealth, 8000)

function openAIFor(project) {
	linkedProject.value = project
	aiOpen.value = true
}

function closeAI() {
	aiOpen.value = false
	linkedProject.value = null
}

function onThemeChange(color){
  // 可在此同步到应用状态或持久化
  console.debug('Theme color changed to', color)
}

function onLogin(payload){
  // 占位：此处可对接后端登录接口
  console.debug('Login submit', payload)
}
</script>

<template>
	<div id="app" class="min-h-screen" >
		<div class="flex">
			<Sidebar :project="linkedProject" @theme-change="onThemeChange" @login="onLogin" />

			<div class="flex-1 p-6">
				<header class="mb-6">
					<h1 class="text-2xl font-bold">WOOP Management</h1>
					<p class="text-sm text-gray-600 mt-1">项目列表 — 将鼠标悬停以查看详情，右键打开操作菜单</p>
				</header>

				<ProjectGrid :backend-online="backendOnline" @link-ai="openAIFor" />
			</div>

			<AIChatPanel v-if="aiOpen" :project="linkedProject" @close="closeAI" />
		</div>
	</div>
</template>

<style scoped>
/* 基本布局调整与主题背景/前景 */
.min-h-screen { min-height: 100vh }
#app{ background: var(--bg); color: var(--fg) }
</style>
