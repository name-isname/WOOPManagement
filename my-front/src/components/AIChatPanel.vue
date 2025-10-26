<template>
  <aside class="ai-panel border-l p-4" :style="{ width: panelWidth + 'px' }" ref="panelEl">
    <!-- 左侧水平拖拽手柄（紧贴左边缘） -->
    <div class="resize-handle-left" @mousedown="startResizeLeft" aria-label="从左侧拖拽调整面板宽度"></div>
    <div class="flex justify-between items-center mb-3">
      <div class="font-semibold">AI Chat</div>
      <button @click="$emit('close')" class="close-btn" aria-label="关闭" title="关闭">×</button>
    </div>

    <div v-if="project" class="mb-3 text-sm text-slate-600">当前项目： <strong>{{ project.name || project.title }}</strong></div>

    <div class="chat-window mb-3" ref="chatEl">
      <div v-for="(m,i) in messages" :key="i" class="msg" :class="m.role">
        <div class="avatar" aria-hidden="true">{{ m.role === 'user' ? '🧑' : (m.role === 'system' ? '⚙️' : '🤖') }}</div>
        <div class="bubble" :class="m.role">
          <template v-for="(seg, si) in parseSegments(m.text)" :key="si">
            <pre v-if="seg.type==='code'" class="code"><code>{{ seg.content }}</code></pre>
            <div v-else class="text" v-html="renderMarkdown(seg.content)"></div>
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
        <span class="hint" v-if="statusMsg">{{ statusMsg }}</span>
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
const sending = ref(false)
const ta = ref(null)
const statusMsg = ref('')
const messages = ref([])
const chatEl = ref(null)

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

// （保留仅侧栏宽度拖拽）

onMounted(()=>{})

onBeforeUnmount(()=>{})

// 加载历史记录
watch(()=>props.project, async (v)=>{
  messages.value = []
  if (v) {
    messages.value.push({ role:'system', text:`已链接到项目 ${v.name || v.title}` })
    try{
      const name = encodeURIComponent(v.name || v.title)
      const res = await fetch(`${apiBase}/ai/history?project_name=${name}&limit=500`, { cache: 'no-store' })
      if(res.ok){
        const data = await res.json()
        const arr = Array.isArray(data.items) ? data.items : []
        for(const it of arr){
          if(it.role === 'user' || it.role === 'ai' || it.role === 'system'){
            const text = it.role === 'user' ? stripProjectPrefix(it.text) : it.text
            messages.value.push({ role: it.role, text })
          }
        }
        await nextTick(); scrollToBottom()
      }
    }catch{}
  } else {
    try{
      const res = await fetch(`${apiBase}/ai/history?limit=200`, { cache: 'no-store' })
      if(res.ok){
        const data = await res.json()
        const arr = Array.isArray(data.items) ? data.items : []
        for(const it of arr){
          const text = it.role === 'user' ? stripProjectPrefix(it.text) : it.text
          messages.value.push({ role: it.role, text })
        }
        await nextTick(); scrollToBottom()
      }
    }catch{}
  }
}, { immediate: true })

async function send(){
  if (!input.value) return
  const prompt = input.value
  input.value = ''
  await nextTick(); autoGrow()
  try{
    sending.value = true
    const body = { prompt, project_name: props.project?.name || props.project?.title || null }
    const res = await fetch(`${apiBase}/ai/chat`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(body) })
    if (!res.ok){
      const txt = await res.text()
      throw new Error(txt || ('Status ' + res.status))
    }
    messages.value.push({ role:'user', text: prompt })
    const data = await res.json()
    messages.value.push({ role:'ai', text: data.text || '[无回复]' })
    await nextTick(); scrollToBottom()
  }catch(err){
    statusMsg.value = `出错：${err?.message || err}`
    setTimeout(()=> statusMsg.value = '', 2000)
  }finally{
    sending.value = false
  }
}

