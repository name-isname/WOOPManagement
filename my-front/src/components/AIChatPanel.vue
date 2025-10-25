<template>
  <aside class="ai-panel border-l p-4" :style="{ width: panelWidth + 'px' }" ref="panelEl">
    <!-- 左侧水平拖拽手柄（紧贴左边缘） -->
    <div class="resize-handle-left" @mousedown="startResizeLeft" aria-label="从左侧拖拽调整面板宽度"></div>
    <div class="flex justify-between items-center mb-3">
      <div class="font-semibold">AI Chat</div>
      <button @click="$emit('close')" class="text-sm text-gray-500">关闭</button>
    </div>

    <div v-if="project" class="mb-3 text-sm text-slate-600">当前项目： <strong>{{ project.name || project.title }}</strong></div>

    <div class="chat-window overflow-auto border rounded p-2 mb-3" :style="{ height: chatHeight + 'px' }" ref="chatEl">
      <!-- 顶部 / 底部垂直拖拽手柄 -->
      <div class="chat-handle chat-handle-top" @mousedown="(e)=>startChatResize('top', e)" aria-label="从上侧拖拽调整聊天框高度"></div>
      <div class="chat-handle chat-handle-bottom" @mousedown="(e)=>startChatResize('bottom', e)" aria-label="从下侧拖拽调整聊天框高度"></div>
      <div v-for="(m,i) in messages" :key="i" class="mb-2">
        <div class="text-xs text-gray-500">{{ m.role }}</div>
        <div class="bubble">{{ m.text }}</div>
      </div>
    </div>

    <div class="flex gap-2">
      <input v-model="input" class="flex-1 border px-2 py-1" @keydown.enter.prevent="send" />
      <button class="send" @click="send">发送</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const props = defineProps({ project: Object })
const emit = defineEmits(['close'])
const input = ref('')
const messages = ref([])

// 面板宽度（持久化）
const panelEl = ref(null)
const panelWidth = ref(Number(localStorage.getItem('aiPanelWidth') || 384))
const minPanelWidth = 280
const maxPanelWidth = 720
let panelResizing = false
let panelStartX = 0
let panelStartW = 0

function startResizeLeft(e){
  panelResizing = true
  panelStartX = e.clientX
  panelStartW = panelEl.value ? panelEl.value.getBoundingClientRect().width : panelWidth.value
  window.addEventListener('mousemove', onDragPanel)
  window.addEventListener('mouseup', stopResizePanel, { once: true })
}

function onDragPanel(e){
  if(!panelResizing) return
  const dx = e.clientX - panelStartX
  // 左侧拖拽：向左拖（dx < 0）应当增大宽度，因此使用 startW - dx
  const next = Math.min(maxPanelWidth, Math.max(minPanelWidth, Math.round(panelStartW - dx)))
  panelWidth.value = next
}

function stopResizePanel(){
  panelResizing = false
  window.removeEventListener('mousemove', onDragPanel)
  try{ localStorage.setItem('aiPanelWidth', String(panelWidth.value)) }catch{}
}

// 聊天窗高度（通过顶部/底部手柄拖拽，持久化保存）
const chatEl = ref(null)
const chatHeight = ref(Number(localStorage.getItem('aiChatHeight') || 256))
let chatResizing = false
let chatStartY = 0
let chatStartH = 0
let chatDir = 'bottom'

function startChatResize(dir, e){
  chatResizing = true
  chatDir = dir
  chatStartY = e.clientY
  chatStartH = chatEl.value ? chatEl.value.getBoundingClientRect().height : chatHeight.value
  window.addEventListener('mousemove', onDragChat)
  window.addEventListener('mouseup', stopChatResize, { once: true })
}

function onDragChat(e){
  if(!chatResizing) return
  const dy = e.clientY - chatStartY
  let next
  if(chatDir === 'bottom'){
    next = chatStartH + dy
  } else { // 'top'
    next = chatStartH - dy
  }
  next = Math.min(Math.round(window.innerHeight * 0.7), Math.max(160, Math.round(next)))
  chatHeight.value = next
}

