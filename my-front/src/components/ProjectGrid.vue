<template>
  <section>
    <div class="mb-4 flex justify-between items-center">
      <div class="text-sm text-gray-600">共 {{ total }} 项</div>
      <div class="flex gap-2">
        <button class="bg-green-600 text-white px-3 py-1 rounded disabled:opacity-50 disabled:cursor-not-allowed" @click="showModal = true" :disabled="!backendOnline">创建新项目</button>
        <button class="bg-blue-600 text-white px-3 py-1 rounded" @click="fetchList">刷新</button>
      </div>
    </div>

    <div v-if="!backendOnline" class="mb-4 p-3 rounded border text-sm bg-yellow-50 border-yellow-200 text-yellow-700">
      后端未连接（127.0.0.1:8000）。请先启动后端，再点击“刷新”。
    </div>

    <!-- 列表区域：加载骨架 / 空状态 / 卡片网格 -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <!-- 骨架屏 -->
      <template v-if="loading">
        <div v-for="n in 6" :key="'sk-'+n" class="skeleton" />
      </template>
      <!-- 空状态 -->
      <template v-else-if="!items.length">
        <div class="empty col-span-full">
          <div class="empty-title">还没有项目</div>
          <div class="empty-desc">点击右上角“创建新项目”开始你的第一个 WOOP。</div>
          <button class="btn" @click="showModal=true">创建新项目</button>
        </div>
      </template>
      <!-- 卡片 -->
      <template v-else>
        <div v-for="(item, i) in items" :key="item.id" class="dnd-item" draggable="true"
             @dragstart="onDragStart(i)" @dragover.prevent @drop="onDrop(i)">
          <ProjectCard :item="item" :index="i+1" @link-ai="onLinkAI" @edit="onEdit" @delete="onDelete" @context="onCardContext" />
        </div>
      </template>
    </div>

    <!-- 创建弹窗：与编辑弹窗同步风格 -->
    <div v-if="showModal" class="fixed inset-0 z-50">
      <div class="backdrop" @click="closeCreate"></div>
      <div class="edit-panel" role="dialog" aria-modal="true">
        <div class="edit-header">
          <div>
            <div class="edit-title">创建新项目</div>
            <div class="edit-sub">填写 WOOP 的关键信息</div>
          </div>
          <button class="icon-btn" title="关闭" @click="closeCreate">×</button>
        </div>

        <div class="edit-body">
          <label class="field">
            <span class="label">名称</span>
            <input v-model="form.name" class="input" placeholder="示例：学习" />
          </label>
          <label class="field">
            <span class="label">愿望</span>
            <input v-model="form.wish" class="input" placeholder="我想要…" />
          </label>
          <label class="field">
            <span class="label">障碍</span>
            <input v-model="form.obstacle" class="input" placeholder="我会遇到…" />
          </label>
          <label class="field">
            <span class="label">计划</span>
            <input v-model="form.plan" class="input" placeholder="如果…那么我就…" />
          </label>
          <label class="field">
            <span class="label">结果</span>
            <input v-model="form.outcome" class="input" placeholder="我将达成…" />
          </label>
          <label class="field field-col">
            <span class="label">描述</span>
            <textarea v-model="form.description" class="input" rows="4" placeholder="补充说明（可选）"></textarea>
          </label>
        </div>

        <div class="edit-footer">
          <div class="grow"></div>
          <button class="btn ghost" @click="closeCreate" :disabled="creating">取消</button>
          <button class="btn primary" @click="createProject" :disabled="creating">{{ creating ? '创建中…' : '创建' }}</button>
        </div>
        <div v-if="formError" class="msg-err">{{ formError }}</div>
      </div>
    </div>

    <!-- 编辑弹窗：参考后图的现代卡片风格 -->
    <div v-if="editModal" class="fixed inset-0 z-50">
      <div class="backdrop" @click="closeEdit"></div>
      <div class="edit-panel" role="dialog" aria-modal="true">
        <div class="edit-header">
          <div>
            <div class="edit-title">编辑项目</div>
            <div class="edit-sub">请完善 WOOP 的关键信息</div>
          </div>
          <button class="icon-btn" title="关闭" @click="closeEdit">×</button>
        </div>

        <div class="edit-body">
          <label class="field">
            <span class="label">名称</span>
            <input v-model="editForm.name" class="input" placeholder="示例：学习" />
          </label>
          <label class="field">
            <span class="label">愿望</span>
            <input v-model="editForm.wish" class="input" placeholder="我想要…" />
          </label>
          <label class="field">
            <span class="label">障碍</span>
            <input v-model="editForm.obstacle" class="input" placeholder="我会遇到…" />
          </label>
          <label class="field">
            <span class="label">计划</span>
            <input v-model="editForm.plan" class="input" placeholder="如果…那么我就…" />
          </label>
          <label class="field">
            <span class="label">结果</span>
            <input v-model="editForm.outcome" class="input" placeholder="我将达成…" />
          </label>
          <label class="field field-col">
            <span class="label">描述</span>
            <textarea v-model="editForm.description" class="input" rows="4" placeholder="补充说明（可选）"></textarea>
          </label>
        </div>

        <div class="edit-footer">
          <div class="grow"></div>
          <button class="btn ghost" @click="closeEdit">取消</button>
          <button class="btn primary" @click="updateProject" :disabled="editing">{{ editing ? '保存中…' : '保存' }}</button>
        </div>
        <div v-if="editError" class="msg-err">{{ editError }}</div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="confirmDeleteModal" class="fixed inset-0 flex items-center justify-center bg-black/40 z-50">
      <div class="modal-card rounded shadow p-4 w-96">
        <h3 class="font-semibold mb-2">确认删除</h3>
        <p class="text-sm text-gray-600">确定要删除“{{ toDeleteItem?.name || '该项目' }}”吗？此操作不可撤回。</p>
        <div v-if="deleteError" class="text-red-600 text-sm mt-2">{{ deleteError }}</div>
        <div class="mt-3 flex justify-end gap-2">
          <button class="px-3 py-1 rounded border" @click="confirmDeleteModal=false" :disabled="deleteLoading">取消</button>
          <button class="px-3 py-1 rounded bg-red-600 text-white" @click="doDelete" :disabled="deleteLoading">{{ deleteLoading ? '删除中...' : '删除' }}</button>
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div v-if="menu.visible" :style="menuStyle" class="context-menu shadow p-2 rounded">
      <button class="block px-3 py-1 hover:bg-slate-100 w-full text-left" @click="menuEdit">编辑</button>
      <button class="block px-3 py-1 hover:bg-slate-100 w-full text-left" @click="menuDelete">删除</button>
      <button class="block px-3 py-1 hover:bg-slate-100 w-full text-left" @click="menuLinkAI">链接 AI</button>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