// 文本分段（代码块与普通文本）
function parseSegments(t){
  const out = []
  if(!t) return out
  const parts = String(t).split(/```/g)
  for(let i=0;i<parts.length;i++){
    const content = parts[i]
    if(i % 2 === 1){ out.push({ type:'code', content }) }
    else if(content){ out.push({ type:'text', content }) }
  }
  return out
}

function copy(text){
  try{ navigator.clipboard.writeText(text) }catch{}
}

function renderMarkdown(t){
  if(!t) return ''
  const safe = escapeHtml(String(t))
  const lines = safe.split(/\r?\n/)
  let html = ''
  let inList = false
  for(const raw of lines){
    const line = raw
    const m = /^\s*[-*]\s+(.+)$/.exec(line)
    if(m){
      if(!inList){ html += '<ul>'; inList = true }
      html += `<li>${m[1]}</li>`
    }else if(line.trim()===''){
      if(inList){ html += '</ul>'; inList = false }
      html += '<div class="gap"></div>'
    }else{
      if(inList){ html += '</ul>'; inList = false }
      html += `<p>${line}</p>`
    }
  }
  if(inList){ html += '</ul>' }
  return html
}

function escapeHtml(s){
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// 兼容旧历史：移除开头形如“项目: xxx\n”的前缀，仅用于界面展示
function stripProjectPrefix(s){
  if(!s) return s
  return String(s).replace(/^\s*项目\s*:\s*.*\r?\n/, '')
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

function clearChat(){ messages.value = [] }

async function scrollToBottom(){
  await nextTick()
  if(chatEl.value){ chatEl.value.scrollTop = chatEl.value.scrollHeight }
}

</script>

<style scoped>
  .ai-panel{ background: var(--chat-bg, #fff); color: var(--fg); position: relative; min-width: 280px; max-width: 720px; border-left: 1px solid var(--surface-border); display:flex; flex-direction: column; height: 100vh; overflow: hidden; padding-bottom: 0; box-sizing: border-box }
  .resize-handle-left{ position:absolute; left:-3px; top:0; width:6px; height:100%; cursor: ew-resize; user-select:none }
  /* 聊天区：默认隐藏滚动条，悬停时显示；保持内容可滚动 */
  .chat-window{ background: transparent; border: none; color: var(--fg); flex: 1 1 auto; min-height: 0; overflow: auto; padding: 8px; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; scrollbar-gutter: stable }
  /* 默认隐藏（Firefox/旧版IE Edge） */
  .chat-window{ -ms-overflow-style: none; scrollbar-width: none }
  /* 默认隐藏（Chromium/WebKit） */
  .chat-window::-webkit-scrollbar{ width: 0; height: 0 }
  /* 悬停时显示 */
  .chat-window:hover{ scrollbar-width: thin }
  .chat-window:hover::-webkit-scrollbar{ width: 8px; height: 8px }
  .chat-window:hover::-webkit-scrollbar-track{ background: transparent }
  .chat-window:hover::-webkit-scrollbar-thumb{ background: color-mix(in oklab, var(--surface-border) 80%, #0000); border-radius: 8px }
  .chat-window:hover::-webkit-scrollbar-thumb:hover{ background: color-mix(in oklab, var(--surface-border) 100%, #0000) }
  .msg{ display:flex; gap:10px; align-items:flex-start; padding:8px 6px }
  .msg.user{ flex-direction: row-reverse }
  .avatar{ width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; background: color-mix(in oklab, var(--surface) 70%, #0000001a); border:1px solid var(--surface-border) }
  .bubble{ position:relative; max-width: calc(100% - 48px); padding:10px 16px 10px 12px; border-radius: 12px; white-space: normal; word-break: break-word; line-height: 1.6 }
  .bubble.ai, .bubble.system{ background: color-mix(in oklab, var(--surface) 85%, #00000010); border:1px solid var(--surface-border); color: var(--fg) }
  .bubble.user{ background: color-mix(in oklab, var(--brand) 86%, #ffffff); border:1px solid color-mix(in oklab, var(--brand) 60%, var(--surface-border)); color: #0b1220 }
  .bubble .text{ margin: 0 0 8px 0; white-space: pre-wrap }
  .bubble p{ margin: 6px 0 }
  .bubble ul{ margin: 6px 0 6px 1.2em; padding: 0; list-style: disc }
  .bubble .gap{ height: 6px }
  .bubble .code{ margin: 8px 0; padding:10px; border-radius:8px; background: #0b1220; color:#e6edf3; overflow:auto }
  /* 代码块：默认隐藏，悬停显示（与聊天区一致） */
  .bubble .code{ -ms-overflow-style: none; scrollbar-width: none; -webkit-overflow-scrolling: touch }
  .bubble .code::-webkit-scrollbar{ width: 0; height: 0 }
  .bubble .code:hover{ scrollbar-width: thin }
  .bubble .code:hover::-webkit-scrollbar{ width: 8px; height: 8px }
  .bubble .code:hover::-webkit-scrollbar-thumb{ background: #3b82f655; border-radius: 8px }
  .bubble .code:hover::-webkit-scrollbar-thumb:hover{ background: #3b82f6aa }
  .bubble .copy{ position:absolute; top:-12px; right:8px; opacity:.0; transform: translateY(-2px); transition: opacity .15s ease; background: var(--surface); border:1px solid var(--surface-border); border-radius:8px; padding:2px 6px; cursor:pointer; color: inherit; z-index:2; box-shadow: 0 2px 6px rgba(0,0,0,.08) }
  .bubble:hover .copy{ opacity:.9 }
  .hint{ font-size: 12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8); margin-right: auto; align-self: center }

  /* 输入区固定在底部 */
  .composer{ display:flex; flex-direction: column; gap:8px; margin-top: auto }
  .input{ width:100%; background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 8px; padding:8px 10px; resize: none; line-height:1.5 }
  .actions{ display:flex; gap:8px; justify-content:flex-end }
  .btn{ border:1px solid var(--surface-border); border-radius:8px; padding:6px 12px; cursor:pointer }
  .btn.ghost{ background: transparent; color: var(--fg) }
  .btn.primary{ background: var(--brand, #3b82f6); color:#fff; border-color: transparent }
  .btn:disabled{ opacity:.6; cursor: not-allowed }
  /* 关闭按钮：圆角 + 悬停高亮 */
  .close-btn{ width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; border-radius: 9999px; border: 1px solid var(--surface-border); background: transparent; color: color-mix(in oklab, var(--fg) 80%, #94a3b8); cursor: pointer; transition: background-color .15s ease, border-color .15s ease, transform .08s ease; font-size: 18px; line-height: 1 }
  .close-btn:hover{ background: color-mix(in oklab, var(--surface) 88%, #00000018); border-color: color-mix(in oklab, var(--surface-border) 80%, #00000033) }
  .close-btn:active{ transform: scale(.96) }
  .close-btn:focus-visible{ outline: 2px solid var(--brand, #3b82f6); outline-offset: 2px }
  
</style>
