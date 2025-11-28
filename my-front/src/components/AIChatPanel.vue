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
            <div v-if="seg.type==='think'" class="think-block">
              <details>
                <summary>思考过程</summary>
                <div class="think-content">{{ seg.content }}</div>
              </details>
            </div>
            <div v-else-if="seg.type==='action'" class="action-card">
              <div class="action-title">💡 建议创建项目</div>
              <div class="action-preview">
                <div><strong>名称：</strong>{{ seg.data.name }}</div>
                <div><strong>愿望：</strong>{{ seg.data.wish }}</div>
              </div>
              <button class="btn primary sm" @click="confirmCreate(seg.data)">立即创建</button>
            </div>
            <pre v-else-if="seg.type==='code'" class="code"><code>{{ seg.content }}</code></pre>
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
const emit = defineEmits(['close', 'project-created'])
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

// 文本分段（代码块、思考过程、Action与普通文本）
function parseSegments(t){
  const out = []
  if(!t) return out
  
  // 1. 提取 <think> 块
  const thinkRegex = /<think>([\s\S]*?)<\/think>/g
  let lastIndex = 0
  let match
  const rawSegments = []
  
  while ((match = thinkRegex.exec(t)) !== null) {
    if (match.index > lastIndex) {
      rawSegments.push({ type: 'content', content: t.slice(lastIndex, match.index) })
    }
    rawSegments.push({ type: 'think', content: match[1] })
    lastIndex = thinkRegex.lastIndex
  }
  if (lastIndex < t.length) {
    rawSegments.push({ type: 'content', content: t.slice(lastIndex) })
  }

  // 2. 处理内容中的代码块和 JSON Action
  for (const seg of rawSegments) {
    if (seg.type === 'think') {
      out.push(seg)
    } else {
      const parts = seg.content.split(/```/g)
      for(let i=0; i<parts.length; i++){
        const content = parts[i]
        if(i % 2 === 1){ 
          // 代码块
          let isAction = false
          if (content.trim().startsWith('json')) {
             try {
               const jsonStr = content.replace(/^json\s*/, '')
               if (jsonStr.includes('"action": "create_woop"')) {
                 const data = JSON.parse(jsonStr)
                 if (data.action === 'create_woop') {
                   out.push({ type: 'action', data: data.data, raw: content })
                   isAction = true
                 }
               }
             } catch(e) {}
          }
          if (!isAction) out.push({ type:'code', content }) 
        }
        else if(content){ 
          out.push({ type:'text', content }) 
        }
      }
    }
  }
  return out
}

async function confirmCreate(data){
  if(!confirm(`确认创建项目“${data.name}”吗？`)) return
  try {
    const res = await fetch(`${apiBase}/woops/`, { 
      method:'POST', 
      headers:{ 'Content-Type':'application/json' }, 
      body: JSON.stringify(data) 
    })
    if(res.ok){
      statusMsg.value = '项目创建成功！'
      emit('project-created')
      setTimeout(()=> statusMsg.value='', 3000)
    } else {
      throw new Error('创建失败')
    }
  } catch(e) {
    alert(e.message)
  }
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
  .ai-panel{ background: var(--chat-bg, #fff); color: var(--fg); position: relative; min-width: 280px; max-width: 720px; border-left: 1px solid var(--surface-border); display:flex; flex-direction: column; height: 100%; overflow: hidden; padding-bottom: 0; box-sizing: border-box; /* avatar edge offset (negative moves toward edge) */ --avatar-edge-offset: -8px }
  .resize-handle-left{ position:absolute; left:-3px; top:0; width:6px; height:100%; cursor: ew-resize; user-select:none }
  /* 聊天区：隐藏滚动条但保留滚动功能（跨浏览器） */
  .chat-window{ background: transparent; border: none; color: var(--fg); flex: 1 1 auto; min-height: 0; overflow: auto; padding: 8px; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; scrollbar-gutter: stable }
  /* Firefox / IE */
  .chat-window{ -ms-overflow-style: none; scrollbar-width: none }
  /* Chromium/WebKit */
  .chat-window::-webkit-scrollbar{ width: 0; height: 0 }
  .msg{ display:flex; gap:10px; align-items:flex-start; padding:8px 6px }
  .msg.user{ flex-direction: row-reverse }
  .avatar{ width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; background: color-mix(in oklab, var(--surface) 70%, #0000001a); border:1px solid var(--surface-border) }
  /* 让头像更靠近面板边缘（左侧消息靠左，用户消息靠右）。使用变量便于调整。 */
  .avatar{ margin-left: var(--avatar-edge-offset) }
  .msg.user .avatar{ margin-left: 0; margin-right: var(--avatar-edge-offset) }
  .bubble{ position:relative; max-width: calc(100% - 48px); padding:10px 16px 10px 12px; border-radius: 12px; white-space: normal; word-break: break-word; line-height: 1.6 }
  .bubble.ai, .bubble.system{ background: color-mix(in oklab, var(--surface) 85%, #00000010); border:1px solid var(--surface-border); color: var(--fg) }
  .bubble.user{ background: color-mix(in oklab, var(--brand) 86%, #ffffff); border:1px solid color-mix(in oklab, var(--brand) 60%, var(--surface-border)); color: #0b1220 }
  .bubble .text{ margin: 0 0 8px 0; white-space: pre-wrap }
  .bubble p{ margin: 6px 0 }
  .bubble ul{ margin: 6px 0 6px 1.2em; padding: 0; list-style: disc }
  .bubble .gap{ height: 6px }
  .bubble .code{ margin: 8px 0; padding:10px; border-radius:8px; background: #0b1220; color:#e6edf3; overflow:auto }
  /* 代码块：隐藏滚动条但允许横向/纵向滚动（保留用户滚动体验） */
  .bubble .code{ -ms-overflow-style: none; scrollbar-width: none; -webkit-overflow-scrolling: touch; overflow: auto }
  .bubble .code::-webkit-scrollbar{ width: 0; height: 0 }
  .bubble .copy{ position:absolute; top:-12px; right:8px; opacity:.0; transform: translateY(-2px); transition: opacity .15s ease; background: var(--surface); border:1px solid var(--surface-border); border-radius:8px; padding:2px 6px; cursor:pointer; color: inherit; z-index:2; box-shadow: 0 2px 6px rgba(0,0,0,.08) }
  .bubble:hover .copy{ opacity:.9 }
  .hint{ font-size: 12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8); margin-right: auto; align-self: center }

  /* 输入区固定在底部 */
  .composer{ display:flex; flex-direction: column; gap:10px; margin-top: auto; background: var(--surface); padding: 16px; border-top: 1px solid var(--surface-border); }
  .input{ width:100%; background: #f8fafc; color: var(--fg); border: 1px solid var(--surface-border); border-radius: 12px; padding:12px 14px; resize: none; line-height:1.5; transition: all .2s; box-shadow: inset 0 1px 2px rgba(0,0,0,0.03); }
  .input:focus { background: #fff; border-color: var(--brand, #3b82f6); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15); outline: none; }
  /* 隐藏输入框滚动条但保留滚动（当达到最大高度时用户仍可滚动） */
  .input{ overflow: auto; -ms-overflow-style: none; scrollbar-width: none }
  .input::-webkit-scrollbar{ width: 0; height: 0 }
  .actions{ display:flex; gap:10px; justify-content:flex-end; align-items: center; }
  .btn{ border:1px solid var(--surface-border); border-radius:8px; padding:8px 16px; cursor:pointer; font-weight: 500; transition: all .15s; }
  .btn.ghost{ background: transparent; color: #64748b; border-color: transparent; }
  .btn.ghost:hover { background: #f1f5f9; color: #334155; }
  .btn.primary{ background: var(--brand, #3b82f6); color:#fff; border-color: transparent; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.25); }
  .btn.primary:hover { filter: brightness(1.08); box-shadow: 0 4px 8px rgba(59, 130, 246, 0.35); transform: translateY(-1px); }
  .btn:disabled{ opacity:.6; cursor: not-allowed; transform: none !important; box-shadow: none !important; }
  /* 关闭按钮：圆角 + 悬停高亮 */
  .close-btn{ width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; border-radius: 9999px; border: 1px solid var(--surface-border); background: transparent; color: color-mix(in oklab, var(--fg) 80%, #94a3b8); cursor: pointer; transition: background-color .15s ease, border-color .15s ease, transform .08s ease; font-size: 18px; line-height: 1 }
  .close-btn:hover{ background: color-mix(in oklab, var(--surface) 88%, #00000018); border-color: color-mix(in oklab, var(--surface-border) 80%, #00000033) }
  .close-btn:active{ transform: scale(.96) }
  .close-btn:focus-visible{ outline: 2px solid var(--brand, #3b82f6); outline-offset: 2px }
  
  /* 思考过程样式 */
  .think-block { margin: 8px 0; font-size: 0.85em; color: #64748b; background: #f8fafc; border-radius: 8px; padding: 8px 12px; border: 1px solid #e2e8f0; }
  .think-block summary { cursor: pointer; user-select: none; font-weight: 600; opacity: 0.8; display: flex; align-items: center; gap: 6px; color: #475569; }
  .think-block summary:hover { opacity: 1; color: #3b82f6; }
  .think-block summary::before { content: '💭'; font-size: 1.1em; }
  .think-content { margin-top: 8px; white-space: pre-wrap; line-height: 1.6; color: #475569; padding-left: 4px; border-left: 2px solid #cbd5e1; margin-left: 4px; }

  /* Action Card 样式 */
  .action-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin: 12px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: all .2s; position: relative; overflow: hidden; }
  .action-card::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background: linear-gradient(to bottom, #3b82f6, #8b5cf6); }
  .action-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
  .action-title { font-weight: 700; color: #1e293b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; font-size: 1.05em; }
  .action-preview { font-size: 0.95em; color: #475569; margin-bottom: 16px; display: grid; gap: 8px; background: #f8fafc; padding: 12px; border-radius: 8px; }
  .btn.sm { padding: 6px 14px; font-size: 13px; font-weight: 500; border-radius: 6px; }
</style>