function stopChatResize(){
  chatResizing = false
  window.removeEventListener('mousemove', onDragChat)
  try{ localStorage.setItem('aiChatHeight', String(chatHeight.value)) }catch{}
}

function syncChatHeight(){
  if(!chatEl.value) return
  const h = Math.round(chatEl.value.getBoundingClientRect().height)
  if(h && h !== chatHeight.value){
    chatHeight.value = h
    try{ localStorage.setItem('aiChatHeight', String(h)) }catch{}
  }
}

onMounted(()=>{})

onBeforeUnmount(()=>{})

watch(()=>props.project, async (v)=>{
  messages.value = []
  if (v) {
    messages.value.push({ role:'system', text:`已链接到项目 ${v.name || v.title}` })
    // 拉取历史记录
    try{
      const name = encodeURIComponent(v.name || v.title)
      const res = await fetch(`${apiBase}/ai/history?project_name=${name}&limit=500`, { cache: 'no-store' })
      if(res.ok){
        const data = await res.json()
        const arr = Array.isArray(data.items) ? data.items : []
        for(const it of arr){
          if(it.role === 'user' || it.role === 'ai' || it.role === 'system'){
            messages.value.push({ role: it.role, text: it.text })
          }
        }
      }
    }catch{}
  } else {
    // 无项目：尝试加载通用会话
    try{
      const res = await fetch(`${apiBase}/ai/history?limit=200`, { cache: 'no-store' })
      if(res.ok){
        const data = await res.json()
        const arr = Array.isArray(data.items) ? data.items : []
        for(const it of arr){
          messages.value.push({ role: it.role, text: it.text })
        }
      }
    }catch{}
  }
})

async function send(){
  // 在发送前同步一次当前高度，避免重渲染导致回退
  syncChatHeight()
  if (!input.value) return
  const prompt = input.value
  messages.value.push({ role:'user', text: prompt })
  input.value = ''

  // 占位消息
  const idx = messages.value.push({ role:'ai', text: '思考中…' }) - 1
  try{
    const body = { prompt, project_name: props.project?.name || props.project?.title || null }
    const res = await fetch(`${apiBase}/ai/chat`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(body) })
    if (!res.ok){
      const txt = await res.text()
      throw new Error(txt || ('Status ' + res.status))
    }
    const data = await res.json()
    messages.value[idx].text = data.text || '[无回复]'
  }catch(err){
    messages.value[idx].text = `出错了：${err?.message || err}`
  }
}
</script>

<style scoped>
  .ai-panel{ background: var(--chat-bg, #fff); color: var(--fg); position: relative; min-width: 280px; max-width: 720px; border-left: 1px solid var(--surface-border) }
  .resize-handle-left{ position:absolute; left:-3px; top:0; width:6px; height:100%; cursor: ew-resize; user-select:none }
  .chat-window{ background: color-mix(in oklab, var(--brand) 6%, var(--surface)); border-color: var(--surface-border); color: var(--fg) }
  .bubble{ padding: 8px; background: color-mix(in oklab, var(--brand) 12%, var(--surface)); border-radius: 8px; white-space: pre-wrap; word-break: break-word; line-height: 1.5; color: var(--fg) }
  .send{ background: var(--brand, #3b82f6); color:#fff; border:none; border-radius:6px; padding:6px 10px; cursor:pointer }
  .send:hover{ filter: brightness(1.05) }
  /* 输入框在暗夜模式下的适配 */
  .ai-panel input{ background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 6px }
  /* 允许用户通过顶部/底部手柄改变聊天窗高度（禁用原生 resize，避免样式被重置） */
  .chat-window{ resize: none; min-height: 160px; max-height: 70vh; position: relative }
  .chat-handle{ position:absolute; left:0; width:100%; height:8px; cursor: ns-resize; user-select:none }
  .chat-handle-top{ top:-4px }
  .chat-handle-bottom{ bottom:-4px }
</style>
