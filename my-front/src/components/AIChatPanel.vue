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

      <div v-for="(m,i) in messages" :key="i" class="msg" :class="m.role">
        <div class="avatar" aria-hidden="true">{{ m.role === 'user' ? '🧑' : (m.role === 'system' ? '⚙️' : '🤖') }}</div>
        <div class="bubble" :class="m.role">
          <template v-for="(seg, si) in parseSegments(m.text)" :key="si">
            <pre v-if="seg.type==='code'" class="code"><code>{{ seg.content }}</code></pre>
            <p v-else class="text">{{ seg.content }}</p>
          </template>
          <button class="copy" title="复制" @click="copy(m.text)">复制</button>
        </div>
      </div>
    </div>

    <div class="composer">
      <textarea ref="ta" v-model="input" class="input" rows="1" placeholder="说点什么…(Enter 发送，Shift+Enter 换行)"
        @keydown="onKeydown" @input="autoGrow"></textarea>
      <div class="actions">
        <button class="btn ghost" @click="clearChat" :disabled="!messages.length">清空</button>
        <button class="btn primary" @click="send" :disabled="sending || !input.trim()">{{ sending ? '发送中…' : '发送' }}</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const props = defineProps({ project: Object })
const emit = defineEmits(['close'])
const input = ref('')
const messages = ref([])
const sending = ref(false)
const ta = ref(null)

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
  await nextTick(); autoGrow()
  // 占位消息
  const idx = messages.value.push({ role:'ai', text: '思考中…' }) - 1
  try{
    sending.value = true
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
  }finally{
    sending.value = false
  }
}

// 将文本按 ``` 包裹的代码块与普通文本切分
function parseSegments(t){
  const out = []
  if(!t) return out
  const parts = String(t).split(/```/g)
  for(let i=0;i<parts.length;i++){
    const content = parts[i]
    if(i % 2 === 1){
      // 代码段，可能包含首行语言标识，这里仅保留原文
      out.push({ type:'code', content })
    }else if(content){
      out.push({ type:'text', content })
    }
  }
  return out
}

function copy(text){
  try{ navigator.clipboard.writeText(text) }catch{}
}

function onKeydown(e){
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault()
    if(!sending.value) send()
  }
}

function autoGrow(){
  const el = ta.value
  if(!el) return
  el.style.height = 'auto'
  const max = 160
  el.style.height = Math.min(el.scrollHeight, max) + 'px'
}

function clearChat(){
  messages.value = []
}
// 自动滚动到底部
watch(messages, async ()=>{
  await nextTick()
  if(chatEl.value){ chatEl.value.scrollTop = chatEl.value.scrollHeight }
},{ deep:true })

</script>

<style scoped>
  .ai-panel{ background: var(--chat-bg, #fff); color: var(--fg); position: relative; min-width: 280px; max-width: 720px; border-left: 1px solid var(--surface-border) }
  .resize-handle-left{ position:absolute; left:-3px; top:0; width:6px; height:100%; cursor: ew-resize; user-select:none }
  .chat-window{ background: color-mix(in oklab, var(--brand) 6%, var(--surface)); border-color: var(--surface-border); color: var(--fg) }
  /* 对话列表布局：左右气泡 + 头像 */
  .msg{ display:flex; gap:10px; align-items:flex-start; padding:8px 6px }
  .msg.user{ flex-direction: row-reverse }
  .avatar{ width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; background: color-mix(in oklab, var(--surface) 70%, #0000001a); border:1px solid var(--surface-border) }
  .bubble{ position:relative; max-width: calc(100% - 48px); padding:10px 12px; border-radius: 12px; white-space: normal; word-break: break-word; line-height: 1.6 }
  .bubble.ai, .bubble.system{ background: color-mix(in oklab, var(--surface) 85%, #00000010); border:1px solid var(--surface-border); color: var(--fg) }
  .bubble.user{ background: color-mix(in oklab, var(--brand) 86%, #ffffff); border:1px solid color-mix(in oklab, var(--brand) 60%, var(--surface-border)); color: #0b1220 }
  .bubble .text{ margin: 0 0 8px 0; white-space: pre-wrap }
  .bubble .code{ margin: 8px 0; padding:10px; border-radius:8px; background: #0b1220; color:#e6edf3; overflow:auto }
  .bubble .copy{ position:absolute; top:6px; right:6px; opacity:.0; transform: translateY(-2px); transition: opacity .15s ease; background: transparent; border:1px solid var(--surface-border); border-radius:6px; padding:2px 6px; cursor:pointer; color: inherit }
  .bubble:hover .copy{ opacity:.9 }

  .composer{ display:flex; flex-direction: column; gap:8px }
  .input{ width:100%; background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 8px; padding:8px 10px; resize: none; line-height:1.5 }
  .actions{ display:flex; gap:8px; justify-content:flex-end }
  .btn{ border:1px solid var(--surface-border); border-radius:8px; padding:6px 12px; cursor:pointer }
  .btn.ghost{ background: transparent; color: var(--fg) }
  .btn.primary{ background: var(--brand, #3b82f6); color:#fff; border-color: transparent }
  .btn:disabled{ opacity:.6; cursor: not-allowed }
  /* 允许用户通过顶部/底部手柄改变聊天窗高度（禁用原生 resize，避免样式被重置） */
  .chat-window{ resize: none; min-height: 160px; max-height: 70vh; position: relative }
  .chat-handle{ position:absolute; left:0; width:100%; height:8px; cursor: ns-resize; user-select:none }
  .chat-handle-top{ top:-4px }
  .chat-handle-bottom{ bottom:-4px }
</style>