const props = defineProps({ backendOnline: { type: Boolean, default: true } })
import ProjectCard from './ProjectCard.vue'

const emit = defineEmits(['link-ai','backend-online'])

// 优先使用环境变量，默认使用 127.0.0.1 以规避某些代理对 localhost 的拦截
const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const items = ref([])
const total = ref(0)
const loading = ref(false)

const menu = ref({ visible:false, x:0, y:0, item:null })

// delete confirm state
const confirmDeleteModal = ref(false)
const toDeleteItem = ref(null)
const deleteLoading = ref(false)
const deleteError = ref('')

// create modal state
const showModal = ref(false)
const creating = ref(false)
const formError = ref('')
const form = ref({ name:'示例', wish:'', obstacle:'', plan:'', outcome:'', description:'' })

// edit modal state
const editModal = ref(false)
const editing = ref(false)
const editError = ref('')
const editForm = ref({ id:null, name:'', wish:'', obstacle:'', plan:'', outcome:'', description:'' })

function fetchList(){
  loading.value = true
  fetch(`${apiBase}/woops/?page=1&size=50`)
    .then(r=>{
      if(!r.ok) throw new Error('Status ' + r.status)
      return r.json()
    })
    .then(d=>{ items.value = d.items || []; total.value = d.total || items.value.length; emit('backend-online', true) })
    .catch(e=>{ console.error(e); emit('backend-online', false) })
    .finally(()=>{ loading.value = false })
}

function onLinkAI(item){
  emit('link-ai', item)
}

function onEdit(item){
  // 打开编辑弹窗并填充表单
  editForm.value = { id: item.id, name:item.name||'', wish:item.wish||'', obstacle:item.obstacle||'', plan:item.plan||'', outcome:item.outcome||'', description:item.description||'' }
  editError.value = ''
  editModal.value = true
}

function onDelete(item){
  // 使用自定义弹窗确认，兼容某些浏览器或内嵌环境禁用 window.confirm 的情况
  toDeleteItem.value = item
  deleteError.value = ''
  confirmDeleteModal.value = true
}

async function doDelete(){
  if (!toDeleteItem.value) return
  deleteLoading.value = true
  deleteError.value = ''
  try{
    const res = await fetch(`${apiBase}/woops/${toDeleteItem.value.id}`, { method: 'DELETE' })
    if (!res.ok){
      const txt = await res.text()
      deleteError.value = `删除失败: ${txt || ('Status ' + res.status)}`
      return
    }
    confirmDeleteModal.value = false
    toDeleteItem.value = null
    fetchList()
  }catch(err){
    deleteError.value = `网络错误，删除未完成: ${err?.message || err}`
  }finally{
    deleteLoading.value = false
  }
}

function showMenu(e, item){
  e.preventDefault()
  menu.value = { visible:true, x:e.clientX, y:e.clientY, item }
}

function hideMenu(){ menu.value.visible=false }

function menuEdit(){ onEdit(menu.value.item); hideMenu() }
function menuDelete(){ onDelete(menu.value.item); hideMenu() }
function menuLinkAI(){ emit('link-ai', menu.value.item); hideMenu() }

function onCardContext(payload){
  const { originalEvent, item } = payload || {}
  if (originalEvent) showMenu(originalEvent, item)
}

onMounted(()=>{ fetchList(); window.addEventListener('click', hideMenu) })

const menuStyle = computed(()=>({ position:'fixed', left: menu.value.x + 'px', top: menu.value.y + 'px', zIndex:1000 }))

async function createProject(){
  formError.value = ''
  creating.value = true
  try{
    // 基础必填校验，避免 422
    const required = ['name','wish','obstacle','plan','outcome']
    for (const k of required){
      if (!String(form.value[k] ?? '').trim()){
        throw new Error('请填写所有必填字段（名称/愿望/障碍/计划/结果）')
      }
    }
    const res = await fetch(`${apiBase}/woops/`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(form.value) })
    if (!res.ok){
      const txt = await res.text()
      throw new Error(txt || ('Status ' + res.status))
    }
    // success
    showModal.value = false
    form.value = { name:'示例', wish:'', obstacle:'', plan:'', outcome:'', description:'' }
    fetchList()
  }catch(e){
    formError.value = e.message || String(e)
  }finally{ creating.value = false }
}

async function updateProject(){
  editError.value = ''
  editing.value = true
  try{
    const required = ['name','wish','obstacle','plan','outcome']
    for (const k of required){
      if (!String(editForm.value[k] ?? '').trim()){
        throw new Error('请填写所有必填字段（名称/愿望/障碍/计划/结果）')
      }
    }

    const id = editForm.value.id
    // 构造仅包含非空值的更新数据，避免触发最小长度校验
    const payload = {}
    for (const k of ['name','wish','obstacle','plan','outcome','description']){
      const v = editForm.value[k]
      if (v !== undefined && v !== null && String(v).trim() !== ''){
        payload[k] = v
      }
    }

    const res = await fetch(`${apiBase}/woops/${id}`, { method:'PUT', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(payload) })
    if (!res.ok){
      const txt = await res.text()
      throw new Error(txt || ('Status ' + res.status))
    }
    editModal.value = false
    fetchList()
  }catch(e){
    editError.value = e.message || String(e)
  }finally{
    editing.value = false
  }
}

function closeCreate(){ showModal.value = false }
function closeEdit(){ editModal.value = false }

// ===== 拖拽排序 =====
const dragIndex = ref(-1)
function onDragStart(i){ dragIndex.value = i }
function onDrop(i){
  if (dragIndex.value < 0 || dragIndex.value === i) return
  const arr = items.value.slice()
  const [moved] = arr.splice(dragIndex.value, 1)
  arr.splice(i, 0, moved)
  items.value = arr
  dragIndex.value = -1
  persistRanks()
}

async function persistRanks(){
  // 仅对排序发生变化的项提交 rank，rank 从 1 开始
  const updates = []
  for (let i=0;i<items.value.length;i++){
    const it = items.value[i]
    const desired = i + 1
    if (it.rank !== desired){
      updates.push(fetch(`${apiBase}/woops/${it.id}`, { method:'PUT', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ rank: desired }) }))
      it.rank = desired
    }
  }
  if (updates.length){
    try{ await Promise.allSettled(updates) }catch{}
  }
}
</script>

<style scoped>
.context-menu{ min-width:140px }
/* 主题化：模态卡片与输入在暗色/亮色下适配 */
.modal-card{ background: var(--surface); border: 1px solid var(--surface-border) }
.modal-input{ background: transparent; color: var(--fg); border-color: var(--surface-border) }
.context-menu{ background: var(--surface); border: 1px solid var(--surface-border) }
/* 使用响应式 Grid，由最高卡片决定该行高度，其下各行整体下移 */
/* 骨架屏 */
.skeleton{ height: 92px; border-radius: 12px; border:1px solid var(--color-gray-200); background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 37%, #f1f5f9 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite }
@keyframes shimmer{ 0%{ background-position: 100% 0 } 100%{ background-position: -100% 0 } }
/* 空状态 */
.empty{ background:#fff; border:1px dashed var(--color-gray-400); border-radius:12px; padding:28px; text-align:center }
.empty-title{ font-weight:700; font-size:18px; color:#0f172a }
.empty-desc{ color:#475569; font-size:13px; margin-top:6px; margin-bottom:12px }
.btn{ background: var(--brand, #3b82f6); color:#fff; border:none; border-radius:8px; padding:8px 12px; cursor:pointer }
.btn:hover{ filter: brightness(1.05) }
/* 拖拽放置时的轻微提示边框 */
.dnd-item{ border-radius: 12px }
.dnd-item:where([draggable="true"]){ cursor: grab }
.dnd-item:where([draggable="true"]:active){ cursor: grabbing }

/* ===== 编辑弹窗新样式 ===== */
.backdrop{ position: fixed; inset:0; background: rgba(0,0,0,.45); backdrop-filter: blur(2px) }
.edit-panel{ position: fixed; inset: 50% auto auto 50%; transform: translate(-50%, -50%); width: 560px; max-width: 92vw; background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 14px; box-shadow: 0 24px 60px rgba(0,0,0,.2); display:flex; flex-direction: column; max-height: 82vh; min-height: 60vh }
.edit-header{ display:flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--surface-border) }
.edit-title{ font-size: 16px; font-weight: 700 }
.edit-sub{ font-size: 12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8) }
.icon-btn{ width:28px; height:28px; display:flex; align-items:center; justify-content:center; border:1px solid var(--surface-border); border-radius: 8px; background: transparent; cursor: pointer }
.icon-btn:hover{ background: color-mix(in oklab, var(--surface) 70%, #00000010) }
.edit-body{ padding: 14px 16px 28px; display:grid; grid-template-columns: 1fr 1fr; gap: 12px; flex: 1 1 auto; overflow: auto }
.field{ display:flex; flex-direction: column; gap: 6px }
.field-col{ grid-column: 1 / -1; margin-bottom: 12px }
.label{ font-size: 12px; color: color-mix(in oklab, var(--fg) 60%, #94a3b8) }
.input{ background: var(--surface); color: var(--fg); border: 1px solid var(--surface-border); border-radius: 8px; padding: 8px 10px }
.input[type="textarea"], textarea.input{ min-height: 96px }
.input:focus{ outline: none; border-color: color-mix(in oklab, var(--brand) 60%, var(--surface-border)); box-shadow: 0 0 0 3px color-mix(in oklab, var(--brand) 18%, transparent) }
.edit-footer{ display:flex; align-items:center; gap:8px; padding: 12px 16px; border-top: 1px solid var(--surface-border); background: var(--surface); margin-top: auto }
.btn.ghost{ background: transparent; color: var(--fg); border:1px solid var(--surface-border); border-radius:8px; padding: 6px 12px; cursor: pointer }
.btn.primary{ background: var(--brand, #3b82f6); color:#fff; border:none; border-radius:8px; padding: 6px 12px; cursor: pointer }
.btn:disabled{ opacity:.6; cursor:not-allowed }
.msg-err{ color:#ef4444; font-size: 12px; padding: 6px 16px }
</style>
